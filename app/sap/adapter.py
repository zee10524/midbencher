"""Read-only access to the SAP stand-in (`sap_extract.sqlite`), plus one write path into `parsed_bill`.

Everything the intake checks need from SAP goes through this module: the vendor master (checks P1/H1),
work orders with validity and balance (P3/H3, the work-order runway view), posted invoices (H13) and
properties (routing). Nothing else in the app opens the database.

How it keeps the extract safe
- The read connection is opened with SQLite `mode=ro` and `PRAGMA query_only`, and carries an authoriser that
  refuses everything except reads, so a bug elsewhere cannot write.
- The only write is `SapAdapter.write_parsed_bill`. It opens a second connection for the length of one call,
  with an authoriser that permits an INSERT into `parsed_bill` and nothing else.
- `pack/` is never edited. Point `db_path` at a working copy when you want `parsed_bill` writes; the adapter
  does not copy the file.

Data problems handled (numbers refer to `notes/data-audit.md`)
- Every column is stored as text; amounts and dates are converted here and a blank or bad value becomes None.
- D07  A blank `msme_status` is returned as `Unknown` and the vendor is flagged `msme_blank`. It is never guessed.
- D08  An order whose `valid_to` has passed is reported as `expired` with `expiry_may_be_stale` set. The caller
       may route to a human look, but should not hard-block on it: the extract may not hold amendments.
- D09  An order with `valid_to` before `valid_from` has validity `unknown`; dates are returned as stored and
       no burn or days-to-end is computed.
- D10  `billed` above `approved` is real signal, not an error. The balance is returned negative and `overbilled` is set.
- D11  `posted_invoices` has exact duplicate rows. They are collapsed before anything is returned.
- D12  `posted_invoices` is incomplete for some posted bills, so an empty result from `find_posted_invoices`
       does not prove an invoice was never posted. The caller must not treat it as the whole truth.
- D04  The same vendor and invoice number can belong to different bills (reuse, not double billing). All are
       returned; the caller decides on amount and date.
- D02  Property codes arrive in different cases, with spaces for hyphens and stray spaces. `get_property` normalises.
- D16, D17  Vendor names with a repeated word and near-duplicate vendor names. Names are normalised for matching
       (repeated words, `Pvt`, `Ltd` and similar dropped), only an exact normalised match counts, and vendors are
       never merged. An ambiguous name returns every candidate.

Real connection
    The adapter is the seam where RFC replaces SQLite: each method below names the access it would need. Reading is
    approved (`context/documents/sap-extract-spec.md`). Table and function names are from general SAP knowledge and are
    **not verified against this company's system**; IT must confirm them. Writing is a different matter:
    writing invoices into SAP needs a separate project with the SAP partner and audit sign-off, so the
    product never posts and `parsed_bill` stays in the product's own store.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path

# The extract was taken on this date (latest posting date in `posted_invoices`). Burn and days-to-end are measured to it.
AS_OF = date(2026, 4, 30)
DAYS_PER_MONTH = 30.4375

_GSTIN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
_NAME_NOISE = {"pvt", "private", "ltd", "limited", "llp", "co", "company", "and", "the"}


# --------------------------------------------------------------------------------------- result types
@dataclass(frozen=True)
class Vendor:
    vendor_id: str
    name: str
    category: str
    state: str
    gstin: str
    msme_status: str  # Micro, Small, Medium, Not MSME, or Unknown when blank in the master (D07)
    flags: tuple[str, ...] = ()

    @property
    def msme_known(self) -> bool:
        return self.msme_status != "Unknown"


@dataclass(frozen=True)
class VendorLookup:
    """status: found | not_found | ambiguous | bad_format | no_query.
    name_match is set when both a GSTIN and a name were given: True if the master's name equals the printed name after normalising."""
    status: str
    vendors: tuple[Vendor, ...] = ()
    name_match: bool | None = None
    gstin_used: str | None = None

    @property
    def vendor(self) -> Vendor | None:
        return self.vendors[0] if self.status == "found" else None


@dataclass(frozen=True)
class WorkOrder:
    wo_id: str
    vendor_id: str
    property_code: str
    category: str
    valid_from: date | None
    valid_to: date | None
    gl_code: str
    cost_centre: str
    approved: float | None
    billed: float | None
    validity: str  # valid | not_yet_valid | expired | unknown (D09, or no date given)
    on_date: date | None
    expiry_may_be_stale: bool  # D08: set when validity is `expired`
    flags: tuple[str, ...] = field(default=())

    @property
    def remaining(self) -> float | None:
        """Approved less billed to date. Negative when the order is over-billed (D10)."""
        if self.approved is None or self.billed is None:
            return None
        return self.approved - self.billed

    @property
    def overbilled(self) -> bool:
        return self.remaining is not None and self.remaining < 0

    def headroom_after(self, amount: float) -> float | None:
        """Remaining value if a bill of `amount` (not yet in `billed`) is booked against the order."""
        return None if self.remaining is None else self.remaining - amount

    @property
    def months_elapsed(self) -> float | None:
        """Months from `valid_from` to the earlier of the extract date and `valid_to`, at least one."""
        if self.validity == "unknown" and (self.valid_from is None or self.valid_to is None or self.valid_to < self.valid_from):
            return None
        if self.valid_from is None or self.valid_from > AS_OF:
            return None
        end = min(AS_OF, self.valid_to) if self.valid_to else AS_OF
        return max((end - self.valid_from).days / DAYS_PER_MONTH, 1.0)

    @property
    def monthly_burn(self) -> float | None:
        """Value billed so far divided by the months elapsed."""
        m = self.months_elapsed
        return None if m is None or self.billed is None else self.billed / m

    @property
    def runway_months(self) -> float | None:
        """Months of remaining value at the current burn. 0 when nothing is left, None when there is no burn to divide by."""
        if self.remaining is None:
            return None
        if self.remaining <= 0:
            return 0.0
        burn = self.monthly_burn
        return None if not burn else self.remaining / burn

    @property
    def days_to_end(self) -> int | None:
        """Days from the extract date to `valid_to`; negative once passed. None when the validity dates are unusable (D09)."""
        if self.valid_to is None or self.valid_from is None or self.valid_to < self.valid_from:
            return None
        return (self.valid_to - AS_OF).days


@dataclass(frozen=True)
class PostedInvoice:
    bill_id: str
    vendor_id: str
    invoice_no: str
    invoice_date: date | None
    posted_date: date | None
    amount: float | None
    gst: float | None
    wo_id: str


@dataclass(frozen=True)
class Property:
    property_code: str
    name: str
    property_type: str
    city: str
    state: str
    size: float | None
    matched_as_given: bool  # False when the code needed normalising (D02)


# --------------------------------------------------------------------------------------- helpers
def _num(x) -> float | None:
    try:
        return float(x) if x not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _date(x) -> date | None:
    try:
        return date.fromisoformat(str(x)[:10]) if x else None
    except ValueError:
        return None


def norm_gstin(x: str | None) -> str:
    return re.sub(r"\s+", "", x or "").upper()


def norm_name(x: str | None) -> str:
    """Lower case, punctuation dropped, `Pvt`/`Ltd` and similar dropped, repeated neighbouring words collapsed (D16)."""
    words = [w for w in re.sub(r"[^a-z0-9 ]+", " ", (x or "").casefold()).split() if w not in _NAME_NOISE]
    return " ".join(w for i, w in enumerate(words) if i == 0 or w != words[i - 1])


def norm_invoice_no(x: str | None) -> str:
    return re.sub(r"\s+", "", x or "").upper()


def norm_property(x: str | None) -> str:
    return re.sub(r"[\s_-]+", "-", (x or "").strip()).upper()


def _read_only_guard(action, arg1, arg2, db, source):
    return sqlite3.SQLITE_OK if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION) else sqlite3.SQLITE_DENY


def _parsed_bill_guard(action, arg1, arg2, db, source):
    if action == sqlite3.SQLITE_INSERT and arg1 == "parsed_bill":
        return sqlite3.SQLITE_OK
    if action in (sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_FUNCTION):
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


_INSERT = ("INSERT INTO parsed_bill (source_file, parsed_at, vendor_gstin, vendor_name, invoice_no, invoice_date, property_code, wo_id, "
           "taxable_inr, cgst_inr, sgst_inr, igst_inr, total_inr, confidence, check_status, check_notes) "
           "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")


# --------------------------------------------------------------------------------------- the adapter
class SapAdapter:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        if not self.db_path.is_file():
            raise FileNotFoundError(self.db_path)
        self._ro = sqlite3.connect(f"file:{self.db_path.as_posix()}?mode=ro", uri=True)
        self._ro.row_factory = sqlite3.Row
        self._ro.execute("PRAGMA query_only = ON")
        self._ro.set_authorizer(_read_only_guard)
        self._names: dict[str, list[sqlite3.Row]] | None = None

    def close(self) -> None:
        self._ro.close()

    def __enter__(self) -> SapAdapter:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ---------------------------------------------------------------- vendors
    def _vendor(self, r: sqlite3.Row) -> Vendor:
        flags = []
        msme = (r["msme_status"] or "").strip()
        if not msme:
            flags.append("msme_blank")  # D07
        words = norm_name(r["vendor_name"]).split()
        raw = re.sub(r"[^a-z0-9 ]+", " ", (r["vendor_name"] or "").casefold()).split()
        if len([w for w in raw if w not in _NAME_NOISE]) != len(words):
            flags.append("name_repeated_word")  # D16
        return Vendor(r["vendor_id"], r["vendor_name"], r["category"], r["state"], norm_gstin(r["gstin"]), msme or "Unknown", tuple(flags))

    def get_vendor(self, gstin: str | None = None, name: str | None = None) -> VendorLookup:
        """Find a vendor by GSTIN, by name, or by both.

        With a GSTIN: the GSTIN is trimmed and upper-cased; one that is not a well-formed GSTIN returns `bad_format` and is not looked up.
        GSTINs are unique in the master, so a hit is `found`. If a name is also given, `name_match` says whether it equals the master's
        name after normalising (this is check P1/H1).
        With a name only: an exact match on the normalised name. One hit is `found`, several are `ambiguous` with every candidate, none is
        `not_found`. Similar names are never merged or guessed (D17).

        Real connection: vendor master over RFC read access, `RFC_READ_TABLE` on LFA1 (name, state, tax numbers including the GSTIN) and
        the India vendor extension that holds the MSME or Udyam type (table name to be confirmed by IT), or `BAPI_VENDOR_GETDETAIL` where
        enabled. Read-only; no change to the master.
        """
        if gstin:
            g = norm_gstin(gstin)
            if not _GSTIN.match(g):
                return VendorLookup("bad_format", gstin_used=g)
            rows = self._ro.execute("SELECT * FROM vendor_master WHERE upper(replace(gstin, ' ', '')) = ?", (g,)).fetchall()
            if not rows:
                return VendorLookup("not_found", gstin_used=g)
            vs = tuple(self._vendor(r) for r in rows)
            nm = None if not name else norm_name(name) == norm_name(vs[0].name)
            return VendorLookup("found" if len(vs) == 1 else "ambiguous", vs, nm, g)
        if name:
            if self._names is None:
                self._names = {}
                for r in self._ro.execute("SELECT * FROM vendor_master"):
                    self._names.setdefault(norm_name(r["vendor_name"]), []).append(r)
            rows = self._names.get(norm_name(name), [])
            vs = tuple(self._vendor(r) for r in rows)
            return VendorLookup("not_found" if not vs else "found" if len(vs) == 1 else "ambiguous", vs)
        return VendorLookup("no_query")

    def get_vendor_by_id(self, vendor_id: str) -> Vendor | None:
        """Return the vendor with this vendor code, or None. Used by the tracker to attach a name and MSME status to each bill.

        Real connection: the same vendor master read as `get_vendor`, keyed on the vendor account number (LIFNR in LFA1).
        """
        r = self._ro.execute("SELECT * FROM vendor_master WHERE vendor_id = ?", ((vendor_id or "").strip(),)).fetchone()
        return None if r is None else self._vendor(r)

    # ---------------------------------------------------------------- work orders
    def get_work_order(self, wo_id: str, on_date: date | str | None = None) -> WorkOrder | None:
        """Return a work order or purchase order with validity on `on_date` (normally the bill date), remaining balance and monthly burn.

        None when the number is not in the extract (check P3: the number on the bill must exist). Validity is `valid`, `not_yet_valid`,
        `expired` (D08, flagged as possibly stale), or `unknown` when `valid_to` is before `valid_from` (D09) or no date is given.
        `remaining` is approved less billed to date and can be negative (D10); `headroom_after(amount)` takes a bill's amount off it.
        `monthly_burn` is billed value over the months from `valid_from` to the extract date (or `valid_to` if earlier), at least one month,
        and `runway_months` is remaining over burn. These are simple averages; the extract has no period balance or open quantity.

        Real connection: purchase orders and outline agreements over RFC read access: `BAPI_PO_GETDETAIL1` (header, items, account
        assignment, validity) or `RFC_READ_TABLE` on EKKO and EKPO (validity dates, target value) and EKKN (GL account and cost centre),
        plus purchase-order history EKBE (or `BAPI_PO_GETDETAIL1` history tables) for value billed so far. Period balance, open quantity and
        rates need the item and schedule-line tables, which the extract lacks; IT must confirm where this company keeps the approved value.
        """
        r = self._ro.execute("SELECT * FROM work_orders WHERE wo_id = ?", ((wo_id or "").strip(),)).fetchone()
        if r is None:
            return None
        vf, vt = _date(r["valid_from"]), _date(r["valid_to"])
        d = _date(on_date) if isinstance(on_date, str) else on_date
        flags = []
        if vf is None or vt is None or vt < vf:
            validity = "unknown"
            flags.append("validity_inverted" if vf and vt and vt < vf else "validity_missing")  # D09
        elif d is None:
            validity = "unknown"
        elif d < vf:
            validity = "not_yet_valid"
        elif d > vt:
            validity = "expired"
        else:
            validity = "valid"
        wo = WorkOrder(r["wo_id"], r["vendor_id"], r["property_code"], r["category"], vf, vt, r["gl_code"], r["cost_centre"],
                       _num(r["approved_value_inr"]), _num(r["billed_value_inr"]), validity, d, validity == "expired", tuple(flags))
        return wo

    # ---------------------------------------------------------------- posted invoices
    def find_posted_invoices(self, vendor_id: str, invoice_no: str) -> list[PostedInvoice]:
        """Invoices already posted for this vendor with this invoice number, oldest first (check H13).

        Exact duplicate rows are collapsed (D11). Several different bills can share one number (D04), so the caller compares amount and
        date. An empty list does not prove the invoice was never posted (D12).

        Real connection: posted vendor invoices over RFC read access: `RFC_READ_TABLE` on RBKP (invoice document header: reference
        number, document and posting dates, gross amount) with RSEG for the purchase-order link, or BKPF and BSIK/BSAK filtered on the
        vendor and the reference field (XBLNR); or `BAPI_INCOMINGINVOICE_GETDETAIL` for one known document. Include parked and held
        documents, or the duplicate check will miss them.
        """
        want = norm_invoice_no(invoice_no)
        rows = self._ro.execute("SELECT DISTINCT * FROM posted_invoices WHERE vendor_id = ?", ((vendor_id or "").strip(),)).fetchall()
        out = [PostedInvoice(r["bill_id"], r["vendor_id"], r["invoice_no"], _date(r["invoice_date"]), _date(r["posted_date"]), _num(r["amount_inr"]),
                             _num(r["gst_inr"]), r["wo_id"]) for r in rows if norm_invoice_no(r["invoice_no"]) == want]
        return sorted(out, key=lambda p: (p.posted_date or date.max, p.bill_id))

    # ---------------------------------------------------------------- properties
    def get_property(self, code: str) -> Property | None:
        """Return a property by code, tolerating case, spaces for hyphens and stray spaces (D02). None if unknown.

        Real connection: plants or business places and cost-centre master over RFC read access: `RFC_READ_TABLE` on T001W (plant name, city,
        region) and CSKS or the company's own property table for type and size. Which object represents a property is for IT to confirm.
        """
        code_n = norm_property(code)
        r = self._ro.execute("SELECT * FROM properties WHERE upper(trim(property_code)) = ?", (code_n,)).fetchone()
        if r is None:
            return None
        return Property(r["property_code"], r["property_name"], r["property_type"], r["city"], r["state"], _num(r["units_or_sqft"]),
                        (code or "") == r["property_code"])

    # ---------------------------------------------------------------- the one write
    def write_parsed_bill(self, *, source_file: str, vendor_gstin: str | None = None, vendor_name: str | None = None, invoice_no: str | None = None,
                          invoice_date: str | None = None, property_code: str | None = None, wo_id: str | None = None,
                          taxable_inr: float | None = None, cgst_inr: float | None = None, sgst_inr: float | None = None,
                          igst_inr: float | None = None, total_inr: float | None = None, confidence: float | None = None,
                          check_status: str | None = None, check_notes: str | None = None, parsed_at: str | None = None) -> int:
        """Record a bill as read from the inbox, before any posting. Returns the new row id. The only write this adapter allows.

        `source_file` is required and `confidence`, when given, must be between 0 and 1. `parsed_at` defaults to now in UTC. Values are stored as
        printed on the bill. The write uses its own connection that can insert into `parsed_bill` and nothing else, and the file must already
        exist (it is never created).

        Real connection: there is none to SAP. Writing invoices into SAP needs a separate project with the SAP partner and audit sign-off
        (`BAPI_INCOMINGINVOICE_CREATE` or `BAPI_INCOMINGINVOICE_PARK` would be the calls, and neither is requested). In production `parsed_bill` is
        a table in the product's own store in India, with the file hash and an audit trail, and SAP is still only read.
        """
        if not source_file or not str(source_file).strip():
            raise ValueError("source_file is required")
        if confidence is not None and not 0.0 <= float(confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        stamp = parsed_at or datetime.now(UTC).isoformat(timespec="seconds")
        vals = (str(source_file).strip(), stamp, vendor_gstin, vendor_name, invoice_no, invoice_date, property_code, wo_id,
                taxable_inr, cgst_inr, sgst_inr, igst_inr, total_inr, confidence, check_status, check_notes)
        rw = sqlite3.connect(f"file:{self.db_path.as_posix()}?mode=rw", uri=True)
        try:
            rw.set_authorizer(_parsed_bill_guard)
            cur = rw.execute(_INSERT, vals)
            rw.commit()
            return int(cur.lastrowid)
        finally:
            rw.close()
