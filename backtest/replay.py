"""Replay last year's register through three levers and report what each, and all together, would have done to days to pay.

Levers, each alone and combined (shifting each bill's own dates, so nothing is counted twice):
1. Pay on the first Tuesday or Friday run after posting, with the run list closing 0, 1 or 2 days before the run.
2. A balanced AP pick order: each AP-1 bill gets the pick-up wait of the other four verifiers at the same rank in the queue.
3. The intake rules the register and the SAP extract can test, as if checked on `desk_received_date`: duplicate invoice number (H13), work order expired
   on the invoice date (H3) and work order value exhausted (H3, as value headroom). A caught query costs a residual delay of 3 days (low), 1 day (middle)
   or, optimistically, every layer A and B query goes with a 1-day residual.

Low, middle and high are always cut-off 2 / 1 / 0, residual 3 / 1 / optimistic. This is the analysis that `analysis/09_levers.py` used to hold; that script
now calls `run()` here and registers the same figure ids, so the numbers in `notes/numbers.md` and in section 8 of `notes/solution-design.md` are these.

`run()` also gives the confusion table per rule (bill level), the share of bills with no flag, and the vendor-calls ceiling. `write_impact()` writes
`backtest/out/impact.csv` and `confusion.csv`, and `screen_data()` gives the impact screen what it shows.

What it cannot prove is in `LIMITS` below and is repeated in `notes/solution-design.md` part f.

Run on its own:   python -m backtest.replay      (needs `mingw32-make analyse` to have run, for bills_clean.parquet and the query forensics)
Real connection: none. The replay reads the register and the SAP extract (through files); in a pilot the same measures come from the event log.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
IMPACT_DIR = ROOT / "backtest" / "out"
LABEL_NO_FLAG = "share of bills with no flag from the three rules we can test; AP still runs all other checks on these bills"
LABEL_CEILING = "ceiling if every call were a status call that the tool removes; not an estimate"
CALLS_PER_BILL = 3  # vendor status calls per bill: the vendor survey figure, used as an assumption (see LIMITS)

RULES = [("dup", "Duplicate invoice number for the vendor (H13)", ["R01"]), ("exp", "Work order expired on the invoice date (H3)", ["R26"]),
         ("bal", "Work order value exhausted (H3, as value headroom)", ["R25", "R24", "R10"])]
# low, middle, high for each lever: the lever codes in `levers`
SETTINGS = {"pay": ("pay2", "pay1", "pay0"), "queue": ("queue", "queue", "queue"), "intake": ("in3", "in1", "inopt"), "combined": ("low", "mid", "high")}
LABELS = {"pay": "Pay on the first run after posting (cut-off 2 / 1 / 0 days)", "queue": "Balanced AP pick order",
          "intake": "Three intake rules (residual 3 days / 1 day / optimistic)", "combined": "All three together"}
NOT_RUN = [
    ("GST type from place of supply", "The register holds only the GST amount, not its type or the place of supply printed on the bill, and the place-of-supply reading is unsettled (notes/research.md). Needs the bill itself."),
    ("GSTIN match", "The register carries no GSTIN as printed on the bill: the vendor is already the master's vendor, so a match would be true by construction. Needs the bill itself."),
    ("MSME", "MSME status is context for the countdown, not a cause of a query, so there is nothing to catch. It enters through the MSME bills-over-45-days measure."),
]
LIMITS = [
    "Counterfactual. The days saved assume a caught problem is fixed at the source in 1 or 3 days. Nothing in the register shows how fast a vendor would fix a bill, so the three settings are assumptions, not findings.",
    "Three rules only. GST type, GSTIN match and MSME are not run (see NOT_RUN); the other checks need the paper, rates, quantities or service entries. The rules run touch a minority of last year's queries.",
    "Final values, not day-0 values. Work-order validity and approved value are as they stand in the extract; amendments made later are not visible (data-audit D08). Value headroom is rebuilt from invoices in desk order, not from SAP's balance on the day. 'Flagged on day 0' is therefore an approximation.",
    "False alarms cannot be sized. A bill that is flagged and never queried may be a real problem nobody raised or a flag with nothing behind it; the register cannot tell which.",
    "Shift model. Where the payment-run lever is not applied, the pick-order and intake savings assume payment follows posting at the same gap. Payments go out on two weekdays, so this is a simplification.",
    "Payment-run lever depends on Treasury. The real cut-off, approval step and funding rule are unknown (notes/payment-lag.md); the three cut-offs are settings, not a finding.",
    "Pick order is a replay. It matches AP-1's historical pick-up waits to the other verifiers' on bills that are already paid. It does not show that a queue run this way would hold the same saving on a live queue.",
    f"Vendor calls: {LABEL_CEILING}. The survey gives about 3 calls per bill but not what share are status calls or how many a status message would remove.",
    "Rows versus bills. The register has 11,220 rows, of which 220 are exact duplicates (data-audit D01); the replay uses the 11,000 distinct bills, and the rate-of-flag figures are of those.",
]


def gap_table(cutoff: int) -> np.ndarray:
    """days from a posting weekday to the first Tuesday or Friday at least 1 + cutoff days later"""
    t = np.zeros(7, int)
    for d in range(7):
        k = 1 + cutoff
        while (d + k) % 7 not in (1, 4):
            k += 1
        t[d] = k
    return t


def next_run(dates: pd.Series, cutoff: int) -> pd.Series:
    return dates + pd.to_timedelta(gap_table(cutoff)[dates.dt.dayofweek.to_numpy()], unit="D")


@dataclass
class Replay:
    figs: dict = field(default_factory=dict)       # id -> (value, description): the figures this module owns
    rules: list = field(default_factory=list)      # catch table rows, one per rule (backtest_rules.csv)
    levers: list = field(default_factory=list)     # one dict per setting (levers.csv)
    confusion: list = field(default_factory=list)  # one dict per rule and for any rule
    base: dict = field(default_factory=dict)
    live_waiting: int = 0


def run(out: Path = OUT) -> Replay:
    R = Replay()

    def fig(k, v, d=""):
        R.figs[k] = (round(float(v), 3) if isinstance(v, (float, np.floating)) else v, d)

    S = {r.id: float(r.value) for r in pd.read_csv(out / "figures_query_forensics.csv", keep_default_na=False).itertuples() if str(r.value).replace(".", "", 1).isdigit()}
    b = pd.read_parquet(out / "bills_clean.parquet")
    q = pd.read_csv(out / "query_forensics.csv", parse_dates=["paid_date"])
    pop = b[(b.doc_type == "invoice") & b.paid_date.notna()].copy().set_index("bill_id")
    N = len(pop)
    ms = pop.msme_status.isin(["Micro", "Small"])
    NMS = int(ms.sum())
    tot = (pop.paid_date - pop.desk_received_date).dt.days
    tot_inv = (pop.paid_date - pop.invoice_date).dt.days
    over = tot > 45

    # ---- intake rules, as if checked on the desk date
    bt = b.sort_values(["desk_received_date", "bill_id"]).copy()
    bt["f_dup"] = bt.groupby(bt.vendor_id + "|" + bt.invoice_no).cumcount() > 0
    bt["f_exp"] = (bt.invoice_date > bt.wo_valid_to) & ~bt.f_wo_validity_inverted
    _inv = bt[bt.doc_type == "invoice"]
    bt["f_bal"] = False
    bt.loc[_inv.index, "f_bal"] = _inv.groupby("wo_id").amount_inr.cumsum() > _inv.wo_approved_value_inr
    bt["f_any"] = bt.f_dup | bt.f_exp | bt.f_bal
    rk = {r: k for k, _, rs in RULES for r in rs}
    for key, label, rules in RULES:
        fl = bt["f_" + key]
        qs = q[q.rule_id.isin(rules)]
        R.rules.append(dict(key=key, rule=label, query_rules=", ".join(rules), queries=len(qs), caught=int(qs.bill_id.isin(bt.loc[fl, "bill_id"]).sum()),
                            flagged=int(fl.sum()), flagged_never_queried=int((fl & ~bt.bill_id.isin(q.bill_id)).sum())))
    for c in R.rules:
        for k in ["queries", "caught", "flagged", "flagged_never_queried"]:
            fig(f"l.bt.{c['key']}.{k}", c[k], f"backtest, {c['rule']}: {k.replace('_', ' ')}")
    raw_rows = len(pd.read_csv(ROOT / "pack" / "data" / "bill_register.csv", dtype=str, keep_default_na=False))
    fig("l.bt.raw_rows", raw_rows, "rows in bill_register.csv")
    fig("l.bt.bills", len(bt), "distinct bills replayed (raw rows less the exact duplicate rows, data-audit D01)")
    fig("l.bt.dropped", raw_rows - len(bt), "exact duplicate rows removed before the replay")
    fig("l.bt.flag_any", int(bt.f_any.sum()), "bills flagged by at least one of the three rules")
    fig("l.bt.flag_any_pct", 100 * bt.f_any.mean(), "% of replayed bills flagged by at least one rule")
    fig("l.bt.q_total", len(q), "queries last year, all rules")
    fig("l.bt.q_testable", sum(c["queries"] for c in R.rules), "queries on the rules the backtest can test")
    fig("l.bt.q_caught", sum(c["caught"] for c in R.rules), "of those, on bills flagged on the desk date")
    EXTRA = S["added.s99"] - S["added.s07"]
    fig("l.bt.extra", EXTRA, "days a queried bill carries beyond the days its query stays open")
    qp = q[(q.doc_type == "invoice") & q.bill_id.isin(pop.index) & q.days_open.notna()].copy()
    qc = qp[qp.rule_id.isin(rk)]
    qc = qc[[bool(bt.set_index("bill_id").at[i, "f_" + rk[r]]) for i, r in zip(qc.bill_id, qc.rule_id)]]
    fig("l.bt.n_caught_paid", len(qc), "queries on paid invoices that the three rules would have caught")
    ab = qp[qp.catch_layer.isin(["A", "B"])]

    # ---- confusion table, bill level: flagged on day 0 against really queried for the same cause
    ids = bt.bill_id
    for key, label, rules in [*RULES, ("any", "Any of the three rules", list(rk))]:
        flagged = bt["f_" + key] if key != "any" else bt.f_any
        queried = ids.isin(q[q.rule_id.isin(rules)].bill_id)
        tp, fp, fn = int((flagged & queried).sum()), int((flagged & ~queried).sum()), int((~flagged & queried).sum())
        tn = int((~flagged & ~queried).sum())
        R.confusion.append(dict(key=key, rule=label, flagged_and_queried=tp, flagged_not_queried=fp, queried_not_flagged=fn, neither=tn,
                                precision_pct=100 * tp / max(1, tp + fp), recall_pct=100 * tp / max(1, tp + fn)))
        for k, v in (("tp", tp), ("fp", fp), ("fn", fn), ("tn", tn)):
            fig(f"l.cf.{key}.{k}", v, f"confusion, bills, {label}: {dict(tp='flagged and queried for this cause', fp='flagged, not queried for this cause', fn='queried for this cause, not flagged', tn='neither')[k]}")
        fig(f"l.cf.{key}.precision_pct", R.confusion[-1]["precision_pct"], f"{label}: % of flagged bills that really had a query for this cause")
        fig(f"l.cf.{key}.recall_pct", R.confusion[-1]["recall_pct"], f"{label}: % of bills with a query for this cause that were flagged on day 0")
    fig("l.impact.no_flag_pct", 100 - 100 * bt.f_any.mean(), LABEL_NO_FLAG[0].upper() + LABEL_NO_FLAG[1:] + " (%)")
    fig("l.assume.calls_per_bill", CALLS_PER_BILL, "ASSUMPTION: vendor status calls per bill (vendor survey, about 3)")
    fig("l.impact.calls_ceiling", CALLS_PER_BILL * len(bt), "Vendor calls a year, " + LABEL_CEILING + " (ASSUMPTION: 3 calls per bill on the replayed bills)")
    live = b[b.ho_received_date.notna() & b.ho_picked_date.isna()]
    R.live_waiting = len(live)
    fig("l.live.waiting", R.live_waiting, "bills waiting at head office for AP to pick them up on 30 April 2026 (not yet picked)")

    # ---- the levers
    def intake_saving(residual, optimistic=False):
        src = ab if optimistic else qc
        s = src.groupby("bill_id").days_open.sum() + (EXTRA if optimistic else 0)
        return (s - residual).clip(lower=0).reindex(pop.index).fillna(0)

    qd_all = (pop.ho_picked_date - pop.ho_received_date).dt.days
    a1m = pop.ho_verifier == "AP-1"
    rank = qd_all[a1m].rank(method="average") / (a1m.sum() + 1)
    newq = pd.Series(np.quantile(qd_all[~a1m], rank.to_numpy()), index=rank.index)
    s_queue = (qd_all[a1m] - newq).clip(lower=0).reindex(pop.index).fillna(0)
    fig("l.lever.queue.days", s_queue.sum() / N, "days off the mean: AP-1's pick-up waits matched to the other verifiers' at the same rank")
    fig("l.lever.queue.bills", int((s_queue > 0).sum()), "paid invoices that gain days from the balanced pick order")

    ms_late = lambda t: int((t[ms] > 45).sum())
    p90 = lambda t: float(np.percentile(t, 90))
    R.base = dict(mean=tot.mean(), inv_mean=tot_inv.mean(), ms_late=ms_late(tot), ms_pct=100 * ms_late(tot) / NMS, p90=p90(tot), p90_inv=p90(tot_inv), over=int(over.sum()), over_pct=100 * over.mean(), n=N, n_msme=NMS)
    fig("l.base.desk_mean", R.base["mean"], "mean days desk to paid, paid invoices, as run")
    fig("l.base.inv_mean", R.base["inv_mean"], "mean days invoice to paid, paid invoices, as run")
    fig("l.base.ms_late", R.base["ms_late"], "known Micro and Small paid invoices over 45 days from the desk, as run")
    fig("l.base.ms_late_pct", R.base["ms_pct"], "...as % of known Micro and Small paid invoices")
    fig("l.base.p90", R.base["p90"], "p90 days desk to paid, as run")
    fig("l.base.p90_inv", R.base["p90_inv"], "p90 days invoice to paid, as run")
    fig("l.base.over45", R.base["over"], "all paid invoices over 45 days from the desk, as run")
    fig("l.base.over45_pct", R.base["over_pct"], "...as % of paid invoices")

    def replay(cut=None, queue=False, intake=None):
        """Shift each bill's own dates. cut: payment-run cut-off in days (None = payment as it ran). intake: (residual, optimistic) or None."""
        s = pd.Series(0.0, index=pop.index)
        if queue:
            s += s_queue
        if intake is not None:
            s += intake_saving(*intake)
        s = np.minimum(s, (pop.posted_date - pop.desk_received_date).dt.days.clip(lower=0))
        paid = (pop.paid_date - pop.desk_received_date).dt.days - s
        if cut is not None:
            newpost = pop.posted_date - pd.to_timedelta(s.round().astype(int), unit="D")
            paid = np.minimum(paid, (next_run(newpost, cut) - pop.desk_received_date).dt.days)
        save = tot - paid
        after = tot - save
        return dict(save=save.mean(), ms_late=ms_late(after), ms_pct=100 * ms_late(after) / NMS, p90=p90(after), p90_inv=p90(tot_inv - save), over=int((after > 45).sum()), bills=int((save > 0).sum()))

    def add(code, lever, setting, **kw):
        r = replay(**kw)
        R.levers.append(dict(code=code, lever=lever, setting=setting, **r))
        for k, v in r.items():
            fig(f"l.lever.{code}.{k}", v, f"{lever}, {setting}: {k}")

    add("pay0", "Pay on the first run after posting", "list closes the same day (cut-off 0)", cut=0)
    add("pay1", "Pay on the first run after posting", "list closes 1 day before (cut-off 1)", cut=1)
    add("pay2", "Pay on the first run after posting", "list closes 2 days before (cut-off 2)", cut=2)
    add("queue", "Balanced AP pick order", "AP-1 matched to the other four", queue=True)
    add("in3", "Three intake rules", "residual delay 3 days", intake=(3, False))
    add("in1", "Three intake rules", "residual delay 1 day", intake=(1, False))
    add("inopt", "Intake rules, optimistic", "all layer A and B queries, residual 1 day", intake=(1, True))
    add("low", "All three combined", "cut-off 2, balanced order, residual 3", cut=2, queue=True, intake=(3, False))
    add("mid", "All three combined", "cut-off 1, balanced order, residual 1", cut=1, queue=True, intake=(1, False))
    add("high", "All three combined", "cut-off 0, balanced order, optimistic intake", cut=0, queue=True, intake=(1, True))
    code = {r["code"]: r for r in R.levers}
    for tag, a, bb, c in [("low", "pay2", "queue", "in3"), ("mid", "pay1", "queue", "in1"), ("high", "pay0", "queue", "inopt")]:
        s = sum(code[k]["save"] for k in (a, bb, c))
        fig(f"l.lever.{tag}.sum_alone", s, f"sum of the three levers' days off the mean taken separately, {tag} case")
        fig(f"l.lever.{tag}.overlap", s - R.figs[f"l.lever.{tag}.save"][0], f"days the separate levers count twice, {tag} case")
    return R


def impact_rows(R: Replay) -> list[dict]:
    """Long table for impact.csv: each lever and the three together, with low, middle and high for every measure, and the baseline beside them."""
    code = {r["code"]: r for r in R.levers}
    base, rows = R.base, []

    def add(group, metric, lo, mid, hi, unit, note=""):
        rows.append(dict(group=group, metric=metric, low=lo, middle=mid, high=hi, unit=unit, note=note))

    for g, (lo, mid, hi) in SETTINGS.items():
        c = [code[lo], code[mid], code[hi]]
        add(g, "days_off_mean", *[round(x["save"], 2) for x in c], "days", LABELS[g])
        add(g, "mean_days_desk_to_paid_after", *[round(base["mean"] - x["save"], 2) for x in c], "days", f"before: {base['mean']:.2f}")
        add(g, "mean_days_invoice_to_paid_after", *[round(base["inv_mean"] - x["save"], 2) for x in c], "days", f"before: {base['inv_mean']:.2f}")
        add(g, "msme_over_45_days_count", *[x["ms_late"] for x in c], f"known Micro and Small paid invoices, of {base['n_msme']:,}", f"before: {base['ms_late']}")
        add(g, "msme_over_45_days_pct", *[round(x["ms_pct"], 1) for x in c], "% of known Micro and Small paid invoices", f"before: {base['ms_pct']:.1f}")
        add(g, "all_over_45_days_count", *[x["over"] for x in c], f"paid invoices, of {base['n']:,}", f"before: {base['over']}")
        add(g, "p90_days_desk_to_paid", *[round(x["p90"]) for x in c], "days", f"before: {base['p90']:.0f}")
        add(g, "p90_days_invoice_to_paid", *[round(x["p90_inv"]) for x in c], "days", f"before: {base['p90_inv']:.0f}")
        add(g, "paid_invoices_gaining_days", *[x["bills"] for x in c], "paid invoices", "")
    f = R.figs
    add("ap_work", LABEL_NO_FLAG, f["l.impact.no_flag_pct"][0], f["l.impact.no_flag_pct"][0], f["l.impact.no_flag_pct"][0], "% of bills", "AP still runs rates, quantities, service entries and attendance checks on every bill")
    add("vendor_calls", "vendor calls a year: " + LABEL_CEILING, "", "", f["l.impact.calls_ceiling"][0], "calls a year", f"ASSUMPTION: {CALLS_PER_BILL} calls per bill (survey) x {f['l.bt.bills'][0]:,.0f} bills. No low or middle figure exists")
    return rows


def write_impact(R: Replay, folder: Path = IMPACT_DIR) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(impact_rows(R)).to_csv(folder / "impact.csv", index=False, lineterminator="\n")
    pd.DataFrame(R.confusion).round(2).to_csv(folder / "confusion.csv", index=False, lineterminator="\n")


def pick_order_note(R: Replay) -> str:
    return (f"The pick-order lever is a replay on historical bills: each AP-1 bill is given the pick-up wait of the other four verifiers at the same rank. "
            f"The live queue on 30 April 2026 holds only {R.live_waiting} waiting bills, so the pick order cannot repeat that saving on today's queue; it can only stop a backlog building.")


def screen_data(R: Replay) -> dict:
    """What the impact screen shows: the baseline, the three levers and the combination (low, middle, high), the notes it must carry, and what was not run."""
    return dict(base=R.base, levers=impact_rows(R), confusion=R.confusion, rules=R.rules, pick_order_note=pick_order_note(R), limits=LIMITS, not_run=NOT_RUN,
                label="Replay on last year's register: a counterfactual, not a result", labels=dict(no_flag=LABEL_NO_FLAG, calls_ceiling=LABEL_CEILING))


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    res = run()
    write_impact(res)
    print(pick_order_note(res))
    print(pd.DataFrame(impact_rows(res)).to_string(index=False))
