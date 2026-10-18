"""Cross-check of the two readers, field by field. Neither reading is ever picked automatically.

For each field both readers can read:
- they agree          -> `agree`: the field is marked "two readers agree". (A value Tesseract did not read but took from the vendor master gives `vision_confirms` instead: the vision reading
                         matches the master, which is weaker than two independent readings.)
- they disagree       -> `differ`: the field is marked "needs human review", both values are shown side by side, and the field is treated as not read (so the checks that need
                         it do not run) until a person types the value. A person can click either value to fill the box, but still has to run the checks.
- only the vision reader has a value (Tesseract did not read it, or read it below 0.70) -> `vision_only`: the field stays unread; the vision value is offered as a suggestion.
- only Tesseract has a value -> `tesseract_only`: nothing changes; there is no second opinion to show.

A reading below 0.70 confidence counts as no reading, the same rule as everywhere else. A tax line that is not printed is not compared unless both readers found a value.
A field a person has typed (`human_review`) is left alone.
"""
from __future__ import annotations

import copy
import re

from app.rules.model import LOOK

AGREE, DIFFER, VISION_ONLY, TESS_ONLY, CONFIRMS = "agree", "differ", "vision_only", "tesseract_only", "vision_confirms"
COMPARED = ["vendor_name", "vendor_gstin", "invoice_no", "invoice_date", "wo_id", "taxable", "total", "cgst", "sgst", "igst", "hsn_sac", "place_of_supply", "recipient_gstin"]
AMOUNTS = {"taxable", "cgst", "sgst", "igst", "total"}
TAX_LINES = {"cgst", "sgst", "igst"}


def norm(key: str, v):
    """A value in the form the two readers are compared in: formatting only (case, spaces, number format, date order). None stays None."""
    if v is None:
        return None
    if key in AMOUNTS:
        try:
            return round(float(str(v).replace(",", "")), 2)
        except ValueError:
            return str(v).strip()
    s = " ".join(str(v).split())
    if key == "invoice_date":
        m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", s)
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else s
    if key in ("vendor_gstin", "recipient_gstin", "invoice_no", "hsn_sac"):
        return s.replace(" ", "").upper()
    return s.upper()


def _tess(x: dict):
    v, c = (x or {}).get("value"), float((x or {}).get("conf", 0) or 0)
    return v if (v is not None and c >= LOOK) else None


def _vis(x: dict):
    v, c = (x or {}).get("value"), float((x or {}).get("conf", 0) or 0)
    return v if (v is not None and c >= LOOK) else None


def compare(res: dict, vision: dict | None) -> dict[str, dict]:
    """{field: {state, tesseract, vision}} for each field where at least one reader has a value. Values are as each reader gave them (not normalised)."""
    out = {}
    if not vision:
        return out
    for k in COMPARED:
        tx = (res.get("fields") or {}).get(k) or {}
        if tx.get("source") == "human_review":
            continue
        t, v = _tess(tx), _vis((vision.get("fields") or {}).get(k))
        if t is None and v is None:
            continue
        if k in TAX_LINES and (t is None or v is None):
            continue
        if t is not None and v is not None:
            same = norm(k, t) == norm(k, v)
            # a GSTIN or name looked up from the vendor master (or repaired to it) was not read by Tesseract: a matching vision reading confirms it, but it is not "two readers agree"
            state = (CONFIRMS if tx.get("source") in ("vendor_master", "repaired") else AGREE) if same else DIFFER
        elif v is not None:
            state = VISION_ONLY
        else:
            state = TESS_ONLY
        out[k] = dict(state=state, tesseract=t, vision=v)
    return out


def apply(res: dict, vision: dict | None) -> dict:
    """A copy of a reader result with the cross-check on each field (`cross`). Where the readers differ the field's value is withheld (None, confidence 0) and the Tesseract
    reading is kept under `tesseract`, so a field that needs a person is treated as not read by the checks. Nothing is picked."""
    res2 = copy.deepcopy(res)
    if not vision or res.get("vision"):      # nothing stored, or already applied
        return res2
    res2["vision"] = dict(model=(vision.get("reader") or {}).get("model"), read_at=(vision.get("reader") or {}).get("read_at"), prompt_version=(vision.get("reader") or {}).get("prompt_version"))
    for k, c in compare(res, vision).items():
        x = res2["fields"].setdefault(k, dict(value=None, conf=0.0, note="", source="read", raw=None))
        x["cross"] = c
        if c["state"] == DIFFER:
            x["tesseract"] = dict(value=x.get("value"), conf=float(x.get("conf", 0) or 0))
            x["value"], x["conf"] = None, 0.0
            x["note"] = "the two readers differ"
    return res2
