"""Number audit (4.3): headline figures re-derived a second way from the cleaned register, no bill counted twice, one definition of 'late' everywhere.
The hand-labelled file is never opened here."""
import json
import re
import shutil
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

from app import intake
from app.reader import pipeline
from app.rules import Context
from app.sap.adapter import SapAdapter
from app.tracker import seed
from app.tracker.msme import LIMIT_DAYS, days_remaining
from app.ui.data import Numbers

ROOT = Path(__file__).resolve().parent.parent
N = Numbers()
BILLS = pd.read_parquet(ROOT / "analysis" / "out" / "bills_clean.parquet")


def paid_invoices() -> pd.DataFrame:
    p = BILLS[(BILLS.doc_type == "invoice") & (BILLS.status == "Paid") & BILLS.paid_date.notna() & BILLS.desk_received_date.notna()].copy()
    p["desk_to_paid"] = (p.paid_date - p.desk_received_date).dt.days
    return p


def test_the_register_has_no_bill_twice():
    assert BILLS.bill_id.is_unique and len(BILLS) == int(N("bill_register.rows_after_dedup"))
    assert len(BILLS.drop_duplicates(["vendor_id", "invoice_no", "invoice_date", "amount_inr"])) == len(BILLS)       # the same invoice is not in twice under two ids


def test_the_headline_days_figures_are_reproduced_from_the_cleaned_register_alone():
    p = paid_invoices()
    assert round(p.desk_to_paid.mean(), 3) == N("l.base.desk_mean")
    assert int((p.desk_to_paid > 45).sum()) == int(N("l.base.over45"))
    ms = p[p.msme_status.isin(["Micro", "Small"])]
    assert len(ms) == int(N("l.n_msme_known")) and int((ms.desk_to_paid > 45).sum()) == int(N("l.base.ms_late"))
    assert round(100 * N("l.base.ms_late") / N("l.n_msme_known"), 1) == round(N("l.base.ms_late_pct"), 1)


def test_the_after_figures_are_the_registered_before_minus_the_registered_saving():
    assert round(N("l.base.desk_mean") - N("l.lever.high.save"), 3) == N("d.after.desk_mean_low")
    assert round(N("l.base.desk_mean") - N("l.lever.low.save"), 3) == N("d.after.desk_mean_high")
    assert N("d.after.desk_mean_low") < N("d.after.desk_mean_high") < N("l.base.desk_mean")


def test_one_definition_of_late_in_the_tracker_and_in_the_analysis():
    """Late means more than 45 days from the desk date (46 or more), in the tracker as in every analysis script."""
    from app.tracker.ledger import Bill

    import inspect
    sig = inspect.signature(Bill)
    assert LIMIT_DAYS == 45
    src = (ROOT / "app" / "tracker" / "msme.py").read_text(encoding="utf-8")
    assert "LIMIT_DAYS - b.days_since_desk" in src and "remaining < 0" in src          # 45 days since the desk: 0 left, on time; 46: -1, late
    for f in ("analysis/06_msme_exposure.py", "analysis/09_levers.py", "backtest/replay.py", "analysis/08_problem_ranking.py"):
        assert not re.search(r">= ?45\b", (ROOT / f).read_text(encoding="utf-8")), f        # no script counts day 45 as late


def test_the_intake_counts_add_up_and_no_register_bill_is_claimed_by_two_inbox_bills(tmp_path):
    assert N("ir.all.files") == sum(N(f"ir.all.route.{r}") for r in ("auto-clear", "fix-before-sending", "fix-internal", "human-look", "resend")) == 40
    shutil.copyfile(ROOT / "pack" / "data" / "sap_extract.sqlite", tmp_path / "c.sqlite")
    with SapAdapter(tmp_path / "c.sqlite") as sap:
        bills = seed(ROOT / "pack" / "data" / "bill_register.csv", ROOT / "pack" / "data" / "queries.csv", sap)
        ctx = Context(sap, bills, bill_counted_in_billed=True)
        own = {}
        for p in sorted(pipeline.CACHE_DIR.glob("*.json")):
            res = json.loads(p.read_text(encoding="utf-8"))
            b = intake.find_own_bill(intake.bill_read(res), ctx)
            if b:
                own.setdefault(b, []).append(res["file"])
    assert len(list(pipeline.CACHE_DIR.glob("*.json"))) == 40
    assert all(len(v) == 1 for v in own.values()), {k: v for k, v in own.items() if len(v) > 1}
