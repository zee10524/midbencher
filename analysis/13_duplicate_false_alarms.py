"""How often loose near-duplicate matching raises an alarm, measured on every invoice in the SAP extract's posted_invoices table.

For each distinct posted invoice (exact duplicate rows collapsed, data-audit D11) the adapter's `find_posted_invoices(vendor, invoice_no, loose=True)` is run and
the invoice's own bill id is ignored. An invoice is flagged when any other posted invoice of the same vendor matches on letters and digits (case, slashes, dashes
and spaces ignored). The same is run with `loose=False` to see what loose matching adds. A flagged invoice is "confirmed" if the register has a duplicate-bill
query (R01) on it and "unconfirmed" if not; the false-alarm share is the unconfirmed share. Nothing here changes a rule.

Reads pack/data through a read-only connection. Writes analysis/out/figures_dupalarm.csv and notes/duplicate-false-alarms.md.
Run: python analysis/13_duplicate_false_alarms.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.sap.adapter import SapAdapter  # noqa: E402

OUT = ROOT / "analysis" / "out"
q = pd.read_csv(OUT / "query_forensics.csv")
dup_queried = set(q[q.rule_id == "R01"].bill_id)

with SapAdapter(ROOT / "pack" / "data" / "sap_extract.sqlite") as sap:
    rows = sap._ro.execute("SELECT DISTINCT * FROM posted_invoices ORDER BY bill_id").fetchall()
    raw_rows = sap._ro.execute("SELECT count(*) FROM posted_invoices").fetchone()[0]
    inv = [dict(r) for r in rows]
    flagged, pairs = {}, {}
    exact_flagged = set()
    for r in inv:
        for loose in (True, False):
            hits = [p for p in sap.find_posted_invoices(r["vendor_id"], r["invoice_no"], loose=loose) if p.bill_id != r["bill_id"]]
            if not hits:
                continue
            if loose:
                flagged[r["bill_id"]] = hits
            else:
                exact_flagged.add(r["bill_id"])
n = len(inv)
confirmed = {b for b in flagged if b in dup_queried}
extra = set(flagged) - exact_flagged
by_id = {r["bill_id"]: r for r in inv}
for b, hits in flagged.items():
    for h in hits:
        key = tuple(sorted((b, h.bill_id)))
        pairs.setdefault(key, (b, h))
same = lambda a, b_: a is not None and b_ is not None and abs(float(a) - float(b_)) < 0.5
pair_rows = []
for (a_id, b_id), _ in sorted(pairs.items()):
    a, b = by_id[a_id], by_id[b_id]
    pair_rows.append(dict(a=a_id, b=b_id, vendor=a["vendor_id"], invoice_a=a["invoice_no"], invoice_b=b["invoice_no"], date_a=a["invoice_date"], date_b=b["invoice_date"],
                          amount_a=float(a["amount_inr"]), amount_b=float(b["amount_inr"]), wo_a=a["wo_id"], wo_b=b["wo_id"],
                          same_text=a["invoice_no"] == b["invoice_no"], same_date=a["invoice_date"] == b["invoice_date"], same_amount=same(a["amount_inr"], b["amount_inr"]),
                          same_wo=a["wo_id"] == b["wo_id"], either_queried_dup=a_id in dup_queried or b_id in dup_queried,
                          n_queried=int(a_id in dup_queried) + int(b_id in dup_queried)))
P = pd.DataFrame(pair_rows)
figs = [
    ("da.rows", raw_rows, "rows in posted_invoices"),
    ("da.invoices", n, "distinct posted invoices after collapsing exact duplicate rows (D11)"),
    ("da.flagged_loose", len(flagged), "posted invoices that loose matching flags: another posted invoice of the same vendor matches on letters and digits"),
    ("da.flagged_exact", len(exact_flagged), "posted invoices flagged by exact matching (case and whitespace normalised, as the adapter does)"),
    ("da.flagged_extra", len(extra), "posted invoices that loose matching flags and exact matching does not"),
    ("da.flag_rate_per_1000", 1000 * len(flagged) / n, "loose flags per 1,000 posted invoices"),
    ("da.pairs", len(P), "distinct flagged pairs"),
    ("da.pairs_same_date_and_amount", int((P.same_date & P.same_amount).sum()), "pairs with the same invoice date and the same amount (the fail grade of check H13)"),
    ("da.pairs_same_amount", int(P.same_amount.sum()), "pairs with the same amount"),
    ("da.pairs_same_date", int(P.same_date.sum()), "pairs with the same invoice date"),
    ("da.pairs_same_wo", int(P.same_wo.sum()), "pairs on the same work order"),
    ("da.pairs_same_text", int(P.same_text.sum()), "pairs whose invoice numbers are written identically"),
    ("da.confirmed", len(confirmed), "flagged invoices that the register shows with a duplicate-bill query (R01)"),
    ("da.unconfirmed", len(flagged) - len(confirmed), "flagged invoices with no duplicate-bill query"),
    ("da.false_alarm_pct", 100 * (len(flagged) - len(confirmed)) / len(flagged), "share of flagged invoices with no duplicate-bill query, %"),
    ("da.pairs_either_queried", int(P.either_queried_dup.sum()), "pairs where at least one of the two invoices has a duplicate-bill query"),
    ("da.pairs_both_queried", int((P.n_queried == 2).sum()), "pairs where both invoices have a duplicate-bill query"),
    ("da.pairs_one_queried", int((P.n_queried == 1).sum()), "pairs where exactly one invoice has a duplicate-bill query"),
    ("da.pairs_none_queried", int((P.n_queried == 0).sum()), "pairs where neither invoice has a duplicate-bill query"),
    ("da.intake.flagged", len(P), "as at intake: one flag per pair, raised when the second bill of the pair arrives"),
    ("da.intake.confirmed", int(P.either_queried_dup.sum()), "of those, pairs with a duplicate-bill query on at least one of the two invoices"),
    ("da.intake.false_alarms", int((~P.either_queried_dup).sum()), "of those, pairs with no duplicate-bill query on either invoice"),
    ("da.intake.false_alarm_pct", 100 * (~P.either_queried_dup).mean(), "share of intake flags (pairs) with no duplicate-bill query on either invoice, %"),
    ("da.intake.rate_per_1000", 1000 * len(P) / n, "intake flags (pairs) per 1,000 posted invoices"),
    ("da.queried_dup_not_flagged", len(dup_queried & set(by_id) - set(flagged)), "posted invoices with a duplicate-bill query that loose matching does not flag"),
]
pd.DataFrame(figs, columns=["id", "value", "description"]).round(3).to_csv(OUT / "figures_dupalarm.csv", index=False, lineterminator="\n")
F = {k: v for k, v, _ in figs}

ex = P.sort_values(["same_amount", "same_date", "a"], ascending=[False, False, True]).head(10)
EX = "\n".join(f"| {r.a} / {r.b} | {r.vendor} | {r.invoice_a}" + (" / " + r.invoice_b if not r.same_text else "") + f" | {r.date_a} / {r.date_b} | {r.amount_a:,.0f} / {r.amount_b:,.0f} | {r.wo_a} / {r.wo_b} | "
               f"{'text' if r.same_text else 'loose only'}{', date' if r.same_date else ''}{', amount' if r.same_amount else ''}{', work order' if r.same_wo else ''} | {'yes' if r.either_queried_dup else 'no'} |" for r in ex.itertuples())
md = f"""# Duplicate matching: how often loose matching raises an alarm

Generated by `analysis/13_duplicate_false_alarms.py`; every figure is registered in `notes/numbers.md` under `da.*`. No rule was changed. Loose matching is
`find_posted_invoices(vendor, invoice_no, loose=True)` in `app/sap/adapter.py`: the same vendor and the same letters and digits, ignoring case, slashes, dashes and spaces.

## Result

Every invoice in `posted_invoices` was matched against the others: {F['da.rows']:,.0f} rows, {F['da.invoices']:,.0f} distinct invoices once exact duplicate rows are collapsed (data-audit D11).

| Measure | Value |
|---|---|
| Invoices flagged by loose matching | **{F['da.flagged_loose']:,.0f}** |
| Flag rate | **{F['da.flag_rate_per_1000']:.1f} per 1,000 invoices** |
| Flagged by exact matching | {F['da.flagged_exact']:,.0f} |
| Flagged by loose matching only | {F['da.flagged_extra']:,.0f} |
| Distinct flagged pairs | {F['da.pairs']:,.0f} |
| Pairs with the same date and the same amount (check H13 would fail the bill) | {F['da.pairs_same_date_and_amount']:,.0f} |
| Pairs with the same amount / the same date / the same work order | {F['da.pairs_same_amount']:,.0f} / {F['da.pairs_same_date']:,.0f} / {F['da.pairs_same_wo']:,.0f} |
| Flagged invoices with a duplicate-bill query in the register | {F['da.confirmed']:,.0f} |
| Flagged invoices with no duplicate-bill query | {F['da.unconfirmed']:,.0f} ({F['da.false_alarm_pct']:.1f}%; see the note below on why this overstates it) |
| **As at intake (one flag per pair): flags / with a query / false-alarm share** | **{F['da.intake.flagged']:,.0f} ({F['da.intake.rate_per_1000']:.1f} per 1,000) / {F['da.intake.confirmed']:,.0f} / {F['da.intake.false_alarm_pct']:.1f}%** |
| Invoices with a duplicate-bill query that loose matching does not flag | {F['da.queried_dup_not_flagged']:,.0f} |

**What it says.**
- **Nothing extra.** Loose matching adds {F['da.flagged_extra']:,.0f} invoices to what exact matching already flags: every invoice number in the extract is written in one form, so there is no near-duplicate for loose matching to find.
- **What is flagged is reused numbers.** All alarms are the same vendor with the same invoice number (D04), mostly on a different date and amount. {F['da.pairs_same_date_and_amount']:,.0f} of {F['da.pairs']:,.0f} pairs share a date and an amount, so none would be failed by H13; they would be warned for a person to decide.
- **Counting every invoice, as asked,** {F['da.flagged_loose']:,.0f} invoices are flagged and {F['da.unconfirmed']:,.0f} ({F['da.false_alarm_pct']:.1f}%) have no duplicate-bill query. That figure overstates the false alarms: the flag is symmetrical, so both invoices of a pair are flagged, and the verifier's query sits on only one of them.
- **Counting as at intake**, one flag is raised per pair, when the second bill arrives: {F['da.intake.flagged']:,.0f} flags ({F['da.intake.rate_per_1000']:.1f} per 1,000 posted invoices). {F['da.intake.confirmed']:,.0f} of them have a duplicate-bill query on at least one of the two invoices and {F['da.intake.false_alarms']:,.0f} have none: a **false-alarm share of {F['da.intake.false_alarm_pct']:.1f}%** if a query is taken as the truth. {F['da.pairs_both_queried']:,.0f} pair has a query on both invoices, {F['da.pairs_one_queried']:,.0f} on exactly one and {F['da.pairs_none_queried']:,.0f} on neither.
- **The other direction is not measured here.** {F['da.queried_dup_not_flagged']:,.0f} posted invoices with a duplicate-bill query have no matching posted invoice, so no matching rule on this table could flag them (data-audit D05).
- **Direction of the error is unknown.** A flag without a query may be a missed duplicate or a harmless reused number; the data cannot say which.

## Ten flagged pairs

Ordered by how much they match (same amount first, then same date). "Matched on" lists the fields that agree beyond the vendor and the loose invoice number.

| Bills | Vendor | Invoice number | Invoice dates | Amounts (₹) | Work orders | Matched on | Duplicate-bill query on either |
|---|---|---|---|---|---|---|---|
{EX}

## Limits

- This measures posted invoices only. Bills not yet posted are not in `posted_invoices` (data-audit D12), so duplicates among them are not counted.
- A duplicate-bill query is taken as the sign that a real duplicate or reuse was found. The register cannot show a duplicate that nobody queried.
- Loose matching is used at intake only. The backtest uses exact matching: see `backtest/replay.py`.
"""
(ROOT / "notes" / "duplicate-false-alarms.md").write_text(md, encoding="utf-8", newline="\n")
print("\n".join(f"{k:<32} {v}" for k, v, _ in figs))
print(ex[["a", "b", "same_date", "same_amount", "same_wo", "either_queried_dup"]].to_string(index=False))
