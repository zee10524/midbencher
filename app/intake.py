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

from dataclasses import replace

from app.reader import pipeline
from app.rules import Context, Field, route
from app.rules import checks as checks_mod
from app.rules.model import LOOK, BillRead, CheckResult
from app.rules.routing import AUTO, HUMAN, RESEND, Action, Routing
from app.sap.adapter import norm_invoice_loose

BLANK_CONF = 0.95   # the reader saw the label and nothing after it: it is sure the number is not printed


def _f(res: dict, name: str, as_date: bool = False) -> Field:
    x = (res.get("fields") or {}).get(name) or {}
    v = x.get("value")
    if v is not None and as_date:
        v = date.fromisoformat(v)
    return Field(v, float(x.get("conf", 0.0) or 0.0), x.get("source", "read") or "read")


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
    date and the same taxable value. Without an invoice number, when exactly one register bill of the same vendor has that date and that taxable value. Used only
    when replaying historical bills; the doubtful reading of an unread number is good enough to find the row, though never to give a verdict."""
    if not (b.invoice_date.value and b.taxable_inr.value is not None):
        return None
    amt = lambda r: abs(float(r.amount) - float(b.taxable_inr.value)) < 0.5
    if b.invoice_no.value:
        key = re.sub(r"^CN", "", norm_invoice_loose(b.invoice_no.value))
        hits = [r for r in ctx.known_bills if re.sub(r"^CN", "", norm_invoice_loose(r.invoice_no)) == key and r.invoice_date == b.invoice_date.value and amt(r)]
        if len(hits) == 1:
            return hits[0].bill_id
    vid = None
    if b.vendor_gstin.value:
        v = ctx.sap.get_vendor(gstin=b.vendor_gstin.value)
        vid = v.vendor.vendor_id if v.status == "found" else None
    if vid:
        hits = [r for r in ctx.register_for(vid) if r.invoice_date == b.invoice_date.value and amt(r)]
        return hits[0].bill_id if len(hits) == 1 else None
    return None


# What each check needs on the bill. A check runs when every field it needs was read at 0.70 or more (or is a work order line seen printed blank).
CHECK_NEEDS = {
    "P1/H1": [("vendor_gstin", "Vendor GSTIN as printed")],
    "P3": [("wo_id", "Work order number")],
    "H3": [("wo_id", "Work order number"), ("invoice_date", "Invoice date"), ("taxable_inr", "Taxable value")],
    "H13": [("vendor_gstin", "Vendor GSTIN"), ("invoice_no", "Invoice number"), ("invoice_date", "Invoice date"), ("taxable_inr", "Taxable value")],
    "H11": [("hsn_sac", "HSN or SAC code"), ("taxable_inr", "Taxable value"), ("tax", "Tax lines"), ("wo_id", "Work order number")],
    "H10": [("vendor_gstin", "Vendor GSTIN"), ("recipient_gstin", "Buyer GSTIN"), ("place_of_supply", "Place of supply"), ("tax", "Tax lines")],
}
PARTIAL_H13 = [("vendor_gstin", "Vendor GSTIN"), ("invoice_date", "Invoice date"), ("taxable_inr", "Taxable value")]
CHECK_TITLE = {"P1/H1": "Vendor GSTIN against the vendor master", "P3": "Work order number on the bill", "H3": "Work order valid, with value left", "H13": "Invoice number already used",
               "H11": "HSN or SAC code and GST rate", "H10": "Tax type against place of supply"}
CHECK_IDS = ("P1/H1", "P3", "H3", "H13", "H11", "H10")
READ_FIELDS = [("vendor_name", "Vendor"), ("vendor_gstin", "Vendor GSTIN"), ("invoice_no", "Invoice number"), ("invoice_date", "Invoice date"), ("wo_id", "Work order"),
               ("taxable", "Taxable value"), ("total", "Total")]


def _conf_of(b: BillRead, name: str) -> float:
    if name == "tax":
        return min(getattr(b, k).confidence for k in ("cgst_inr", "sgst_inr", "igst_inr"))
    return getattr(b, name).confidence


def _available(b: BillRead, name: str, check: str) -> bool:
    if _conf_of(b, name) < LOOK:
        return False
    if name in ("tax", "wo_id"):
        return True                       # tax lines judged together; a work order is a number, or a line seen printed blank
    f = getattr(b, name)
    if name == "vendor_gstin" and check == "P1/H1":
        return f.value is not None and f.source in ("read", "human_review", "repaired")   # a GSTIN looked up from the vendor name says nothing about the printed one
    return f.value is not None


def unread_fields(res: dict) -> list[str]:
    """The names of required fields the reader did not read (not found, or below 0.70), except a work order line seen printed blank. A GSTIN looked up from the vendor
    master by name is not counted as unread: it is shown as resolved from the vendor master, never as read."""
    out = []
    for key, label in READ_FIELDS:
        x = (res.get("fields") or {}).get(key) or {}
        if key == "wo_id" and x.get("value") is None and "printed blank" in x.get("note", ""):
            continue
        if (x.get("cross") or {}).get("state") == "differ":
            continue                 # the two readers differ: not unread, a person settles it (see `disputed_fields`)
        if x.get("value") is None or float(x.get("conf", 0) or 0) < LOOK:
            out.append(label)
    return out


def disputed_fields(res: dict) -> list[str]:
    """The names of fields on which the stored vision reading and Tesseract differ. They are treated as not read until a person types the value."""
    return [label for key, label in READ_FIELDS if ((res.get("fields") or {}).get(key) or {}).get("cross", {}).get("state") == "differ"]


def run_available(b: BillRead, ctx: Context) -> tuple[list, list[dict]]:
    """Run every check whose inputs are available, never stopping at a failure, and list those that could not run with the fields each needs.
    When only the invoice number is missing, the duplicate check runs on vendor, date and amount alone, and says `possible repeat, confirm the invoice number`."""
    results, not_run = [], []
    for cid, fn in zip(CHECK_IDS, checks_mod.CHECKS):
        used = CHECK_NEEDS[cid]
        missing = [lab for name, lab in used if not _available(b, name, cid)]
        if missing and cid == "H13" and missing == ["Invoice number"]:
            fn = lambda bb, cc: checks_mod.check_h13_partial(bb, cc, hint_invoice_no=bb.invoice_no.value)   # noqa: E731
            used, missing = PARTIAL_H13, []
        if missing:
            not_run.append(dict(check=cid, title=CHECK_TITLE[cid], needs=missing))
            continue
        try:
            r = fn(b, ctx)
        except Exception as e:  # noqa: BLE001 - one broken check must not hide the others
            r = CheckResult(check_id=cid, name=CHECK_TITLE[cid], status="warn", evidence={"error": f"{type(e).__name__}: {e}"}, owner="AP", fix="This check could not run. A person must do it by hand.",
                            field_confidence=1.0, certainty=0.0)
        results.append(replace(r, field_confidence=min(_conf_of(b, n) for n, _ in used)))
    return results, not_run


def check_bill(res: dict, ctx: Context) -> dict:
    """Run the checks that can run on one reader result and route it. Returns the BillRead, the CheckResults that ran, the checks that could not run (with the fields each needs),
    the fields not read, and the Routing. A field the reader could not read does not switch off the verdict: the checks that do not need it still run and still route the bill,
    and the unread fields are asked for in a message (or typed by a person). Only a bill on which no check could run is routed `resend`."""
    b = bill_read(res)
    own = find_own_bill(b, ctx)
    b = bill_read(res, own_bill_id=own)
    results, not_run = run_available(b, ctx)
    unread = unread_fields(res)
    disputed = disputed_fields(res)
    routing = route(results) if results else Routing(RESEND, (), ("no check could run on what was read",))
    actions = list(routing.actions)
    if unread:
        actions.append(Action("resend", "vendor", ("read",), "Please send a clearer photo or scan: could not read " + ", ".join(unread) + "."))
    label, reasons = routing.route, list(routing.reasons)
    soft = [lab for key, lab in READ_FIELDS if ((res.get("fields") or {}).get(key) or {}).get("source") in ("vendor_master", "repaired")]
    if unread and label == AUTO:
        label = HUMAN
        reasons.append("the verdict is partial: " + ", ".join(unread) + " could not be read")
    if disputed and label == AUTO:
        label = HUMAN
        reasons.append("the two readers differ on " + ", ".join(disputed) + ": a person decides")
    if soft and label == AUTO:
        label = HUMAN
        reasons.append(", ".join(soft) + " was not read cleanly from the bill (looked up or repaired from the vendor master): a person confirms it")
    return dict(file=res["file"], bill=b, own_bill_id=own, results=results, not_run=not_run, unread=unread, disputed=disputed, partial=bool(not_run or unread or disputed),
                routing=Routing(label, tuple(actions), tuple(reasons)))


def verdict_notes(res: dict, out: dict) -> str:
    """The text for `parsed_bill.check_notes`: the reader's own notes, then every check that did not pass, then the actions."""
    notes = [pipeline.parsed_bill_args(res)["check_notes"]]
    flags = [f"{r.check_id} {r.status}: {r.fix or 'confirm the value read'}" for r in out["results"] if r.status != "pass"]
    notes.append("checks: " + ("; ".join(flags) if flags else "all that ran passed"))
    if out.get("not_run"):
        notes.append("could not run: " + "; ".join(f"{n['check']} (needs {', '.join(n['needs'])})" for n in out["not_run"]))
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
