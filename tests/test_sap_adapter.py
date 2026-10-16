"""Tests for app/sap/adapter.py on a small fixture database that reproduces each data problem from notes/data-audit.md,
plus a few checks against the real extract (skipped if the pack is absent). The fixture is rebuilt for every test."""
import shutil
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from app.sap.adapter import SapAdapter, norm_name, norm_property

ROOT = Path(__file__).resolve().parent.parent
REAL = ROOT / "pack" / "data" / "sap_extract.sqlite"

SCHEMA = """
CREATE TABLE vendor_master (vendor_id, vendor_name, category, state, gstin, msme_status);
CREATE TABLE work_orders (wo_id, vendor_id, property_code, category, valid_from, valid_to, gl_code, cost_centre, approved_value_inr, billed_value_inr);
CREATE TABLE properties (property_code, property_name, property_type, city, state, units_or_sqft);
CREATE TABLE posted_invoices (bill_id, vendor_id, invoice_no, invoice_date, posted_date, amount_inr, gst_inr, wo_id);
CREATE TABLE parsed_bill (source_file TEXT NOT NULL, parsed_at TEXT NOT NULL, vendor_gstin TEXT, vendor_name TEXT, invoice_no TEXT, invoice_date TEXT,
    property_code TEXT, wo_id TEXT, taxable_inr REAL, cgst_inr REAL, sgst_inr REAL, igst_inr REAL, total_inr REAL, confidence REAL, check_status TEXT, check_notes TEXT);
"""
G1, G2, G3, G4 = "07SBDPT4452Q1ZF", "07BTTFV3567V1Z1", "06EPVCF6069Z1ZZ", "09WMLCG8394Z1Z9"


@pytest.fixture
def db(tmp_path):
    p = tmp_path / "sap.sqlite"
    c = sqlite3.connect(p)
    c.executescript(SCHEMA)
    c.executemany("INSERT INTO vendor_master VALUES (?,?,?,?,?,?)", [
        ("V1", "Yamuna Elevator Care Pvt Ltd", "Lift AMC", "Delhi", G1, "Micro"),
        ("V2", "Ojas Ojas Traders", "Diesel Supply", "Delhi", G2, ""),           # D16 repeated word, D07 blank MSME
        ("V3", "Ojas Elevator Care Pvt Ltd", "Lift AMC", "Haryana", G3, "Small"),  # D17 near duplicate pair with V4
        ("V4", "Tejas Elevator Care Pvt Ltd", "Lift AMC", "Haryana", G4, "Not MSME"),
        ("V5", "Ojas Elevator Care Private Limited", "Lift AMC", "Haryana", "06AAAAA0000A1Z5", "Small"),  # same normalised name as V3
    ])
    c.executemany("INSERT INTO work_orders VALUES (?,?,?,?,?,?,?,?,?,?)", [
        ("W1", "V1", "NOI-C32", "Lift AMC", "2025-01-01", "2026-12-31", "680722", "CC1", "1000000", "600000"),  # open
        ("W2", "V1", "NOI-C32", "Lift AMC", "2024-01-01", "2025-06-30", "680722", "CC1", "500000", "500000"),  # expired, fully billed
        ("W3", "V1", "NOI-C32", "Lift AMC", "2026-03-14", "2025-03-14", "680722", "CC1", "30000", "32850"),    # D09 inverted, D10 over-billed
        ("W4", "V1", "NOI-C32", "Lift AMC", "2026-06-01", "2027-05-31", "680722", "CC1", "900", "0"),          # not yet valid, nothing billed
        ("W5", "V1", "NOI-C32", "Lift AMC", "2025-01-01", "2026-12-31", "680722", "CC1", "1000000", "1000000"),  # nothing left
    ])
    c.executemany("INSERT INTO properties VALUES (?,?,?,?,?,?)", [("NOI-C32", "Tower", "Office Tower", "Noida", "Uttar Pradesh", "1728"), ("DEL-R03", "Society", "Residential Society", "Delhi", "Delhi", "310")])
    dup = ("TRK1", "V1", "100/25-26/1", "2025-05-30", "2025-06-20", "3380", "608", "W1")
    c.executemany("INSERT INTO posted_invoices VALUES (?,?,?,?,?,?,?,?)", [
        dup, dup,                                                                  # D11 exact duplicate
        ("TRK2", "V1", "100/25-26/1", "2025-08-01", "2025-09-01", "9000", "1620", "W1"),  # D04 same number, other bill
        ("TRK3", "V1", "200/25-26/2", "2025-05-30", "2025-06-20", "100", "18", "W1"),
    ])
    c.commit()
    c.close()
    return p


@pytest.fixture
def sap(db):
    with SapAdapter(db) as a:
        yield a


# ---------------------------------------------------------------- read-only
def test_read_connection_refuses_writes(sap):
    for sql in ["INSERT INTO parsed_bill (source_file, parsed_at) VALUES ('x','y')", "UPDATE vendor_master SET vendor_name = 'x'",
                "DELETE FROM posted_invoices", "DROP TABLE properties", "CREATE TABLE t (a)"]:
        with pytest.raises(sqlite3.DatabaseError):
            sap._ro.execute(sql)


def test_missing_file_is_not_created(tmp_path):
    with pytest.raises(FileNotFoundError):
        SapAdapter(tmp_path / "nope.sqlite")
    assert not (tmp_path / "nope.sqlite").exists()


# ---------------------------------------------------------------- vendors
def test_vendor_by_gstin_trims_and_upper_cases(sap):
    r = sap.get_vendor(gstin=f"  {G1.lower()} ")
    assert r.status == "found" and r.vendor.vendor_id == "V1" and r.vendor.msme_status == "Micro" and r.vendor.msme_known


def test_vendor_by_gstin_with_name_match(sap):
    assert sap.get_vendor(gstin=G1, name="YAMUNA ELEVATOR CARE PVT. LTD.").name_match is True
    assert sap.get_vendor(gstin=G1, name="Tejas Elevator Care").name_match is False


def test_bad_format_and_unknown_gstin(sap):
    assert sap.get_vendor(gstin="12345").status == "bad_format"
    assert sap.get_vendor(gstin="29ABCDE1234F1Z5").status == "not_found"
    assert sap.get_vendor().status == "no_query"


def test_blank_msme_is_unknown_not_guessed_d07(sap):
    v = sap.get_vendor(gstin=G2).vendor
    assert v.msme_status == "Unknown" and not v.msme_known and "msme_blank" in v.flags


def test_repeated_word_name_d16(sap):
    r = sap.get_vendor(name="Ojas Traders")
    assert r.status == "found" and r.vendor.vendor_id == "V2" and "name_repeated_word" in r.vendor.flags


def test_near_duplicate_names_are_not_merged_d17(sap):
    assert sap.get_vendor(name="Tejas Elevator Care Pvt Ltd").vendor.vendor_id == "V4"
    amb = sap.get_vendor(name="Ojas Elevator Care")
    assert amb.status == "ambiguous" and {v.vendor_id for v in amb.vendors} == {"V3", "V5"}
    assert sap.get_vendor(name="Ojas Elevators Care").status == "not_found"


# ---------------------------------------------------------------- work orders
def test_open_order_balance_and_burn(sap):
    wo = sap.get_work_order("W1", date(2025, 6, 1))
    assert wo.validity == "valid" and not wo.expiry_may_be_stale
    assert wo.approved == 1_000_000 and wo.billed == 600_000 and wo.remaining == 400_000 and not wo.overbilled
    assert wo.headroom_after(150_000) == 250_000 and wo.headroom_after(500_000) == -100_000
    days = (date(2026, 4, 30) - date(2025, 1, 1)).days
    assert wo.months_elapsed == pytest.approx(days / 30.4375)
    assert wo.monthly_burn == pytest.approx(600_000 / (days / 30.4375))
    assert wo.runway_months == pytest.approx(400_000 / wo.monthly_burn)
    assert wo.days_to_end == (date(2026, 12, 31) - date(2026, 4, 30)).days


def test_expired_is_flagged_possibly_stale_d08(sap):
    wo = sap.get_work_order("W2", "2025-07-15")
    assert wo.validity == "expired" and wo.expiry_may_be_stale
    assert sap.get_work_order("W2", date(2025, 6, 30)).validity == "valid"
    assert wo.days_to_end < 0
    assert wo.months_elapsed == pytest.approx((date(2025, 6, 30) - date(2024, 1, 1)).days / 30.4375)  # capped at valid_to


def test_inverted_validity_is_unknown_and_has_no_burn_d09(sap):
    wo = sap.get_work_order("W3", date(2025, 3, 20))
    assert wo.validity == "unknown" and "validity_inverted" in wo.flags
    assert wo.monthly_burn is None and wo.days_to_end is None and wo.runway_months == 0.0


def test_overbilled_keeps_negative_balance_d10(sap):
    wo = sap.get_work_order("W3")
    assert wo.overbilled and wo.remaining == pytest.approx(-2850)


def test_not_yet_valid_and_no_burn_before_start(sap):
    wo = sap.get_work_order("W4", date(2026, 5, 1))
    assert wo.validity == "not_yet_valid" and wo.monthly_burn is None and wo.runway_months is None


def test_no_date_gives_unknown_validity_but_balance_still_returned(sap):
    wo = sap.get_work_order("W1")
    assert wo.validity == "unknown" and wo.remaining == 400_000 and wo.monthly_burn is not None


def test_nothing_left_has_zero_runway(sap):
    assert sap.get_work_order("W5", date(2025, 6, 1)).runway_months == 0.0


def test_unknown_work_order_is_none(sap):
    assert sap.get_work_order("nope") is None and sap.get_work_order("") is None


# ---------------------------------------------------------------- posted invoices
def test_posted_invoices_dedupe_and_keep_reused_numbers_d11_d04(sap):
    r = sap.find_posted_invoices("V1", " 100/25-26/1 ")
    assert [p.bill_id for p in r] == ["TRK1", "TRK2"]
    assert r[0].amount == 3380 and r[0].invoice_date == date(2025, 5, 30) and r[1].amount == 9000


def test_posted_invoices_other_vendor_or_number_is_empty(sap):
    assert sap.find_posted_invoices("V2", "100/25-26/1") == []
    assert sap.find_posted_invoices("V1", "999") == []


# ---------------------------------------------------------------- properties
def test_property_codes_are_normalised_d02(sap):
    assert norm_property(" noi c32 ") == "NOI-C32"
    p = sap.get_property("noi c32 ")
    assert p.property_code == "NOI-C32" and not p.matched_as_given and p.size == 1728
    assert sap.get_property("DEL-R03").matched_as_given
    assert sap.get_property("ZZZ-9") is None


def test_name_normalisation():
    assert norm_name("Ojas Ojas Traders Pvt. Ltd.") == "ojas traders"


# ---------------------------------------------------------------- the one write
def test_write_parsed_bill(sap, db):
    rid = sap.write_parsed_bill(source_file="bill-11.pdf", vendor_gstin=G4, invoice_no="085/25-26/730", total_inr=72700.0, confidence=0.93,
                                check_status="ok", parsed_at="2026-10-17T10:00:00+00:00")
    assert rid == 1
    c = sqlite3.connect(db)
    row = c.execute("SELECT source_file, parsed_at, vendor_gstin, total_inr, confidence, check_status FROM parsed_bill").fetchall()
    c.close()
    assert row == [("bill-11.pdf", "2026-10-17T10:00:00+00:00", G4, 72700.0, 0.93, "ok")]


def test_write_validates_and_leaves_other_tables_alone(sap, db):
    with pytest.raises(ValueError):
        sap.write_parsed_bill(source_file="")
    with pytest.raises(ValueError):
        sap.write_parsed_bill(source_file="x.pdf", confidence=1.5)
    c = sqlite3.connect(db)
    assert c.execute("SELECT count(*) FROM parsed_bill").fetchone()[0] == 0
    assert c.execute("SELECT count(*) FROM posted_invoices").fetchone()[0] == 4
    c.close()


def test_write_connection_cannot_touch_other_tables(db):
    import app.sap.adapter as m
    rw = sqlite3.connect(f"file:{db.as_posix()}?mode=rw", uri=True)
    rw.set_authorizer(m._parsed_bill_guard)
    for sql in ["DELETE FROM vendor_master", "UPDATE work_orders SET billed_value_inr = '0'", "INSERT INTO posted_invoices VALUES (1,2,3,4,5,6,7,8)"]:
        with pytest.raises(sqlite3.DatabaseError):
            rw.execute(sql)
    rw.close()


# ---------------------------------------------------------------- real extract, read through a copy (the pack is never opened for writing)
real = pytest.mark.skipif(not REAL.is_file(), reason="pack not present")


@real
def test_real_extract_inbox_bills(tmp_path):
    p = tmp_path / "copy.sqlite"
    shutil.copy(REAL, p)
    with SapAdapter(p) as sap:
        v = sap.get_vendor(gstin="09WMLCG8394Z1Z9")
        assert v.status == "found" and v.vendor.vendor_id == "V10085" and v.vendor.msme_status == "Unknown"
        wo = sap.get_work_order("4101752", date(2025, 8, 2))
        assert wo.validity == "valid" and wo.remaining == pytest.approx(38064.0)
        assert sap.get_work_order("4100602", date(2025, 6, 4)).remaining == pytest.approx(-422500.0)
        pk = sap.find_posted_invoices("V10550", "550/25-26/340")
        assert len(pk) == len({p.bill_id for p in pk}) and len(pk) >= 1
        assert sap.get_property("noi c32") is not None or sap.get_property("NOI-C32") is not None


@real
def test_real_extract_posted_invoices_have_no_duplicate_rows(tmp_path):
    p = tmp_path / "copy.sqlite"
    shutil.copy(REAL, p)
    with SapAdapter(p) as sap:
        ids = [r["vendor_id"] for r in sap._ro.execute("SELECT DISTINCT vendor_id FROM posted_invoices LIMIT 50")]
        for vid in ids:
            rows = sap._ro.execute("SELECT DISTINCT invoice_no FROM posted_invoices WHERE vendor_id = ?", (vid,)).fetchall()
            for r in rows:
                got = sap.find_posted_invoices(vid, r["invoice_no"])
                assert len({x.bill_id for x in got}) == len(got)


def test_vendor_by_id(sap):
    assert sap.get_vendor_by_id("V2").msme_status == "Unknown"
    assert sap.get_vendor_by_id(" V1 ").name.startswith("Yamuna")
    assert sap.get_vendor_by_id("V99") is None
