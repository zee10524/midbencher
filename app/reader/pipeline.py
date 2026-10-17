"""Read a bill file into `parsed_bill` fields, cache the result as JSON, and write it to the SAP stand-in's `parsed_bill` table.

Flow for one file: if a cached result exists for the same file (same SHA-256) it is used, so the app runs without Tesseract; otherwise each page is turned into
an image (PDFs rendered at 300 dpi, because none has a text layer; photos opened as they are), cleaned, and read with Tesseract. Pages are classified as bill,
attendance, challan, service report, PF or ESIC challan or other; the bill page gives the fields; the other pages are recorded as supporting documents.
pdfplumber is only a fast path: if a PDF does have a text layer, its text is used and OCR is skipped for that page.

A result is `ok` when every required field was found with confidence 0.90 or more and the amounts add up, and `review` otherwise. A field below 0.70 is withheld
from `parsed_bill` (its reading is kept in the notes) and the route hint is `resend`; between 0.70 and 0.90 it is `human-look`. Nothing is guessed to fill a gap.

The vision-model fallback is behind `VISION_FALLBACK`, which is off. This build has no API key and makes no network call; turning the flag on raises an error
that says so.

Real connection: the originals would arrive from the desk scanner or the WhatsApp Business API and be hashed and stored on the company side first; `parsed_bill`
would live in the product's own store, not in SAP (writing invoices into SAP is a separate project).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from . import classify, fields, images, ocr, resolve

READER_VERSION = "reader-2026.10.2"
VISION_FALLBACK = os.environ.get("RIKLR_VISION_FALLBACK", "0") == "1"   # OFF by default
CACHE_DIR = Path(__file__).resolve().parent / "cache"
ROOT = Path(__file__).resolve().parent.parent.parent
INBOX = ROOT / "pack" / "context" / "documents" / "bill-inbox"
PACK_DB = ROOT / "pack" / "data" / "sap_extract.sqlite"
WORKING_DB = ROOT / "app" / "data" / "sap_working.sqlite"
REQUIRED = ["vendor_gstin", "vendor_name", "invoice_no", "invoice_date", "wo_id", "taxable", "total"]
AMOUNTS = ["taxable", "cgst", "sgst", "igst", "total"]


def bill_type_of(path: Path) -> str:
    """By how the file arrived: a photo, a single-bill PDF or a packet. Taken from the file name and extension only."""
    p = Path(path)
    return "phone_photo" if p.suffix.lower() in images.PHOTO_SUFFIXES else ("pdf_packet" if p.name.startswith("packet-") else "pdf_single")


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def vision_fallback(image, missing: list[str]):
    """Placeholder for a vision-model read of fields Tesseract could not get. Off by default. This build has no API key and makes no network call."""
    if not VISION_FALLBACK:
        return None
    raise RuntimeError("The vision-model fallback is switched on but not built: this build has no API key and makes no network call.")


# ------------------------------------------------------------------------------------------------ one file
def read_pages(path: Path) -> tuple[list[ocr.OcrPage], list[dict], bool]:
    """OCR pages and per-page facts. Uses the pdfplumber text layer when a PDF has one."""
    path = Path(path)
    layer = images.pdf_text_layer(path) if path.suffix.lower() == ".pdf" else None
    if layer:
        return [ocr.text_page(t) for t in layer], [dict(page=i + 1, source="text layer") for i in range(len(layer))], True
    pages, facts = [], []
    for pi in images.page_images(path):
        o = ocr.ocr_page(pi.image)
        pages.append(o)
        facts.append(dict(page=pi.page, source="tesseract", skew_degrees=pi.skew_degrees, background_cropped=pi.cropped,
                          mean_word_conf=round(sum(w.conf for w in o.words) / max(1, len(o.words)), 3)))
    return pages, facts, False


def judge(b: fields.BillFields) -> tuple[str, str, float, list[str]]:
    """(status, route hint, overall confidence, reasons) from the extracted fields."""
    reasons = list(b.reasons)
    confs = []
    for name in REQUIRED:
        f = getattr(b, name)
        if f.value is None:
            reasons.append(f"{name}: not found")
            confs.append(0.0)
        else:
            confs.append(f.conf)
            if f.conf < fields.AUTO:
                reasons.append(f"{name}: confidence {f.conf:.2f} ({f.note})")
            elif f.source != "read":
                reasons.append(f"{name}: {f.source.replace('_', ' ')}, not read from the bill ({f.note})")
    if b.arithmetic_ok is None:
        reasons.append("amounts: not all of taxable value and total were found")
    taxed = (b.cgst.value is not None and b.sgst.value is not None) or b.igst.value is not None or b.no_gst_printed
    if not taxed and b.taxable.value is not None:
        reasons.append("tax: no complete tax line found")
    overall = round(min(confs), 3) if confs else 0.0
    ok = not reasons and b.arithmetic_ok is True and taxed
    status = "ok" if ok else "review"
    hint = "auto-clear" if ok else ("resend" if overall < fields.RESEND else "human-look")
    return status, hint, overall, reasons


def read_file(path: Path, sap=None, use_cache: bool = True, refresh: bool = False, cache_dir: Path = CACHE_DIR) -> dict:
    """Read one inbox file and return its result as a plain dict (the cached JSON). With a cache hit and no `refresh`, nothing is OCR'd. If Tesseract is not
    installed and there is no cache, the result is `review` with that reason and no values."""
    path = Path(path)
    digest = sha256(path)
    cache_file = cache_dir / f"{path.name}.json"
    if use_cache and not refresh and cache_file.is_file():
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        if cached.get("sha256") == digest:
            cached["reader"]["simulated"] = not ocr.tesseract_available()
            return cached
    base = dict(file=path.name, sha256=digest, bill_type=bill_type_of(path), reader=dict(version=READER_VERSION, dpi=images.RENDER_DPI, vision_fallback=VISION_FALLBACK,
                                                                                        simulated=False))
    if not ocr.tesseract_available() and not (path.suffix.lower() == ".pdf" and images.pdf_text_layer(path)):
        return base | dict(pages=[], supporting={}, fields={}, status="review", route_hint="resend", overall_confidence=0.0,
                           reasons=["Tesseract is not installed and there is no cached result for this file"], reader=base["reader"] | dict(simulated=True))
    pages, facts, fast = read_pages(path)
    classes = [classify.classify_page(p) for p in pages]
    for f, c in zip(facts, classes):
        f["class"] = c
    bill_idx = next((i for i, c in enumerate(classes) if c == "bill"), None)
    if bill_idx is None:
        res = base | dict(pages=facts, supporting=classify.supporting_documents(classes), fields={}, status="review", route_hint="resend", overall_confidence=0.0,
                          reasons=["no page was recognised as the bill"])
    else:
        pages[bill_idx].header = ocr.ocr_header(pages[bill_idx])
        b = fields.extract_bill(pages[bill_idx], sap)
        if pages[bill_idx].header is not None:
            fields.merge_header(b, fields.extract_bill(pages[bill_idx].header))
        if sap is not None:
            resolve.resolve_vendor(b, sap)
        status, hint, overall, reasons = judge(b)
        res = base | dict(pages=facts, bill_page=bill_idx + 1, doc_type=b.doc_type, supporting=classify.supporting_documents(classes),
                          other_pages=[c for c in classes if c.startswith("other")], fields={k: asdict(getattr(b, k)) for k in
                          ["vendor_name", "vendor_gstin", "invoice_no", "invoice_date", "property_name", "wo_id", "taxable", "cgst", "sgst", "igst", "total",
                           "hsn_sac", "place_of_supply", "recipient_gstin", "udyam"]},
                          no_gst_printed=b.no_gst_printed, arithmetic_ok=b.arithmetic_ok, status=status, route_hint=hint, overall_confidence=overall, reasons=reasons)
        res["reader"]["text_layer_fast_path"] = fast
        if status == "review" and VISION_FALLBACK:
            vision_fallback(None, [r.split(":")[0] for r in reasons])
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    return res


# ------------------------------------------------------------------------------------------------ parsed_bill
def parsed_bill_args(res: dict) -> dict:
    """The arguments for `SapAdapter.write_parsed_bill`. A field below 0.70 is withheld (NULL) and its reading kept in the notes."""
    f = res.get("fields", {})

    def val(name):
        x = f.get(name)
        return x["value"] if x and x["value"] is not None and x["conf"] >= fields.RESEND else None

    notes = list(res.get("reasons", []))
    for name, x in f.items():
        if x["value"] is not None and x["conf"] < fields.RESEND and name in REQUIRED + ["cgst", "sgst", "igst", "property_name"]:
            notes.append(f"{name}: withheld, low-confidence reading {x['value']!r} ({x['conf']:.2f})")
    sup = [k for k, v in res.get("supporting", {}).items() if v]
    notes.append("supporting documents present: " + (", ".join(sup) if sup else "none"))
    notes.append(f"route: {res.get('route_hint')}; bill type: {res.get('bill_type')}; document: {res.get('doc_type', 'unknown')}")
    if res.get("reader", {}).get("simulated"):
        notes.append("reader simulated: result from the cache, not read now")
    pn = f.get("property_name", {})
    typed = {k: x["original"] for k, x in f.items() if x.get("source") == "human_review" and "original" in x}
    if typed:
        notes.append("typed by a person: " + ", ".join(sorted(typed)))
    return dict(source=("human_review" if typed else "reader"), reader_original=(json.dumps(typed, ensure_ascii=False) if typed else None), source_file=res["file"], vendor_gstin=val("vendor_gstin"), vendor_name=val("vendor_name"), invoice_no=val("invoice_no"), invoice_date=val("invoice_date"),
                property_code=pn.get("value") if pn.get("conf", 0) >= fields.RESEND and re.fullmatch(r"[A-Z]{3}-[A-Z]\d{2}", str(pn.get("value") or "")) else None,
                wo_id=val("wo_id"), taxable_inr=val("taxable"), cgst_inr=val("cgst"), sgst_inr=val("sgst"), igst_inr=val("igst"), total_inr=val("total"),
                confidence=res.get("overall_confidence"), check_status=res["status"], check_notes="; ".join(notes),
                parsed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))


def make_working_copy(src: Path | None = None, dst: Path | None = None) -> Path:
    """A fresh copy of the SAP stand-in to write `parsed_bill` into. The pack is never written to."""
    src, dst = Path(src or PACK_DB), Path(dst or WORKING_DB)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    import sqlite3

    con = sqlite3.connect(dst)          # this project's own copy: two columns the extract spec does not have, so a person's entry never overwrites the reader's reading
    try:
        for col in ("source TEXT", "reader_original TEXT"):
            con.execute(f"ALTER TABLE parsed_bill ADD COLUMN {col}")
        con.commit()
    finally:
        con.close()
    return dst


def run_all(inbox: Path = INBOX, refresh: bool = False, db: Path | None = None, cache_dir: Path = CACHE_DIR) -> list[dict]:
    """Read every file in the inbox, write each result to `parsed_bill` in a fresh working copy of the stand-in, and return the results."""
    from app.sap.adapter import SapAdapter

    work = make_working_copy() if db is None else Path(db)
    out = []
    with SapAdapter(work) as sap:
        for path in sorted(p for p in Path(inbox).iterdir() if p.suffix.lower() in {".pdf", *images.PHOTO_SUFFIXES}):
            res = read_file(path, sap=sap, refresh=refresh, cache_dir=cache_dir)
            sap.write_parsed_bill(**parsed_bill_args(res))
            out.append(res)
    return out


def summary(results: list[dict]) -> dict:
    """Counts of ok and review, and of the review route hints, overall and by bill type."""
    tot: dict = {}
    for r in results:
        for key in ("all", r["bill_type"]):
            d = tot.setdefault(key, dict(files=0, ok=0, review=0, human_look=0, resend=0))
            d["files"] += 1
            d["ok" if r["status"] == "ok" else "review"] += 1
            if r["status"] != "ok":
                d["resend" if r["route_hint"] == "resend" else "human_look"] += 1
    return tot

