"""Query classification and the vendor-facing status sentence.

Each query's text is matched to one of 26 patterns (the patterns the analysis found in the register, `analysis/out/query_rules.csv`), which give who must
act next (vendor, property, procurement or AP), the reason in plain words and what that party must do. The sentence a vendor reads never carries an
internal name, a verifier id or a tracker number. It says what stage the bill is in, and for a query, the reason and who must act.

Real connection: the sentence would be sent as a WhatsApp Business template message or shown in a vendor link. That needs an approved template for each
sentence, the vendor's recorded opt-in, and the files kept on the company side (see notes/solution-design.md section 7). Here nothing is sent.
"""
from __future__ import annotations

import re

from .ledger import Bill, Query
from .payruns import DEFAULT_CUTOFF_DAYS, label, next_run_for_open_bill

# (pattern searched in the query text, owner, reason in plain words, what the owner must do)
RULES = [
    (r"Same invoice number already booked", "vendor", "an invoice with the same number has already been booked", "confirm whether this is a new bill and, if it is, send it with a new invoice number"),
    (r"Cost centre on service entry belongs to a different property", "property", "the cost centre on the entry in our system belongs to another property", "correct the cost centre"),
    (r"GL on WO .* does not match the expense type", "property", "the accounting code on the work order does not fit this kind of expense", "confirm the right code"),
    (r"WBS element closed", "AP", "the project code for this spend has been closed", "get the project code reopened or replaced"),
    (r"IGST charged on an intra-state supply", "vendor", "the tax type on your bill (IGST) does not fit where the service was supplied", "send a corrected bill with the right tax type"),
    (r"HSN/SAC code missing", "vendor", "the HSN or SAC code is missing from your bill", "send a corrected bill with the code"),
    (r"Tax rate on bill is", "vendor", "the tax rate on your bill does not look right", "send a corrected bill"),
    (r"GSTIN on bill does not match vendor master", "vendor", "the GSTIN on your bill does not match the one we hold for you", "send a corrected bill, or tell us if your GSTIN has changed"),
    (r"Discussed with property team, on hold", "AP", "the bill is on hold after a discussion with the property team", "release it or say what is needed"),
    (r"Pls check WO bal before sending", "procurement", "the work order may not have enough balance left for this bill", "check the balance and extend the order if needed"),
    (r"Bill amount and SE amount not matching", "property", "the bill amount differs from the amount confirmed at the property", "agree the amount and correct the entry"),
    (r"PO not released yet", "procurement", "the purchase order has not been released", "release the order"),
    (r"Wrong company name on bill", "vendor", "the company name on your bill is wrong", "send a corrected bill in the right company name"),
    (r"Hard copy not received yet, only scan", "property", "only a scan has reached us and the original has not", "send the original bill to head office"),
    (r"Vendor bank details changed", "vendor", "your bank details have changed", "send a cancelled cheque"),
    (r"Overtime billed but not approved in WO", "vendor", "overtime is billed that the work order does not cover", "send a corrected bill, or a work-order amendment if it was agreed"),
    (r"Rate on bill is higher than WO rate", "vendor", "the rate on your bill is higher than the work order rate", "send a corrected bill at the work order rate"),
    (r"Service entry still parked", "property", "the property has not yet confirmed receipt of the work in our system", "post the service entry"),
    (r"GRN not found in SAP", "property", "the property has not yet confirmed receipt of the goods in our system", "post the goods receipt"),
    (r"Service report for the quarter not attached", "vendor", "the service report is not attached", "send the signed service report"),
    (r"Delivery challan missing security stamp", "property", "the delivery challan does not carry the security gate stamp", "get the challan stamped"),
    (r"PF and ESIC challan for previous month not attached", "vendor", "the PF and ESIC challans for last month are not attached", "send the challans"),
    (r"Attendance sheet not signed by property head", "property", "the attendance sheet has not been signed by the property head", "get the attendance sheet signed"),
    (r"Quantity billed exceeds open quantity on WO", "procurement", "the quantity billed is more than the work order has left", "extend the order or reduce the bill"),
    (r"WO .* has no balance left for this period", "procurement", "the work order has no balance left for this period", "extend the order or release more value"),
    (r"WO .* expired on \d{2}-\d{2}-\d{4}", "procurement", "the work order had expired on the date of the bill", "extend the work order"),
]
_COMPILED = [(re.compile(p, re.I), o, r, a) for p, o, r, a in RULES]
OWNER_WORDS = {"vendor": "You", "property": "The property team", "procurement": "Our procurement team", "AP": "Our accounts team"}


def classify(text: str) -> tuple[str, str, str]:
    """(owner, reason, action) for a query text. A text matching no pattern goes to AP for a person to read, and says so."""
    for rx, owner, reason, action in _COMPILED:
        if rx.search(text or ""):
            return owner, reason, action
    return "AP", "we are checking a detail on the bill", "look at the query and say who must act"


def make_query(query_id: str, raised, resolved, category: str, text: str) -> Query:
    owner, reason, action = classify(text)
    return Query(query_id, raised, resolved, category, text, owner, reason, action)


def is_classified(text: str) -> bool:
    return any(rx.search(text or "") for rx, *_ in _COMPILED)


def vendor_sentence(b: Bill, cutoff_days: int = DEFAULT_CUTOFF_DAYS) -> str:
    """The status of a bill in plain words, for the vendor."""
    what = "credit note" if b.doc_type == "credit_note" else "bill"
    ref = f"Your {what} {b.invoice_no}"
    e = b.entered
    d = lambda k: label(e[k]) if e.get(k) else "an unrecorded date"
    if b.stage == "paid":
        if "paid_before_posted" in b.flags:
            return f"{ref} has been paid. The payment date is being confirmed."
        return f"{ref} was paid on {d('paid')}."
    q = b.open_query
    if q:
        return (f"{ref} is on hold. On {label(q.raised_date)} we raised a query: {q.reason}. {OWNER_WORDS[q.owner]} must {q.action}.")
    if b.stage == "desk":
        return f"We received {ref[5:]} on {d('desk')}. The property is checking it."
    if b.stage == "verified":
        return f"{ref} was checked at the property on {d('verified')}. It is waiting for the property head's signature."
    if b.stage == "signed":
        return f"{ref} was checked and signed at the property on {d('signed')}. It is on its way to our head office."
    if b.stage == "received":
        return f"{ref} reached our head office on {d('received')} and is waiting for our accounts team to pick it up."
    if b.stage == "picked":
        return f"Our accounts team picked up {ref[5:]} on {d('picked')} and is checking it."
    if b.doc_type == "credit_note":
        return f"{ref} has been booked in our system."  # not a payment-run item here, so no run date is promised
    run = next_run_for_open_bill(e.get("posted"), b.as_of, cutoff_days)
    return f"{ref} has been booked in our system. It can go into the payment run on {label(run)}. Payments go out on Tuesdays and Fridays."
