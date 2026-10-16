"""The payment-run calendar: payments go out on Tuesdays and Fridays only (policy; in the register every valid payment date is one of the two).

`cutoff_days` is the setting for how many days before a run the run list closes. A bill posted on day P can join the first run that is at least
1 + cutoff_days after P: cutoff 0 means a bill posted today can join tomorrow's run if there is one, 2 means the list closes two days earlier.
The register does not hold Treasury's real cut-off (see `notes/payment-lag.md`), so it is a setting, defaulting to the middle value tested.

Real connection: the run dates and each run's list would come from Treasury (the payment proposal run in SAP, read over RFC, for example the payment
proposal tables of the automatic payment program, to be confirmed by IT). The product proposes the list; Treasury approves and pays.
"""
from __future__ import annotations

from datetime import date, timedelta

RUN_WEEKDAYS = (1, 4)  # Tuesday, Friday
DEFAULT_CUTOFF_DAYS = 1


def is_run_day(d: date) -> bool:
    return d.weekday() in RUN_WEEKDAYS


def first_run_on_or_after(d: date) -> date:
    while not is_run_day(d):
        d += timedelta(days=1)
    return d


def first_run_after_posting(posted: date, cutoff_days: int = DEFAULT_CUTOFF_DAYS) -> date:
    """The first run a bill posted on `posted` could join under the cut-off."""
    return first_run_on_or_after(posted + timedelta(days=1 + cutoff_days))


def next_run_for_open_bill(posted: date | None, as_of: date, cutoff_days: int = DEFAULT_CUTOFF_DAYS) -> date:
    """The first run still ahead of the as-of date that the bill could join. A bill not yet posted is counted as if posted at the as-of date."""
    earliest = first_run_after_posting(posted or as_of, cutoff_days)
    return first_run_on_or_after(max(earliest, as_of + timedelta(days=1)))


def runs_between(first: date, last: date) -> list[date]:
    """Run dates from `first` to `last`, both included."""
    out, d = [], first_run_on_or_after(first)
    while d <= last:
        out.append(d)
        d = first_run_on_or_after(d + timedelta(days=1))
    return out


def runs_missed(posted: date, as_of: date, cutoff_days: int = DEFAULT_CUTOFF_DAYS) -> int:
    """Runs that were open to a posted bill and have already gone by (up to and including the as-of date) without it being paid."""
    return len(runs_between(first_run_after_posting(posted, cutoff_days), as_of))


def label(d: date) -> str:
    """For example `Tuesday 5 May 2026`."""
    return f"{d:%A} {d.day} {d:%B %Y}"
