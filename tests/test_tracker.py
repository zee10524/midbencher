"""Tests for app/tracker on a small fixture (hand-made register, queries and SAP database), and on the real pack seeded as of 30 April 2026."""
import csv
import shutil
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest

from app.sap.adapter import SapAdapter
from app.tracker import ageing, countdown, next_run_list, oldest, pick_order, runway, seed, vendor_sentence
from app.tracker.payruns import first_run_after_posting, label, next_run_for_open_bill, runs_between, runs_missed
from app.tracker.pickorder import current_load
from app.tracker.status import classify, is_classified
from tests.test_sap_adapter import SCHEMA

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "pack" / "data"
AS_OF = date(2026, 4, 30)  # a Thursday
COLS = ["bill_id", "vendor_id", "property_code", "category", "doc_type", "invoice_no", "invoice_date", "desk_received_date", "property_verified_date",
        "property_head_signed_date", "ho_received_date", "ho_picked_date", "ho_verifier", "posted_date", "paid_date", "amount_inr", "gst_inr", "wo_id", "status"]


def ago(n):
    return (AS_OF - timedelta(days=n)).isoformat()


def row(bill_id, vendor="V1", desk=10, ver=None, sign=None, rec=None, pick=None, verifier="", posted=None, paid=None, amount="1000", doc="invoice", wo="W1", prop="NOI-C32"):
    d = lambda n: "" if n is None else ago(n)
    return dict(bill_id=bill_id, vendor_id=vendor, property_code=prop, category="Lift AMC", doc_type=doc, invoice_no=f"INV-{bill_id}", invoice_date=ago(desk + 3),
                desk_received_date=d(desk), property_verified_date=d(ver), property_head_signed_date=d(sign), ho_received_date=d(rec), ho_picked_date=d(pick),
                ho_verifier=verifier, posted_date=d(posted), paid_date=d(paid), amount_inr=amount, gst_inr="0", wo_id=wo, status="")


def write_csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


@pytest.fixture
def world(tmp_path):
    db = tmp_path / "sap.sqlite"
    c = sqlite3.connect(db)
    c.executescript(SCHEMA)
    c.executemany("INSERT INTO vendor_master VALUES (?,?,?,?,?,?)", [
        ("V1", "Small Vendor", "Lift AMC", "Delhi", "07SBDPT4452Q1ZF", "Small"), ("V2", "Big Vendor", "Lift AMC", "Delhi", "07BTTFV3567V1Z1", "Not MSME"),
        ("V3", "Blank Vendor", "Lift AMC", "Delhi", "06EPVCF6069Z1ZZ", ""), ("V4", "Tiny Vendor", "Lift AMC", "Delhi", "09WMLCG8394Z1Z9", "Micro")])
    c.executemany("INSERT INTO work_orders VALUES (?,?,?,?,?,?,?,?,?,?)", [
        ("W1", "V1", "NOI-C32", "Lift AMC", "2025-10-01", "2026-12-31", "1", "CC", "1000000", "100000"),     # lots of room
        ("W2", "V1", "NOI-C32", "Lift AMC", "2025-10-01", "2026-06-05", "1", "CC", "1000000", "100000"),     # expires within 45 days
        ("W3", "V1", "NOI-C32", "Lift AMC", "2025-10-01", "2026-12-31", "1", "CC", "1000000", "990000"),     # balance runs out within 45 days
        ("W4", "V1", "NOI-C32", "Lift AMC", "2025-10-01", "2026-12-31", "1", "CC", "1000", "5000"),          # over-billed
        ("W5", "V1", "NOI-C32", "Lift AMC", "2024-01-01", "2025-12-31", "1", "CC", "1000000", "1000"),       # expired
        ("W6", "V1", "NOI-C32", "Lift AMC", "2025-10-01", "2026-12-31", "1", "CC", "1000000", "100000")])
    c.execute("INSERT INTO properties VALUES ('NOI-C32','Tower','Office Tower','Noida','UP','100')")
    c.commit()
    c.close()
    reg = [
        row("PAID1", desk=40, ver=36, sign=35, rec=30, pick=25, verifier="AP-2", posted=20, paid=14),
        row("PAIDBAD", desk=40, ver=36, sign=35, rec=30, pick=25, verifier="AP-2", posted=10, paid=14),   # D03: paid before posted
        row("DESK1", desk=2), row("VER1", desk=5, ver=3), row("SIGN1", desk=8, ver=6, sign=5),
        row("WAIT_MSME_OLD", vendor="V1", desk=40, ver=38, sign=37, rec=20),
        row("WAIT_MSME_NEW", vendor="V4", desk=10, ver=9, sign=8, rec=5),
        row("WAIT_BLANK", vendor="V3", desk=30, ver=29, sign=28, rec=12),
        row("WAIT_OTHER_OLDEST", vendor="V2", desk=90, ver=88, sign=87, rec=60),
        row("WAIT_CREDIT", vendor="V1", desk=50, ver=48, sign=47, rec=15, doc="credit_note", amount="-500"),
        row("PICKED_A", desk=20, ver=19, sign=18, rec=15, pick=12, verifier="AP-1"), row("PICKED_B", desk=20, ver=19, sign=18, rec=15, pick=12, verifier="AP-1"),
        row("PICKED_C", desk=20, ver=19, sign=18, rec=15, pick=12, verifier="AP-2"),
        row("QUERY1", vendor="V1", desk=44, ver=42, sign=41, rec=35, pick=30, verifier="AP-3"),
        row("POSTED_TODAY", vendor="V1", desk=20, ver=18, sign=17, rec=12, pick=8, verifier="AP-4", posted=0),
        row("POSTED_OLD", vendor="V4", desk=42, ver=40, sign=39, rec=34, pick=30, verifier="AP-4", posted=9),
        row("POSTED_OTHER", vendor="V2", desk=30, ver=28, sign=27, rec=22, pick=20, verifier="AP-4", posted=9),
        row("WO2", desk=5, ver=3, wo="W2"), row("WO3", desk=5, ver=3, wo="W3"), row("WO4", desk=5, ver=3, wo="W4"), row("WO5", desk=5, ver=3, wo="W5"),
        row("WO6_OLD", desk=200, ver=198, sign=197, rec=190, pick=189, verifier="AP-5", posted=185, paid=180, wo="W6"),   # not live: ignored by runway
    ]
    reg.append(dict(reg[0]))  # D01: an exact duplicate row
    write_csv(tmp_path / "reg.csv", reg, COLS)
    qs = [dict(query_id="Q1", bill_id="QUERY1", raised_date=ago(2), resolved_date="", raised_by="AP-3", query_category="GST", query_text="HSN/SAC code missing"),
          dict(query_id="Q2", bill_id="PAID1", raised_date=ago(24), resolved_date=ago(22), raised_by="AP-2", query_category="Other", query_text="PO not released yet"),
          dict(query_id="Q3", bill_id="DESK1", raised_date=ago(-3), resolved_date="", raised_by="AP-1", query_category="GST", query_text="HSN/SAC code missing")]  # after as-of
    write_csv(tmp_path / "q.csv", qs, ["query_id", "bill_id", "raised_date", "resolved_date", "raised_by", "query_category", "query_text"])
    with SapAdapter(db) as sap:
        yield seed(tmp_path / "reg.csv", tmp_path / "q.csv", sap, AS_OF), sap


def by(bills, i):
    return next(b for b in bills if b.bill_id == i)


# ---------------------------------------------------------------- ledger
def test_seed_drops_exact_duplicates_and_future_queries(world):
    bills, _ = world
    assert sum(1 for b in bills if b.bill_id == "PAID1") == 1
    assert by(bills, "DESK1").open_query is None and by(bills, "DESK1").queries == ()


@pytest.mark.parametrize("bill, stage, status, owner", [
    ("DESK1", "desk", "At property", "property"), ("VER1", "verified", "At property", "property"), ("SIGN1", "signed", "In transit", "courier"),
    ("WAIT_MSME_OLD", "received", "With AP", "AP"), ("PICKED_A", "picked", "With AP", "AP"), ("QUERY1", "picked", "Query", "vendor"),
    ("POSTED_TODAY", "posted", "Posted", "treasury"), ("PAID1", "paid", "Paid", None)])
def test_stage_status_and_owner(world, bill, stage, status, owner):
    b = by(world[0], bill)
    assert (b.stage, b.status, b.owner) == (stage, status, owner)


def test_entered_dates_and_days_in_stage(world):
    b = by(world[0], "PICKED_A")
    assert b.entered["desk"] == AS_OF - timedelta(days=20) and b.entered["picked"] == AS_OF - timedelta(days=12) and b.entered["posted"] is None
    assert b.days_in_stage == 12 and b.days_since_desk == 20
    assert by(world[0], "PAID1").days_in_stage is None


def test_open_query_overlay_owner_and_days(world):
    b = by(world[0], "QUERY1")
    assert b.days_in_query == 2 and b.open_query.owner == "vendor" and b.stage == "picked"
    assert by(world[0], "PAID1").queries[0].is_open is False and by(world[0], "PAID1").status == "Paid"


def test_paid_before_posted_is_flagged_d03(world):
    assert "paid_before_posted" in by(world[0], "PAIDBAD").flags and "paid_before_posted" not in by(world[0], "PAID1").flags


def test_oldest_uses_open_invoices_only_oldest_first(world):
    top = oldest(world[0], 3)
    assert [b.bill_id for b in top] == ["WAIT_OTHER_OLDEST", "QUERY1", "POSTED_OLD"]
    assert all(b.is_invoice and b.is_open for b in oldest(world[0], 50)) and len(oldest(world[0], 2)) == 2
    assert "WAIT_CREDIT" not in [b.bill_id for b in oldest(world[0], 50)]


def test_ageing_buckets_add_up(world):
    rows = ageing(world[0])
    opens = [b for b in world[0] if b.is_open and b.is_invoice]
    assert sum(r["bills"] for r in rows) == len(opens)
    assert [r["bucket"] for r in rows][0] == "0 to 15 days" and rows[-1]["bucket"] == "Over 60 days"
    assert rows[-1]["bills"] == 1 and rows[-1]["value_inr"] == 1000   # only the 90-day bill is over 60


# ---------------------------------------------------------------- payment runs
def test_run_calendar():
    assert label(date(2026, 5, 5)) == "Tuesday 5 May 2026"
    assert first_run_after_posting(date(2026, 4, 30), 0) == date(2026, 5, 1)   # Thursday -> Friday
    assert first_run_after_posting(date(2026, 4, 30), 1) == date(2026, 5, 5)   # list closes a day earlier -> Tuesday
    assert first_run_after_posting(date(2026, 5, 1), 0) == date(2026, 5, 5)    # posted on a run day, not the same run
    assert runs_between(date(2026, 5, 1), date(2026, 5, 12)) == [date(2026, 5, 1), date(2026, 5, 5), date(2026, 5, 8), date(2026, 5, 12)]
    assert next_run_for_open_bill(date(2026, 4, 1), AS_OF, 1) == date(2026, 5, 1)  # old posting: first run ahead of the as-of date
    assert runs_missed(date(2026, 4, 21), AS_OF, 0) == len(runs_between(date(2026, 4, 22), AS_OF))


def test_next_run_list_groups_by_run_and_puts_msme_first(world):
    runs = next_run_list(world[0], cutoff_days=1)
    assert [r["run_date"] for r in runs] == [date(2026, 5, 1), date(2026, 5, 5)]
    fri, tue = runs
    assert [x["bill_id"] for x in fri["bills"]] == ["POSTED_OLD", "POSTED_OTHER"]    # missed runs: next one ahead
    assert [x["bill_id"] for x in tue["bills"]] == ["POSTED_TODAY"]                  # posted today, cut-off 1
    assert fri["count"] == 2 and fri["value_inr"] == 2000
    zero = next_run_list(world[0], cutoff_days=0)
    assert [x["bill_id"] for x in zero[0]["bills"]] == ["POSTED_OLD", "POSTED_TODAY", "POSTED_OTHER"]   # cut-off 0: all on Friday, MSME first


def test_next_run_list_msme_fields(world):
    old = next_run_list(world[0], 1)[0]["bills"][0]
    assert old["msme_days_remaining"] == 45 - 42 and old["runs_missed"] >= 1 and old["last_run_before_limit"] is True   # Fri 1 May is its last run before 3 May
    plain = next_run_list(world[0], 1)[0]["bills"][1]
    assert plain["msme_days_remaining"] is None and plain["last_run_before_limit"] is False


# ---------------------------------------------------------------- MSME countdown
def test_countdown_clock_and_groups(world):
    rows = {r["bill_id"]: r for r in countdown(world[0])}
    assert "POSTED_OTHER" not in rows and "WAIT_CREDIT" not in rows and "WAIT_OTHER_OLDEST" not in rows   # not covered / credit note
    assert rows["QUERY1"]["days_remaining"] == 1 and rows["QUERY1"]["due_date"] == AS_OF - timedelta(days=44) + timedelta(days=45)
    assert rows["WAIT_BLANK"]["group"].startswith("Unknown") and rows["WAIT_BLANK"]["days_remaining"] == 15
    assert rows["WAIT_MSME_NEW"]["days_remaining"] == 35 and rows["WAIT_MSME_NEW"]["state"] == "on track"
    assert "15 days" in rows["QUERY1"]["note"]


def test_countdown_states_and_order(world):
    rows = countdown(world[0])
    assert [r["days_remaining"] for r in rows] == sorted(r["days_remaining"] for r in rows)
    q = next(r for r in rows if r["bill_id"] == "QUERY1")
    assert q["state"] == "will be late: no run left" and q["runs_left"] == 0   # cut-off 1: not posted, first run Tue 5 May, due Fri 1 May
    q0 = next(r for r in countdown(world[0], 0) if r["bill_id"] == "QUERY1")
    assert q0["state"] == "due soon" and q0["runs_left"] == 1                  # cut-off 0: Fri 1 May is still reachable
    late = next(r for r in rows if r["bill_id"] == "POSTED_OLD")
    assert late["days_remaining"] == 3 and late["runs_left"] >= 1


def test_countdown_runs_left_depends_on_cutoff(world):
    q0 = next(r for r in countdown(world[0], 0) if r["bill_id"] == "POSTED_TODAY")
    q2 = next(r for r in countdown(world[0], 2) if r["bill_id"] == "POSTED_TODAY")
    assert q0["runs_left"] >= q2["runs_left"] and q0["last_run"] is not None


# ---------------------------------------------------------------- pick order
def test_pick_order_msme_first_and_balanced(world):
    bills = world[0]
    assert current_load(bills) == {"AP-1": 2, "AP-2": 1, "AP-3": 0, "AP-4": 0, "AP-5": 0}     # QUERY1 is blocked and not counted
    po = pick_order(bills)
    assert [p["bill_id"] for p in po] == ["WAIT_CREDIT", "WAIT_MSME_OLD", "WAIT_MSME_NEW", "WAIT_BLANK", "WAIT_OTHER_OLDEST"]   # MSME by age, then unknown, then the rest
    assert [p["rank"] for p in po] == list(range(1, len(po) + 1))
    loads = dict(current_load(bills))
    for p in po:
        loads[p["verifier"]] += 1
    assert max(loads.values()) - min(loads.values()) <= 1 or loads["AP-1"] == 2


def test_pick_order_gives_nothing_to_the_busiest(world):
    po = pick_order(world[0])
    assert [p["verifier"] for p in po][:3] == ["AP-3", "AP-4", "AP-5"]          # lightest first, ties by id
    assert "AP-1" not in [p["verifier"] for p in po]


def test_pick_order_known_msme_before_unknown_before_rest(world):
    order = [p["msme_status"] for p in pick_order(world[0])]
    rank = {"Micro": 0, "Small": 0, "Unknown": 1}
    keys = [rank.get(s, 2) for s in order]
    assert keys == sorted(keys)


# ---------------------------------------------------------------- runway
def test_runway_flags_ahead_and_already(world):
    bills, sap = world
    rows = {r["wo_id"]: r for r in runway(bills, sap)}
    assert "W1" not in rows and "W6" not in rows                           # plenty of room, and not live
    assert rows["W2"]["kind"] == "ahead" and rows["W2"]["flags"] == ["expires within 45 days"] and rows["W2"]["days_to_expiry"] == (date(2026, 6, 5) - AS_OF).days
    assert rows["W3"]["kind"] == "ahead" and "balance runs out within 45 days" in rows["W3"]["flags"]
    assert rows["W4"]["kind"] == "already" and "over-billed" in rows["W4"]["flags"]
    assert rows["W5"]["kind"] == "already" and "expired, may be stale" in rows["W5"]["flags"]
    kinds = [r["kind"] for r in runway(bills, sap)]
    assert kinds == sorted(kinds)                                         # warnings first


def test_runway_balance_over_burn(world):
    bills, sap = world
    r = next(x for x in runway(bills, sap) if x["wo_id"] == "W3")
    assert r["balance_inr"] == 10000 and r["runway_days"] == pytest.approx(10000 / r["monthly_burn_inr"] * 30.4375)


# ---------------------------------------------------------------- vendor sentence
def test_sentences_in_plain_words(world):
    b = world[0]
    s = {i: vendor_sentence(by(b, i)) for i in ["DESK1", "VER1", "SIGN1", "WAIT_MSME_OLD", "PICKED_A", "QUERY1", "POSTED_TODAY", "PAID1", "PAIDBAD", "WAIT_CREDIT"]}
    assert s["DESK1"].startswith("We received bill INV-DESK1 on ") and "property is checking" in s["DESK1"]
    assert "checked at the property" in s["VER1"] and "signature" in s["VER1"]
    assert "on its way to our head office" in s["SIGN1"]
    assert "reached our head office" in s["WAIT_MSME_OLD"] and "pick it up" in s["WAIT_MSME_OLD"]
    assert "accounts team picked up bill INV-PICKED_A" in s["PICKED_A"]
    assert "on hold" in s["QUERY1"] and "HSN or SAC code is missing" in s["QUERY1"] and s["QUERY1"].endswith("You must send a corrected bill with the code.")
    assert "payment run on Tuesday 5 May 2026" in s["POSTED_TODAY"]
    assert s["PAID1"] == f"Your bill INV-PAID1 was paid on {label(AS_OF - timedelta(days=14))}."
    assert "date is being confirmed" in s["PAIDBAD"]
    assert s["WAIT_CREDIT"].startswith("Your credit note INV-WAIT_CREDIT")
    for text in s.values():
        assert "AP-" not in text and "TRK" not in text


def test_posted_credit_note_promises_no_payment_run(world):
    import dataclasses
    b = dataclasses.replace(by(world[0], "POSTED_TODAY"), doc_type="credit_note")
    assert vendor_sentence(b) == "Your credit note INV-POSTED_TODAY has been booked in our system."


def test_sentence_follows_the_cutoff_setting(world):
    b = by(world[0], "POSTED_TODAY")
    assert "Friday 1 May 2026" in vendor_sentence(b, 0) and "Tuesday 5 May 2026" in vendor_sentence(b, 1)


# ---------------------------------------------------------------- query classification
def test_classify_known_and_unknown_text():
    assert classify("PO not released yet")[0] == "procurement"
    assert classify("Wrong company name on bill, should be the property entity")[0] == "vendor"
    assert classify("Service entry still parked. Please post so we can book.")[0] == "property"
    assert not is_classified("something new") and classify("something new")[0] == "AP"


# ---------------------------------------------------------------- the real pack as of 30 April 2026
real = pytest.mark.skipif(not PACK.is_dir(), reason="pack not present")


@pytest.fixture(scope="module")
def pack_world(tmp_path_factory):
    d = tmp_path_factory.mktemp("sap")
    shutil.copy(PACK / "sap_extract.sqlite", d / "c.sqlite")
    sap = SapAdapter(d / "c.sqlite")
    yield seed(PACK / "bill_register.csv", PACK / "queries.csv", sap), sap
    sap.close()


@real
def test_pack_seed_matches_register_status(pack_world):
    bills, _ = pack_world
    reg = {r["bill_id"]: r["status"] for r in csv.DictReader(open(PACK / "bill_register.csv", encoding="utf-8"))}
    names = {"Paid": "Paid", "Posted": "Posted", "Query": "Query", "With AP": "With AP", "In Transit": "In transit"}
    assert len(bills) == len({b.bill_id for b in bills}) == len(reg)
    assert all(names[reg[b.bill_id]] == b.status for b in bills)
    assert all(b.owner in {"vendor", "property", "courier", "AP", "procurement", "treasury"} for b in bills if b.is_open)


@real
def test_pack_every_query_is_classified_and_every_open_query_has_an_owner(pack_world):
    bills, _ = pack_world
    qs = [q for b in bills for q in b.queries]
    assert qs and all(is_classified(q.text) for q in qs)
    assert all(b.open_query is not None for b in bills if b.status == "Query")


@real
def test_pack_msme_countdown_agrees_with_the_analysis(pack_world):
    bills, _ = pack_world
    ana = {r["bill_id"]: int(r["days_left_desk"]) for r in csv.DictReader(open(ROOT / "analysis" / "out" / "msme_open_bills.csv", encoding="utf-8"))
           if r["msme_status"] in ("Micro", "Small")}
    mine = {r["bill_id"]: r["days_remaining"] for r in countdown(bills) if r["msme_status"] in ("Micro", "Small")}
    assert ana and set(ana) == set(mine)
    assert all(ana[k] == mine[k] for k in ana)


@real
def test_pack_lists_run(pack_world):
    bills, sap = pack_world
    assert len(oldest(bills)) == 20
    assert sum(r["bills"] for r in ageing(bills)) == len([b for b in bills if b.is_open and b.is_invoice])
    runs = next_run_list(bills)
    assert all(r["run_date"].weekday() in (1, 4) and r["run_date"] > AS_OF for r in runs)
    po = pick_order(bills)
    assert len({p["bill_id"] for p in po}) == len(po) == len([b for b in bills if b.stage == "received"])
    assert runway(bills, sap)


# ---------------------------------------------------------------- control tower and balance under two definitions
def test_control_tower_columns_and_definitions(world):
    from app.tracker import balance_check, control_tower
    bills = world[0]
    rows = {r["verifier"]: r for r in control_tower(bills)}
    assert rows["AP-3"]["open_queries"] == 1 and rows["AP-3"]["in_hand"] == 0         # QUERY1 is blocked: not in hand, but follow-up work
    assert rows["AP-1"]["in_hand"] == 2 and rows["AP-1"]["open_queries"] == 0
    for r in rows.values():
        assert r["in_hand_after"] == r["in_hand"] + r["new_from_pick_order"]
    assert sum(r["new_from_pick_order"] for r in rows.values()) == len(pick_order(bills))
    assert {v: r["in_hand"] + r["open_queries"] for v, r in rows.items()} == current_load(bills, include_queried=True)


def test_balance_check_reports_both_definitions_without_changing_the_count(world):
    from app.tracker import balance_check
    res = balance_check(world[0])
    assert res["def1"]["before"] == current_load(world[0]) and res["def2"]["before"] == current_load(world[0], include_queried=True)
    assert res["def1"]["after"]["AP-3"] == 2 and res["def2"]["after"]["AP-3"] == 3     # def. 2 carries the blocked QUERY1 as well
    assert set(res["def1"]) == {"before", "after", "spread", "within_tolerance"}


@real
def test_pack_balance_holds_only_under_definition_1(pack_world):
    from app.tracker import balance_check
    res = balance_check(pack_world[0])
    assert res["def1"]["within_tolerance"] and not res["def2"]["within_tolerance"]
