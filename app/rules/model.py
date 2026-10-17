"""Types for the intake checks: what the reader gives, what a check returns, and what a check can look things up in.

A check is a pure function `check(bill: BillRead, ctx: Context) -> CheckResult`. It reads the bill and looks up SAP data through the adapter, changes nothing,
and always returns a result, so every check can be run on every bill.

Statuses: `pass`; `fail` (a rule is clearly broken); `warn` (a person must look: the rule is unsettled, the facts disagree or the owner is unclear);
`needs-document` (a value the check needs is not on what was read, so the page or paper must be supplied).

Real connection: `Context.sap` is the adapter over `sap_extract.sqlite`; with a real connection it is the same adapter reading over RFC (see app/sap/adapter.py).
`Context.known_bills` is the register; in production it is the event log plus posted invoices read from SAP.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.sap.adapter import SapAdapter

RULES_VERSION = "intake-2026.10.1"
AUTO_CLEAR = 0.90   # every needed confidence at or above this, and every check passes: auto-clear
LOOK = 0.70         # a needed field below this: ask for a clearer image. Between LOOK and AUTO_CLEAR: a person looks
PASS, FAIL, WARN, NEEDS_DOC = "pass", "fail", "warn", "needs-document"
OWNERS = ("vendor", "property", "procurement", "AP")


@dataclass(frozen=True)
class Field:
    """One value read from the bill and the reader's confidence in it (0 to 1). A value of None with high confidence means the reader is sure it is not on the bill."""
    value: Any = None
    confidence: float = 1.0
    source: str = "read"   # read (from the page), repaired (one confusable character fixed and found in the vendor master), vendor_master (looked up from the vendor name), human_review (typed by a person)


def read(source_file: str = "", confidence: float = 0.98, own_bill_id: str | None = None, **values) -> "BillRead":
    """Build a BillRead from plain values, giving each the same confidence. A `(value, confidence)` pair sets one field's confidence."""
    fields = {}
    for k, v in values.items():
        fields[k] = Field(*v) if isinstance(v, tuple) else Field(v, confidence)
    return BillRead(source_file=source_file, own_bill_id=own_bill_id, **fields)


@dataclass(frozen=True)
class BillRead:
    """The fields the intake checks use, as printed on the bill. `own_bill_id` is the bill's own row in the register, ignored by the duplicate check."""
    source_file: str = ""
    own_bill_id: str | None = None
    vendor_gstin: Field = field(default_factory=Field)
    vendor_name: Field = field(default_factory=Field)
    invoice_no: Field = field(default_factory=Field)
    invoice_date: Field = field(default_factory=Field)   # a date
    wo_id: Field = field(default_factory=Field)
    taxable_inr: Field = field(default_factory=Field)
    cgst_inr: Field = field(default_factory=Field)
    sgst_inr: Field = field(default_factory=Field)
    igst_inr: Field = field(default_factory=Field)
    hsn_sac: Field = field(default_factory=Field)
    place_of_supply: Field = field(default_factory=Field)  # a state name or a two-digit state code
    recipient_gstin: Field = field(default_factory=Field)

    @property
    def tax_inr(self) -> float | None:
        parts = [self.cgst_inr.value, self.sgst_inr.value, self.igst_inr.value]
        return None if all(p is None for p in parts) else float(sum(p or 0 for p in parts))


@dataclass
class Context:
    """What the checks may look up. `bill_counted_in_billed` is True when the bill is a historical row whose value is already in the work order's billed
    value (replaying the register); at live intake it is False and the bill's amount is taken off the remaining balance."""
    sap: SapAdapter
    known_bills: list = field(default_factory=list)   # register bills (objects with vendor_id, invoice_no, invoice_date, amount, bill_id)
    bill_counted_in_billed: bool = False

    def __post_init__(self):
        self._by_vendor: dict[str, list] = {}
        for b in self.known_bills:
            self._by_vendor.setdefault(b.vendor_id, []).append(b)

    def register_for(self, vendor_id: str) -> list:
        return self._by_vendor.get(vendor_id, [])


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    name: str
    status: str
    evidence: dict
    owner: str | None          # who must act: vendor, property, procurement or AP; None when nothing is needed
    fix: str                   # the fix in plain words; empty when the check passes
    field_confidence: float    # lowest confidence among the fields the check used
    certainty: float = 1.0     # how settled the rule itself is: 1.0 for a lookup, lower for an unsettled rule
    version: str = RULES_VERSION

    @property
    def confidence(self) -> float:
        return round(self.field_confidence * self.certainty, 4)
