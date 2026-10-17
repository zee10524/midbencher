"""Read the fields of a bill page from OCR text, each with a confidence, and never guess.

Each field's confidence starts from Tesseract's confidence in the words it came from. It is lowered for every character that had to be repaired by position
(a letter where a digit must be, as `O` for `0`), and it is checked against independent evidence on the same page:

- the three amounts: taxable value plus tax equals the total, and each tax line equals the taxable value at its printed rate. If both hold, a chance OCR error
  is very unlikely to have kept them true, so the amounts are confident. If the sum fails, no amount is trusted;
- the vendor GSTIN: its state code against the state printed beside it;
- the vendor name: against the `For <name>` line at the foot of the bill;
- the invoice date: against the financial year in the invoice number, and a plausible year.

A field that cannot be found has value None and confidence 0, and the bill goes to human review. The vendor's GSTIN is the one in the supplier block above
`Bill to`; the buyer's, below it, is kept separately.

Real connection: nothing here depends on how the page was captured, so a vision model or a scanner's own OCR could replace the OCR text with the same
checks applied.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from difflib import SequenceMatcher
from typing import Any

from .ocr import OcrPage, Word, reread

AUTO = 0.90          # a field at or above this, with every check consistent, needs no review
RESEND = 0.70        # a required field below this: ask for a clearer image
REPAIR_PENALTY = 0.06
STATES = {
    "01": "jammu and kashmir", "02": "himachal pradesh", "03": "punjab", "04": "chandigarh", "05": "uttarakhand", "06": "haryana", "07": "delhi", "08": "rajasthan",
    "09": "uttar pradesh", "10": "bihar", "11": "sikkim", "12": "arunachal pradesh", "13": "nagaland", "14": "manipur", "15": "mizoram", "16": "tripura",
    "17": "meghalaya", "18": "assam", "19": "west bengal", "20": "jharkhand", "21": "odisha", "22": "chhattisgarh", "23": "madhya pradesh", "24": "gujarat",
    "27": "maharashtra", "29": "karnataka", "30": "goa", "32": "kerala", "33": "tamil nadu", "36": "telangana", "37": "andhra pradesh", "38": "ladakh"}
_TO_DIGIT = {"O": "0", "D": "0", "Q": "0", "I": "1", "L": "1", "Z": "2", "S": "5", "B": "8", "G": "6"}
_TO_LETTER = {"0": "O", "1": "I", "2": "Z", "5": "S", "8": "B", "6": "G"}
_DIGIT_SLOTS, _LETTER_SLOTS = {0, 1, 7, 8, 9, 10}, {2, 3, 4, 5, 6, 11}
_GSTIN_SHAPE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
WL_ID = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
WL_DIGITS = "0123456789"
WL_INVOICE = "0123456789/-CN"
_CONFUSABLE = {"0": "ODQ0", "1": "IL1|", "2": "Z2", "3": "3", "4": "4", "5": "S5", "6": "G6B", "7": "7", "8": "B8", "9": "9GQ"}
_AMOUNT = re.compile(r"[-−–]?\(?\d[\d,]*\.\d{1,2}\)?")
_DATE = re.compile(r"(\d{2})[-/.](\d{2})[-/.](\d{4})")


@dataclass
class F:
    """A field: its value, a confidence from 0 to 1, and a note on how it was got or why it is doubtful."""
    value: Any = None
    conf: float = 0.0
    note: str = ""


@dataclass
class BillFields:
    doc_type: str = "invoice"
    vendor_name: F = field(default_factory=F)
    vendor_gstin: F = field(default_factory=F)
    invoice_no: F = field(default_factory=F)
    invoice_date: F = field(default_factory=F)
    property_name: F = field(default_factory=F)
    wo_id: F = field(default_factory=F)
    taxable: F = field(default_factory=F)
    cgst: F = field(default_factory=F)
    sgst: F = field(default_factory=F)
    igst: F = field(default_factory=F)
    total: F = field(default_factory=F)
    # not in parsed_bill but needed by the intake rules
    hsn_sac: F = field(default_factory=F)
    place_of_supply: F = field(default_factory=F)
    recipient_gstin: F = field(default_factory=F)
    udyam: F = field(default_factory=F)
    no_gst_printed: bool = False
    arithmetic_ok: bool | None = None
    reasons: list[str] = field(default_factory=list)


# ------------------------------------------------------------------------------------------------ helpers
def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, re.sub(r"[^a-z0-9]", "", a.lower()), re.sub(r"[^a-z0-9]", "", b.lower())).ratio()


def _line_text(ln: list[Word]) -> str:
    return " ".join(w.text for w in ln)


def _mean(ws: list[Word]) -> float:
    return sum(w.conf for w in ws) / len(ws) if ws else 0.0


def _find_word(ln: list[Word], token: str) -> Word | None:
    return next((w for w in ln if token in w.text), None)


def parse_amount(tok: str) -> float | None:
    """`5,75,510.00` -> 575510.0. Commas are noise (Indian and western grouping both occur in the OCR), a minus sign or brackets mean negative."""
    neg = tok[:1] in ("-", "−", "–", "(")
    digits = re.sub(r"[^\d.]", "", tok)
    try:
        v = float(digits)
    except ValueError:
        return None
    return -v if neg else v


def repair_gstin(raw: str) -> tuple[str, int]:
    """Repair a read GSTIN by position: digits where the format needs digits, letters where it needs letters, a Z at position 14. Returns the text and how many characters changed."""
    s, out, n = raw.upper(), "", 0
    for i, c in enumerate(s[:15]):
        r = c
        if i in _DIGIT_SLOTS and not c.isdigit():
            r = _TO_DIGIT.get(c, c)
        elif i in _LETTER_SLOTS and not c.isalpha():
            r = _TO_LETTER.get(c, c)
        elif i == 13 and c != "Z":
            r = "Z" if c in "2" else c
        n += r != c
        out += r
    return out, n


def second_read(page: OcrPage, w: Word | None, whitelist: str, fixed: str, fix) -> tuple[bool | None, float]:
    """Read word `w` again from the page image, choosing only from `whitelist`, repair the result the same way and compare it with `fixed`.
    Returns (agree, confidence of the second read); agree is None if there was no word or no image to read again."""
    if w is None:
        return None, 0.0
    rr = reread(page, w, whitelist)
    if rr is None:
        return None, 0.0
    text, conf = rr
    return fix(text) == fixed, conf


def read_gstin(page: OcrPage, ln: list[Word], line_text: str, m: re.Match) -> F:
    """The vendor's GSTIN from the line `<state> | GSTIN <15 characters>`.

    Tesseract's own confidence for this token is a poor guide (a correct GSTIN often scores low because `0` and `O` look alike), so the confidence comes from
    three independent signs: the shape is valid after repairing characters by position; the state code agrees with the state name printed beside it; and a
    second read of the word, from the page image with only capitals and digits allowed, gives the same text. All three: 0.95. Shape and state agree but the
    second read differs: 0.80. State code and state name disagree: 0.30. A last character of `O` or `I` could be a digit, so the confidence is capped at 0.80.
    These levels are starting values set on the files outside the labelled ten, by comparing the reads with the vendor master; they are not measured accuracy.
    """
    raw = m.group(1)
    fixed, n = repair_gstin(raw)
    w = _find_word(ln, raw)
    base = w.conf if w else _mean(ln)
    state_text = line_text[:m.start()].replace("|", " ")
    code, sim = _state_of_line(state_text)
    note = f"{n} character(s) repaired by position" if n else "read as printed"
    if len(raw) == 15 and code and sim >= 0.8 and fixed[:2] != code and all(raw[i].upper() in _CONFUSABLE[code[i]] for i in (0, 1)):
        fixed, note = code + fixed[2:], f"state code taken from the state name '{state_text.strip()}': the printed '{raw[:2]}' is confusable with {code}"
    if not (len(raw) == 15 and _GSTIN_SHAPE.match(fixed)):
        return F(None, 0.0, f"printed text '{raw}' is not a valid GSTIN shape")
    state_ok = code is not None and sim >= 0.8 and code == fixed[:2]
    agree, _ = second_read(page, w, WL_ID, fixed, lambda x: repair_gstin(x)[0])
    if base >= AUTO and n == 0 and state_ok:
        conf, note = min(0.99, base + 0.04), note + "; state name agrees with the state code"
    elif not state_ok:
        conf, note = 0.30, note + f"; the state printed beside it ('{state_text.strip()}') does not clearly agree with state code {fixed[:2]}"
    elif agree:
        conf, note = 0.95, note + "; state name agrees with the state code; a second read of the word agrees"
    else:
        conf, note = 0.80, note + "; state name agrees with the state code; " + ("a second read of the word differs" if agree is False else "no second read was possible")
    if fixed[-1] in "OI":
        conf, note = min(conf, 0.80), note + "; the last character could be a digit"
    return F(fixed, conf, note)


def parse_date(s: str) -> date | None:
    m = _DATE.search(s)
    if not m:
        return None
    d, mo, y = (int(x) for x in m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def _fy_of(invoice_no: str) -> tuple[date, date] | None:
    m = re.search(r"(\d{2})-(\d{2})", invoice_no or "")
    if not m or int(m.group(2)) != (int(m.group(1)) + 1) % 100:
        return None
    y = 2000 + int(m.group(1))
    return date(y, 4, 1), date(y + 1, 3, 31)


def _state_of_line(text: str) -> tuple[str | None, float]:
    """The state named in text, by closest name. Returns (code, similarity)."""
    best, code = 0.0, None
    for c, name in STATES.items():
        r = _ratio(text, name)
        if r > best:
            best, code = r, c
    return code, best


# ------------------------------------------------------------------------------------------------ extraction
def extract_bill(page: OcrPage, sap=None) -> BillFields:
    """Extract and cross-check the fields of one bill page. `sap` is an optional SapAdapter used only to identify the property from the name printed on the bill."""
    b = BillFields()
    lines = page.lines
    texts = [_line_text(ln) for ln in lines]
    low = [t.lower() for t in texts]
    head = " ".join(low[:6])
    b.doc_type = "credit_note" if re.search(r"credit\s*n[o0]te", head) else "invoice"
    bill_to = next((i for i, t in enumerate(low) if re.match(r"\s*b[il1]{3}\s*t[o0]\b", t)), None)
    top = lines[:bill_to] if bill_to is not None else lines[:6]
    top_t = texts[:bill_to] if bill_to is not None else texts[:6]

    # ---- supplier block: name, GSTIN, state, Udyam
    for ln, t in zip(top, top_t):
        letters = sum(c.isalpha() or c in " &.-" for c in t)
        if len(t.strip()) >= 6 and letters >= 0.85 * len(t) and "gstin" not in t.lower() and "invoice" not in t.lower():
            b.vendor_name = F(t.strip(" |"), _mean(ln), "first clean line of the bill")
            break
    for ln, t in zip(top, top_t):
        m = re.search(r"GST[IL1]N\s*[:\-]?\s*([A-Za-z0-9]{12,16})", t)
        if m and "udyam" not in t.lower():
            b.vendor_gstin = read_gstin(page, ln, t, m)
            break
    for ln, t in zip(top, top_t):
        if re.search(r"ud[yv]am|regist", t.lower()):
            m = re.search(r"(micro|small|medium)", t.lower())
            b.udyam = F(m.group(1).title() if m else None, _mean(ln) if m else 0.0, "claim printed by the vendor, not proof")
            break
    if bill_to is None:
        b.reasons.append("no 'Bill to' block found: the supplier GSTIN cannot be told from the buyer's")
        b.vendor_gstin = F(None, 0.0, "no 'Bill to' block")

    # ---- the buyer block: property, buyer GSTIN, place of supply
    if bill_to is not None:
        prop_lines, started = [], False
        for ln, t in zip(lines[bill_to + 1:], texts[bill_to + 1:]):
            tl = t.lower()
            if re.search(r"work\s*order|description", tl):
                break
            if "gst" in tl or "place of" in tl:
                m = re.search(r"GST[IL1]N\s*[:\-]?\s*([A-Za-z0-9]{12,16})", t)
                if m:
                    fixed, n = repair_gstin(m.group(1))
                    if len(m.group(1)) == 15 and _GSTIN_SHAPE.match(fixed):
                        # no state name is printed beside it, so the signs are the valid shape and a second read of the word from the image
                        w = _find_word(ln, m.group(1))
                        base = w.conf if w else _mean(ln)
                        agree, _ = second_read(page, w, WL_ID, fixed, lambda x: repair_gstin(x)[0])
                        conf = base if (base >= AUTO and n == 0) else 0.92 if agree else max(0.0, min(0.80, base) - REPAIR_PENALTY * n)
                        b.recipient_gstin = F(fixed, conf, "buyer's GSTIN" + ("; a second read of the word agrees" if agree else ""))
                m = re.search(r"place\s*of\s*supp?ly\s*[:\-]?\s*(.+)$", t, re.I)
                if m:
                    code, sim = _state_of_line(m.group(1))
                    b.place_of_supply = F(STATES[code].title() if sim >= 0.7 else m.group(1).strip(), _mean(ln) * (1.0 if sim >= 0.7 else 0.5),
                                          f"closest state name, similarity {sim:.2f}")
                continue
            if "property management" in tl:
                started = True
                continue
            if started:
                prop_lines.append((t.strip(), _mean(ln)))
        if prop_lines:
            name = " ".join(p[0] for p in prop_lines)
            conf = min(p[1] for p in prop_lines)
            b.property_name = F(name, conf, "printed on the bill")
            if sap is not None:
                hits = sap.find_property_by_name(re.sub(r"\s*[.;]\s*", ", ", name))
                if len(hits) == 1:
                    b.property_name = F(hits[0].property_code, min(0.99, conf + 0.05), f"matched to SAP property '{hits[0].name}'")
                else:
                    b.property_name = F(None, 0.0, f"'{name}' matches {len(hits)} SAP properties by name")

    # ---- invoice number and date
    for ln, t in zip(lines, texts):
        m = re.search(r"(?:inv[o0]ice|credit\s*note|bill|cn)\s*(?:no|number|#)\.?\s*[:\-]?\s*([A-Za-z0-9/\-]+)", t, re.I)
        if m:
            raw = m.group(1)
            w = next((x for x in ln if raw in x.text), None)
            base = w.conf if w else _mean(ln)
            std = re.fullmatch(r"(CN/)?([0-9OIlS]{3})/([0-9OIlS]{2})-([0-9OIlS]{2})/([0-9OIlS]{3})", raw)
            if std:
                pre, *segs = std.groups()
                fixed = (pre or "") + f"{segs[0]}/{segs[1]}-{segs[2]}/{segs[3]}"
                digits = re.sub(r"[^0-9OIlS]", "", fixed.replace("CN", ""))
                n = sum(c in "OIlS" for c in digits)
                fixed = re.sub(r"[OIlS]", lambda mm: {"O": "0", "I": "1", "l": "1", "S": "5"}[mm.group()], fixed)
                conf, note = max(0.0, base - REPAIR_PENALTY * n), f"{n} character(s) repaired by position" if n else "read as printed"
                if base < AUTO or n:
                    agree, c2 = second_read(page, w, WL_INVOICE, fixed, lambda x: x)
                    if agree:
                        conf, note = max(base, c2), note + "; a second read of the word agrees"
                    elif agree is False:
                        conf, note = min(base, c2) * 0.7, note + "; a second read of the word disagrees"
                b.invoice_no = F(fixed, conf, note)
            else:
                b.invoice_no = F(raw, min(base, 0.6), "not in the usual NNN/YY-YY/NNN form")
            d = re.search(r"date\s*[:\-]?\s*(\d{2}[-/.]\d{2}[-/.]\d{4})", t, re.I)
            if d:
                dv = parse_date(d.group(1))
                dw = next((x for x in ln if re.search(r"\d{2}[-/.]\d{2}", x.text)), None)
                b.invoice_date = F(dv.isoformat() if dv else None, (dw.conf if dw else _mean(ln)) if dv else 0.0, "day-month-year as printed" if dv else "not a real date")
            break

    # ---- work order
    for ln, t in zip(lines, texts):
        m = re.search(r"w[o0]rk\s*[o0]rder\s*/?\s*P[O0]\s*[:\-]?\s*([0-9OIlS]{7,10})", t, re.I)
        if m:
            raw = m.group(1)
            fixed = re.sub(r"[OIlS]", lambda mm: {"O": "0", "I": "1", "l": "1", "S": "5"}[mm.group()], raw)
            n = sum(c in "OIlS" for c in raw)
            w = next((x for x in ln if raw in x.text), None)
            base = w.conf if w else _mean(ln)
            conf, note = max(0.0, base - REPAIR_PENALTY * n), f"{n} character(s) repaired by position" if n else "read as printed"
            if base < AUTO or n:
                agree, c2 = second_read(page, w, WL_DIGITS, fixed, lambda x: x)
                if agree:
                    conf, note = max(base, c2), note + "; a second read of the word agrees"
                elif agree is False:
                    conf, note = min(base, c2) * 0.7, note + "; a second read of the word disagrees"
            if not re.fullmatch(r"41\d{5}", fixed):
                conf = min(conf, 0.8)
            b.wo_id = F(fixed, conf, note)
            break
        if re.search(r"w[o0]rk\s*[o0]rder\s*/?\s*P[O0]\s*[:\-]?\s*$", t, re.I):
            b.wo_id = F(None, 0.0, "printed blank: the label is on the bill and no number follows it")
            break

    # ---- HSN or SAC: the first 4 to 8 digit word in the item rows, which lie between the work order line (or the table header) and the taxable value line.
    # The header is not relied on: its wording varies (`Description`, `Item`) and OCR sometimes drops it.
    end = next((i for i, t in enumerate(low) if re.match(r"\s*tax\w{2,4}\s*va", t)), len(lines))
    start = next((i + 1 for i, t in enumerate(low) if re.search(r"w[o0]rk\s*[o0]rder|billing\s*period|^\s*(description|item)", t)), None)
    if start is not None:
        for i in range(start, end):
            t = low[i]
            if re.search(r"w[o0]rk\s*[o0]rder|billing\s*period|^\s*(description|item)|hsn|sac", t) and not re.search(r"\d{1,3},\d{2}", t):
                continue
            toks = [w for w in lines[i] if re.fullmatch(r"\d{4,8}", w.text)]
            if toks and _AMOUNT.search(texts[i]):      # an item row carries an amount; a bank or footer line with a number does not
                b.hsn_sac = F(toks[0].text, toks[0].conf, "code printed in the first item line")
                break

    # ---- amounts
    def amount(ln: list[Word]) -> F:
        toks = [w for w in ln if _AMOUNT.fullmatch(w.text.strip("|"))]
        if not toks:
            return F()
        w = toks[-1]
        v = parse_amount(w.text)
        return F(v, w.conf if v is not None else 0.0, "")

    rates: dict[str, float] = {}
    for ln, t in zip(lines, texts):
        tl = re.sub(r"[^a-z ]", "", t.lower()).strip()
        first = t.split()[0].upper() if t.split() else ""
        if re.match(r"tax\w{2,4}\s*va\w{2,4}", tl) and b.taxable.value is None:
            b.taxable = amount(ln)
        elif first[:4] in ("CGST", "SGST", "IGST") or _ratio(first, "CGST") >= 0.74 and len(first) == 4 or _ratio(first, "SGST") >= 0.74 and len(first) == 4 or _ratio(first, "IGST") >= 0.74 and len(first) == 4:
            kind = max(("CGST", "SGST", "IGST"), key=lambda k: _ratio(first, k)).lower()
            setattr(b, kind, amount(ln))
            r = re.search(r"@\s*(\d+(?:\.\d+)?)\s*%", t)
            if r:
                rates[kind] = float(r.group(1))
        elif re.match(r"(grand\s+)?t[o0]tal\b", tl) and "taxable" not in tl:
            b.total = amount(ln)
        elif "not applicable" in tl or "outside gst" in tl:
            b.no_gst_printed = True

    # ---- cross-checks
    T, G = b.taxable.value, b.total.value
    taxes = [x.value for x in (b.cgst, b.sgst, b.igst) if x.value is not None]
    if T is not None and G is not None:
        tax_sum = sum(taxes)
        sum_ok = abs(T + tax_sum - G) <= 1.0
        rate_ok = all(abs(getattr(b, k).value - T * r / 100) <= 1.0 for k, r in rates.items() if getattr(b, k).value is not None)
        if not taxes and not b.no_gst_printed:
            b.arithmetic_ok = False
            b.reasons.append("no tax line and no 'GST not applicable' line found")
        elif sum_ok and rate_ok:
            b.arithmetic_ok = True
        else:
            b.arithmetic_ok = False
            b.reasons.append(f"taxable {T:,.2f} + tax {tax_sum:,.2f} does not equal total {G:,.2f}" if not sum_ok else "a tax line does not equal the taxable value at its printed rate")
        for f in (b.taxable, b.total, b.cgst, b.sgst, b.igst):
            if f.value is None:
                continue
            if b.arithmetic_ok:
                f.conf = max(f.conf, 0.97)
                f.note = "taxable + tax = total, and each tax line matches its rate"
            else:
                f.conf = min(f.conf, 0.5)
                f.note = "amounts do not add up"
    else:
        b.arithmetic_ok = None
    # date against the financial year in the invoice number
    if b.invoice_date.value and b.invoice_no.value:
        d = date.fromisoformat(b.invoice_date.value)
        fy = _fy_of(b.invoice_no.value)
        if fy and fy[0] <= d <= fy[1]:
            b.invoice_date.conf = min(0.99, b.invoice_date.conf + 0.04)
            b.invoice_date.note += "; inside the financial year in the invoice number"
        elif fy:
            b.invoice_date.conf *= 0.5
            b.invoice_date.note += f"; outside the financial year in the invoice number ({fy[0].year}-{fy[1].year})"
            b.reasons.append("invoice date is outside the financial year in the invoice number")
        if not 2023 <= d.year <= 2026:
            b.invoice_date.conf *= 0.5
            b.reasons.append(f"invoice year {d.year} is implausible")
    # vendor name against the 'For <name>' line at the foot
    foot = next((m.group(1) for t in reversed(texts[-5:]) if (m := re.search(r"\bf[o0]r\s+(\S.*)$", t, re.I))), None)
    if foot and b.vendor_name.value:
        sim = _ratio(foot, b.vendor_name.value)
        if sim >= 0.9:
            b.vendor_name.conf = min(0.99, max(b.vendor_name.conf, 0.9) + 0.03)
            b.vendor_name.note = "agrees with the 'For ...' line at the foot of the bill"
        else:
            b.vendor_name.conf *= 0.6
            b.vendor_name.note = f"differs from the 'For ...' line at the foot (similarity {sim:.2f})"
    return b
