"""The next-run payment list: the Tuesday or Friday run each posted bill could join, with the cut-off as a setting.

Open invoices with status `Posted` are listed. For each, `model_first_run` is the first run open to it under the cut-off, `runs_missed` is how many
runs have gone by since without it being paid, and `run_date` is the first run still ahead of the as-of date. Within a run, known Micro and Small
bills come first by fewest days remaining, then bills of vendors with no MSME status, then the rest oldest first. `last_run_before_limit` marks an
MSME bill for which this is the last run on or before day 45. Credit notes are not listed (not an amount paid to the vendor).

Real connection: Treasury's payment proposal for each run, read over RFC (the proposal list and its exceptions, for example the automatic payment
program tables, to be confirmed by IT). Nothing is released by the product.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

from .ledger import Bill, open_invoices
from .msme import days_remaining, last_run_before_limit
from .payruns import DEFAULT_CUTOFF_DAYS, first_run_after_posting, next_run_for_open_bill, runs_missed

GROUP_RANK = {"Micro": 0, "Small": 0, "Unknown": 1}


def priority(b: Bill) -> tuple:
    """Known Micro and Small first, then Unknown status, then the rest; within each, oldest desk date first (the fewest days remaining for MSME)."""
    return (GROUP_RANK.get(b.msme_status, 2), b.desk_date or date.max, b.bill_id)


def next_run_list(bills: list[Bill], cutoff_days: int = DEFAULT_CUTOFF_DAYS) -> list[dict]:
    """One dict per run date, soonest first: the run, the bills on it in priority order, their count and value before GST."""
    by_run: dict[date, list[dict]] = defaultdict(list)
    for b in sorted((x for x in open_invoices(bills) if x.status == "Posted"), key=priority):
        posted = b.entered["posted"]
        run = next_run_for_open_bill(posted, b.as_of, cutoff_days)
        by_run[run].append(dict(
            bill_id=b.bill_id, vendor=b.vendor_name, invoice_no=b.invoice_no, amount_inr=b.amount, posted_date=posted,
            model_first_run=first_run_after_posting(posted, cutoff_days), runs_missed=runs_missed(posted, b.as_of, cutoff_days),
            msme_status=b.msme_status, msme_days_remaining=days_remaining(b), last_run_before_limit=(last_run_before_limit(b, cutoff_days) == run)
            if days_remaining(b) is not None else False))
    return [dict(run_date=r, bills=rows, count=len(rows), value_inr=sum(x["amount_inr"] for x in rows)) for r, rows in sorted(by_run.items())]
