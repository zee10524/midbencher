"""A second reader for the cross-check: a vision model (Gemini) that extracts the same fields as the Tesseract reader. It never decides pass or fail.

OFF by default. It runs only when `GEMINI_API_KEY` is set, in the environment or in a `.env` file at the project root (`.env` is git-ignored; `.env.example`, with a blank value,
is committed). The key is read, sent in a request header and nothing else: it is never printed, logged, put in a URL or written to the cache.

Every response is cached as JSON under `data/cache/vision/<file name>.json`, and that cache is meant to be committed, so the app, the analysis and the tests run with no key and
no network. `stored(name)` reads the cache only; the app never calls the model. To fill the cache (one call per bill, sends the bill image to Google):

    python -m app.reader.vision --all          # all 40 inbox bills, skipping any already cached
    python -m app.reader.vision --file bill-11.pdf [--force]

What goes to the model is the bill file and a fixed instruction (PROMPT, versioned by PROMPT_VERSION). The model returns JSON: for each field a value, or null, and a confidence
from 0 to 1. Nothing it returns is trusted by itself: `crosscheck.py` compares it with the Tesseract reading, field by field, and a person decides wherever they differ.

Privacy: the free tier of a hosted model may use inputs to improve the provider's products. The case-pack bills are synthetic, so that is acceptable here. Real vendor bills would need
a paid, no-training tier or an in-house model (see notes/reader-comparison.md).
"""
from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VISION_DIR = Path(os.environ["RIKLR_VISION_DIR"]) if os.environ.get("RIKLR_VISION_DIR") else ROOT / "data" / "cache" / "vision"   # the override is for the tests
INBOX = ROOT / "pack" / "context" / "documents" / "bill-inbox"
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")   # not verified from here (no key, no network): change with GEMINI_MODEL if the name has moved on
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
PROMPT_VERSION = "vision-prompt-1"

# the fields the Tesseract reader extracts that can be compared as printed (property_name is matched to SAP by the Tesseract reader, so it is not compared)
FIELDS = ["vendor_name", "vendor_gstin", "invoice_no", "invoice_date", "wo_id", "taxable", "cgst", "sgst", "igst", "total", "hsn_sac", "place_of_supply", "recipient_gstin"]

PROMPT = """You are reading one Indian vendor bill (an invoice or a credit note) for an accounts-payable team. The file may be a scan, a phone photo, or a PDF packet with supporting pages
(attendance sheets, challans, service reports). Read only the invoice or credit note page and ignore the supporting pages.

Extract exactly these fields, as printed on the page, and answer with JSON only, in this shape:
{"doc_type": "invoice" or "credit_note",
 "fields": {"vendor_name": {"value": ..., "confidence": ...}, "vendor_gstin": {...}, "invoice_no": {...}, "invoice_date": {...}, "wo_id": {...}, "taxable": {...}, "cgst": {...},
            "sgst": {...}, "igst": {...}, "total": {...}, "hsn_sac": {...}, "place_of_supply": {...}, "recipient_gstin": {...}}}

Rules:
- vendor_name: the seller's name. vendor_gstin: the seller's 15-character GSTIN. recipient_gstin: the buyer's GSTIN. invoice_no: the invoice or credit note number, exactly as printed.
- invoice_date: as YYYY-MM-DD. wo_id: the work order or purchase order number if one is printed, else null.
- taxable, cgst, sgst, igst, total: numbers in rupees with no commas or currency signs. If a tax line is not printed, use null (do not use 0).
- hsn_sac: the HSN or SAC code. place_of_supply: as printed.
- confidence is your own estimate from 0 to 1 of how sure you are that the value is exactly what is printed. If you cannot read a field, use null for the value and 0 for the confidence.
- Do not guess, correct, or infer a value that is not legible. Do not say whether the bill is acceptable. Output the JSON and nothing else."""


# ------------------------------------------------------------------------------------------------ key handling
def _env_file_value(name: str) -> str | None:
    p = ROOT / ".env"
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == name:
            return v.strip().strip('"').strip("'") or None
    return None


def api_key() -> str | None:
    """The key from the environment or `.env`, or None. Never printed or logged: callers use `has_key()` to ask whether there is one."""
    return os.environ.get("GEMINI_API_KEY") or _env_file_value("GEMINI_API_KEY")


def has_key() -> bool:
    return bool(api_key())


# ------------------------------------------------------------------------------------------------ cache
def cache_path(name: str, folder: Path | None = None) -> Path:
    return (folder or VISION_DIR) / f"{Path(name).name}.json"


def stored(name: str, sha256: str | None = None, folder: Path | None = None) -> dict | None:
    """The stored vision reading for a file name, or None. If `sha256` is given and the stored reading was made from different bytes, it is not used."""
    p = cache_path(name, folder)
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    if sha256 and d.get("sha256") and d["sha256"] != sha256:
        return None
    return d


def normalise_response(obj: dict) -> dict:
    """The model's JSON as {doc_type, fields: {name: {value, conf}}}. Unknown fields are dropped, a value below nothing legible is None, a confidence is clamped to 0..1."""
    fields = {}
    raw = (obj or {}).get("fields") or {}
    for k in FIELDS:
        x = raw.get(k) or {}
        v = x.get("value") if isinstance(x, dict) else None
        try:
            c = float(x.get("confidence", 0) or 0) if isinstance(x, dict) else 0.0
        except (TypeError, ValueError):
            c = 0.0
        if isinstance(v, str):
            v = v.strip() or None
        fields[k] = dict(value=v, conf=max(0.0, min(1.0, c if v is not None else 0.0)))
    dt = (obj or {}).get("doc_type")
    return dict(doc_type="credit_note" if dt == "credit_note" else "invoice", fields=fields)


# ------------------------------------------------------------------------------------------------ the call (only when a key is set)
def _call(body: bytes, mime: str, key: str, model: str) -> dict:
    payload = {"contents": [{"parts": [{"text": PROMPT}, {"inline_data": {"mime_type": mime, "data": base64.b64encode(body).decode("ascii")}}]}],
               "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    req = urllib.request.Request(ENDPOINT.format(model=model), data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key})   # a header, never the URL
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            out = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"The vision model answered with HTTP {e.code}.") from None   # no URL, no headers in the message
    except urllib.error.URLError as e:
        raise RuntimeError(f"The vision model could not be reached ({type(e.reason).__name__}).") from None
    try:
        text = out["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except (KeyError, IndexError, TypeError, ValueError):
        raise RuntimeError("The vision model's answer was not the JSON that was asked for.") from None


def read_file(path: Path, force: bool = False, folder: Path | None = None) -> dict:
    """The vision reading of one bill file: from the cache if there is one, else one call to the model (needs a key), then cached."""
    path = Path(path)
    body = path.read_bytes()
    sha = hashlib.sha256(body).hexdigest()
    if not force:
        hit = stored(path.name, sha, folder)
        if hit:
            return hit
    key = api_key()
    if not key:
        raise RuntimeError("No GEMINI_API_KEY: put it in a .env file (see .env.example). The app and the tests do not need it; only filling the cache does.")
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    t0 = time.time()
    got = normalise_response(_call(body, mime, key, MODEL))
    rec = dict(file=path.name, sha256=sha, reader=dict(name="vision", provider="Gemini", model=MODEL, prompt_version=PROMPT_VERSION, read_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                                                       seconds=round(time.time() - t0, 1)), **got)
    p = cache_path(path.name, folder)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return rec


def main(argv: list[str]) -> int:
    force = "--force" in argv
    if "--file" in argv:
        files = [INBOX / argv[argv.index("--file") + 1]]
    elif "--all" in argv:
        files = sorted(p for p in INBOX.iterdir() if p.is_file())
    else:
        print(__doc__)
        return 2
    if not has_key():
        print("No GEMINI_API_KEY (environment or .env). Nothing was sent.")
        return 1
    print(f"Reading {len(files)} file(s) with {MODEL}. Each bill image is sent to Google.", flush=True)
    for i, p in enumerate(files, 1):
        try:
            cached = stored(p.name, hashlib.sha256(p.read_bytes()).hexdigest()) is not None and not force
            read_file(p, force=force)
            print(f"{i}/{len(files)} {p.name}: {'already cached' if cached else 'read and cached'}", flush=True)
            if not cached:
                time.sleep(float(os.environ.get("GEMINI_PAUSE_SECONDS", "6")))   # stays under free-tier request limits
        except RuntimeError as e:
            print(f"{i}/{len(files)} {p.name}: {e}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
