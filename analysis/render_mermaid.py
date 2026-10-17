"""Render notes/workflows/swimlane.mmd to notes/workflows/swimlane.svg.

No Node or Mermaid CLI is installed here, so Mermaid runs in a browser. This script serves a small local page (localhost only), the page
renders the diagram with Mermaid (pinned version, loaded from the jsDelivr CDN) and posts the SVG back to this script, which writes it
next to the source and exits.

Run:  .venv\\Scripts\\python.exe -I analysis\\render_mermaid.py
then open http://localhost:8765/render.html in any browser. The page closes the loop by itself; the script prints 'saved' and stops.
Nothing leaves the machine except the CDN download of the Mermaid library by the browser.
"""
import http.server
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MMD = ROOT / "notes" / "workflows" / "swimlane.mmd"
SVG = ROOT / "notes" / "workflows" / "swimlane.svg"
PORT = 8765
MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.esm.min.mjs"

PAGE = f"""<!doctype html><meta charset="utf-8"><title>render</title>
<body style="font-family:sans-serif"><p id="s">rendering...</p><div id="out"></div>
<script type="module">
import mermaid from "{MERMAID}";
mermaid.initialize({{startOnLoad:false, theme:"default", themeVariables:{{noteBkgColor:"#fff7d6", noteTextColor:"#222222", noteBorderColor:"#d9c46a", actorBkg:"#eef3fb", actorBorder:"#7a8fb5", fontSize:"15px"}}, securityLevel:"strict", fontFamily:"Segoe UI, Arial, sans-serif",
  sequence:{{useMaxWidth:false, wrap:true, width:200, height:46, actorMargin:20, messageMargin:28, noteMargin:12, boxMargin:8, mirrorActors:true, messageAlign:"left", noteAlign:"left"}}}});
try {{
  const src = await (await fetch("/swimlane.mmd")).text();
  const {{svg}} = await mermaid.render("swimlane", src);
  document.getElementById("out").innerHTML = svg;
  const r = await fetch("/save", {{method:"POST", body:svg}});
  document.getElementById("s").textContent = "saved " + svg.length + " chars: " + (await r.text());
}} catch (e) {{
  document.getElementById("s").textContent = "ERROR " + e;
  await fetch("/error", {{method:"POST", body:String(e)}});
}}
</script>"""


class H(http.server.BaseHTTPRequestHandler):
    def _send(self, body, ctype="text/html; charset=utf-8", code=200):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/render.html"):
            self._send(PAGE)
        elif self.path.startswith("/swimlane.mmd"):
            self._send(MMD.read_text(encoding="utf-8"), "text/plain; charset=utf-8")
        else:
            self._send("not found", code=404)

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8")
        if self.path == "/save":
            if "<svg" not in body[:400]:
                self._send("not an svg", code=400)
                return
            if "xmlns=" not in body[:400]:
                body = body.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
            SVG.write_text(body, encoding="utf-8", newline="\n")
            self._send("ok")
            print(f"saved {SVG} ({len(body)} chars)", flush=True)
        else:
            self._send("ok")
            print("render error:", body, flush=True)
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H)
    print(f"open http://localhost:{PORT}/render.html", flush=True)
    try:
        webbrowser.open(f"http://localhost:{PORT}/render.html")
    except Exception:
        pass
    srv.serve_forever()
