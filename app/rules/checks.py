"""The intake checks in the Saturday slice (notes/solution-design.md sections 4, 5 and 9): P1/H1, P3, H3, H13, H11 and the H10 facts.

`run_all(bill, ctx)` runs every check on the bill and returns every result. It never stops at the first failure, and a check that raises is recorded as a
`warn` that it could not run, so one failing rule cannot hide the others. A bill that fails in sequence would otherwise get one query per failure.

Checks that need the rest of the packet (attendance sheet, PF and ESIC challans, gate stamp, service report: P6 to P9, H6 to H9) cannot run on a bill alone and
are not built here. Rate against the work order (P4/H4), entity and property (P2/H2) need data the pack does not hold. Quantity, service entry, GL and cost
centre, and TDS (P5, P10, P11, H5, H12, H14) depend on a step that has not happened at intake. The full table is in notes/solution-design.md section 4.

Real connection: every lookup goes through app/sap/adapter.py, whose docstrings name the RFC or BAPI access each would need. The checks themselves do not change.
"""
from __future__ import annotations

import re
from datetime import date

from app.sap.adapter import norm_invoice_loose, norm_name

from .model import FAIL, NEEDS_DOC, PASS, WARN, BillRead, CheckResult, Context

STATE_NAMES = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan",
    "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura", "17": "Meghalaya",
    "18": "Assam", "19": "West Bengal", "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra and Nagar Haveli and Daman and Diu", "27": "Maharashtra", "29": "Karnataka", "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
    "34": "Puducherry", "35": "Andaman and Nicobar Islands", "36": "Telangana", "37": "Andhra Pradesh", "38": "Ladakh"}
_STATE_CODE = {re.sub(r"[^a-z]", "", v.lower()): k for k, v in STATE_NAMES.items()} | {"newdelhi": "07", "orissa": "21"}
_GSTIN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
_HSN_SAC = re.compile(r"^[0-9]{4}([0-9]{2}([0-9]{2})?)?$")  # 4, 6 or 8 digits
STANDARD_RATE = 18.0
NO_GST_CATEGORIES = {"Diesel Supply"}  # in the register diesel carries no GST
RATE_TOLERANCE = 0.15  # percentage points; amounts are rounded to whole rupees


def _rupees(x) -> str:
    return "minus ₹" + f"{abs(x):,.0f}" if x < 0 else f"₹{x:,.0f}"


def _conf(*fields) -> float:
    return min((f.confidence for f in fields), default=1.0)


def state_code(x) -> str | None:
    """A two-digit GST state code from a GSTIN, a code or a state name."""
    s = str(x or "").strip()
    if re.fullmatch(r"[0-9]{2}", s):
        return s
    if len(s) >= 2 and s[:2].isdigit() and _GSTIN.match(s.upper()):
        return s[:2]
    return _STATE_CODE.get(re.sub(r"[^a-z]", "", s.lower()))


def _vendor_id(bill: BillRead, ctx: Context) -> str | None:
    r = ctx.sap.get_vendor(gstin=bill.vendor_gstin.value) if bill.vendor_gstin.value else ctx.sap.get_vendor(name=bill.vendor_name.value)
    return r.vendor.vendor_id if r.status == "found" else None


# ----------------------------------------------------------------------------------------------- P1 / H1
def check_p1_h1(bill: BillRead, ctx: Context) -> CheckResult:
    """Vendor name and GSTIN on the bill match the vendor master (P1, H1: one implementation).

    pass: the GSTIN is well formed, is in the master, and the name agrees after normalising.
    fail (vendor): the GSTIN is malformed, or differs from the record of the vendor whose name is on the bill.
    warn: the GSTIN is in the master under a different name, or the vendor is not in the master at all (owner unclear).
    """
    g, n = bill.vendor_gstin, bill.vendor_name
    printed = (g.value or "").replace(" ", "").upper()
    ev = {"gstin_on_bill": printed or None, "name_on_bill": n.value}
    fc = _conf(g, n)
    base = dict(check_id="P1/H1", name="Vendor name and GSTIN match the vendor master", field_confidence=fc)
    if not printed:
        return CheckResult(**base, status=FAIL, evidence=ev, owner="vendor", fix="The GSTIN is missing from the bill. Send the bill again with the supplier GSTIN printed.")
    if not _GSTIN.match(printed):
        return CheckResult(**base, status=FAIL, evidence=ev | {"format_ok": False}, owner="vendor",
                           fix=f"The GSTIN on the bill ({printed}) is not a valid 15-character GSTIN. Send a corrected bill.")
    hit = ctx.sap.get_vendor(gstin=printed, name=n.value)
    if hit.status == "found":
        v = hit.vendor
        ev |= {"master_name": v.name, "master_gstin": v.gstin, "vendor_id": v.vendor_id, "name_matches": hit.name_match}
        if hit.name_match is not False:
            return CheckResult(**base, status=PASS, evidence=ev, owner=None, fix="")
        return CheckResult(**base, status=WARN, evidence=ev, owner="vendor",
                           fix=f"The GSTIN is ours on file but the name on the bill ({n.value}) differs from the record ({v.name}). Confirm it is the same supplier.")
    by_name = ctx.sap.get_vendor(name=n.value) if n.value else None
    if by_name is not None and by_name.status == "found":
        v = by_name.vendor
        ev |= {"master_name": v.name, "master_gstin": v.gstin, "vendor_id": v.vendor_id}
        return CheckResult(**base, status=FAIL, evidence=ev, owner="vendor",
                           fix=f"The GSTIN on the bill ({printed}) differs from our record for {v.name}. Send a corrected bill, or tell us if your GSTIN has changed.")
    return CheckResult(**base, status=WARN, evidence=ev | {"in_master": False}, owner="AP",
                       fix="This GSTIN and name are not in the vendor master. A person must check whether this is a new vendor or a wrong bill.")


# ----------------------------------------------------------------------------------------------- P3
def check_p3(bill: BillRead, ctx: Context) -> CheckResult:
    """The work order or purchase order number is on the bill, and the number exists in SAP."""
    w = bill.wo_id
    base = dict(check_id="P3", name="Work order number is on the bill and exists in SAP", field_confidence=_conf(w))
    wid = (str(w.value).strip() if w.value is not None else "")
    if not wid:
        return CheckResult(**base, status=FAIL, evidence={"wo_on_bill": None}, owner="vendor", fix="The work order or purchase order number is missing. Send the bill again with it printed.")
    wo = ctx.sap.get_work_order(wid)
    if wo is None:
        return CheckResult(**base, status=FAIL, evidence={"wo_on_bill": wid, "in_sap": False}, owner="vendor",
                           fix=f"The work order number {wid} is not one we have. Check the number and send a corrected bill.")
    return CheckResult(**base, status=PASS, evidence={"wo_on_bill": wid, "in_sap": True, "wo_vendor_id": wo.vendor_id, "wo_property": wo.property_code}, owner=None, fix="")


# ----------------------------------------------------------------------------------------------- H3
def check_h3(bill: BillRead, ctx: Context) -> CheckResult:
    """The work order is valid on the bill date, and has value left after this bill (value headroom: the extract has no period balance or open quantity).

    fail (procurement): not yet valid or expired on the bill date, or the value left after this bill is below zero. Both are reported when both apply.
    warn (procurement): the validity dates are unusable (end before start), so validity cannot be judged.
    needs-document: the work order is missing or unknown, or the date or amount was not read, so the check cannot run.
    An expiry is flagged as possibly stale: the extract may not carry amendments, so the route is a task, not a block.
    """
    w, d, a = bill.wo_id, bill.invoice_date, bill.taxable_inr
    base = dict(check_id="H3", name="Work order valid on the bill date, with value left", field_confidence=_conf(w, d, a))
    wo = ctx.sap.get_work_order(str(w.value).strip(), d.value) if w.value and d.value else None
    if wo is None:
        return CheckResult(**base, status=NEEDS_DOC, evidence={"wo_on_bill": w.value, "bill_date": d.value}, owner="vendor",
                           fix="The work order, or the bill date, could not be used, so validity and balance cannot be checked. Send the bill with the work order number and date clear.")
    remaining = wo.remaining
    headroom = None if remaining is None else (remaining if ctx.bill_counted_in_billed else (None if a.value is None else wo.headroom_after(float(a.value))))
    ev = {"wo_id": wo.wo_id, "valid_from": wo.valid_from, "valid_to": wo.valid_to, "bill_date": d.value, "validity": wo.validity, "approved_inr": wo.approved,
          "billed_inr": wo.billed, "bill_taxable_inr": a.value, "headroom_after_inr": headroom, "bill_already_in_billed": ctx.bill_counted_in_billed}
    problems, status = [], PASS
    if wo.validity in ("expired", "not_yet_valid"):
        status = FAIL
        ev["expiry_may_be_stale"] = wo.expiry_may_be_stale
        edge = f"ended on {wo.valid_to:%d %b %Y}" if wo.validity == "expired" else f"starts on {wo.valid_from:%d %b %Y}"
        problems.append(f"The work order {wo.wo_id} {edge}, which is {'before' if wo.validity == 'expired' else 'after'} the bill date {d.value:%d %b %Y}. "
                        "Start the amendment now and collect the papers it needs (the extract may not show an amendment already made).")
    elif wo.validity == "unknown":
        status = WARN
        problems.append(f"The validity dates of work order {wo.wo_id} cannot be used (end date before start date). A person must check the work order.")
    if headroom is not None and headroom < 0:
        status = FAIL
        problems.append(f"After this bill the work order {wo.wo_id} is over its approved value by {_rupees(-headroom)}. Extend the value before the service entry is made.")
    elif headroom is None and status == PASS:
        status = WARN
        problems.append("The value left on the work order could not be worked out. A person must check it.")
    return CheckResult(**base, status=status, evidence=ev, owner=None if status == PASS else "procurement", fix=" ".join(problems))


# ----------------------------------------------------------------------------------------------- H13
def check_h13(bill: BillRead, ctx: Context) -> CheckResult:
    """The invoice number has not been booked before for this vendor, ignoring the bill's own row. Near-duplicates count: case, slashes, dashes and spaces are ignored.

    Loose matching is used at intake only. The backtest and the impact figures (`backtest/replay.py`) use exact matching, and the register holds no near-duplicate
    for loose matching to add (`ld.extra.flagged` in notes/numbers.md), so its value is untested on real rows and shown only by constructed variants in the unit tests.

    fail (vendor): an earlier bill of the vendor has the same number, the same invoice date and the same amount.
    warn (AP): an earlier bill has the same number but another date or amount (invoice numbers are reused in this data), so a person decides.
    """
    no, d, a = bill.invoice_no, bill.invoice_date, bill.taxable_inr
    base = dict(check_id="H13", name="Invoice number not booked before for this vendor", field_confidence=_conf(no, d, a, bill.vendor_gstin))
    vid = _vendor_id(bill, ctx)
    if vid is None or not no.value:
        return CheckResult(**base, status=WARN, evidence={"vendor_id": vid, "invoice_no": no.value}, owner="AP",
                           fix="The vendor or the invoice number could not be identified, so earlier bills cannot be checked. A person must check for a duplicate.")
    want = norm_invoice_loose(no.value)
    seen: dict[str, dict] = {}
    for p in ctx.sap.find_posted_invoices(vid, no.value, loose=True):
        seen[p.bill_id] = dict(bill_id=p.bill_id, invoice_no=p.invoice_no, invoice_date=p.invoice_date, amount_inr=p.amount, source="posted in SAP")
    for r in ctx.register_for(vid):
        if norm_invoice_loose(r.invoice_no) == want:
            seen.setdefault(r.bill_id, dict(bill_id=r.bill_id, invoice_no=r.invoice_no, invoice_date=r.invoice_date, amount_inr=r.amount, source="register"))
    matches = [m for m in seen.values() if m["bill_id"] != bill.own_bill_id]
    for m in matches:
        m["exact_text"] = m["invoice_no"] == no.value
        m["same_date"] = m["invoice_date"] == d.value
        m["same_amount"] = a.value is not None and m["amount_inr"] is not None and abs(float(m["amount_inr"]) - float(a.value)) < 0.5
    ev = {"vendor_id": vid, "invoice_no_on_bill": no.value, "matches": matches}
    if not matches:
        return CheckResult(**base, status=PASS, evidence=ev, owner=None, fix="")
    twin = next((m for m in matches if m["same_date"] and m["same_amount"]), None)
    if twin:
        kind = "the same" if twin["exact_text"] else "a near-identical"
        return CheckResult(**base, status=FAIL, evidence=ev, owner="vendor",
                           fix=f"A bill with {kind} number ({twin['invoice_no']}), the same date and the same amount is already booked. Confirm this is not a second copy; if it is a new bill, send it with a new invoice number.")
    return CheckResult(**base, status=WARN, evidence=ev, owner="AP",
                       fix=f"The invoice number is already used by {len(matches)} earlier bill(s) of this vendor with a different date or amount. A person must decide whether this is a reused number or a duplicate.")


# ----------------------------------------------------------------------------------------------- H11
def check_h11(bill: BillRead, ctx: Context) -> CheckResult:
    """The HSN or SAC code is on the bill and well formed (4, 6 or 8 digits), and the GST rate is the rate that applies: 18% for the services and goods in
    the register, none for diesel. The category comes from the work order. The code is checked for presence and form only: the pack holds no code table.

    fail (vendor): the code is missing or malformed, or the rate printed is not the rate that applies. Both are reported when both apply.
    needs-document: the taxable value or the tax lines were not read.
    warn (AP): the category of the supply cannot be found, so the rate cannot be judged.
    """
    h, a = bill.hsn_sac, bill.taxable_inr
    base = dict(check_id="H11", name="HSN or SAC code present, and GST rate correct", field_confidence=_conf(h, a, bill.cgst_inr, bill.sgst_inr, bill.igst_inr))
    code = re.sub(r"\s+", "", str(h.value)) if h.value else ""
    tax = bill.tax_inr
    ev = {"hsn_sac": code or None, "taxable_inr": a.value, "tax_inr": tax}
    problems, status = [], PASS
    if not code:
        status = FAIL
        problems.append("The HSN or SAC code is missing from the bill. Send a corrected bill with the code.")
    elif not _HSN_SAC.match(code):
        status = FAIL
        problems.append(f"The HSN or SAC code {code} is not a valid 4, 6 or 8 digit code. Send a corrected bill.")
    if a.value in (None, 0) or tax is None:
        return CheckResult(**base, status=NEEDS_DOC if status == PASS else FAIL, evidence=ev | {"rate_checked": False}, owner="vendor",
                           fix=" ".join(problems + ["The taxable value or the tax lines could not be read, so the GST rate cannot be checked. Send the bill page with the tax lines clear."]))
    wo = ctx.sap.get_work_order(str(bill.wo_id.value).strip()) if bill.wo_id.value else None
    category = wo.category if wo else None
    rate = round(100 * tax / float(a.value), 2)
    ev |= {"rate_printed_pct": rate, "category": category}
    if category is None:
        status = FAIL if status == FAIL else WARN
        problems.append("The type of supply could not be found from the work order, so the GST rate cannot be judged. A person must check the rate.")
        owner = "vendor" if status == FAIL else "AP"
    else:
        expected = 0.0 if category in NO_GST_CATEGORIES else STANDARD_RATE
        ev["rate_expected_pct"] = expected
        owner = "vendor"
        if abs(rate - expected) > RATE_TOLERANCE:
            status = FAIL
            problems.append(f"The GST rate on the bill is {rate:g}% but {expected:g}% applies to {category}. Send a corrected bill.")
    return CheckResult(**base, status=status, evidence=ev, owner=None if status == PASS else owner, fix=" ".join(problems))


# ----------------------------------------------------------------------------------------------- H10 (facts)
def check_h10(bill: BillRead, ctx: Context) -> CheckResult:
    """GST type against place of supply: shows the facts and never fails the bill, because the place-of-supply rule is unsettled (notes/research.md section 7).

    The facts: the supplier's state (from its GSTIN), the recipient's state (from the recipient GSTIN printed), the place of supply printed, and the tax charged.
    Two readings: supplier against recipient location, and supplier against the printed place of supply. Each says whether IGST or CGST plus SGST applies.
    pass: both readings agree with the tax charged, or no GST is charged. warn (AP): the readings disagree with each other or with the tax charged; the facts
    are in the evidence for a person. needs-document: the recipient GSTIN or the place of supply was not read.
    """
    base = dict(check_id="H10", name="GST type against place of supply: the facts", field_confidence=_conf(bill.vendor_gstin, bill.recipient_gstin, bill.place_of_supply, bill.cgst_inr, bill.sgst_inr, bill.igst_inr))
    sup, rec, pos = state_code(bill.vendor_gstin.value), state_code(bill.recipient_gstin.value), state_code(bill.place_of_supply.value)
    igst, cs = float(bill.igst_inr.value or 0), float(bill.cgst_inr.value or 0) + float(bill.sgst_inr.value or 0)
    charged = "none" if igst == 0 and cs == 0 else "IGST" if igst > 0 and cs == 0 else "CGST+SGST" if cs > 0 and igst == 0 else "mixed"
    ev = {"supplier_state": STATE_NAMES.get(sup, sup), "recipient_state": STATE_NAMES.get(rec, rec), "place_of_supply": STATE_NAMES.get(pos, bill.place_of_supply.value), "tax_charged": charged}
    if charged == "none":
        return CheckResult(**base, status=PASS, evidence=ev | {"note": "no GST charged"}, owner=None, fix="")
    if sup is None or rec is None or pos is None:
        missing = [n for n, v in (("supplier GSTIN", sup), ("recipient GSTIN", rec), ("place of supply", pos)) if v is None]
        return CheckResult(**base, status=NEEDS_DOC, evidence=ev, owner="vendor", fix=f"The bill page showing the {', '.join(missing)} is needed to compare the tax type with the place of supply.")
    want = lambda other: "CGST+SGST" if sup == other else "IGST"
    by_recipient, by_pos = want(rec), want(pos)
    ev |= {"expected_by_recipient_location": by_recipient, "expected_by_printed_place_of_supply": by_pos}
    if by_recipient == by_pos == charged:
        return CheckResult(**base, status=PASS, evidence=ev, owner=None, fix="")
    agree = by_recipient == by_pos
    return CheckResult(**base, status=WARN, evidence=ev, owner="AP", certainty=1.0 if agree else 0.5,
                       fix=("The tax type charged differs from what both readings give. A person must check it." if agree else
                            "The two readings of the place of supply give different tax types, so the law does not settle this from the bill. A person must decide."))


CHECKS = [check_p1_h1, check_p3, check_h3, check_h13, check_h11, check_h10]


def run_all(bill: BillRead, ctx: Context) -> list[CheckResult]:
    """Run every check on the bill and return all results, in order. A check that raises becomes a `warn` saying it could not run; none is skipped."""
    out = []
    for fn in CHECKS:
        try:
            out.append(fn(bill, ctx))
        except Exception as e:  # noqa: BLE001 - one broken check must not hide the others
            out.append(CheckResult(check_id=fn.__name__.removeprefix("check_").upper().replace("_", "/"), name=fn.__doc__.splitlines()[0] if fn.__doc__ else fn.__name__,
                                   status=WARN, evidence={"error": f"{type(e).__name__}: {e}"}, owner="AP", fix="This check could not run. A person must do it by hand.",
                                   field_confidence=1.0, certainty=0.0))
    return out
