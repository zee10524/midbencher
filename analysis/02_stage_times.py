"""Stage-by-stage time from invoice date to paid date, from analysis/out/bills_clean.parquet.

Writes (analysis/out/):
  stage_times.csv          mean / median / p90 of every stage, calendar and working days, by dimension
  policy_compliance.csv    total days against the CFO's 45-50 and the 45 / 60 day policy limits, by clock start
  figures_stage_times.csv  every headline number, with an id (picked up by register_numbers.py)

Population: invoices (not credit notes) with a trustworthy paid_date (D03 rows excluded, see notes/data-audit.md).
Calendar days = date difference. Working days = Monday to Friday between the two dates, start inclusive, end exclusive,
no holiday calendar (none in the pack). Stages chain, so calendar days and working days each add up exactly.

Worked vs waiting is a label on the stage, not a measurement of effort: the data holds dates, not effort.
"Worked" = a named person is acting on the bill. "Waiting" = the bill sits in a tray, a courier bag, a queue,
a query or a payment-run calendar. Elapsed days in a "worked" stage are an upper bound on effort.

Run: python analysis/02_stage_times.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
ASOF = pd.Timestamp("2026-04-30")
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

b = pd.read_parquet(OUT / "bills_clean.parquet")
q = pd.read_csv(ROOT / "pack" / "data" / "queries.csv", dtype=str, keep_default_na=False)
q["raised_date"] = pd.to_datetime(q.raised_date)
q["resolved_date"] = pd.to_datetime(q.resolved_date.where(q.resolved_date != ""))
figs: dict[str, tuple] = {}


def fig(k, v, d=""):
    figs[k] = (v, d)


# ------------------------------------------------------------------ population
is_inv = b.doc_type == "invoice"
fig("pop.bills_in_clean", len(b), "bills in bills_clean.parquet")
fig("pop.credit_notes_excluded", int((~is_inv).sum()), "credit notes, not a payment of a bill")
fig("pop.invoices_unpaid_excluded", int((is_inv & b.paid_date_raw.isna()).sum()), "invoices with no paid_date: still in the pipeline")
fig("pop.invoices_bad_paid_date_excluded", int((is_inv & b.f_paid_before_posted).sum()), "invoices in D03: paid_date unusable")
pop = is_inv & b.paid_date.notna()
fig("pop.invoices_analysed", int(pop.sum()), "paid invoices with a trustworthy paid_date")
d = b[pop].copy().merge(q[["bill_id", "raised_date", "resolved_date"]], on="bill_id", how="left")
if d.bill_id.duplicated().any():
    raise SystemExit("a bill has more than one query; query split needs rework")

# ------------------------------------------------------------------ per-bill stage days
D = lambda c: d[c].values.astype("datetime64[D]")
cal = lambda a, z: (d[z] - d[a]).dt.days.to_numpy(float)
wd = lambda a, z: np.busday_count(D(a), D(z)).astype(float)

stage_def = [  # order, name, start col, end col, kind, owner
    (1, "Vendor to facility desk", "invoice_date", "desk_received_date", "waiting", "Vendor"),
    (2, "Property check and service entry", "desk_received_date", "property_verified_date", "worked", "Commercial executive"),
    (3, "Waiting for property head's signature", "property_verified_date", "property_head_signed_date", "waiting", "Property head"),
    (4, "Courier to head office", "property_head_signed_date", "ho_received_date", "waiting", "Courier"),
    (5, "Queue at central AP", "ho_received_date", "ho_picked_date", "waiting", "Central AP"),
    (6, "AP verification, no query open", "ho_picked_date", "posted_date", "worked", "Central AP"),
    (7, "Query open", "ho_picked_date", "posted_date", "waiting", "Property / vendor / procurement"),
    (8, "Waiting for payment run", "posted_date", "paid_date", "waiting", "Treasury"),
]
days = {}
for order, name, a, z, kind, owner in stage_def:
    days[order] = (cal(a, z), wd(a, z))
# split pick-to-post (stage 6+7) into query-open days and the rest
has_q = d.raised_date.notna() & d.resolved_date.notna()
r0 = d.raised_date.where(d.raised_date > d.ho_picked_date, d.ho_picked_date)  # clip to the pick..post window
r1 = d.resolved_date.where(d.resolved_date < d.posted_date, d.posted_date)
fig("query.clipped_to_window", int((has_q & ((d.raised_date < d.ho_picked_date) | (d.resolved_date > d.posted_date))).sum()),
    "queries that fell outside the pick..post window and were clipped")
q_cal = np.where(has_q, (r1 - r0).dt.days.fillna(0), 0).astype(float)
q_wd = np.where(has_q, np.busday_count(r0.fillna(d.ho_picked_date).values.astype("datetime64[D]"),
                                       r1.fillna(d.ho_picked_date).values.astype("datetime64[D]")), 0).astype(float)
days[7] = (q_cal, q_wd)
days[6] = (days[6][0] - q_cal, days[6][1] - q_wd)
total_cal, total_wd = cal("invoice_date", "paid_date"), wd("invoice_date", "paid_date")
assert np.allclose(sum(v[0] for v in days.values()), total_cal), "calendar stages do not add up"
assert np.allclose(sum(v[1] for v in days.values()), total_wd), "working-day stages do not add up"
assert (days[6][0] >= 0).all() and (days[6][1] >= 0).all()
fig("query.bills_with_query", int(has_q.sum()), "analysed invoices that had a query")

kind_of = {o: k for o, _, _, _, k, _ in stage_def}
days[98] = (sum(days[o][0] for o in kind_of if kind_of[o] == "worked"), sum(days[o][1] for o in kind_of if kind_of[o] == "worked"))
days[97] = (sum(days[o][0] for o in kind_of if kind_of[o] == "waiting"), sum(days[o][1] for o in kind_of if kind_of[o] == "waiting"))
days[99] = (total_cal, total_wd)
meta = {o: (n, k, w) for o, n, _, _, k, w in stage_def}
meta |= {97: ("Total waiting", "waiting", "all"), 98: ("Total worked", "worked", "all"), 99: ("Total invoice to paid", "total", "all")}
start_col = {o: s for o, _, s, _, _, _ in stage_def} | {97: "invoice_date", 98: "invoice_date", 99: "invoice_date"}
start_col[7] = "ho_picked_date"

# ------------------------------------------------------------------ long table
msme_group = d.msme_status.map({"Micro": "Micro or Small", "Small": "Micro or Small", "Medium": "Medium or Not MSME",
                                "Not MSME": "Medium or Not MSME", "Unknown": "Unknown"})
dims = pd.DataFrame({
    "bill_id": d.bill_id,
    "category": d.category,
    "property_type": d.property_type,
    "verifier": d.ho_verifier,
    "month": d.invoice_date.dt.to_period("M").astype(str),
    "has_query": np.where(has_q, "query", "no query"),
    "msme_group": msme_group,
    "overall": "all paid invoices",
})
parts = []
for o, (c, w) in days.items():
    t = dims.copy()
    t["stage_order"], t["stage"], t["kind"], t["owner"] = o, *[meta[o][0], meta[o][1], meta[o][2]]
    t["cal"], t["wd"] = c, w
    t["weekday"] = d[start_col[o]].dt.day_name().to_numpy()
    parts.append(t)
long = pd.concat(parts, ignore_index=True)


def p90(s):
    return s.quantile(0.9)


rows = []
for dim in ["overall", "category", "property_type", "verifier", "month", "weekday", "has_query", "msme_group"]:
    sub = long if dim != "verifier" else long[long.stage_order.isin([5, 6, 7])]  # only HO stages are the verifier's
    g = sub.groupby([dim, "stage_order", "stage", "kind", "owner"])[["cal", "wd"]].agg(["mean", "median", p90, "size"])
    g.columns = ["cal_mean", "cal_median", "cal_p90", "n", "wd_mean", "wd_median", "wd_p90", "_n2"]
    g = g.drop(columns="_n2").reset_index().rename(columns={dim: "group"})
    g.insert(0, "dimension", dim)
    rows.append(g)
res = pd.concat(rows, ignore_index=True)
tot = res[res.stage_order == 99].set_index(["dimension", "group"]).cal_mean
res["share_of_total_cal_mean"] = [r.cal_mean / tot.get((r.dimension, r.group), np.nan) if r.dimension != "verifier" else np.nan
                                  for r in res.itertuples()]
res["_gsort"] = res.group.map({k: i for i, k in enumerate(WEEKDAYS)}).fillna(0)
res = res.sort_values(["dimension", "_gsort", "group", "stage_order"]).drop(columns="_gsort")
cols = ["dimension", "group", "stage_order", "stage", "kind", "owner", "n", "cal_mean", "cal_median", "cal_p90",
        "wd_mean", "wd_median", "wd_p90", "share_of_total_cal_mean"]
res[cols].round(3).to_csv(OUT / "stage_times.csv", index=False, lineterminator="\n")

# headline figures
ov = res[res.dimension == "overall"].set_index("stage_order")
for o, r in ov.iterrows():
    for m in ("cal_mean", "cal_median", "cal_p90", "wd_mean", "wd_median", "wd_p90"):
        fig(f"overall.s{o:02d}.{m}", round(float(r[m]), 2), f"{r.stage}: {m}")
    fig(f"overall.s{o:02d}.share", round(float(r.share_of_total_cal_mean), 4), f"{r.stage}: share of mean calendar days")

# who holds the bill: mean calendar days grouped by owner of the stage
side = {"Vendor (to the desk)": [1], "Property (check, signature)": [2, 3], "Courier": [4],
        "Central AP (queue, verify, query)": [5, 6, 7], "Treasury (payment run)": [8]}
tot_mean = ov.loc[99, "cal_mean"]
for name, os_ in side.items():
    m = float(ov.loc[os_, "cal_mean"].sum())
    fig(f"side.{os_[0]}.cal_mean", round(m, 2), f"mean calendar days with: {name}")
    fig(f"side.{os_[0]}.share", round(m / tot_mean, 4), f"share of mean total with: {name}")
n_q = int(has_q.sum())
fig("query.mean_days_among_queried", round(float(q_cal[has_q.to_numpy()].mean()), 2), "mean calendar days a query was open, on bills that had one")
fig("query.share_of_bills", round(n_q / len(d), 4), "share of analysed invoices that had a query")

# ------------------------------------------------------------------ policy and CFO comparison
pol = []
clocks = {"invoice_date": "invoice date on the bill", "desk_received_date": "facility desk logs it",
          "property_verified_date": "property verified, service entry created (proxy for acceptance)"}
allinv = b[is_inv].copy()
allinv["msme_group"] = allinv.msme_status.map({"Micro": "Micro or Small", "Small": "Micro or Small", "Medium": "Medium or Not MSME",
                                               "Not MSME": "Medium or Not MSME", "Unknown": "Unknown"})
pd_ = allinv[allinv.paid_date.notna()]
op = allinv[allinv.paid_date_raw.isna()]  # still unpaid at 30 Apr 2026
limit = {"Micro or Small": "45", "Medium or Not MSME": "60", "Unknown": "45 or 60", "All": "45 (MSME) / 60 (others)"}
MATURE = pd.Timestamp("2026-01-31")  # invoices dated up to here have had at least 89 days to be paid by 30 Apr 2026
limit["All, invoiced to 31 Jan 2026"] = "45 (MSME) / 60 (others)"
for grp in ["Micro or Small", "Medium or Not MSME", "Unknown", "All", "All, invoiced to 31 Jan 2026"]:
    if grp == "All":
        sel, selo = pd_, op
    elif grp.startswith("All,"):
        sel, selo = pd_[pd_.invoice_date <= MATURE], op[op.invoice_date <= MATURE]
    else:
        sel, selo = pd_[pd_.msme_group == grp], op[op.msme_group == grp]
    for c, desc in clocks.items():
        x = (sel.paid_date - sel[c]).dt.days
        age = (ASOF - selo[c]).dt.days
        pol.append(dict(
            msme_group=grp, clock_starts=c, clock_meaning=desc, limit_days=limit[grp], n_paid=len(x),
            mean=x.mean(), median=x.median(), p90=x.quantile(0.9),
            pct_over_45=100 * (x > 45).mean(), pct_over_60=100 * (x > 60).mean(),
            pct_in_cfo_band_45_to_50=100 * x.between(45, 50).mean(),
            n_unpaid=len(selo), unpaid_median_age=age.median(),
            n_unpaid_already_over_45=int((age > 45).sum()), n_unpaid_already_over_60=int((age > 60).sum()),
        ))
pol = pd.DataFrame(pol)
pol.round(2).to_csv(OUT / "policy_compliance.csv", index=False, lineterminator="\n")
for r in pol.itertuples():
    k = f"policy.{'matured' if r.msme_group.startswith('All,') else r.msme_group.split()[0].lower()}.{r.clock_starts.replace('_date', '')}"
    for m in ("n_paid", "mean", "median", "p90", "pct_over_45", "pct_over_60", "pct_in_cfo_band_45_to_50",
              "n_unpaid", "n_unpaid_already_over_45", "n_unpaid_already_over_60"):
        fig(f"{k}.{m}", round(float(getattr(r, m)), 2), f"{r.msme_group}, clock from {r.clock_starts}: {m}")

pd.DataFrame([dict(id=k, value=v, description=dsc) for k, (v, dsc) in figs.items()]).to_csv(OUT / "figures_stage_times.csv", index=False, lineterminator="\n")

# ------------------------------------------------------------------ console summary
pd.set_option("display.width", 220, "display.max_columns", 30)
print(f"population: {int(pop.sum())} paid invoices of {len(b)} bills")
print(ov[["stage", "kind", "cal_mean", "cal_median", "cal_p90", "wd_mean", "wd_median", "wd_p90", "share_of_total_cal_mean"]].round(2).to_string())
print(pol.round(1).to_string())
