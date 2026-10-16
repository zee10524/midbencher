"""Work-order runway: how long a work order's balance lasts at its monthly burn, and how long until it expires, flagged 45 days ahead.

For each work order that is still being billed (a bill logged at the desk in the last `live_days`), the adapter gives the balance (approved less
billed to date), the monthly burn and the days to the end date. Runway in days is balance divided by monthly burn, converted at the adapter's days per
month. Each flagged row has a `kind`. `ahead` means the order is still within its dates and has balance but runs out or expires within `horizon_days`: these
are the 45-day warnings. `already` means it is over-billed, past its end date or has end before start: these are shown after the warnings. An expired order
is flagged `may be stale` because the extract may not carry amendments, so the flag asks for a look, not a block.

Real connection: purchase orders and outline agreements over RFC (the adapter's `get_work_order`), with item and schedule-line balances and open
quantity once IT exposes them; the burn would then be a real period burn, not an average over the order's life.
"""
from __future__ import annotations

from datetime import timedelta

from app.sap.adapter import DAYS_PER_MONTH, SapAdapter

from .ledger import Bill

HORIZON_DAYS = 45
LIVE_DAYS = 90


def runway(bills: list[Bill], sap: SapAdapter, horizon_days: int = HORIZON_DAYS, live_days: int = LIVE_DAYS) -> list[dict]:
    """Flagged work orders: the 45-day warnings first (soonest first), then those already past. Each row says which flags apply."""
    if not bills:
        return []
    as_of = bills[0].as_of
    since = as_of - timedelta(days=live_days)
    live = {b.wo_id for b in bills if b.desk_date and b.desk_date >= since and b.wo_id}
    rows = []
    for wo_id in sorted(live):
        wo = sap.get_work_order(wo_id, as_of)
        if wo is None:
            continue
        balance_days = None
        if wo.runway_months is not None:
            balance_days = wo.runway_months * DAYS_PER_MONTH
        flags, kind = [], "ahead"
        if wo.overbilled:
            flags.append("over-billed")
            kind = "already"
        elif balance_days is not None and balance_days <= horizon_days:
            flags.append(f"balance runs out within {horizon_days} days")
        if wo.days_to_end is not None:
            if wo.days_to_end < 0:
                flags.append("expired, may be stale")
                kind = "already"
            elif wo.days_to_end <= horizon_days:
                flags.append(f"expires within {horizon_days} days")
        if wo.validity == "unknown" and wo.valid_to and wo.valid_from and wo.valid_to < wo.valid_from:
            flags.append("end date before start date")
            kind = "already"
        if not flags:
            continue
        soonest = min([x for x in (balance_days, wo.days_to_end) if x is not None], default=0)
        rows.append(dict(wo_id=wo_id, vendor_id=wo.vendor_id, property_code=wo.property_code, balance_inr=wo.remaining, monthly_burn_inr=wo.monthly_burn,
                         runway_days=balance_days, days_to_expiry=wo.days_to_end, flags=flags, kind=kind, _sort=soonest))
    rows.sort(key=lambda r: (r["kind"] != "ahead", r["_sort"], r["wo_id"]))
    for r in rows:
        r.pop("_sort")
    return rows
