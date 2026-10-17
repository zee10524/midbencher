"""What loose duplicate matching adds on the register, compared with the exact matching the backtest uses.

Exact (the backtest's rule, `backtest/replay.py`): a bill is flagged when an earlier bill (desk order) of the same vendor has the same invoice number as written.
Loose (the intake check H13, `app/rules/checks.py`): the same, comparing letters and digits only, so case, slashes, dashes and spaces do not hide a match.
The false-alarm rate of the extra bills is the share of them with no duplicate-bill query (rule R01).

The loose match is used at intake only. This script measures it; nothing in the backtest or the impact figures reads it.

Reads analysis/out/bills_clean.parquet and query_forensics.csv. Writes analysis/out/figures_loose.csv.   Run: python analysis/12_loose_duplicates.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.sap.adapter import norm_invoice_loose  # noqa: E402

OUT = ROOT / "analysis" / "out"
b = pd.read_parquet(OUT / "bills_clean.parquet").sort_values(["desk_received_date", "bill_id"])
q = pd.read_csv(OUT / "query_forensics.csv")
dup_q = set(q[q.rule_id == "R01"].bill_id)
exact = b.groupby(b.vendor_id + "|" + b.invoice_no).cumcount() > 0
loose = b.groupby(b.vendor_id + "|" + b.invoice_no.map(norm_invoice_loose)).cumcount() > 0
extra = loose & ~exact
isq = b.bill_id.isin(dup_q)
standard = b.invoice_no.str.fullmatch(r"\d{3}/\d{2}-\d{2}/\d{3}")
figs = [
    ("ld.bills", len(b), "distinct bills in the register (after the exact duplicate rows are removed)"),
    ("ld.exact.flagged", int(exact.sum()), "bills flagged by exact matching: an earlier bill of the vendor has the same invoice number as written"),
    ("ld.loose.flagged", int(loose.sum()), "bills flagged by loose matching: same vendor, same letters and digits ignoring case, slashes, dashes and spaces"),
    ("ld.extra.flagged", int(extra.sum()), "extra bills that loose matching flags and exact matching does not"),
    ("ld.extra.queried_dup", int((extra & isq).sum()), "of the extra bills, those with a duplicate-bill query (R01)"),
    ("ld.extra.not_queried", int((extra & ~isq).sum()), "of the extra bills, those with no duplicate-bill query: the false alarms"),
    ("ld.extra.false_alarm_pct", 100 * (extra & ~isq).sum() / extra.sum() if extra.sum() else -1.0, "false-alarm share of the extra bills, % (-1 = there are no extra bills, so the rate cannot be measured on this register)"),
    ("ld.exact.queried_dup", int((exact & isq).sum()), "of the exactly flagged bills, those with a duplicate-bill query (R01)"),
    ("ld.exact.false_alarm_pct", 100 * (exact & ~isq).sum() / exact.sum(), "false-alarm share of the exactly flagged bills, % (for comparison)"),
    ("ld.invoice_no.nonstandard", int((~standard).sum()), "bills whose invoice number is not in the form NNN/YY-YY/NNN, the only form the register uses when it is clean"),
    ("ld.invoice_no.distinct_forms_per_loose_key", int((b.groupby(b.vendor_id + "|" + b.invoice_no.map(norm_invoice_loose)).invoice_no.nunique() > 1).sum()), "vendor and invoice-number keys written in more than one way"),
]
pd.DataFrame(figs, columns=["id", "value", "description"]).round(3).to_csv(OUT / "figures_loose.csv", index=False, lineterminator="\n")
for k, v, d in figs:
    print(f"{k:<45} {v}")
