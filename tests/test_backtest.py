"""backtest/replay.py reproduces the registered figures exactly and writes impact.csv. Needs `mingw32-make analyse` to have run."""
from pathlib import Path

import pandas as pd
import pytest

from backtest.replay import LABEL_CEILING, LABEL_NO_FLAG, LIMITS, NOT_RUN, impact_rows, pick_order_note, run, screen_data

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
pytestmark = pytest.mark.skipif(not (OUT / "figures_levers.csv").is_file(), reason="analysis not run")


@pytest.fixture(scope="module")
def res():
    return run()


def test_every_figure_matches_the_registered_value(res):
    reg = pd.read_csv(OUT / "figures_levers.csv").set_index("id").value
    assert len(res.figs) > 100
    for k, (v, _) in res.figs.items():
        assert reg[k] == pytest.approx(float(v)), k


def test_section_8_headline_numbers(res):
    code = {r["code"]: r for r in res.levers}
    assert [round(code[k]["save"], 2) for k in ("low", "mid", "high")] == [3.94, 4.75, 6.34]
    assert [code[k]["ms_late"] for k in ("low", "mid", "high")] == [303, 288, 200]
    assert res.base["ms_late"] == 530 and res.base["over"] == 1153


def test_impact_rows_have_ranges_for_every_lever(res):
    rows = pd.DataFrame(impact_rows(res))
    assert set(rows.group) >= {"pay", "queue", "intake", "combined", "ap_work", "vendor_calls"}
    d = rows[rows.metric == "days_off_mean"].set_index("group")
    assert d.loc["pay", "low"] < d.loc["pay", "middle"] < d.loc["pay", "high"]
    assert d.loc["combined", "high"] > d.loc["combined", "low"]


def test_confusion_table_adds_up(res):
    bills = res.figs["l.bt.bills"][0]
    for c in res.confusion:
        assert c["flagged_and_queried"] + c["flagged_not_queried"] + c["queried_not_flagged"] + c["neither"] == bills


def test_pick_order_note_states_replay_and_live_queue(res):
    assert res.live_waiting == 27
    note = pick_order_note(res)
    assert "replay on historical bills" in note and "27 waiting bills" in note
    sd = screen_data(res)
    assert sd["limits"] == LIMITS and sd["not_run"] == NOT_RUN and "counterfactual" in sd["label"]


def test_relabelled_figures_use_the_new_wording(res):
    rows = pd.DataFrame(impact_rows(res))
    assert LABEL_NO_FLAG in set(rows.metric) and "ceiling if every call were a status call that the tool removes; not an estimate" in " ".join(rows.metric)
    assert not rows.metric.str.contains("exceptions-only|avoided", case=False).any()
    labels = screen_data(res)["labels"]
    assert labels["no_flag"] == "share of bills with no flag from the three rules we can test; AP still runs all other checks on these bills"
    assert labels["calls_ceiling"] == "ceiling if every call were a status call that the tool removes; not an estimate"
