"""The web server for the three screens: standard library only (no framework to install), so `make run` works the same on Windows and Linux.

    GET  /                         the page (static/index.html)
    GET  /api/meta                 what this machine can do (is Tesseract there?), and the screen names
    GET  /api/samples              the files in the bill inbox, for the picker
    POST /api/intake               a dropped file (raw body, X-Filename header) or ?sample=<file>: the stored reading, checked, as one card
    POST /api/intake/live          the same file read live by the reader (only when Tesseract is found)
    POST /api/intake/review        values a clerk typed for fields that were not read ({key, values}): the checks run again and the result is saved to parsed_bill as human_review
    GET  /api/control?cutoff=1     the control tower
    GET  /api/impact               the backtest ranges

It listens on 127.0.0.1 only. Nothing leaves the machine: messages are composed and shown, never sent, and there is no network call.
"""
from __future__ import annotations

import json
import mimetypes
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import data

STATIC = Path(__file__).resolve().parent / "static"
MAX_BODY = 40 * 1024 * 1024


def make_handler(S: data.State):
    class Handler(BaseHTTPRequestHandler):
        server_version = "RiklrIntake"

        def log_message(self, *a):  # quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code: int = 200):
            self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"))

        def _wait(self) -> bool:
            S.ready.wait(timeout=60)
            if S.error:
                self._json(dict(error=f"The register could not be loaded: {S.error}"), 500)
                return False
            return True

        def do_GET(self):
            u = urlparse(self.path)
            q = parse_qs(u.query)
            try:
                if u.path == "/api/meta":
                    return self._json(dict(tesseract=data.tesseract_found(), screens=["Intake", "Control tower", "Impact"]))
                if u.path == "/api/samples":
                    return self._json(data.samples(S))
                if u.path == "/api/control":
                    if not self._wait():
                        return
                    cutoff = int(q.get("cutoff", [data.DEFAULT_CUTOFF_DAYS])[0])
                    return self._json(data.control(S, cutoff if cutoff in (0, 1, 2) else data.DEFAULT_CUTOFF_DAYS))
                if u.path == "/api/impact":
                    if not self._wait():
                        return
                    return self._json(data.impact(S))
                path = STATIC / ("index.html" if u.path in ("/", "") else u.path.lstrip("/"))
                path = path.resolve()
                if STATIC.resolve() in path.parents or path == STATIC.resolve():
                    if path.is_file():
                        return self._send(200, path.read_bytes(), (mimetypes.guess_type(str(path))[0] or "application/octet-stream") + "; charset=utf-8")
                return self._send(404, b"Not found", "text/plain; charset=utf-8")
            except Exception as e:  # noqa: BLE001 - the page shows the message instead of failing silently
                return self._json(dict(error=f"{type(e).__name__}: {e}"), 500)

        def do_POST(self):
            u = urlparse(self.path)
            q = parse_qs(u.query)
            try:
                if u.path not in ("/api/intake", "/api/intake/live", "/api/intake/review"):
                    return self._send(404, b"Not found", "text/plain; charset=utf-8")
                if not self._wait():
                    return
                n = int(self.headers.get("Content-Length") or 0)
                if n > MAX_BODY:
                    return self._json(dict(error="That file is too large."), 413)
                body = self.rfile.read(n) if n else b""
                if u.path == "/api/intake/review":
                    req = json.loads(body.decode("utf-8") or "{}")
                    try:
                        return self._json(data.apply_review(S, req.get("key"), req.get("values") or {}))
                    except ValueError as e:
                        return self._json(dict(error=str(e)), 400)
                name = q.get("sample", [None])[0] or self.headers.get("X-Filename") or "upload"
                t = time.time()
                if u.path == "/api/intake/live":
                    if not data.tesseract_found():
                        return self._json(dict(error="Tesseract is not installed on this machine, so the live reader is not available."), 400)
                    if not body and name in S.by_name:
                        body = (data.pipeline.INBOX / name).read_bytes()
                    res = data.live_read(S, name, body)
                    return self._json(data.card(S, res, "live", replay=False, ms=(time.time() - t) * 1000))
                res = data.stored_for(S, name if not body else None, body or None)
                if res is None:
                    return self._json(dict(file=name, no_stored=True, tesseract=data.tesseract_found(), reading_label=data.reading_label(S, "stored"),
                                           message="There is no stored reading for this file. It is not one of the bills the reader has already read."))
                return self._json(data.card(S, res, "stored", replay=True, ms=(time.time() - t) * 1000))
            except Exception as e:  # noqa: BLE001
                return self._json(dict(error=f"{type(e).__name__}: {e}"), 500)

    return Handler


def serve(host: str = "127.0.0.1", port: int | None = None, open_browser: bool = False) -> None:
    port = port or int(os.environ.get("RIKLR_PORT", "8765"))
    S = data.State().start()
    httpd = ThreadingHTTPServer((host, port), make_handler(S))
    url = f"http://{host}:{port}/"
    print(f"Riklr intake is running at {url}  (Ctrl+C to stop)", flush=True)
    print("Tesseract found: " + ("yes, the live reader is available" if data.tesseract_found() else "no, the app uses the stored readings"), flush=True)
    if open_browser:
        import webbrowser

        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        httpd.server_close()
