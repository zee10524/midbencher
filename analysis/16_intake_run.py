"""Run all 40 inbox bills through the reader's results, the checks, the routing and `parsed_bill`, and list which bills raise which flags.

The reader results come from the cache (`python -m app.reader`), the checks from `app/rules`, the register for the duplicate check from `bill_register.csv`. The bills are
historical, so each is already in the register and already counted in its work order's billed value: the duplicate check ignores a bill's own register row and the balance
check does not take the bill's amount off the balance a second time (`app/intake.py`). One row per file is written to `parsed_bill` in a fresh working copy of the SAP
stand-in (app/data/sap_working.sqlite, git-ignored), with the verdict in `check_status`.

Writes analysis/out/figures_intake.csv and notes/intake-run.md.   Run: python analysis/16_intake_run.py
"""
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.intake import run_inbox  # noqa: E402
from app.reader import pipeline  # noqa: E402

OUT = ROOT / "analysis" / "out"
runs = run_inbox()
TYPES = ["pdf_single", "pdf_packet", "phone_photo"]
ROUTES = ["auto-clear", "fix-before-sending", "fix-internal", "human-look", "resend"]
by_file = {o["file"]: o for o in runs}
rows = sqlite3.connect(f"file:{pipeline.WORKING_DB.as_posix()}?mode=ro", uri=True).execute("select count(*), count(distinct source_file) from parsed_bill").fetchone()
assert rows == (40, 40), rows

figs = [("ir.files", len(runs), "bills run through reader results, checks, routing and parsed_bill"), ("ir.parsed_bill_rows", rows[0], "rows written to parsed_bill in the working copy")]
for t in ["all", *TYPES]:
    rs = [o for o in runs if t == "all" or o["reader"]["bill_type"] == t]
    c = Counter(o["routing"].route for o in rs)
    for r in ROUTES:
        figs.append((f"ir.{t}.route.{r}", c.get(r, 0), f"verdict {r}, {t}"))
    figs.append((f"ir.{t}.files", len(rs), f"bills, {t}"))
checks = ["P1/H1", "P3", "H3", "H13", "H11", "H10"]
cs = Counter((r.check_id, r.status) for o in runs for r in o["results"])
for cid in checks:
    figs.append((f"ir.check.{cid}.not_run", sum(any(n["check"] == cid for n in o["not_run"]) for o in runs), f"bills where check {cid} could not run (a field it needs was not read)"))
    for st in ["pass", "fail", "warn", "needs-document"]:
        figs.append((f"ir.check.{cid}.{st}", cs.get((cid, st), 0), f"bills where check {cid} returns {st}"))


def res_of(o, cid):
    return next((r for r in o["results"] if r.check_id == cid), None)


def h3(o):
    return res_of(o, "H3")


exp = [o for o in runs if h3(o) and h3(o).status == "fail" and h3(o).evidence.get("validity") in ("expired", "not_yet_valid")]
exh = [o for o in runs if h3(o) and h3(o).status == "fail" and (h3(o).evidence.get("headroom_after_inr") or 0) < 0]
both = [o for o in exp if o in exh]
figs += [("ir.h3.expired", len(exp), "bills whose work order is expired (or not yet valid) on the bill date"), ("ir.h3.exhausted", len(exh), "bills whose work order is over its approved value after the bill"),
         ("ir.h3.both", len(both), "bills with both"), ("ir.h3.fail_any", sum(bool(h3(o)) and h3(o).status == "fail" for o in runs), "bills where H3 fails")]
h10 = [o for o in runs if res_of(o, "H10") and res_of(o, "H10").status == "warn"]
figs.append(("ir.h10.warn_two_readings_differ", sum(res_of(o, "H10").certainty < 1 for o in h10), "bills where H10 warns because the two place-of-supply readings give different tax types"))
figs.append(("ir.reader_ok_but_flagged", sum(o["reader"]["status"] == "ok" and any(r.status in ("fail", "warn") for r in o["results"]) for o in runs), "bills the reader passes (status ok) that a check still fails or warns on"))
figs.append(("ir.own_row_linked", sum(o["own_bill_id"] is not None for o in runs), "inbox bills linked to their own register row (needed to replay the duplicate check)"))
pd.DataFrame(figs, columns=["id", "value", "description"]).to_csv(OUT / "figures_intake.csv", index=False, lineterminator="\n")
F = {k: v for k, v, _ in figs}


def flags(o):
    return [r for r in o["results"] if r.status != "pass"]


def plain(r):
    ev = r.evidence
    if r.check_id == "H3" and r.status == "fail":
        bits = []
        if ev.get("validity") in ("expired", "not_yet_valid"):
            bits.append(f"work order {ev['validity'].replace('_', ' ')} (valid to {ev.get('valid_to')}, bill dated {ev.get('bill_date')})")
        if (ev.get("headroom_after_inr") or 0) < 0:
            bits.append(f"over approved value by Rs {-ev['headroom_after_inr']:,.0f}")
        return "; ".join(bits)
    if r.check_id == "H13":
        m = ev.get("matches", [])
        return "same vendor and invoice number as " + ", ".join(f"{x['bill_id']} ({x['invoice_date']}, Rs {float(x['amount_inr']):,.0f})" for x in m[:2]) if m else r.fix
    if r.check_id == "H10":
        return f"supplier {ev.get('supplier_state')}, recipient {ev.get('recipient_state')}, printed place of supply {ev.get('place_of_supply')}, tax charged {ev.get('tax_charged')}"
    return r.fix[:140]


tab = ["| Bill | Type | Verdict | Flags raised (check: status) |", "|---|---|---|---|"]
for o in runs:
    fl = flags(o)
    tab.append(f"| `{o['file']}` | {o['reader']['bill_type']} | {o['routing'].route} | " + ("; ".join(f"{r.check_id}: {r.status}" for r in fl) if fl else "none") + " |")


def block(title, sel, kinds):
    L = [f"### {title}", "", "| Bill | Check | Status | What it found |", "|---|---|---|---|"]
    for o in sel:
        for r in o["results"]:
            if r.check_id in kinds and r.status != "pass":
                L.append(f"| `{o['file']}` | {r.check_id} | {r.status} | {plain(r)} |")
    return L


p8, p10 = by_file["packet-08-repeat-invoice.pdf"], by_file["packet-10-credit-note.pdf"]
md = ["# Intake run: all 40 bills through reader, checks, verdict and parsed_bill", "",
      "Generated by `analysis/16_intake_run.py`; counts are registered in `notes/numbers.md` under `ir.*`. The bills are last year's, so each is already in the register and already counted in its work order's billed value: the "
      "duplicate check ignores the bill's own register row, and the balance check does not take the bill off the balance a second time. Checks run on what the reader read, at the reader's confidence: a field it could not read sends the bill to `resend`, "
      "it does not fail the bill. One row per file is in `parsed_bill` (working copy `app/data/sap_working.sqlite`) with the verdict in `check_status`.", "",
      "## Verdicts", "", "| Verdict | pdf_single | pdf_packet | phone_photo | All |", "|---|---|---|---|---|"]
for r in ROUTES:
    md.append(f"| {r} | " + " | ".join(str(int(F[f'ir.{t}.route.{r}'])) for t in [*TYPES, "all"]) + " |")
md.append("| **Files** | " + " | ".join(str(int(F[f'ir.{t}.files'])) for t in [*TYPES, "all"]) + " |")
auto = [o["file"] for o in runs if o["routing"].route == "auto-clear"]
md += ["", (f"{len(auto)} bill(s) are `auto-clear`: " + ", ".join(f"`{a}`" for a in auto) + ". " if auto else "No bill is `auto-clear`. ") +
       "Every other bill has a check that is not a clean pass, or a field a check needs read below 0.90. "
       f"The reader passes {int(F['ir.reader_ok_but_flagged'])} bill(s) that a check still fails or warns on, which is what the checks are for.", "",
       "## Check results across the 40 bills", "", "| Check | pass | fail | warn | needs-document | could not run |", "|---|---|---|---|---|---|"]
for cid in checks:
    md.append(f"| {cid} | " + " | ".join(str(int(F[f'ir.check.{cid}.{s}'])) for s in ["pass", "fail", "warn", "needs-document", "not_run"]) + " |")
md += ["", "## The two bills you asked about", "",
       f"**`packet-08-repeat-invoice.pdf`**: verdict **{p8['routing'].route}**. " + "; ".join(f"{r.check_id} {r.status} ({plain(r)})" for r in flags(p8)) + ". "
       f"Its reader confidence in the invoice number is {p8['reader']['fields']['invoice_no']['conf']:.2f}, which is what sends it to `resend`; the checks would otherwise route it to a human look.", "",
       f"**`packet-10-credit-note.pdf`**: verdict **{p10['routing'].route}**, read as a {p10['reader'].get('doc_type', 'unknown').replace('_', ' ')}. " + "; ".join(f"{r.check_id} {r.status}" for r in flags(p10)) +
       ". The vendor GSTIN was not read (the OCR added a character and the reader rejects a GSTIN that is not 15 characters), so the vendor-dependent checks cannot run and the verdict is `resend` for that reason, not because the credit note is wrong.", ""]
md += block("Work orders expired or exhausted (check H3)", [o for o in runs if h3(o) and h3(o).status == "fail"], {"H3"}) + [""]
md += [f"{int(F['ir.h3.fail_any'])} bills fail H3: {int(F['ir.h3.expired'])} on an expired work order, {int(F['ir.h3.exhausted'])} over the approved value, {int(F['ir.h3.both'])} both. "
       "An expiry may be stale (the extract may not carry an amendment), so the route is a task for procurement, not a block.", ""]
md += block("Wrong GST rate or missing HSN/SAC (check H11)", [o for o in runs if any(r.check_id == "H11" and r.status != "pass" for r in o["results"])], {"H11"}) + [""]
md += block("GST type against place of supply (check H10: facts, never a fail)", h10, {"H10"}) + [""]
md += [f"H10 warns on {len(h10)} bills; on {int(F['ir.h10.warn_two_readings_differ'])} of them the two readings of the place of supply give different tax types, so the law does not settle it from the bill. "
       f"On {int(F['ir.check.H10.not_run'])} bills H10 could not run: the vendor GSTIN, the buyer GSTIN, the place of supply or the tax lines were not read.", ""]
md += block("Invoice numbers already used (check H13)", [o for o in runs if any(r.check_id == "H13" and r.status != "pass" for r in o["results"])], {"H13"}) + [""]
md += ["## Every bill and its flags", ""] + tab + ["", "## Limits", "",
       "- The verdicts are on the reader's output, and the reader got the vendor GSTIN wrong or not at all on a number of bills (`notes/reader-evaluation.md`). A `P1/H1` fail on a bill whose GSTIN was read at 0.80 may be the reader's error, not the vendor's.",
       "- Some `H11` and `P1/H1` results are reader gaps, not vendor errors: a GSTIN or HSN code misread by one character, a tax line the reader missed (so the rate is worked out from one line), or a GSTIN not read at all. They are the first things to check on the photos.",
       "- Whether a flag is right cannot be checked against labels for 30 of these bills: the labels cover 10. Of the flags above, none has been confirmed by a person.",
       "- Last year's bills were already booked, so a duplicate or an exhausted work order here describes the register, not a bill that has just arrived."]
(ROOT / "notes" / "intake-run.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
print({r: int(F[f"ir.all.route.{r}"]) for r in ROUTES}, "| H3 fails", int(F["ir.h3.fail_any"]), "expired", int(F["ir.h3.expired"]), "exhausted", int(F["ir.h3.exhausted"]))
