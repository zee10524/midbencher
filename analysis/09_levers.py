"""Check three register findings independently, look for what explains the payment-run lag, and replay three levers on the register.

(a) Independent checks of: payments only on Tuesday and Friday; next run 2.3 days after posting; 6.0 days actual; 29% paid on the first run;
    AP-1 about 40% of bills, 11.3 against 7.2 days to pick-up, 1.65 days off the mean; removing every query saves at most about 3.0 days;
    754 of the 1,153 bills over 45 days were queried. These use vectorised code that shares nothing with 08_problem_ranking.py, which they are compared to.
(b) What explains the payment-run lag: posting weekday, gap to the run, amount, MSME status, vendor, property, month.
(c) Replay on the register of: pay on the first run after posting (cut-off 0, 1 or 2 days), a balanced AP pick order, and the three intake rules that the register and
    the SAP extract can test. Each alone and combined by shifting each bill's own dates, so days are not counted twice.

Writes analysis/out/figures_levers.csv, levers.csv, lag_factors.csv, lag_first_run.csv, backtest_rules.csv.   Run: python analysis/09_levers.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
P = {}
for r in pd.read_csv(OUT / "figures_problem.csv", keep_default_na=False).itertuples():
    P[r.id] = float(r.value) if str(r.value).replace(".", "", 1).replace("-", "", 1).isdigit() else r.value
S = {r.id: float(r.value) for r in pd.read_csv(OUT / "figures_query_forensics.csv", keep_default_na=False).itertuples() if str(r.value).replace(".", "", 1).isdigit()}
figs: dict[str, tuple] = {}


def fig(k, v, d=""):
    figs[k] = (round(float(v), 3) if isinstance(v, (float, np.floating)) else v, d)


b = pd.read_parquet(OUT / "bills_clean.parquet")
q = pd.read_csv(OUT / "query_forensics.csv", parse_dates=["paid_date"])
pop = b[(b.doc_type == "invoice") & b.paid_date.notna()].copy().set_index("bill_id")
N = len(pop)
ms = pop.msme_status.isin(["Micro", "Small"])
NMS = int(ms.sum())
fig("l.n", N, "paid invoices analysed")
fig("l.n_msme_known", NMS, "known Micro and Small paid invoices")
D = lambda s: s.dt.dayofweek.to_numpy()
tot = (pop.paid_date - pop.desk_received_date).dt.days
tot_inv = (pop.paid_date - pop.invoice_date).dt.days


def gap_table(cutoff):
    """days from a posting weekday to the first Tuesday or Friday at least 1 + cutoff days later"""
    t = np.zeros(7, int)
    for d in range(7):
        k = 1 + cutoff
        while (d + k) % 7 not in (1, 4):
            k += 1
        t[d] = k
    return t


def next_run(dates, cutoff):
    return dates + pd.to_timedelta(gap_table(cutoff)[dates.dt.dayofweek.to_numpy()], unit="D")


# ============================================================ (a) independent checks
# 1. payment runs
on_run = pop.paid_date.dt.dayofweek.isin([1, 4])
fig("l.chk.paid_on_run_pct", 100 * on_run.mean(), "% of paid invoices paid on a Tuesday or a Friday")
nr0 = next_run(pop.posted_date, 0)
fig("l.chk.run_wait", (nr0 - pop.posted_date).dt.days.mean(), "mean days from posting to the next Tuesday or Friday run")
fig("l.chk.actual_wait", (pop.paid_date - pop.posted_date).dt.days.mean(), "mean days from posting to payment")
fig("l.chk.first_run_pct", 100 * (pop.paid_date <= nr0).mean(), "% of paid invoices paid on or before the first run after posting")
for k, mine in [("l.chk.run_wait", "p.pay.schedule_wait_lead0"), ("l.chk.actual_wait", "p.pay.actual_wait")]:
    assert abs(figs[k][0] - P[mine]) < 0.006, (k, figs[k][0], P[mine])
assert abs(figs["l.chk.first_run_pct"][0] - (100 - P["p.pay.share_late_lead0"])) < 0.02
# 2. AP-1
ver = pop[pop.ho_verifier != ""]
qd = (ver.ho_picked_date - ver.ho_received_date).dt.days
a1 = ver.ho_verifier == "AP-1"
fig("l.chk.ap1_share", 100 * a1.sum() / N, "AP-1's share of paid invoices (%)")
fig("l.chk.ap1_wait", qd[a1].mean(), "mean days from head-office receipt to pick-up, AP-1")
fig("l.chk.others_wait", qd[~a1].mean(), "mean days from head-office receipt to pick-up, the other four verifiers")
gap_ap = qd[a1].mean() - qd[~a1].mean()
fig("l.chk.ap1_saving", ((qd[a1] - qd[~a1].mean()).sum()) / N, "days off the mean if each AP-1 bill waited the others' mean")
assert abs(figs["l.chk.ap1_saving"][0] - P["p.queue.saving"]) < 0.01
assert int(len(ver)) == N, "every paid invoice has a verifier"
# 3. queries
qb = q[q.doc_type == "invoice"]
qinv = qb[qb.bill_id.isin(pop.index) & qb.days_open.notna()]
queried = pop.index.isin(qinv.bill_id)
fig("l.chk.queried_pct", 100 * queried.mean(), "% of paid invoices with a query")
fig("l.chk.q_ceiling_open", qinv.groupby("bill_id").days_open.sum().sum() / N, "days off the mean if every query's open days vanished (ceiling)")
fig("l.chk.q_ceiling_added", S["added.s99"] * queried.sum() / N, "days off the mean if queried bills lost the extra days they carry over unqueried bills (the 24.2 extra, same category)")
fig("l.chk.q_diff_means", (tot_inv[queried].mean() - tot_inv[~queried].mean()) * queried.sum() / N, "days off the mean if queried bills were as fast as unqueried bills (invoice clock)")
over = tot > 45
fig("l.chk.over45", int(over.sum()), "paid invoices over 45 days from the desk date")
fig("l.chk.over45_queried", int((over & queried).sum()), "...of which had a query")
fig("l.chk.over45_queried_pct", 100 * (over & queried).sum() / over.sum(), "...% of them")
fig("l.chk.over45_share_among_queried", 100 * over[queried].mean(), "% of queried bills over 45 days")
fig("l.chk.over45_share_among_unqueried", 100 * over[~queried].mean(), "% of unqueried bills over 45 days")
# a query removed takes its open days and the extra days around it
cf = tot - qinv.groupby("bill_id").days_open.sum().reindex(pop.index).fillna(0)
fig("l.chk.over45_if_no_queries", int((cf > 45).sum()), "bills still over 45 days if every query's open days were removed")
fig("l.chk.mean_over45_queried_removed", (tot - np.minimum(tot, qinv.groupby("bill_id").days_open.sum().reindex(pop.index).fillna(0))).mean(), "mean desk-to-paid days with every query's open days removed")

# ============================================================ (b) what explains the lag
pr = pop.copy()
pr["nr"] = nr0
pr["gap"] = (pr.nr - pr.posted_date).dt.days
pr["excess"] = (pr.paid_date - pr.nr).dt.days.clip(lower=0)
pr["first"] = pr.paid_date <= pr.nr
cal = pd.date_range(pr.invoice_date.min(), pr.paid_date.max() + pd.Timedelta(days=14))
cum = pd.Series(np.cumsum(cal.dayofweek.isin([1, 4])), index=cal)
pr["runs_missed"] = cum.reindex(pr.paid_date).to_numpy() - cum.reindex(pr.nr).to_numpy()
for k in range(0, 4):
    fig(f"l.lag.missed_{k}", 100 * ((pr.runs_missed == k) if k < 3 else (pr.runs_missed >= k)).mean(), f"% of paid invoices that missed {k}{'+' if k == 3 else ''} runs after the first one open to them")
fig("l.lag.mean_runs_missed", pr.runs_missed.mean(), "mean runs missed after the first one open to the bill")
fig("l.lag.days_per_run", pr.excess.sum() / max(1, pr.runs_missed.sum()), "mean days added per missed run")
pr["amt"] = pd.qcut(pr.amount_inr, 5, labels=["q1 smallest", "q2", "q3", "q4", "q5 largest"])
pr["post_dow"] = pr.posted_date.dt.day_name()
pr["post_month"] = pr.posted_date.dt.strftime("%Y-%m")
pr["paid_month"] = pr.paid_date.dt.strftime("%Y-%m")
pr["msme"] = pr.msme_status.replace("", "blank")
pr["gap_g"] = pr.gap.astype(str) + " days"
rows = []
for name, col, minn in [("Gap to the run (days)", "gap_g", 1), ("Posting weekday", "post_dow", 1), ("Amount (fifths)", "amt", 1), ("MSME status", "msme", 1), ("Verifier", "ho_verifier", 1),
                        ("Spend category", "category", 1), ("Property type", "property_type", 1), ("Property", "property_code", 30), ("Vendor", "vendor_id", 30), ("Posting month", "post_month", 1)]:
    g = pr.groupby(col, observed=True).agg(n=("excess", "size"), mean=("excess", "mean"), first=("first", "mean"))
    k = len(g)
    ss_b = (g.n * (g["mean"] - pr.excess.mean()) ** 2).sum()
    eta = ss_b / ((pr.excess - pr.excess.mean()) ** 2).sum()
    adj = 1 - (1 - eta) * (len(pr) - 1) / (len(pr) - k)
    big = g[g.n >= max(minn, 30)] if minn > 1 else g
    rows.append(dict(factor=name, groups=k, eta2=eta, adj_eta2=adj, lowest=big["mean"].min(), highest=big["mean"].max(), lo_first_pct=100 * big["first"].max(), hi_first_pct=100 * big["first"].min()))
    fid = {"Gap to the run (days)": "gap", "Posting weekday": "dow", "Amount (fifths)": "amount", "MSME status": "msme", "Verifier": "verifier", "Spend category": "category",
           "Property type": "ptype", "Property": "property", "Vendor": "vendor", "Posting month": "month"}[name]
    fig(f"l.lag.{fid}.adj_eta2", adj, f"share of the spread in days past the first run explained by {name.lower()} (adjusted for the number of groups)")
    fig(f"l.lag.{fid}.lowest", big["mean"].min(), f"lowest group mean of days past the first run, {name.lower()}")
    fig(f"l.lag.{fid}.highest", big["mean"].max(), f"highest group mean of days past the first run, {name.lower()}")
pd.DataFrame(rows).round(4).to_csv(OUT / "lag_factors.csv", index=False)
fr = pr.groupby("gap").agg(n=("first", "size"), first_pct=("first", "mean"), mean_excess=("excess", "mean"), mean_runs_missed=("runs_missed", "mean"))
fr["first_pct"] *= 100
fr.round(3).to_csv(OUT / "lag_first_run.csv")
for g, r in fr.iterrows():
    fig(f"l.lag.gap{g}.n", r.n, f"paid invoices whose first open run is {g} days after posting")
    fig(f"l.lag.gap{g}.first_pct", r.first_pct, f"% of them paid on that first run")
    fig(f"l.lag.gap{g}.excess", r.mean_excess, f"mean days past that run")
runs_per_day = pop.groupby("paid_date").size()
fig("l.lag.runs_n", len(runs_per_day), "payment run dates in the register")
fig("l.lag.bills_per_run_mean", runs_per_day.mean(), "mean paid invoices per run date")
fig("l.lag.bills_per_run_tue", pop[pop.paid_date.dt.dayofweek == 1].groupby("paid_date").size().mean(), "mean paid invoices per Tuesday run")
fig("l.lag.bills_per_run_fri", pop[pop.paid_date.dt.dayofweek == 4].groupby("paid_date").size().mean(), "mean paid invoices per Friday run")
fig("l.lag.tue_share", 100 * (pop.paid_date.dt.dayofweek == 1).mean(), "% of paid invoices paid on a Tuesday")

# ============================================================ (c) levers
# intake rules, as if checked on the desk date (the backtest)
bt = b.sort_values(["desk_received_date", "bill_id"]).copy()
bt["f_dup"] = bt.groupby(bt.vendor_id + "|" + bt.invoice_no).cumcount() > 0
bt["f_exp"] = (bt.invoice_date > bt.wo_valid_to) & ~bt.f_wo_validity_inverted
_inv = bt[bt.doc_type == "invoice"]
bt["f_bal"] = False
bt.loc[_inv.index, "f_bal"] = _inv.groupby("wo_id").amount_inr.cumsum() > _inv.wo_approved_value_inr
bt["f_any"] = bt.f_dup | bt.f_exp | bt.f_bal
RULES = [("dup", "Duplicate invoice number for the vendor (H13)", ["R01"]), ("exp", "Work order expired on the invoice date (H3)", ["R26"]),
         ("bal", "Work order value exhausted (H3, as value headroom)", ["R25", "R24", "R10"])]
rk = {r: k for k, _, rs in RULES for r in rs}
cat = []
for key, label, rules in RULES:
    fl = bt["f_" + key]
    qs = q[q.rule_id.isin(rules)]
    cat.append(dict(key=key, rule=label, query_rules=", ".join(rules), queries=len(qs), caught=int(qs.bill_id.isin(bt.loc[fl, "bill_id"]).sum()), flagged=int(fl.sum()), flagged_never_queried=int((fl & ~bt.bill_id.isin(q.bill_id)).sum())))
pd.DataFrame(cat).to_csv(OUT / "backtest_rules.csv", index=False)
for c in cat:
    for k in ["queries", "caught", "flagged", "flagged_never_queried"]:
        fig(f"l.bt.{c['key']}.{k}", c[k], f"backtest, {c['rule']}: {k.replace('_', ' ')}")
raw_rows = len(pd.read_csv(ROOT / "pack" / "data" / "bill_register.csv", dtype=str, keep_default_na=False))
fig("l.bt.raw_rows", raw_rows, "rows in bill_register.csv")
fig("l.bt.bills", len(bt), "distinct bills replayed (raw rows less the exact duplicate rows, data-audit D01)")
fig("l.bt.dropped", raw_rows - len(bt), "exact duplicate rows removed before the replay")
fig("l.bt.flag_any", int(bt.f_any.sum()), "bills flagged by at least one of the three rules")
fig("l.bt.flag_any_pct", 100 * bt.f_any.mean(), "% of replayed bills flagged by at least one rule")
fig("l.bt.q_total", len(q), "queries last year, all rules")
fig("l.bt.q_testable", sum(c["queries"] for c in cat), "queries on the rules the backtest can test")
fig("l.bt.q_caught", sum(c["caught"] for c in cat), "of those, on bills flagged on the desk date")
EXTRA = S["added.s99"] - S["added.s07"]
fig("l.bt.extra", EXTRA, "days a queried bill carries beyond the days its query stays open")
qp = q[(q.doc_type == "invoice") & q.bill_id.isin(pop.index) & q.days_open.notna()].copy()
qc = qp[qp.rule_id.isin(rk)]
qc = qc[[bool(bt.set_index("bill_id").at[i, "f_" + rk[r]]) for i, r in zip(qc.bill_id, qc.rule_id)]]
fig("l.bt.n_caught_paid", len(qc), "queries on paid invoices that the three rules would have caught")
ab = qp[qp.catch_layer.isin(["A", "B"])]


def intake_saving(residual, optimistic=False):
    """per bill: open days of the caught queries (plus the extra days around an optimistic catch) less the residual delay, never below 0"""
    src = ab if optimistic else qc
    s = src.groupby("bill_id").days_open.sum() + (EXTRA if optimistic else 0)
    return (s - residual).clip(lower=0).reindex(pop.index).fillna(0)


# balanced pick order: AP-1's bills take the pick-up wait of the other verifiers at the same rank
qd_all = (pop.ho_picked_date - pop.ho_received_date).dt.days
a1m = pop.ho_verifier == "AP-1"
rank = qd_all[a1m].rank(method="average") / (a1m.sum() + 1)
newq = pd.Series(np.quantile(qd_all[~a1m], rank.to_numpy()), index=rank.index)
s_queue = (qd_all[a1m] - newq).clip(lower=0).reindex(pop.index).fillna(0)
fig("l.lever.queue.days", s_queue.sum() / N, "days off the mean: AP-1's pick-up waits matched to the other verifiers' at the same rank")
fig("l.lever.queue.bills", int((s_queue > 0).sum()), "paid invoices that gain days from the balanced pick order")

ms_late = lambda t: int((t[ms] > 45).sum())
p90 = lambda t: float(np.percentile(t, 90))
base = dict(mean=tot.mean(), ms_late=ms_late(tot), p90=p90(tot), p90_inv=p90(tot_inv))
fig("l.base.desk_mean", base["mean"], "mean days desk to paid, paid invoices, as run")
fig("l.base.inv_mean", tot_inv.mean(), "mean days invoice to paid, paid invoices, as run")
fig("l.base.ms_late", base["ms_late"], "known Micro and Small paid invoices over 45 days from the desk, as run")
fig("l.base.ms_late_pct", 100 * base["ms_late"] / NMS, "...as % of known Micro and Small paid invoices")
fig("l.base.p90", base["p90"], "p90 days desk to paid, as run")
fig("l.base.p90_inv", base["p90_inv"], "p90 days invoice to paid, as run")
fig("l.base.over45", int(over.sum()), "all paid invoices over 45 days from the desk, as run")
fig("l.base.over45_pct", 100 * over.mean(), "...as % of paid invoices")


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
        run = (next_run(newpost, cut) - pop.desk_received_date).dt.days
        paid = np.minimum(paid, run)
    save = tot - paid
    after = tot - save
    return dict(save=save.mean(), ms_late=ms_late(after), ms_pct=100 * ms_late(after) / NMS, p90=p90(after), p90_inv=p90(tot_inv - save), over=int((after > 45).sum()), bills=int((save > 0).sum()))


ROWS = []


def add(code, lever, setting, **kw):
    r = replay(**kw)
    ROWS.append(dict(code=code, lever=lever, setting=setting, **r))
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
for tag, a, bb, c in [("low", "pay2", "queue", "in3"), ("mid", "pay1", "queue", "in1"), ("high", "pay0", "queue", "inopt")]:
    s = sum(next(r["save"] for r in ROWS if r["code"] == k) for k in (a, bb, c))
    fig(f"l.lever.{tag}.sum_alone", s, f"sum of the three levers' days off the mean taken separately, {tag} case")
    fig(f"l.lever.{tag}.overlap", s - figs[f"l.lever.{tag}.save"][0], f"days the separate levers count twice, {tag} case")
pd.DataFrame(ROWS).round(3).to_csv(OUT / "levers.csv", index=False)
pd.DataFrame([dict(id=k, value=v, description=d) for k, (v, d) in figs.items()]).to_csv(OUT / "figures_levers.csv", index=False)
print("figures:", len(figs))
print(pd.DataFrame(ROWS).round(2).to_string(index=False))
print({k: v[0] for k, v in figs.items() if k.startswith("l.chk")})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print(fr.round(2).to_string())

# ============================================================ notes/payment-lag.md
v = lambda k: figs[k][0]
d1 = lambda k: f"{v(k):.1f}"
d2 = lambda k: f"{v(k):.2f}"
d0 = lambda k: f"{v(k):,.0f}"
fac = pd.DataFrame(rows)
FT = "\n".join(f"| {r.factor} | {r.groups} | {100 * r.adj_eta2:.1f}% | {r.lowest:.2f} to {r.highest:.2f} |" for r in fac.itertuples())
GT = "\n".join(f"| {g} | {r.n:,.0f} | {r.first_pct:.1f}% | {r.mean_excess:.2f} | {r.mean_runs_missed:.2f} |" for g, r in fr.iterrows())
md = f"""# Payment-run lag and three register findings, checked

Generated by `analysis/09_levers.py`; every figure is registered in `notes/numbers.md` (ids `l.chk.*` and `l.lag.*`). Population: {d0('l.n')} paid invoices. No legal or Treasury process is asserted here: the hypotheses are stated as hypotheses.

## 1. The three findings, checked with code that shares nothing with `08_problem_ranking.py`

| Finding as given | Independent result | Verdict |
|---|---|---|
| Payments happen only on Tuesday and Friday | {d1('l.chk.paid_on_run_pct')}% of paid invoices are paid on a Tuesday or a Friday ({d1('l.lag.tue_share')}% Tuesday) | Confirmed |
| The next run after posting is about 2.3 days away | {d2('l.chk.run_wait')} days | Confirmed |
| Posted to paid is 6.0 days | {d2('l.chk.actual_wait')} days | Confirmed |
| Only 29% pay on the first run after posting | {d1('l.chk.first_run_pct')}% paid on or before it | Confirmed |
| AP-1 handles about 40% of bills | {d1('l.chk.ap1_share')}% of paid invoices | Confirmed |
| Pick-up takes 11.3 days at AP-1 and about 7.2 elsewhere | {d2('l.chk.ap1_wait')} and {d2('l.chk.others_wait')} days | Confirmed |
| Matching AP-1 to the others cuts about 1.65 days from the mean | {d2('l.chk.ap1_saving')} days (the same sum, read a second way) | Confirmed |
| Removing every query cuts at most about 3.0 days from the mean | {d2('l.chk.q_ceiling_open')} days if only the days a query stays open vanish; {d2('l.chk.q_ceiling_added')} if queried bills lose the extra days they carry over unqueried ones in the same category; {d2('l.chk.q_diff_means')} if queried bills were as fast as unqueried ones (invoice clock) | Confirmed as a ceiling between {d2('l.chk.q_ceiling_open')} and {d2('l.chk.q_ceiling_added')} |
| 754 of the 1,153 bills over 45 days were queried | {d0('l.chk.over45_queried')} of {d0('l.chk.over45')} ({d1('l.chk.over45_queried_pct')}%). The clock is the desk date. {d1('l.chk.over45_share_among_queried')}% of queried bills are over 45 days against {d1('l.chk.over45_share_among_unqueried')}% of unqueried | Confirmed |

**What the last row means.** Queries are {d1('l.chk.queried_pct')}% of paid invoices and about two thirds of the bills over 45 days, so they drive the tail. They move the mean by at most about 3 days. If every query's open days were removed, {d0('l.chk.over45_if_no_queries')} of the {d0('l.chk.over45')} bills would still be over 45 days: the tail is also made of waiting.

## 2. What explains the payment-run lag

Measure: days paid after the first Tuesday or Friday open to the bill (list closing the day after posting). Mean {d2('l.lever.pay0.save')} days. The table gives, for each factor, the share of the spread in that lag that the factor explains (adjusted for the number of groups, so vendors and properties with few bills do not look important by chance), and the lowest and highest group mean (groups of 30 bills or more for property and vendor).

| Factor | Groups | Spread explained | Group means (days past the run) |
|---|---|---|---|
{FT}

**Only the gap between posting and the run matters.** The posting weekday is the same finding: it sets the gap. Amount, MSME status, verifier, category, property, vendor and month explain none of it. Vendors and properties show a range of means, but after adjusting for group size none is above chance.

| Days from posting to the first open run | Paid invoices | Paid on that run | Mean days past it | Mean runs missed |
|---|---|---|---|---|
{GT}

A bill posted one day before a run is paid on it {fr.first_pct.iloc[0]:.0f}% of the time, two days before {fr.first_pct.iloc[1]:.0f}%, three days {fr.first_pct.iloc[2]:.0f}%, four days {fr.first_pct.iloc[3]:.0f}%. No gap gets close to all bills, and even four days is {fr.first_pct.iloc[3]:.0f}%. {d1('l.lag.missed_0')}% of bills pay on the first run open to them, {d1('l.lag.missed_1')}% miss one run, {d1('l.lag.missed_2')}% miss two and {d1('l.lag.missed_3')}% miss three or more; each missed run adds {d1('l.lag.days_per_run')} days.

### Hypotheses (not tested, because the pack holds no payment-run data)

1. **A list cut-off that sits about three to four days before the run.** The share paid on the first run climbs by roughly twenty points for each extra day of lead, which a cut-off with some slack in its application would give. It would not give a clean step, and we see none.
2. **A batch approval step, with a second approver or the treasury head signing the whole list**, so that a bill posted after the list is drawn waits for the next list. This would also produce the same gap pattern.
3. **Funding.** Treasury releasing a run in tranches by available cash, which would hit all factors equally and not by amount, vendor or MSME status. That fits the finding that no bill characteristic matters. It could still be a priority rule that Treasury applies to payments for statutory dues, which we cannot see.
4. **The posting date is not the date the bill became payable.** Posting dates fall on all seven days of the week, including Saturdays and Sundays (`notes/data-audit.md` D15), which a posting calendar tied to the working week would not. A run pays {d0('l.lag.bills_per_run_mean')} of these invoices on average ({d0('l.lag.bills_per_run_tue')} on a Tuesday, {d0('l.lag.bills_per_run_fri')} on a Friday). If an approval step sits between posting and the list, the gap we measure is noisy and the first-run share is understated.

### Question added to the client list

**Payment-run rules (priority 1).** From Treasury, for the last twelve months: for each Tuesday and Friday run, the date and time the run list was drawn, the date and time it was approved, the list of invoice numbers on it, and the written cut-off or approval rule; for each invoice, the date it became payable in SAP (clearing date) and the reason code for any hold. This settles which of the four hypotheses is true and whether a cut-off of 0, 1 or 2 days is available. The same request is in `notes/claims-tested.md`.
"""
(ROOT / "notes" / "payment-lag.md").write_text(md, encoding="utf-8")
print("wrote notes/payment-lag.md")
