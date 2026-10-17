"""Intake: a read bill goes through the checks to a verdict and into `parsed_bill`.

    reader result (app/reader) -> BillRead with the reader's confidences -> every check (app/rules) -> routing -> `parsed_bill` row

`bill_read(result)` turns the reader's cached result into the `BillRead` the checks take. A field the reader did not find stays None with confidence 0, so the routing
asks for a clearer image rather than failing the bill for something the reader may simply have missed. A tax line that is not printed counts as 0 only when the amounts
the reader did find add up (taxable value plus tax equals total). The one exception is a work order line the reader saw printed
blank: that is a fact about the bill, so it is None with high confidence and check P3 fails it for the vendor to fix.

`own_bill_id` links a bill in the inbox to its own row in the register, so the duplicate check ignores itself. This is only for replaying historical bills, where the
bill is already in the register and already counted in its work order's billed value (`Context.bill_counted_in_billed`). In live use there is no own row.

Real connection: the same function runs on a bill as it arrives. The verdict would be sent as the WhatsApp message or task that `app/rules/routing.py` describes, and
`parsed_bill` would live in the product's own store; nothing is sent or posted here.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from app.reader import pipeline
from app.rules import Context, Field, read, route, run_all
from app.rules.model import BillRead
from app.sap.adapter import norm_invoice_loose

BLANK_CONF = 0.95   # the reader saw the label and nothing after it: it is sure the number is not printed


def _f(res: dict, name: str, as_date: bool = False) -> Field:
    x = (res.get("fields") or {}).get(name) or {}
    v = x.get("value")
    if v is not None and as_date:
        v = date.fromisoformat(v)
    return Field(v, float(x.get("conf", 0.0) or 0.0))


def bill_read(res: dict, own_bill_id: str | None = None) -> BillRead:
    """The BillRead for a reader result. If the bill prints 'GST not applicable', the three tax lines are 0 with the reader's confidence in that line."""
    wo = _f(res, "wo_id")
    if wo.value is None and "printed blank" in ((res.get("fields") or {}).get("wo_id") or {}).get("note", ""):
        wo = Field(None, BLANK_CONF)
    tax = {k: _f(res, k) for k in ("cgst", "sgst", "igst")}
    if res.get("no_gst_printed") and all(t.value is None for t in tax.values()):
        tax = {k: Field(0.0, _f(res, "total").confidence) for k in tax}
    elif res.get("arithmetic_ok") is True:
        # taxable + the tax lines read = total, so a tax line that is not printed (CGST and SGST on an IGST bill, say) is genuinely absent: its value is 0
        tax = {k: (t if t.value is not None else Field(0.0, _f(res, "taxable").confidence)) for k, t in tax.items()}
    return BillRead(source_file=res["file"], own_bill_id=own_bill_id, vendor_gstin=_f(res, "vendor_gstin"), vendor_name=_f(res, "vendor_name"), invoice_no=_f(res, "invoice_no"),
                    invoice_date=_f(res, "invoice_date", True), wo_id=wo, taxable_inr=_f(res, "taxable"), cgst_inr=tax["cgst"], sgst_inr=tax["sgst"], igst_inr=tax["igst"],
                    hsn_sac=_f(res, "hsn_sac"), place_of_supply=_f(res, "place_of_supply"), recipient_gstin=_f(res, "recipient_gstin"))


def find_own_bill(b: BillRead, ctx: Context) -> str | None:
    """The register bill that is this inbox bill, when exactly one register bill has the same invoice number (case, slashes and a leading CN ignored), the same
    date and the same taxable value. Used only when replaying historical bills."""
    if not (b.invoice_no.value and b.invoice_date.value and b.taxable_inr.value is not None):
        return None
    key = re.sub(r"^CN", "", norm_invoice_loose(b.invoice_no.value))
    hits = [r for r in ctx.known_bills if re.sub(r"^CN", "", norm_invoice_loose(r.invoice_no)) == key and r.invoice_date == b.invoice_date.value
            and abs(float(r.amount) - float(b.taxable_inr.value)) < 0.5]
    return hits[0].bill_id if len(hits) == 1 else None


def check_bill(res: dict, ctx: Context) -> dict:
    """Run every check on one reader result and route it. Returns the BillRead, every CheckResult and the Routing."""
    b = bill_read(res)
    own = find_own_bill(b, ctx)
    b = bill_read(res, own_bill_id=own)
    results = run_all(b, ctx)
    return dict(file=res["file"], bill=b, own_bill_id=own, results=results, routing=route(results))


def verdict_notes(res: dict, out: dict) -> str:
    """The text for `parsed_bill.check_notes`: the reader's own notes, then every check that did not pass, then the actions."""
    notes = [pipeline.parsed_bill_args(res)["check_notes"]]
    flags = [f"{r.check_id} {r.status}: {r.fix or 'confirm the value read'}" for r in out["results"] if r.status != "pass"]
    notes.append("checks: " + ("; ".join(flags) if flags else "all passed"))
    notes.append("actions: " + (" | ".join(f"{a.kind} to {a.to} ({', '.join(a.checks)})" for a in out["routing"].actions) or "none"))
    if out["own_bill_id"]:
        notes.append(f"replay: this bill is {out['own_bill_id']} in the register")
    return " ".join(notes)


def run_inbox(inbox: Path = pipeline.INBOX, write: bool = True, db: Path | None = None) -> list[dict]:
    """Read every inbox file (from the cache if it is there), run the checks, route, and write one `parsed_bill` row per file with the verdict as `check_status`.

    The rows go to a fresh working copy of the SAP stand-in (the pack is never written to). The register is read for the duplicate check, as a replay of last year."""
    from app.sap.adapter import SapAdapter
    from app.tracker import seed

    work = pipeline.make_working_copy() if (write and db is None) else Path(db or pipeline.PACK_DB)
    out = []
    with SapAdapter(work) as sap:
        bills = seed(pipeline.ROOT / "pack" / "data" / "bill_register.csv", pipeline.ROOT / "pack" / "data" / "queries.csv", sap)
        ctx = Context(sap, bills, bill_counted_in_billed=True)
        for path in sorted(p for p in Path(inbox).iterdir() if p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png"}):
            res = pipeline.read_file(path, sap=sap)
            o = check_bill(res, ctx)
            o["reader"] = res
            if write:
                a = pipeline.parsed_bill_args(res)
                a["check_status"] = o["routing"].route
                a["check_notes"] = verdict_notes(res, o)
                sap.write_parsed_bill(**a)
            out.append(o)
    return out
