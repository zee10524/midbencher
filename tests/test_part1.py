"""Part 1 tests: partial checks when a field is unread, the vendor looked up from the master, human review saved to parsed_bill, and the reader's repair helpers.
The hand-labelled file is never opened here or anywhere in app code."""
import copy
import json
import shutil
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from app import intake
from app.reader import pipeline, resolve
from app.reader.fields import AUTO, F, BillFields, merge_header
from app.rules import Context, read
from app.rules import checks as C
from app.sap.adapter import SapAdapter
from app.tracker import seed
from app.ui import data

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "pack" / "data"


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    d = tmp_path_factory.mktemp("p1")
    shutil.copyfile(PACK / "sap_extract.sqlite", d / "c.sqlite")
    sap = SapAdapter(d / "c.sqlite")
    bills = seed(PACK / "bill_register.csv", PACK / "queries.csv", sap)
    S = data.State()
    S.bills = bills
    yield sap, bills, S
    sap.close()


def cached(name):
    return json.loads((pipeline.CACHE_DIR / f"{name}.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ 1A: partial checks
def test_possible_repeat_when_the_invoice_number_is_unread(world):
    sap, bills, _ = world
    x = next(b for b in bills if b.doc_type == "invoice" and b.vendor_id == "V10444")        # a real bill of a real vendor
    v = sap.get_vendor_by_id(x.vendor_id)
    ctx = Context(sap, bills)
    bill = read(vendor_gstin=v.gstin, invoice_date=x.invoice_date, taxable_inr=x.amount)    # no invoice number at all, and this bill is not in the register
    same = C.check_h13_partial(bill, ctx)
    assert same.status == "warn" and "Possible repeat, confirm the invoice number" in same.fix and same.evidence["partial"] is True
    assert same.evidence["matches"][0]["basis"] == "same date and amount" and same.evidence["matches"][0]["bill_id"] == x.bill_id
    other = C.check_h13_partial(read(vendor_gstin=v.gstin, invoice_date=x.invoice_date, taxable_inr=x.amount + 1000.0), ctx)
    assert other.status == "pass" and other.evidence["matches"] == []
    own = C.check_h13_partial(read(own_bill_id=x.bill_id, vendor_gstin=v.gstin, invoice_date=x.invoice_date, taxable_inr=x.amount), ctx)
    assert own.status == "pass"                                                               # a bill is not a repeat of its own register row


def test_a_doubtful_invoice_number_is_only_a_lead_for_a_person(world):
    sap, bills, _ = world
    res = copy.deepcopy(cached("packet-08-repeat-invoice.pdf"))
    f = res["fields"]["invoice_no"]
    f["conf"] = 0.54                                                                           # as the first-run reader read it: right text, low confidence
    out = intake.check_bill(res, Context(sap, bills, bill_counted_in_billed=True))
    h13 = next(r for r in out["results"] if r.check_id == "H13")
    assert h13.status == "warn" and h13.evidence["partial"] and "Possible repeat, confirm the invoice number" in h13.fix
    assert "Invoice number" in out["unread"] and not any(n["check"] == "H13" for n in out["not_run"])
    assert out["routing"].route != "resend"


def test_every_check_that_can_run_runs_and_the_rest_are_listed_with_what_they_need(world):
    sap, bills, _ = world
    res = copy.deepcopy(cached("bill-13.pdf"))
    for k in ("taxable", "hsn_sac"):
        res["fields"][k]["value"], res["fields"][k]["conf"] = None, 0.0
    out = intake.check_bill(res, Context(sap, bills, bill_counted_in_billed=True))
    ran = {r.check_id for r in out["results"]}
    assert ran == {"P1/H1", "P3"} and {n["check"] for n in out["not_run"]} == {"H3", "H13", "H11", "H10"}      # without the taxable value the amount-based checks cannot run
    need = {n["check"]: n["needs"] for n in out["not_run"]}
    assert "Taxable value" in need["H3"] and "Taxable value" in need["H13"] and "HSN or SAC code" in need["H11"] and out["partial"]
    assert out["routing"].route != "resend"


def test_only_a_bill_on_which_no_check_can_run_is_sent_back(world):
    sap, bills, _ = world
    res = copy.deepcopy(cached("bill-13.pdf"))
    for k in list(res["fields"]):
        res["fields"][k]["value"], res["fields"][k]["conf"] = None, 0.0
    out = intake.check_bill(res, Context(sap, bills, bill_counted_in_billed=True))
    assert out["results"] == [] and out["routing"].route == "resend"


def test_a_credit_note_is_recognised_even_when_its_gstin_is_unread(world):
    sap, bills, S = world
    res = copy.deepcopy(cached("packet-10-credit-note.pdf"))
    g = res["fields"]["vendor_gstin"]
    g.update(value=None, conf=0.0, source="read")
    c = data.card(S, res, "stored", True)
    assert c["doc_type"] == "credit_note" and "Vendor GSTIN" in [r["name"] for r in c["fields"] if r["state"] == "unread"]
    assert any("credit note" in m["text"] for m in c["messages"])
    assert c["route"] != "resend" and c["checks_ran"] >= 2


def test_a_gstin_looked_up_from_the_master_is_never_treated_as_read(world):
    sap, bills, _ = world
    res = copy.deepcopy(cached("bill-13.pdf"))
    v = sap.get_vendor(gstin=res["fields"]["vendor_gstin"]["value"]).vendor
    res["fields"]["vendor_gstin"].update(source="vendor_master", conf=0.9)
    out = intake.check_bill(res, Context(sap, bills, bill_counted_in_billed=True))
    assert "P1/H1" in {n["check"] for n in out["not_run"]} and any(r.check_id == "H13" for r in out["results"])      # P1 needs the printed GSTIN; the others can use the looked-up one
    assert intake.bill_read(res).vendor_gstin.source == "vendor_master" and v.vendor_id


def test_a_repaired_gstin_is_a_warning_for_a_person_not_a_pass(world):
    sap, bills, _ = world
    res = copy.deepcopy(cached("bill-13.pdf"))
    res["fields"]["vendor_gstin"].update(source="repaired", conf=0.85)
    out = intake.check_bill(res, Context(sap, bills, bill_counted_in_billed=True))
    p1 = next(r for r in out["results"] if r.check_id == "P1/H1")
    assert p1.status == "warn" and "confusable" in p1.fix


# ------------------------------------------------------------------ 1B: human review
def test_a_clerk_types_an_unread_field_and_the_result_is_saved_with_the_readers_original(world, tmp_path, monkeypatch):
    sap, bills, S = world
    S.cache = {r["sha256"]: r for r in (cached(p.name[:-5]) for p in pipeline.CACHE_DIR.glob("*.json"))}
    monkeypatch.setattr(pipeline, "WORKING_DB", tmp_path / "work.sqlite")
    key = cached("bill-16.jpg")["sha256"]
    first = data.card(S, S.cache[key], "stored", True)
    assert "taxable" in first["inputs"]
    out = data.apply_review(S, key, {"taxable": "86,330.00"})
    assert out["saved"]["source"] == "human_review" and out["saved"]["typed"] == ["taxable"]
    typed = next(r for r in out["fields"] if r["key"] == "taxable")
    assert typed["state"] == "typed" and typed["value"] == "86,330.00" and out["checks_ran"] >= first["checks_ran"]
    row = sqlite3.connect(tmp_path / "work.sqlite").execute("select source_file, taxable_inr, source, reader_original, check_status from parsed_bill").fetchone()
    assert row[0] == "bill-16.jpg" and row[1] == 86330.0 and row[2] == "human_review" and row[4] == out["route"]
    original = json.loads(row[3])
    assert original == {"taxable": {"value": None, "conf": 0.0}}                              # the reader's own value and confidence are kept apart
    assert cached("bill-16.jpg")["fields"]["taxable"]["value"] is None                         # and the stored reading itself is unchanged


def test_typed_values_are_checked_and_nothing_empty_is_saved(world, tmp_path, monkeypatch):
    sap, bills, S = world
    S.cache = {r["sha256"]: r for r in (cached(p.name[:-5]) for p in pipeline.CACHE_DIR.glob("*.json"))}
    monkeypatch.setattr(pipeline, "WORKING_DB", tmp_path / "work.sqlite")
    key = cached("packet-10-credit-note.pdf")["sha256"]
    with pytest.raises(ValueError, match="HSN"):
        data.apply_review(S, key, {"hsn_sac": "12"})
    with pytest.raises(ValueError, match="Nothing was typed"):
        data.apply_review(S, key, {"hsn_sac": ""})
    with pytest.raises(ValueError, match="no longer held"):
        data.apply_review(S, "nope", {"taxable": "1"})
    assert not (tmp_path / "work.sqlite").exists()
    ok = data.apply_review(S, key, {"hsn_sac": "3304"})
    assert any(r["key"] == "hsn_sac" and r["state"] == "typed" for r in ok["fields"]) and not any(n["check"] == "H11" for n in ok["not_run"])


def test_normalise_typed_values():
    assert data.normalise_typed("vendor_gstin", " 07 sbdpt4452q1zf ") == "07SBDPT4452Q1ZF"
    assert data.normalise_typed("invoice_date", "05-11-2025") == "2025-11-05" and data.normalise_typed("invoice_date", "2025-11-05") == "2025-11-05"
    assert data.normalise_typed("taxable", "Rs 1,23,456.50") == 123456.5 and data.normalise_typed("wo_id", "4101 752") == "4101752"
    for k, bad in (("invoice_date", "31-02-2025"), ("vendor_gstin", "12345"), ("wo_id", "12"), ("taxable", "lots")):
        with pytest.raises(ValueError):
            data.normalise_typed(k, bad)


def test_the_parsed_bill_extra_columns_exist_in_the_working_copy(tmp_path):
    dst = pipeline.make_working_copy(PACK / "sap_extract.sqlite", tmp_path / "w.sqlite")
    cols = {r[1] for r in sqlite3.connect(dst).execute("pragma table_info(parsed_bill)")}
    assert {"source", "reader_original"} <= cols
    base = {r[1] for r in sqlite3.connect(f"file:{(PACK / 'sap_extract.sqlite').as_posix()}?mode=ro", uri=True).execute("pragma table_info(parsed_bill)")}
    assert not {"source", "reader_original"} & base                                           # the extract itself is unchanged


# ------------------------------------------------------------------ 1C: reader helpers
def test_the_gstin_check_digit_cannot_be_used_on_this_pack(world):
    sap, _, _ = world
    ch = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def digit(g):
        t = 0
        for i, c in enumerate(g[:14]):
            v = ch.index(c) * (1 if i % 2 == 0 else 2)
            t += v // 36 + v % 36
        return ch[(36 - t % 36) % 36]
    idx = sap.vendor_gstin_index()
    assert len(idx) == 900 and sum(digit(g) == g[14] for g in idx) == 0                      # none passes: a check-digit test would reject every true GSTIN here


def test_repair_to_master_needs_exactly_one_master_gstin_one_step_away(world):
    sap, _, _ = world
    idx = sap.vendor_gstin_index()
    g = next(x for x in idx if "O" in x[2:] or "0" in x[2:])
    i = next(i for i, c in enumerate(g) if c in "O0")
    swapped = g[:i] + ("0" if g[i] == "O" else "O") + g[i + 1:]
    assert swapped not in idx and resolve.repair_to_master(swapped, idx) == g
    assert resolve.repair_to_master(g[:3] + "X" + g[3:], idx) == g or resolve.repair_to_master(g[:3] + "X" + g[3:], idx) is None   # one extra character: deleted if that gives exactly one match
    assert resolve.repair_to_master("07AAAAA0000A1Z9", idx) is None


def test_the_vendor_is_looked_up_by_name_only_when_the_name_was_read_well_and_is_unique(world):
    sap, _, _ = world
    v = sap.get_vendor_by_id("V10444")
    b = BillFields(vendor_name=F(v.name, 0.97), vendor_gstin=F(None, 0.0))
    resolve.resolve_vendor(b, sap)
    assert b.vendor_gstin.value == v.gstin and b.vendor_gstin.source == "vendor_master" and "not read from the bill" in b.vendor_gstin.note and b.vendor_gstin.conf <= 0.9
    weak = BillFields(vendor_name=F(v.name, 0.80), vendor_gstin=F(None, 0.0))
    resolve.resolve_vendor(weak, sap)
    assert weak.vendor_gstin.value is None
    unknown = BillFields(vendor_name=F("No Such Traders Pvt Ltd", 0.97), vendor_gstin=F(None, 0.0))
    resolve.resolve_vendor(unknown, sap)
    assert unknown.vendor_gstin.value is None
    sure = BillFields(vendor_name=F(v.name, 0.97), vendor_gstin=F(v.gstin, 0.95))
    resolve.resolve_vendor(sure, sap)
    assert sure.vendor_gstin.source == "read"                                                  # a confident read is left alone, even if the master would differ


def test_header_reread_fills_gaps_agrees_or_defers():
    b = BillFields(invoice_no=F(None, 0.0), invoice_date=F("2025-11-01", 0.90), vendor_gstin=F("07FFWFT1642T1ZA", 0.80), vendor_name=F("X", 0.97))
    h = BillFields(invoice_no=F("751/25-26/346", 0.92), invoice_date=F("2025-11-01", 0.95), vendor_gstin=F("07FFWFT1642T1ZA", 0.90), vendor_name=F("Y", 0.50))
    merge_header(b, h)
    assert b.invoice_no.value == "751/25-26/346" and "second read of the header" in b.invoice_no.note          # a gap is filled
    assert b.invoice_date.conf > 0.90 and b.vendor_gstin.conf >= 0.90                                         # agreement raises confidence
    assert b.vendor_name.value == "X"                                                                          # a confident name is not replaced
    d = BillFields(invoice_no=F("111/25-26/111", 0.80))
    merge_header(d, BillFields(invoice_no=F("222/25-26/222", 0.82)))
    assert d.invoice_no.value == "111/25-26/111" and d.invoice_no.conf < 0.80                                  # a disagreement without a clear winner cuts confidence
    e = BillFields(invoice_no=F("111/25-26/111", 0.50))
    merge_header(e, BillFields(invoice_no=F("222/25-26/222", 0.92)))
    assert e.invoice_no.value == "222/25-26/222"


def test_the_working_copy_default_is_resolved_at_call_time(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "WORKING_DB", tmp_path / "later.sqlite")
    assert pipeline.make_working_copy() == tmp_path / "later.sqlite" and (tmp_path / "later.sqlite").exists()


def test_a_bill_whose_gstin_was_looked_up_never_clears_on_its_own(world):
    sap, bills, _ = world
    res = copy.deepcopy(cached("bill-17.pdf"))                                                 # a bill the checks clear
    ctx = Context(sap, bills, bill_counted_in_billed=True)
    assert intake.check_bill(res, ctx)["routing"].route == "auto-clear"
    res["fields"]["vendor_gstin"]["source"] = "vendor_master"
    out = intake.check_bill(res, ctx)
    assert out["routing"].route == "human-look" and any("vendor master" in r for r in out["routing"].reasons)
