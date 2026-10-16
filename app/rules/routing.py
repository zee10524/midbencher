"""Routing: what happens to a bill after the checks (notes/solution-design.md section 5).

Every finding is classified from its status, owner and confidence (the check's field confidence times how settled the rule is):

- a needed field below 0.70                                       -> ask the vendor to resend a clearer image (no verdict is better than a wrong one)
- `fail` at confidence 0.90 or more, fix in the vendor's hands       -> a message to the vendor (all vendor fixes in ONE message)
- `fail` at confidence 0.90 or more, fix in the company's hands      -> a task to procurement, the property or AP; the vendor gets a status message only
- `warn`, `needs-document`, a doubtful read (0.70 to 0.90) or an unsettled rule -> human look, with the evidence side by side
- all pass, every confidence 0.90 or more                            -> auto-clear (no intake finding; every later check still runs)

`route` is the one label for the bill, by precedence: resend, then fix-before-sending when a vendor fix is confirmed, then human-look, then fix-internal,
then auto-clear. The label never hides anything: `actions` lists every message, task and look the bill needs, so a bill that fails three checks yields one
vendor message and not three queries.

Real connection: the actions are what the notification layer sends: a WhatsApp Business template message for `tell-vendor` and `resend` (approved template,
recorded opt-in, files kept company side), and tasks in the product's own queue for the rest. Nothing here sends anything.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .model import AUTO_CLEAR, FAIL, LOOK, PASS, CheckResult

AUTO, FIX_VENDOR, FIX_INTERNAL, HUMAN, RESEND = "auto-clear", "fix-before-sending", "fix-internal", "human-look", "resend"
PRECEDENCE = [RESEND, FIX_VENDOR, HUMAN, FIX_INTERNAL, AUTO]


@dataclass(frozen=True)
class Action:
    kind: str                  # tell-vendor, resend, task, human-look, copy-executive
    to: str                    # vendor, executive, procurement, property or AP
    checks: tuple[str, ...]    # the check ids behind it
    text: str                  # plain words


@dataclass(frozen=True)
class Routing:
    route: str
    actions: tuple[Action, ...]
    reasons: tuple[str, ...] = field(default=())


def classify(r: CheckResult) -> str:
    """One finding's route: resend, fix-before-sending, fix-internal, human-look or auto-clear."""
    if r.field_confidence < LOOK:
        return RESEND
    if r.status == PASS:
        return AUTO if r.confidence >= AUTO_CLEAR else HUMAN
    if r.status == FAIL and r.confidence >= AUTO_CLEAR:
        return FIX_VENDOR if r.owner == "vendor" else FIX_INTERNAL
    return HUMAN


def route(results: list[CheckResult]) -> Routing:
    kinds = {r.check_id: classify(r) for r in results}
    actions, reasons = [], []
    resend = [r for r in results if kinds[r.check_id] == RESEND]
    if resend:
        actions.append(Action("resend", "vendor", tuple(r.check_id for r in resend), "Please send a clearer photo or scan of the bill."))
        reasons += [f"{r.check_id}: a needed field was read with confidence {r.field_confidence:.2f}, below {LOOK:.2f}" for r in resend]
    vendor = [r for r in results if kinds[r.check_id] == FIX_VENDOR]
    if vendor:
        actions.append(Action("tell-vendor", "vendor", tuple(r.check_id for r in vendor), " ".join(r.fix for r in vendor)))
        actions.append(Action("copy-executive", "executive", tuple(r.check_id for r in vendor), "The vendor has been asked to fix: " + "; ".join(r.check_id for r in vendor) + "."))
        reasons += [f"{r.check_id}: failed with confidence {r.confidence:.2f}, the vendor's fix" for r in vendor]
    for r in results:
        if kinds[r.check_id] == FIX_INTERNAL:
            actions.append(Action("task", r.owner or "AP", (r.check_id,), r.fix))
            reasons.append(f"{r.check_id}: failed with confidence {r.confidence:.2f}, the company's fix ({r.owner})")
    look = [r for r in results if kinds[r.check_id] == HUMAN]
    if look:
        actions.append(Action("human-look", "executive", tuple(r.check_id for r in look), " ".join(f"{r.check_id}: {r.fix or 'confirm the value read.'}" for r in look)))
        for r in look:
            why = ("the rule is unsettled" if r.certainty < 1 else "the owner or the facts are unclear" if r.status != PASS else "a read is doubtful")
            reasons.append(f"{r.check_id}: {r.status} at confidence {r.confidence:.2f}: {why}")
    present = {k for k in kinds.values()} - {AUTO}
    label = next((k for k in PRECEDENCE if k in present), AUTO)
    if label == AUTO:
        reasons.append("every check passed and every confidence is 0.90 or more")
    return Routing(label, tuple(actions), tuple(reasons))
