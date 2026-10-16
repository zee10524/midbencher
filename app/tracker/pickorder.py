"""AP pick order: which bill each verifier picks up next, balancing load across the verifiers, oldest MSME bills first.

The bills ranked are those waiting at head office for AP to pick them up (stage `received`). They are ordered known Micro and Small first (oldest desk
date first, which is also the fewest days remaining on the 45-day clock), then vendors with no MSME status, then the rest oldest first. Each is then
given to the verifier with the lightest load, ties to the lowest verifier id, and that verifier's load goes up by one. Load is the bills a verifier has in
hand: stage `picked` with no open query (a query waits on someone else). Bills blocked by a query are shown beside it as `open queries`. The count is of bills, not their value, because the register shows the wait
is not driven by the day's volume but by who holds the bill.

Real connection: the unassigned items in the AP team's work list (the invoice verification or parked-document queue in SAP, read over RFC; the exact
object is for IT to confirm). The product suggests the order and the person; the verifier still picks in SAP.
"""
from __future__ import annotations

from collections import Counter

from .ledger import Bill
from .runlist import priority

VERIFIERS = ("AP-1", "AP-2", "AP-3", "AP-4", "AP-5")


TOLERANCE = 0.20  # the highest verifier's load may be at most this far above the lowest


def current_load(bills: list[Bill], verifiers: tuple[str, ...] = VERIFIERS, include_queried: bool = False) -> dict[str, int]:
    """Bills in hand per verifier. Definition 1 (the pick order's, the default): stage `picked` with no open query. Definition 2: also the bills
    blocked by an open query. The pick order always uses definition 1; definition 2 exists to show the follow-up work and to report the balance under both."""
    held = Counter(b.verifier for b in bills if b.stage == "picked" and (include_queried or b.open_query is None))
    return {v: held.get(v, 0) for v in verifiers}


def open_queries(bills: list[Bill], verifiers: tuple[str, ...] = VERIFIERS) -> dict[str, int]:
    """Bills each verifier holds that are blocked by an open query: the follow-up work."""
    held = Counter(b.verifier for b in bills if b.stage == "picked" and b.open_query is not None)
    return {v: held.get(v, 0) for v in verifiers}


def spread(load: dict[str, int]) -> float:
    """How far the highest load is above the lowest, as a fraction of the lowest. Infinite if the lowest is zero and the highest is not."""
    hi, lo = max(load.values()), min(load.values())
    return 0.0 if hi == lo else float("inf") if lo == 0 else (hi - lo) / lo


def control_tower(bills: list[Bill], verifiers: tuple[str, ...] = VERIFIERS) -> list[dict]:
    """One row per verifier for the control tower: bills in hand (no open query), open queries to follow up, new bills the pick order gives them,
    and the bills in hand after. The AP lead reads `open_queries` as the follow-up work that `in_hand` leaves out."""
    held, queries = current_load(bills, verifiers), open_queries(bills, verifiers)
    new = Counter(p["verifier"] for p in pick_order(bills, verifiers))
    return [dict(verifier=v, in_hand=held[v], open_queries=queries[v], new_from_pick_order=new.get(v, 0), in_hand_after=held[v] + new.get(v, 0)) for v in verifiers]


def balance_check(bills: list[Bill], verifiers: tuple[str, ...] = VERIFIERS) -> dict:
    """After the pick order's assignments, the spread of load under each definition, and whether it is within TOLERANCE.
    Only definition 1 is balanced by the pick order, so the result under definition 2 is reported, not engineered."""
    new = Counter(p["verifier"] for p in pick_order(bills, verifiers))
    out = {}
    for key, incl in (("def1", False), ("def2", True)):
        before = current_load(bills, verifiers, incl)
        after = {v: before[v] + new.get(v, 0) for v in verifiers}
        sp = spread(after)
        out[key] = dict(before=before, after=after, spread=sp, within_tolerance=sp <= TOLERANCE)
    return out


def pick_order(bills: list[Bill], verifiers: tuple[str, ...] = VERIFIERS) -> list[dict]:
    """Waiting bills in pick order, each with the verifier it goes to. `rank` is 1 for the first bill to pick."""
    load = current_load(bills, verifiers)
    out = []
    for rank, b in enumerate(sorted((x for x in bills if x.stage == "received"), key=priority), 1):
        v = min(verifiers, key=lambda x: (load[x], x))
        load[v] += 1
        out.append(dict(rank=rank, bill_id=b.bill_id, vendor=b.vendor_name, invoice_no=b.invoice_no, doc_type=b.doc_type, amount_inr=b.amount,
                        msme_status=b.msme_status, desk_date=b.desk_date, days_since_desk=b.days_since_desk,
                        days_waiting=b.days_in_stage, verifier=v, load_after=load[v]))
    return out
