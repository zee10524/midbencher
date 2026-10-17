"""Classify each page of a file: bill, attendance, challan, service report, PF or ESIC challan, or something else.

A page is named by its headline, found in the first lines of OCR text, matched with a tolerance for OCR slips (`Chalian` for `Challan`). Nothing is inferred
from the body. A page that matches nothing is `other`, which is recorded, never forced into a class. For a packet the reader records which supporting documents
are present, which is what the document-presence checks (P6 to P9, H6 to H9) will need.

Real connection: the same classes would come from the desk scanner's batch separator or the vendor's upload labels, with this headline match as the fallback.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

from .ocr import OcrPage

# class -> headline phrases (letters only, lower case)
HEADLINES = {
    "pf_esic": ["pfesic", "esicchallan", "pfchallan", "epfchallan", "providentfund", "employeesstateinsurance", "esicpaymentchallan"],
    "attendance": ["attendancesummary", "attendancesheet", "attendance"],
    "service_report": ["servicereport", "jobcard", "servicecompletion"],
    "challan": ["deliverychallan"],
    "bill": ["taxinvoice", "creditnote", "invoiceno", "debitnote"],
}
OTHER_LABELS = {"goodsreceiptnote": "goods_receipt_note", "workorderextract": "work_order_extract"}
HEAD_LINES = 8
THRESHOLD = 0.82


def _letters(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower())


def _fuzzy_in(text: str, phrase: str) -> bool:
    """True if `phrase` is in `text`, allowing OCR slips: the best-matching window of the same length scores at least THRESHOLD."""
    if phrase in text:
        return True
    n = len(phrase)
    if len(text) < n:
        return False
    best = max(SequenceMatcher(None, text[i:i + n], phrase).ratio() for i in range(0, len(text) - n + 1))
    return best >= THRESHOLD


def classify_page(page: OcrPage) -> str:
    """One of: pf_esic, attendance, service_report, challan, bill, or `other:<label>` / `other`. Looks at the first lines (and any line that is mostly capitals)."""
    lines = [" ".join(w.text for w in ln) for ln in page.lines]
    head = [_letters(t) for t in lines[:HEAD_LINES]]
    caps = [_letters(t) for t in lines[HEAD_LINES:] if sum(c.isupper() for c in t) > 0.8 * max(1, sum(c.isalpha() for c in t)) and len(t) > 8]
    zone = head + caps
    for label, phrases in OTHER_LABELS.items():
        if any(_fuzzy_in(z, label) for z in zone):
            return f"other:{phrases}"
    for cls, phrases in HEADLINES.items():
        if any(_fuzzy_in(z, p) for z in zone for p in phrases):
            return cls
    return "other"


def supporting_documents(classes: list[str]) -> dict[str, bool]:
    """Which supporting documents a packet contains. A single bill with no other pages has none."""
    return {k: k in classes for k in ("attendance", "challan", "service_report", "pf_esic")}
