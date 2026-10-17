"""Unit tests for app/rules: each check has a passing and a failing case built from real rows of the register and the SAP extract (the pack), and the four
inbox bills of notes/solution-design.md section 5 are the acceptance tests for the routing. Where the register cannot hold a value (the bill's printed GSTIN,
HSN code, tax type), the test says which value was supplied or altered and why. The pack is only ever read through a copy."""
import csv
import shutil
from datetime import date
from pathlib import Path

import pytest

from app.rules import CHECKS, Context, read, route, run_all
from app.rules import checks as C
from app.rules.checks import check_h3, check_h10, check_h11, check_h13, check_p1_h1, check_p3, state_code
from app.rules.model import FAIL, NEEDS_DOC, PASS, WARN
from app.rules.routing import AUTO, FIX_INTERNAL, FIX_VENDOR, HUMAN, RESEND, classify
from app.sap.adapter import SapAdapter
from app.tracker import seed

PACK = Path(__file__).resolve().parent.parent / "pack" / "data"
pytestmark = pytest.mark.skipif(not PACK.is_dir(), reason="pack not present")


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    d = tmp_path_factory.mktemp("rules")
    shutil.copy(PACK / "sap_extract.sqlite", d / "c.sqlite")
    sap = SapAdapter(d / "c.sqlite")
    bills = seed(PACK / "bill_register.csv", PACK / "queries.csv", sap)
    yield sap, bills, {r["bill_id"]: r for r in csv.DictReader(open(PACK / "bill_register.csv", encoding="utf-8"))}
    sap.close()


def ctx(world, counted=True):
    return Context(world[0], world[1], bill_counted_in_billed=counted)


def from_row(world, bill_id, hsn="9985", rate=18.0, **over):
    """A BillRead built from a real register row and its vendor in the master. Tax lines are split CGST/SGST at `rate`; the HSN is a supplied test value."""
    sap, _, reg = world
    r = reg[bill_id]
    v = sap.get_vendor_by_id(r["vendor_id"])
    taxable = float(r["amount_inr"])
    half = round(taxable * rate / 200, 2)
    vals = dict(source_file=f"{bill_id}.pdf", own_bill_id=bill_id, vendor_gstin=v.gstin, vendor_name=v.name, invoice_no=r["invoice_no"], invoice_date=date.fromisoformat(r["invoice_date"]),
                wo_id=r["wo_id"], taxable_inr=taxable, cgst_inr=half, sgst_inr=half, igst_inr=0.0, hsn_sac=hsn, place_of_supply=v.state, recipient_gstin="06AAAAA0000A1Z5")
    vals.update(over)
    return read(**vals)


CLEAN = "TRK251430"       # real bill, DG Set AMC, valid work order, unique invoice number
EXPIRED = "TRK251981"     # real R26 query: work order expired on the bill date
NO_BALANCE = "TRK253775"  # real R25/R24/R10 query on a work order billed past its approved value, valid on the bill date
GSTIN_Q = "TRK253185"     # real R08 query: GSTIN on the bill did not match the master
RATE_Q = "TRK257197"      # real R07 query: 'Tax rate on bill is 12%. Service is taxable at 18%.'
HSN_Q = "TRK256138"       # real R06 query: 'HSN/SAC code missing on bill.'
DIESEL = "TRK260987"      # real Diesel Supply bill, no GST
REUSED = "TRK257233"      # one of a real pair with TRK252149: same vendor, same invoice number, different date and amount


def status(results, cid):
    return next(r for r in results if r.check_id == cid)


# ------------------------------------------------------------------ P1 / H1
def test_p1_h1_pass(world):
    r = check_p1_h1(from_row(world, CLEAN), ctx(world))
    assert r.status == PASS and r.owner is None and r.evidence["name_matches"] is True and r.evidence["vendor_id"] == "V10444"


def test_p1_h1_fail_gstin_differs_from_record(world):
    good = from_row(world, GSTIN_Q)
    master = good.vendor_gstin.value
    wrong = master[:3] + ("A" if master[3] != "A" else "B") + master[4:]    # the printed GSTIN is not in the register: one PAN letter altered, still well formed
    r = check_p1_h1(from_row(world, GSTIN_Q, vendor_gstin=wrong), ctx(world))
    assert r.status == FAIL and r.owner == "vendor" and wrong in r.fix and "differs from our record" in r.fix
    assert r.evidence["master_gstin"] == master


def test_p1_h1_fail_malformed_and_missing(world):
    assert check_p1_h1(from_row(world, CLEAN, vendor_gstin="07SBDPT4452"), ctx(world)).evidence["format_ok"] is False
    assert check_p1_h1(from_row(world, CLEAN, vendor_gstin=None), ctx(world)).status == FAIL


def test_p1_h1_warn_unknown_vendor_and_name_mismatch(world):
    unknown = check_p1_h1(from_row(world, CLEAN, vendor_gstin="29ABCDE1234F1Z5", vendor_name="Nobody Traders"), ctx(world))
    assert unknown.status == WARN and unknown.owner == "AP"
    other_name = check_p1_h1(from_row(world, CLEAN, vendor_name="Completely Different Name Pvt Ltd"), ctx(world))
    assert other_name.status == WARN and other_name.evidence["name_matches"] is False


# ------------------------------------------------------------------ P3
def test_p3_pass(world):
    r = check_p3(from_row(world, CLEAN), ctx(world))
    assert r.status == PASS and r.evidence == {"wo_on_bill": "4100915", "in_sap": True, "wo_vendor_id": "V10444", "wo_property": r.evidence["wo_property"]}


def test_p3_fail_missing_and_unknown_number(world):
    miss = check_p3(from_row(world, CLEAN, wo_id=None), ctx(world))        # real row with the number removed: the register holds only numbers that exist
    assert miss.status == FAIL and miss.owner == "vendor" and "missing" in miss.fix
    unknown = check_p3(from_row(world, CLEAN, wo_id="4999999"), ctx(world))
    assert unknown.status == FAIL and unknown.evidence["in_sap"] is False and "4999999" in unknown.fix


# ------------------------------------------------------------------ H3
def test_h3_pass(world):
    r = check_h3(from_row(world, CLEAN), ctx(world))
    assert r.status == PASS and r.evidence["validity"] == "valid" and r.evidence["headroom_after_inr"] >= 0


def test_h3_fail_expired_work_order_real_query(world):
    r = check_h3(from_row(world, EXPIRED), ctx(world))
    assert r.status == FAIL and r.owner == "procurement" and r.evidence["validity"] == "expired" and r.evidence["expiry_may_be_stale"] is True
    assert "amendment" in r.fix and "ended on" in r.fix


def test_h3_fail_value_exhausted_real_query(world):
    r = check_h3(from_row(world, NO_BALANCE), ctx(world))
    assert r.status == FAIL and r.owner == "procurement" and r.evidence["headroom_after_inr"] < 0 and "over its approved value" in r.fix


def test_h3_live_intake_takes_the_bill_off_the_balance(world):
    wo = world[0].get_work_order("4100915")
    b = from_row(world, CLEAN, taxable_inr=wo.remaining + 1)
    assert check_h3(b, ctx(world, counted=True)).status == PASS     # historical row: already in billed
    live = check_h3(b, ctx(world, counted=False))                    # live intake: this bill is new
    assert live.status == FAIL and live.evidence["headroom_after_inr"] == -1


def test_h3_reports_both_problems_when_both_apply(world):
    r = check_h3(from_row(world, EXPIRED, taxable_inr=10_000_000_000.0), ctx(world, counted=False))
    assert r.status == FAIL and "ended on" in r.fix and "over its approved value" in r.fix


def test_h3_needs_document_when_work_order_unreadable(world):
    assert check_h3(from_row(world, CLEAN, wo_id=None), ctx(world)).status == NEEDS_DOC


# ------------------------------------------------------------------ H13
def test_h13_pass_unique_number(world):
    r = check_h13(from_row(world, CLEAN), ctx(world))
    assert r.status == PASS and r.evidence["matches"] == []


def test_h13_warn_real_reused_number_different_date_and_amount(world):
    r = check_h13(from_row(world, REUSED), ctx(world))
    assert r.status == WARN and r.owner == "AP" and [m["bill_id"] for m in r.evidence["matches"]] == ["TRK252149"]
    assert not r.evidence["matches"][0]["same_date"] and not r.evidence["matches"][0]["same_amount"]


def test_h13_fail_same_number_date_and_amount_even_when_written_differently(world):
    base = from_row(world, CLEAN, own_bill_id=None)             # a new copy of a real bill: its own row is the earlier booking
    exact = check_h13(base, ctx(world))
    assert exact.status == FAIL and exact.owner == "vendor" and exact.evidence["matches"][0]["bill_id"] == CLEAN
    for variant in ("444-25-26-844", "444 25 26 844", "444/25-26/844 "):
        r = check_h13(from_row(world, CLEAN, own_bill_id=None, invoice_no=variant), ctx(world))
        assert r.status == FAIL and r.evidence["matches"][0]["exact_text"] is False, variant


def test_h13_ignores_the_bills_own_row(world):
    assert check_h13(from_row(world, CLEAN, own_bill_id=CLEAN), ctx(world)).status == PASS


def test_h13_warn_when_vendor_cannot_be_identified(world):
    assert check_h13(from_row(world, CLEAN, vendor_gstin="29ABCDE1234F1Z5", vendor_name="Nobody"), ctx(world)).status == WARN


# ------------------------------------------------------------------ H11
def test_h11_pass_standard_rate_and_diesel_without_gst(world):
    assert check_h11(from_row(world, CLEAN), ctx(world)).status == PASS
    d = check_h11(from_row(world, DIESEL, rate=0.0, hsn="2710"), ctx(world))
    assert d.status == PASS and d.evidence["rate_expected_pct"] == 0.0 and d.evidence["category"] == "Diesel Supply"


def test_h11_fail_rate_12_where_18_applies_real_query(world):
    r = check_h11(from_row(world, RATE_Q, rate=12.0), ctx(world))       # the query text says the bill printed 12% where 18% applies
    assert r.status == FAIL and r.owner == "vendor" and r.evidence["rate_printed_pct"] == 12.0 and "12% but 18%" in r.fix


def test_h11_fail_hsn_missing_real_query(world):
    r = check_h11(from_row(world, HSN_Q, hsn=None), ctx(world))
    assert r.status == FAIL and "HSN or SAC code is missing" in r.fix
    assert check_h11(from_row(world, HSN_Q, hsn="99"), ctx(world)).status == FAIL


def test_h11_reports_missing_code_and_wrong_rate_together(world):
    r = check_h11(from_row(world, RATE_Q, rate=12.0, hsn=None), ctx(world))
    assert r.status == FAIL and "missing" in r.fix and "12%" in r.fix


def test_h11_needs_the_tax_lines(world):
    r = check_h11(from_row(world, CLEAN, cgst_inr=None, sgst_inr=None, igst_inr=None), ctx(world))
    assert r.status in (FAIL, NEEDS_DOC) and "tax lines" in r.fix


# ------------------------------------------------------------------ H10, the facts: the four inbox bills read by eye (design note section 5)
INBOX = {   # printed values; recipient GSTIN state 06 on all four; HSN is a placeholder, the by-eye reading did not record codes
    "bill-11": dict(own="TRK259268", gstin="09WMLCG8394Z1Z9", inv="085/25-26/730", wo="4101752", date=date(2025, 8, 2), taxable=61610.0, pos="Uttar Pradesh", tax="igst"),
    "packet-01": dict(own=None, gstin="06EPVCF6069Z1ZZ", inv="668/25-26/138", wo="4100395", date=date(2026, 3, 4), taxable=420980.0, pos="Haryana", tax="split"),
    "bill-16": dict(own="TRK253093", gstin="07QXNPN2966U1ZT", inv="751/25-26/346", wo="4100393", date=date(2025, 11, 1), taxable=86330.0, pos="Haryana", tax="igst"),
    "packet-08": dict(own="TRK257545", gstin="06QVLCO1204A1Z3", inv="550/25-26/340", wo="4100602", date=date(2025, 6, 4), taxable=190740.0, pos="Uttar Pradesh", tax="igst"),
}


def inbox(world, name, **over):
    s = INBOX[name]
    sap = world[0]
    v = sap.get_vendor(gstin=s["gstin"]).vendor
    t = s["taxable"]
    tax = dict(igst_inr=round(t * 0.18, 2), cgst_inr=0.0, sgst_inr=0.0) if s["tax"] == "igst" else dict(igst_inr=0.0, cgst_inr=round(t * 0.09, 2), sgst_inr=round(t * 0.09, 2))
    vals = dict(source_file=name, own_bill_id=s["own"], vendor_gstin=s["gstin"], vendor_name=v.name, invoice_no=s["inv"], invoice_date=s["date"], wo_id=s["wo"], taxable_inr=t,
                hsn_sac="998533", place_of_supply=s["pos"], recipient_gstin="06", **tax)
    vals.update(over)
    return read(**vals)


def test_h10_pass_when_both_readings_agree_with_the_tax(world):
    for name in ("packet-01", "bill-16"):       # intra-State with CGST+SGST; inter-State on both readings with IGST
        r = check_h10(inbox(world, name), ctx(world))
        assert r.status == PASS and r.certainty == 1.0, name
    assert check_h10(inbox(world, "bill-16"), ctx(world)).evidence["expected_by_recipient_location"] == "IGST"


def test_h10_warns_and_shows_three_facts_when_readings_disagree(world):
    for name in ("bill-11", "packet-08"):
        r = check_h10(inbox(world, name), ctx(world))
        assert r.status == WARN and r.certainty == 0.5 and r.owner == "AP", name
        assert {"supplier_state", "recipient_state", "place_of_supply", "tax_charged"} <= set(r.evidence)
    e = check_h10(inbox(world, "bill-11"), ctx(world)).evidence
    assert (e["supplier_state"], e["recipient_state"], e["place_of_supply"], e["tax_charged"]) == ("Uttar Pradesh", "Haryana", "Uttar Pradesh", "IGST")
    assert (e["expected_by_recipient_location"], e["expected_by_printed_place_of_supply"]) == ("IGST", "CGST+SGST")


def test_h10_never_fails_a_bill_and_needs_the_page_when_facts_missing(world):
    wrong = check_h10(inbox(world, "bill-16", igst_inr=0.0, cgst_inr=7769.7, sgst_inr=7769.7), ctx(world))
    assert wrong.status == WARN                                             # both readings say IGST, bill charged CGST+SGST: a person decides
    assert check_h10(inbox(world, "bill-16", place_of_supply=None), ctx(world)).status == NEEDS_DOC
    assert check_h10(from_row(world, DIESEL, rate=0.0), ctx(world)).status == PASS


def test_state_code_reads_codes_names_and_gstins():
    assert state_code("09") == "09" and state_code("Uttar Pradesh") == "09" and state_code("New Delhi") == "07" and state_code("09WMLCG8394Z1Z9") == "09"
    assert state_code("Nowhere") is None and state_code(None) is None


# ------------------------------------------------------------------ run_all and the routing
def test_run_all_runs_every_check_and_never_stops_at_the_first_failure(world):
    bad = from_row(world, EXPIRED, vendor_gstin="07SBDPT4452", hsn=None, wo_id="4100128", own_bill_id=None, invoice_no="276/25-26/722", rate=12.0)
    results = run_all(bad, ctx(world, counted=False))
    assert [r.check_id for r in results] == ["P1/H1", "P3", "H3", "H13", "H11", "H10"] and len(CHECKS) == 6
    failed = [r.check_id for r in results if r.status == FAIL]
    assert {"P1/H1", "H3", "H11"} <= set(failed) and len(failed) >= 3
    routing = route(results)
    assert routing.route == FIX_VENDOR
    vendor_msgs = [a for a in routing.actions if a.kind == "tell-vendor"]
    assert len(vendor_msgs) == 1 and {"P1/H1", "H11"} <= set(vendor_msgs[0].checks)       # one message with every vendor fix, not one per failure
    assert any(a.kind == "task" and a.to == "procurement" and a.checks == ("H3",) for a in routing.actions)


def test_a_check_that_raises_becomes_a_warning_and_the_rest_still_run(world, monkeypatch):
    def boom(bill, c):
        raise RuntimeError("lookup failed")
    boom.__doc__ = "Work order valid"
    monkeypatch.setattr(C, "CHECKS", [check_p1_h1, boom, check_h13])
    res = run_all(from_row(world, CLEAN), ctx(world))
    assert [r.status for r in res] == [PASS, WARN, PASS] and "RuntimeError" in res[1].evidence["error"]


def test_routing_precedence_resend_beats_everything(world):
    b = from_row(world, EXPIRED, invoice_no=("276/25-26/722", 0.5))
    rt = route(run_all(b, ctx(world)))
    assert rt.route == RESEND and rt.actions[0].kind == "resend"


def test_classify_thresholds(world):
    ok = check_p1_h1(from_row(world, CLEAN), ctx(world))
    assert classify(ok) == AUTO
    assert classify(check_p1_h1(from_row(world, CLEAN, vendor_gstin=(from_row(world, CLEAN).vendor_gstin.value, 0.80)), ctx(world))) == HUMAN     # a doubtful read
    assert classify(check_p1_h1(from_row(world, CLEAN, vendor_gstin=(from_row(world, CLEAN).vendor_gstin.value, 0.60)), ctx(world))) == RESEND
    assert classify(check_h3(from_row(world, EXPIRED), ctx(world))) == FIX_INTERNAL
    assert classify(check_h11(from_row(world, HSN_Q, hsn=None), ctx(world))) == FIX_VENDOR


@pytest.mark.parametrize("name, expected, checks_that_matter", [
    ("bill-11", HUMAN, {"H10": WARN}),                                  # tax type against place of supply
    ("packet-01", HUMAN, {"H13": WARN, "H10": PASS}),                    # same number, different date and amount
    ("bill-16", AUTO, {"H10": PASS, "H13": PASS, "H3": PASS}),           # clean when the reader is confident
    ("packet-08", HUMAN, {"H10": WARN, "H13": WARN, "H3": FAIL}),        # place of supply, reused number, work order past its approved value
])
def test_acceptance_routes_of_the_four_inbox_bills(world, name, expected, checks_that_matter):
    res = run_all(inbox(world, name), ctx(world, counted=True))
    got = {r.check_id: r.status for r in res}
    for cid, st in checks_that_matter.items():
        assert got[cid] == st, (name, cid, got)
    assert got["P1/H1"] == PASS and got["P3"] == PASS
    assert route(res).route == expected, (name, route(res).reasons)


def test_auto_clear_needs_every_confidence_at_or_above_090(world):
    clean = inbox(world, "bill-16")
    assert route(run_all(clean, ctx(world))).route == AUTO
    doubtful = inbox(world, "bill-16", wo_id=("4100393", 0.85))
    assert route(run_all(doubtful, ctx(world))).route == HUMAN
