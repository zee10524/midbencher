"""The ledger: every bill with its stage, the date it entered each stage, days in the current stage, who owns the next move, and status.

A bill's stage is read from the dates in the register, the last stage it has entered on or before the as-of date. An open query is not a stage:
it overlays the stage the bill is in, changes the status to `Query`, and moves the owner to whoever the query is waiting on.

Real connection: the register stands in for the event log the product keeps once it sits on the intake. Each date here would be written as an
event (file received, property verified, signed, received at head office, picked, posted) when it happens. Posting and payment dates would be read
from SAP over RFC (posted vendor invoices, and cleared items for payment), which the adapter's docstrings name. The tracker writes nothing to SAP.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

# (key, register column, stage name, owner of the next move while the bill is in this stage)
STAGES = [
    ("desk", "desk_received_date", "At the property for checking", "property"),
    ("verified", "property_verified_date", "Waiting for the property head's signature", "property"),
    ("signed", "property_head_signed_date", "On the courier to head office", "courier"),
    ("received", "ho_received_date", "Waiting at head office for AP to pick it up", "AP"),
    ("picked", "ho_picked_date", "With AP for checking and posting", "AP"),
    ("posted", "posted_date", "Posted, waiting for a payment run", "treasury"),
    ("paid", "paid_date", "Paid", None),
]
STAGE_KEYS = [s[0] for s in STAGES]
STAGE_NAME = {s[0]: s[2] for s in STAGES}
STAGE_OWNER = {s[0]: s[3] for s in STAGES}
OWNERS = ("vendor", "property", "courier", "AP", "procurement", "treasury")
# status shown in the ledger, by stage when no query is open
STATUS_BY_STAGE = {"desk": "At property", "verified": "At property", "signed": "In transit", "received": "With AP", "picked": "With AP", "posted": "Posted", "paid": "Paid"}


@dataclass(frozen=True)
class Query:
    query_id: str
    raised_date: date
    resolved_date: date | None
    category: str
    text: str
    owner: str  # vendor, property, procurement or AP
    reason: str  # plain words for the vendor
    action: str  # what the owner must do

    @property
    def is_open(self) -> bool:
        return self.resolved_date is None


@dataclass(frozen=True)
class Bill:
    bill_id: str
    vendor_id: str
    vendor_name: str
    msme_status: str  # Micro, Small, Medium, Not MSME or Unknown (blank in the master, never guessed)
    property_code: str
    category: str
    doc_type: str  # invoice or credit_note
    invoice_no: str
    invoice_date: date | None
    amount: float
    gst: float
    wo_id: str
    verifier: str
    entered: dict[str, date | None]
    queries: tuple[Query, ...]
    as_of: date
    flags: tuple[str, ...] = field(default=())

    # ---- stage
    @property
    def stage(self) -> str:
        cur = STAGE_KEYS[0]
        for k in STAGE_KEYS:
            d = self.entered.get(k)
            if d is not None and d <= self.as_of:
                cur = k
        return cur

    @property
    def stage_name(self) -> str:
        return STAGE_NAME[self.stage]

    @property
    def stage_entered(self) -> date | None:
        return self.entered.get(self.stage)

    @property
    def days_in_stage(self) -> int | None:
        """Days from entering the current stage to the as-of date. None once paid."""
        if self.stage == "paid" or self.stage_entered is None:
            return None
        return (self.as_of - self.stage_entered).days

    # ---- query overlay
    @property
    def open_query(self) -> Query | None:
        opened = [q for q in self.queries if q.is_open and q.raised_date <= self.as_of]
        return max(opened, key=lambda q: q.raised_date) if opened else None

    @property
    def days_in_query(self) -> int | None:
        q = self.open_query
        return None if q is None else (self.as_of - q.raised_date).days

    @property
    def status(self) -> str:
        if self.stage == "paid":
            return "Paid"
        return "Query" if self.open_query else STATUS_BY_STAGE[self.stage]

    @property
    def owner(self) -> str | None:
        """Who must make the next move. The query's owner while a query is open, else the owner of the stage. None once paid."""
        q = self.open_query
        return q.owner if q and self.stage != "paid" else STAGE_OWNER[self.stage]

    # ---- age
    @property
    def desk_date(self) -> date | None:
        return self.entered.get("desk")

    @property
    def days_since_desk(self) -> int | None:
        return None if self.desk_date is None else (self.as_of - self.desk_date).days

    @property
    def is_open(self) -> bool:
        return self.stage != "paid"

    @property
    def is_invoice(self) -> bool:
        return self.doc_type == "invoice"


# ---------------------------------------------------------------------------------------- views
def open_invoices(bills: list[Bill]) -> list[Bill]:
    """Open invoices. The CFO views (oldest bills, ageing), the MSME countdown and the payment list use invoices only: a credit note is not owed to the vendor."""
    return [b for b in bills if b.is_open and b.is_invoice]


def oldest(bills: list[Bill], n: int = 20) -> list[Bill]:
    """The n open invoices that have waited longest since the desk logged them, oldest first (ties by bill id)."""
    return sorted(open_invoices(bills), key=lambda b: (-b.days_since_desk, b.bill_id))[:n]


AGEING_BUCKETS = [("0 to 15 days", 0, 15), ("16 to 30 days", 16, 30), ("31 to 45 days", 31, 45), ("46 to 60 days", 46, 60), ("Over 60 days", 61, None)]


def ageing(bills: list[Bill]) -> list[dict]:
    """Open invoices by days since the desk logged them: count, value before GST, and how many are from known Micro or Small vendors."""
    rows = []
    for label, lo, hi in AGEING_BUCKETS:
        inb = [b for b in open_invoices(bills) if b.days_since_desk >= lo and (hi is None or b.days_since_desk <= hi)]
        rows.append(dict(bucket=label, bills=len(inb), value_inr=sum(b.amount for b in inb),
                         micro_small=sum(1 for b in inb if b.msme_status in ("Micro", "Small")), unknown_msme=sum(1 for b in inb if b.msme_status == "Unknown")))
    return rows
