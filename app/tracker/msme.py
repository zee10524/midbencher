"""MSME countdown: days and payment runs left before a Micro or Small vendor's invoice passes 45 days.

Clock (notes/assumptions.md, 'MSME payment clock'): day 0 is `desk_received_date`. A bill is on time if paid 45 or fewer calendar days after it
and late at 46 or more, so `days_remaining` is 45 less the days since the desk logged it. Every clock in the register starts after the statutory
one (acceptance or delivery), so a countdown that reads 'late' is at least that late. The pack holds no written payment term per work order, so
every row carries the note that the limit may be 15 days; the 45 days is the policy's figure.

Vendors whose MSME status is blank in the master are their own group (`Unknown`, 'could be Micro or Small') and are never folded into 'not MSME'.
Medium and Not MSME vendors are not on the list.

Real connection: the same clock, with the desk date replaced by the intake timestamp, the status taken from the vendor master (the adapter's
`get_vendor`), and the written payment term read per work order once the client supplies it (a client question in notes/claims-tested.md).
"""
from __future__ import annotations

from datetime import date, timedelta

from .ledger import Bill, open_invoices
from .payruns import DEFAULT_CUTOFF_DAYS, next_run_for_open_bill, runs_between

LIMIT_DAYS = 45
WARN_DAYS = 7  # a bill is 'due soon' when this many days or fewer remain
LIMIT_NOTE = "Limit may be 15 days if the work order has no written payment term (none is recorded)."
GROUP = {"Micro": "Micro or Small", "Small": "Micro or Small", "Unknown": "Unknown (could be Micro or Small)"}


def due_date(b: Bill) -> date:
    """The last day on which payment is still within 45 days of the desk date."""
    return b.desk_date + timedelta(days=LIMIT_DAYS)


def days_remaining(b: Bill) -> int | None:
    """Days left to the 45-day limit as of the as-of date; negative once past. None for vendors the 45-day rule does not cover or bills without a desk date."""
    if b.msme_status not in GROUP or b.desk_date is None:
        return None
    return LIMIT_DAYS - b.days_since_desk


def runs_left(b: Bill, cutoff_days: int = DEFAULT_CUTOFF_DAYS) -> int:
    """Payment runs still ahead that fall on or before the due date. A bill not yet posted is counted as if it could post at the as-of date."""
    first = next_run_for_open_bill(b.entered.get("posted"), b.as_of, cutoff_days)
    return len(runs_between(first, due_date(b)))


def last_run_before_limit(b: Bill, cutoff_days: int = DEFAULT_CUTOFF_DAYS) -> date | None:
    """The last run on or before the due date that is still ahead, or None if there is none."""
    runs = runs_between(next_run_for_open_bill(b.entered.get("posted"), b.as_of, cutoff_days), due_date(b))
    return runs[-1] if runs else None


def state(remaining: int, runs: int) -> str:
    if remaining < 0:
        return "late"
    if runs == 0:
        return "will be late: no run left"
    return "due soon" if remaining <= WARN_DAYS else "on track"


def countdown(bills: list[Bill], cutoff_days: int = DEFAULT_CUTOFF_DAYS) -> list[dict]:
    """Open invoices of Micro, Small and Unknown-status vendors, fewest days remaining first (so oldest first, since both count from the desk date)."""
    rows = []
    for b in open_invoices(bills):
        rem = days_remaining(b)
        if rem is None:
            continue
        runs = runs_left(b, cutoff_days)
        rows.append(dict(bill_id=b.bill_id, vendor=b.vendor_name, msme_status=b.msme_status, group=GROUP[b.msme_status], invoice_no=b.invoice_no,
                         amount_inr=b.amount, desk_date=b.desk_date, due_date=due_date(b), days_remaining=rem, runs_left=runs,
                         last_run=last_run_before_limit(b, cutoff_days), state=state(rem, runs), stage=b.stage_name, owner=b.owner, note=LIMIT_NOTE))
    return sorted(rows, key=lambda r: (r["days_remaining"], r["bill_id"]))

