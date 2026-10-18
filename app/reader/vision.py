"""A second reader for the cross-check: a vision model (Gemini) that extracts the same fields as the Tesseract reader. It never decides pass or fail.

OFF by default. It runs only when `GEMINI_API_KEY` is set, in the environment or in a `.env` file at the project root (`.env` is git-ignored; `.env.example`, with a blank value,
is committed). The key is read, sent in a request header and nothing else: it is never printed, logged, put in a URL or written to the cache.

Every response is cached as JSON under `data/cache/vision/<model>/<file name>.json` (one folder per model, so readings of different models are never mixed; the model name is also
recorded inside every file), and that cache is meant to be committed, so the app, the analysis and the tests run with no key and
no network. `stored(name)` reads the cache only; the app never calls the model. To fill the cache (one call per bill, sends the bill image to Google):

    python -m app.reader.vision --all --confirm-send     # all 40 inbox bills, skipping any already cached; --confirm-send says you accept that the files go to Google
    python -m app.reader.vision --file bill-11.pdf [--force]
    python -m app.reader.vision --files bill-11.pdf bill-12.pdf ...     # just these files

A 503 ("high demand") is retried up to 3 times with a short wait; a 429 (quota) stops the run cleanly, with no retry.

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
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
PROMPT_VERSION = "vision-prompt-1"
BILL_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png"}

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


# gemini-2.5-flash is closed to new users (HTTP 404). The free tier allows 20 requests a day per model, so the 10 labelled bills are read with ONE model that had quota: gemini-3.7-flash.
# Override with GEMINI_MODEL (environment or .env); readings are stored per model.
DEFAULT_MODEL = "gemini-3.7-flash"
MODEL = os.environ.get("GEMINI_MODEL") or _env_file_value("GEMINI_MODEL") or DEFAULT_MODEL


class QuotaExceeded(RuntimeError):
    """HTTP 429: the model's quota is used up. Never retried."""


def api_key() -> str | None:
    """The key from the environment or `.env`, or None. Never printed or logged: callers use `has_key()` to ask whether there is one."""
    return os.environ.get("GEMINI_API_KEY") or _env_file_value("GEMINI_API_KEY")


def has_key() -> bool:
    return bool(api_key())


# ------------------------------------------------------------------------------------------------ cache
def cache_path(name: str, folder: Path | None = None, model: str | None = None) -> Path:
    """`data/cache/vision/<model>/<file>.json`; an explicit `folder` is used as it is."""
    return (folder or VISION_DIR / (model or MODEL)) / f"{Path(name).name}.json"


def stored(name: str, sha256: str | None = None, folder: Path | None = None, model: str | None = None) -> dict | None:
    """The stored vision reading of one model (the app's model unless `model` is given) for a file name, or None. If `sha256` is given and the stored reading was made from different
    bytes, or by a different model than the folder says, it is not used."""
    p = cache_path(name, folder, model)
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    if sha256 and d.get("sha256") and d["sha256"] != sha256:
        return None
    if (d.get("reader") or {}).get("model") not in (None, model or MODEL) and folder is None:
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
    for attempt in (1, 2, 3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                out = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code == 503 and attempt < 3:
                time.sleep(float(os.environ.get("GEMINI_RETRY_SECONDS", "5")) * attempt)    # "high demand" is usually brief
                continue
            _raise_http(e, key, model)
        except urllib.error.URLError as e:
            raise RuntimeError(f"The vision model could not be reached ({type(e.reason).__name__}; model {model}).") from None
    try:
        text = out["candidates"][0]["content"]["parts"][0]["text"]
        return dict(json.loads(text), _raw=text)       # `_raw` is the model's own answer, kept in the cache so the normalising below can be audited
    except (KeyError, IndexError, TypeError, ValueError):
        raise RuntimeError("The vision model's answer was not the JSON that was asked for.") from None


def _raise_http(e: urllib.error.HTTPError, key: str, model: str):
    # what is shown: the model, the request path (the key is in a header, so it is never in the path), and the error text Google sent, with the key scrubbed if it were echoed
    try:
        said = (json.loads(e.read().decode("utf-8", "replace")).get("error") or {}).get("message") or ""
    except (ValueError, AttributeError):
        said = ""
    said = " ".join(said.replace(key, "[key hidden]").split())[:600]
    path = ENDPOINT.format(model=model).split("googleapis.com", 1)[1]
    msg = f"The vision model answered with HTTP {e.code} (model {model}, request path {path}). Google says: {said or 'no error text'}"
    raise (QuotaExceeded(msg) if e.code == 429 else RuntimeError(msg)) from None


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
    answer = _call(body, mime, key, MODEL)
    got = normalise_response(answer)
    rec = dict(file=path.name, sha256=sha, reader=dict(name="vision", provider="Gemini", model=MODEL, prompt_version=PROMPT_VERSION, read_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                                                       seconds=round(time.time() - t0, 1)), **got, model_answer=answer.get("_raw"))
    p = cache_path(path.name, folder)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return rec


def main(argv: list[str]) -> int:
    force = "--force" in argv
    if "--files" in argv:
        names = [a for a in argv[argv.index("--files") + 1:] if not a.startswith("--")]
        files = [INBOX / n for n in names]
        missing = [f.name for f in files if not f.is_file()]
        if missing or not files:
            print("Not in the bill inbox: " + ", ".join(missing or ["(no file names given)"]))
            return 2
    elif "--file" in argv:
        files = [INBOX / argv[argv.index("--file") + 1]]
    elif "--all" in argv:
        files = sorted(p for p in INBOX.iterdir() if p.is_file() and p.suffix.lower() in BILL_SUFFIXES)   # bills only: index.md and the like are skipped
    else:
        print(__doc__)
        return 2
    if not has_key():
        print("No GEMINI_API_KEY (environment or .env). Nothing was sent.")
        return 1
    if "--confirm-send" not in argv:
        print(f"Nothing was sent. This command uploads {len(files)} bill file(s) to Google's Gemini API, a third party. The free tier may use inputs to improve Google's products. The case pack says to treat its\n"
              "data as real client data, so only run this if you have decided that is acceptable (see notes/assumptions.md, Known limits). To go ahead, add --confirm-send.")
        return 3
    print(f"Reading {len(files)} file(s) with {MODEL}. Each bill image is sent to Google.", flush=True)
    for i, p in enumerate(files, 1):
        try:
            cached = stored(p.name, hashlib.sha256(p.read_bytes()).hexdigest()) is not None and not force
            read_file(p, force=force)
            print(f"{i}/{len(files)} {p.name}: {'already cached' if cached else 'read and cached'}", flush=True)
            if not cached:
                time.sleep(float(os.environ.get("GEMINI_PAUSE_SECONDS", "6")))   # stays under free-tier request limits
        except QuotaExceeded as e:
            print(f"{i}/{len(files)} {p.name}: {e}\nStopped: the quota for {MODEL} is used up. Nothing more was sent. Try again after the wait Google gives, or use another model (GEMINI_MODEL).", flush=True)
            return 1
        except RuntimeError as e:
            print(f"{i}/{len(files)} {p.name}: {e}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
