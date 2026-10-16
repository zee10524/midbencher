"""Seed the ledger from `bill_register.csv` and `queries.csv` as of a date (default 30 April 2026, the date of the extract).

The files are read and never changed. The register's data problems are handled here (notes/data-audit.md):
- D01  rows identical in every column are one bill: later copies are dropped.
- D02  property codes are normalised through the SAP adapter, which knows the 38 real codes.
- D03  a `paid_date` earlier than `posted_date` is kept but flagged `paid_before_posted`: the payment date is not trusted, the bill is still Paid.
- D07  vendors with a blank MSME status are `Unknown`, set by the adapter.
Queries raised after the as-of date are ignored, and a query resolved after it is treated as still open.

Real connection: in production there is no seed. The ledger is built from the event log the intake writes, and SAP is read for posting and payment.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from app.sap.adapter import AS_OF, SapAdapter

from .ledger import STAGES, Bill
from .status import make_query


def _d(x: str) -> date | None:
    return date.fromisoformat(x) if x else None


def read_rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def seed(register_csv: str | Path, queries_csv: str | Path, sap: SapAdapter, as_of: date = AS_OF) -> list[Bill]:
    seen, rows = set(), []
    for r in read_rows(Path(register_csv)):
        key = tuple(r.values())
        if key not in seen:
            seen.add(key)
            rows.append(r)
    queries: dict[str, list] = {}
    for q in read_rows(Path(queries_csv)):
        raised = _d(q["raised_date"])
        if raised is None or raised > as_of:
            continue
        resolved = _d(q["resolved_date"])
        if resolved is not None and resolved > as_of:
            resolved = None
        queries.setdefault(q["bill_id"], []).append(make_query(q["query_id"], raised, resolved, q["query_category"], q["query_text"]))
    vendors, props = {}, {}
    bills = []
    for r in rows:
        vid = r["vendor_id"]
        if vid not in vendors:
            vendors[vid] = sap.get_vendor_by_id(vid)
        v = vendors[vid]
        code = r["property_code"]
        if code not in props:
            p = sap.get_property(code)
            props[code] = p.property_code if p else code.strip().upper()
        entered = {key: _d(r[col]) for key, col, _, _ in STAGES}
        flags = []
        if entered["paid"] and entered["posted"] and entered["paid"] < entered["posted"]:
            flags.append("paid_before_posted")
        if v is None:
            flags.append("vendor_not_in_master")
        bills.append(Bill(
            bill_id=r["bill_id"], vendor_id=vid, vendor_name=v.name if v else vid, msme_status=v.msme_status if v else "Unknown", property_code=props[code],
            category=r["category"], doc_type=r["doc_type"], invoice_no=r["invoice_no"], invoice_date=_d(r["invoice_date"]), amount=float(r["amount_inr"] or 0),
            gst=float(r["gst_inr"] or 0), wo_id=r["wo_id"], verifier=r["ho_verifier"], entered=entered, queries=tuple(queries.get(r["bill_id"], ())),
            as_of=as_of, flags=tuple(flags)))
    return bills
