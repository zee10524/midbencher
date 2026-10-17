"""Tests for app/intake.py: the glue from a reader result to the checks, the verdict and parsed_bill. Reader results are built by hand here."""
import shutil
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from app import intake
from app.rules import Context
from app.sap.adapter import SapAdapter

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "pack" / "data"


def fld(v, c=0.97, note=""):
    return dict(value=v, conf=c, note=note)


def result(**over):
    f = dict(vendor_gstin=fld("07FFWFT1642T1ZA", 0.95), vendor_name=fld("X", 0.97), invoice_no=fld("866/25-26/737", 0.92), invoice_date=fld("2025-11-05", 0.95), wo_id=fld("4100272", 0.96),
             taxable=fld(575510.0), cgst=fld(None, 0.0), sgst=fld(None, 0.0), igst=fld(103591.8), total=fld(679101.8), hsn_sac=fld("998533", 0.96),
             place_of_supply=fld("Haryana", 0.95), recipient_gstin=fld("06AAACX4421K1ZQ", 0.92))
    f.update(over.pop("fields", {}))
    return dict(file="x.pdf", fields=f, arithmetic_ok=True, no_gst_printed=False, bill_type="pdf_single", status="ok", route_hint="auto-clear", overall_confidence=0.92, reasons=[],
                supporting={}, reader={"simulated": False}, doc_type="invoice") | over


def test_bill_read_carries_the_readers_values_and_confidences():
    b = intake.bill_read(result())
    assert b.invoice_date.value == date(2025, 11, 5) and b.invoice_no.confidence == 0.92 and b.vendor_gstin.confidence == 0.95


def test_tax_lines_not_printed_count_as_zero_only_when_the_amounts_add_up():
    b = intake.bill_read(result())
    assert (b.cgst_inr.value, b.sgst_inr.value, b.igst_inr.value) == (0.0, 0.0, 103591.8) and b.cgst_inr.confidence == 0.97
    b2 = intake.bill_read(result(arithmetic_ok=False))
    assert b2.cgst_inr.value is None and b2.cgst_inr.confidence == 0.0


def test_gst_not_applicable_makes_all_three_tax_lines_zero():
    r = result(no_gst_printed=True, fields=dict(igst=fld(None, 0.0)))
    b = intake.bill_read(r)
    assert (b.cgst_inr.value, b.sgst_inr.value, b.igst_inr.value) == (0.0, 0.0, 0.0)


def test_a_work_order_line_printed_blank_is_a_fact_not_a_missing_read():
    blank = result(fields=dict(wo_id=fld(None, 0.0, "printed blank: the label is on the bill and no number follows it")))
    assert intake.bill_read(blank).wo_id.confidence == intake.BLANK_CONF
    unread = result(fields=dict(wo_id=fld(None, 0.0, "")))
    assert intake.bill_read(unread).wo_id.confidence == 0.0


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    d = tmp_path_factory.mktemp("intake")
    shutil.copyfile(PACK / "sap_extract.sqlite", d / "c.sqlite")
    from app.tracker import seed
    sap = SapAdapter(d / "c.sqlite")
    bills = seed(PACK / "bill_register.csv", PACK / "queries.csv", sap)
    yield sap, Context(sap, bills, bill_counted_in_billed=True), bills
    sap.close()


def test_a_blank_work_order_fails_p3_for_the_vendor_and_a_missing_one_asks_for_a_clearer_image(world):
    sap, ctx, _ = world
    blank = intake.check_bill(result(fields=dict(wo_id=fld(None, 0.0, "printed blank: the label is on the bill and no number follows it"))), ctx)
    p3 = next(r for r in blank["results"] if r.check_id == "P3")
    assert p3.status == "fail" and p3.owner == "vendor" and blank["routing"].route == "fix-before-sending"
    unread = intake.check_bill(result(fields=dict(wo_id=fld(None, 0.0, ""))), ctx)
    assert unread["routing"].route == "human-look" and unread["unread"] == ["Work order"]          # a partial verdict, not a switched-off one
    assert {n["check"] for n in unread["not_run"]} == {"P3", "H3", "H11"} and any(r.check_id == "P1/H1" for r in unread["results"])
    assert any(a.kind == "resend" and "Work order" in a.text for a in unread["routing"].actions)


def test_the_inbox_bill_is_linked_to_its_own_register_row_so_it_is_not_its_own_duplicate(world):
    sap, ctx, bills = world
    row = next(b for b in bills if b.bill_id == "TRK259268")                    # bill-11.pdf in the inbox
    v = sap.get_vendor_by_id(row.vendor_id)
    r = result(fields=dict(vendor_gstin=fld(v.gstin, 0.95), invoice_no=fld(row.invoice_no, 0.95), invoice_date=fld(row.invoice_date.isoformat(), 0.95), taxable=fld(row.amount), wo_id=fld(row.wo_id)))
    out = intake.check_bill(r, ctx)
    assert out["own_bill_id"] == "TRK259268"
    assert next(x for x in out["results"] if x.check_id == "H13").status == "pass"


def test_verdict_is_written_to_parsed_bill_with_the_flags_in_the_notes(world, tmp_path):
    sap, ctx, _ = world
    shutil.copyfile(PACK / "sap_extract.sqlite", tmp_path / "w.sqlite")
    res = result()
    out = intake.check_bill(res, ctx)
    from app.reader import pipeline
    a = pipeline.parsed_bill_args(res)
    a["check_status"], a["check_notes"] = out["routing"].route, intake.verdict_notes(res, out)
    with SapAdapter(tmp_path / "w.sqlite") as w:
        w.write_parsed_bill(**a)
        row = w._ro.execute("select source_file, check_status, check_notes from parsed_bill").fetchone()
    assert row[0] == "x.pdf" and row[1] == out["routing"].route and "checks:" in row[2] and "actions:" in row[2]
