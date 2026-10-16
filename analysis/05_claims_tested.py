"""Test every claim in the ledger of notes/understanding.md (L1 to L57) plus three from the AP lead, against the data.

Reads the outputs of clean.py, 02_stage_times.py and 04_query_forensics.py, and computes what they do not already hold.
Writes:
  analysis/out/figures_claims_tested.csv   figures computed here (ids start with c.)
  analysis/out/claims_tested.csv           one row per claim: verdict, evidence, figure ids, scripts
  notes/claims-tested.md                   the readable version

Verdicts:  CONFIRMED  the data supports the claim's central statement
           PARTLY     some part holds, or only a proxy can be tested, or the data gives a range
           REFUTED    the data contradicts the central statement
           NOT TESTABLE  the pack holds nothing that can speak to it (shown with whatever context exists)
Every number in the evidence is read from a figures file by id, so it cannot drift from the scripts.

Run: python analysis/05_claims_tested.py   (after clean.py, 02_stage_times.py, 04_query_forensics.py)
"""
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
DATA = ROOT / "pack" / "data"
b = pd.read_parquet(OUT / "bills_clean.parquet")
q = pd.read_csv(OUT / "query_forensics.csv", parse_dates=["raised_date", "resolved_date"])
c = {}  # figures computed here


def cf(k, val, desc=""):
    c[k] = (val, desc)


# ------------------------------------------------------------------ what this script computes
dd = lambda a, z: (b[z] - b[a]).dt.days
b["has_q"] = b.bill_id.isin(q.bill_id)
b["sw"] = b.property_head_signed_date.dt.day_name()
b["lag"] = dd("property_head_signed_date", "ho_received_date")
g = b.groupby("sw").lag.agg(["min", "max"])
cf("c.courier.weekdays_with_a_single_lag", int((g["min"] == g["max"]).sum()), "signing weekdays on which every bill took the same number of days to reach head office")
for d_ in ("Wednesday", "Thursday", "Friday"):
    cf(f"c.courier.lag_signed_{d_.lower()}", int(g.loc[d_, "min"]), f"days from head's signature to HO receipt when signed on a {d_}")
cf("c.courier.lag_min", int(b.lag.min())); cf("c.courier.lag_max", int(b.lag.max()))
posted = b.posted_date.notna()
cf("c.packet.posted_before_ho_received", int((b.posted_date < b.ho_received_date).sum()), "bills posted before the packet reached head office")
cf("c.packet.posted_bills", int(posted.sum()))
cf("c.packet.received_bills", int(b.ho_received_date.notna().sum()), "bills whose packet has a head-office receipt date")
b["desk_to_signed"] = dd("desk_received_date", "property_head_signed_date")
b["sign_step"] = dd("property_verified_date", "property_head_signed_date")
b["desk_to_ho"] = dd("desk_received_date", "ho_received_date")
cf("c.prop.desk_to_signed_mean", round(b.desk_to_signed.mean(), 2), "days from desk to head's signature, mean")
cf("c.prop.desk_to_signed_median", float(b.desk_to_signed.median()))
cf("c.prop.desk_to_signed_p90", float(b.desk_to_signed.quantile(0.9)))
cf("c.prop.sign_step_mean", round(b.sign_step.mean(), 2), "days from verified to head's signature, mean")
cf("c.prop.sign_step_median", float(b.sign_step.median())); cf("c.prop.sign_step_max", int(b.sign_step.max()))
cf("c.prop.sign_step_le2_pct", round(100 * (b.sign_step <= 2).mean(), 1), "% signed within 2 days of verification")
cf("c.prop.desk_to_ho_mean", round(b.desk_to_ho.mean(), 2), "days from desk to head-office receipt, mean")
cf("c.prop.desk_to_signed_le2_pct", round(100 * (b.desk_to_signed <= 2).mean(), 1), "% of bills leaving property (signed) within 2 days of the desk")
cf("c.prop.signed_on_weekend_pct", round(100 * b.property_head_signed_date.dt.dayofweek.ge(5).mean(), 1), "% of signatures dated Saturday or Sunday")
b["recv_to_post"] = dd("ho_received_date", "posted_date")
b["recv_to_pick"] = dd("ho_received_date", "ho_picked_date")
b["pick_to_post"] = dd("ho_picked_date", "posted_date")
x = b[posted]
cf("c.ho.recv_to_post_mean", round(x.recv_to_post.mean(), 1), "days at head office from receipt to posting, mean")
cf("c.ho.recv_to_post_median", float(x.recv_to_post.median()))
cf("c.ho.recv_to_post_gt14_pct", round(100 * (x.recv_to_post > 14).mean(), 1), "% of posted bills more than 14 days from HO receipt to posting")
cf("c.ho.recv_to_post_gt21_pct", round(100 * (x.recv_to_post > 21).mean(), 1))
cf("c.ho.recv_to_post_gt28_pct", round(100 * (x.recv_to_post > 28).mean(), 1))
cf("c.ho.recv_to_post_queried_median", float(x[x.has_q].recv_to_post.median()), "same, bills with a query")
cf("c.ho.recv_to_post_queried_mean", round(x[x.has_q].recv_to_post.mean(), 1))
cf("c.ho.recv_to_post_clean_median", float(x[~x.has_q].recv_to_post.median()), "same, bills with no query")
cf("c.ho.recv_to_post_clean_gt14_pct", round(100 * (x[~x.has_q].recv_to_post > 14).mean(), 1))
cf("c.ho.recv_to_pick_gt14_pct", round(100 * (b.recv_to_pick.dropna() > 14).mean(), 1), "% of picked bills that waited more than 14 days for a verifier")
cf("c.ho.clean_pick_to_post_mean", round(x[~x.has_q].pick_to_post.mean(), 2), "days from pick to posting, bills with no query, mean")
cf("c.ho.clean_pick_to_post_median", float(x[~x.has_q].pick_to_post.median())); cf("c.ho.clean_pick_to_post_max", int(x[~x.has_q].pick_to_post.max()))
# verifier load
v = b[b.ho_verifier != ""].copy()
cnt = v.ho_verifier.value_counts().sort_index()
for k, n in cnt.items():
    cf(f"c.ver.{k}.bills", int(n), f"bills handled by {k}")
    cf(f"c.ver.{k}.share_pct", round(100 * n / cnt.sum(), 1))
    cf(f"c.ver.{k}.queue_days", round(v[v.ho_verifier == k].recv_to_pick.mean(), 2), f"mean days waiting for {k} to pick up")
    cf(f"c.ver.{k}.query_pct", round(100 * v[v.ho_verifier == k].has_q.mean(), 1), f"% of {k}'s bills with a query")
    cf(f"c.ver.{k}.mean_amount", round(v[v.ho_verifier == k].amount_inr.mean(), 0), f"mean bill amount for {k}")
    cf(f"c.ver.{k}.residential_pct", round(100 * (v[v.ho_verifier == k].property_type == "Residential Society").mean(), 1))
cf("c.ver.total_with_verifier", int(cnt.sum()))
pv = v.groupby("property_code").ho_verifier.nunique()
cf("c.ver.properties_served_by_all_five", int((pv == 5).sum()), "properties served by all five verifiers")
cf("c.ver.properties", len(pv))
top = v.groupby(["property_code", "ho_verifier"]).size().unstack(fill_value=0)
cf("c.ver.properties_where_AP1_is_main", int((top.idxmax(axis=1) == "AP-1").sum()), "properties where AP-1 handles the most bills")
cf("c.ver.AP1_min_share_in_a_property_pct", round(100 * (top["AP-1"] / top.sum(axis=1)).min(), 1))
cf("c.ver.AP1_max_share_in_a_property_pct", round(100 * (top["AP-1"] / top.sum(axis=1)).max(), 1))
oth = [k for k in cnt.index if k != "AP-1"]
cf("c.ver.other_queue_min", round(min(c[f"c.ver.{k}.queue_days"][0] for k in oth), 2)); cf("c.ver.other_queue_max", round(max(c[f"c.ver.{k}.queue_days"][0] for k in oth), 2))
# weekday and month-start load
pw = b.ho_picked_date.dt.day_name().value_counts()
for d_ in ("Monday", "Tuesday", "Saturday"):
    cf(f"c.load.picked_{d_.lower()}", int(pw[d_]), f"bills picked up on a {d_}")
cf("c.load.picked_mean_per_weekday", round(pw.mean(), 0), "mean bills picked up per weekday")
wk = b.groupby("ho_received_date").size().to_frame("n")
wk["dom"] = wk.index.day
bk = wk.groupby(pd.cut(wk.dom, [0, 7, 14, 21, 31], labels=["1-7", "8-14", "15-21", "22-31"]), observed=True).n.mean()
for k, val in bk.items():
    cf(f"c.load.per_friday_days_{k}", round(float(val), 0), f"bills reaching head office per Friday, Fridays on days {k} of the month")
manp = b.category.isin(["Security Manpower", "Housekeeping Manpower", "Landscaping"])
b["rb"] = pd.cut(b.ho_received_date.dt.day, [0, 14, 31], labels=["1-14", "15-31"])
for k, gg in b.groupby("rb", observed=True):
    cf(f"c.load.manpower_share_received_days_{k}", round(100 * manp[gg.index].mean(), 1), f"% of bills reaching HO on days {k} that are manpower (security, housekeeping, landscaping)")
    cf(f"c.load.queue_days_received_{k}", round(gg.recv_to_pick.mean(), 2))
d10 = b.invoice_date.dt.day <= 10
cf("c.load.invoiced_first10_manpower_pct", round(100 * manp[d10].mean(), 1), "% of bills invoiced on days 1 to 10 that are manpower")
cf("c.load.invoiced_after10_manpower_pct", round(100 * manp[~d10].mean(), 1))
cf("c.load.invoiced_first10_share_pct", round(100 * d10.mean(), 1), "% of all bills invoiced on days 1 to 10")
# work orders
wo = b.drop_duplicates("wo_id")[["wo_id", "wo_valid_from", "wo_valid_to", "wo_approved_value_inr", "wo_billed_value_inr", "category"]].copy()
wo["dur"] = (wo.wo_valid_to - wo.wo_valid_from).dt.days
cf("c.wo.duration_median_days", float(wo.dur.median()), "median validity of a work order in days")
cf("c.wo.duration_330_400_pct", round(100 * wo.dur.between(330, 400).mean(), 1), "% of work orders valid for 330 to 400 days")
cf("c.wo.duration_ge300_pct", round(100 * (wo.dur >= 300).mean(), 1))
ob = (wo.wo_billed_value_inr > wo.wo_approved_value_inr).groupby(wo.category).mean() * 100
cf("c.wo.overbilled_pct_min_category", round(float(ob.min()), 1)); cf("c.wo.overbilled_pct_max_category", round(float(ob.max()), 1))
cf("c.wo.overbilled_pct_security", round(float(ob["Security Manpower"]), 1)); cf("c.wo.overbilled_pct_housekeeping", round(float(ob["Housekeeping Manpower"]), 1))
inv = b[b.doc_type == "invoice"].sort_values(["wo_id", "invoice_date", "bill_id"]).copy()
inv["cum"] = inv.groupby("wo_id").amount_inr.cumsum()
crossed = inv[inv.cum > inv.wo_approved_value_inr].groupby("wo_id").agg(cd=("invoice_date", "min"), vt=("wo_valid_to", "first"))
cf("c.wo.crossed_approved_value", len(crossed), "work orders whose cumulative invoices pass approved value")
cf("c.wo.crossed_before_valid_to", int((crossed.cd < crossed.vt).sum()), "...before their valid_to date")
cf("c.wo.crossed_before_valid_to_pct", round(100 * (crossed.cd < crossed.vt).mean(), 1))
appr = wo.set_index("wo_id").wo_approved_value_inr
for dt_, lab in [("2025-12-31", "dec"), ("2026-02-28", "feb")]:
    t = inv[inv.invoice_date <= dt_].groupby("wo_id").amount_inr.sum()
    cf(f"c.wo.over_approved_by_{lab}", int((t > appr.reindex(t.index)).sum()), f"work orders past approved value by invoice date {dt_}")
cf("c.wo.crossed_in_jan_feb", c["c.wo.over_approved_by_feb"][0] - c["c.wo.over_approved_by_dec"][0], "work orders that crossed approved value during Jan and Feb 2026")
cm = crossed.cd.dt.to_period("M").value_counts().sort_index()
cf("c.wo.crossings_per_month_apr_sep_max", int(cm.loc["2025-04":"2025-09"].max()), "most work orders crossing approved value in any month Apr to Sep 2025")
cf("c.wo.crossings_per_month_oct_feb_min", int(cm.loc["2025-10":"2026-02"].min()), "fewest in any month Oct 2025 to Feb 2026")
e = q[q.rule_id == "R26"].drop(columns=["desk_received_date"]).merge(b[["bill_id", "wo_valid_to", "desk_received_date"]], on="bill_id")
reports = pd.date_range("2025-04-01", "2026-04-01", freq="MS")  # procurement's report: orders ending in the next 60 days, run on the 1st
e["covered"] = e.wo_valid_to.apply(lambda t: bool(((t - reports).days.to_series().between(0, 60)).any()))
cf("c.wo.expiry_query_orders_on_a_60day_report", int(e.covered.sum()), "orders behind an expiry query that fall inside a 'next 60 days' list run on the 1st of a month from 1 Apr 2025")
cf("c.wo.expiry_days_between_expiry_and_desk_median", float((e.desk_received_date - e.wo_valid_to).dt.days.median()), "median days from the order's expiry to the bill reaching the desk")
g3 = q[q.rule_id == "R03"].groupby(q.raised_date.dt.to_period("M")).size()
cf("c.gl.queries_per_month", round(float(g3.iloc[1:-1].mean()), 1), "GL-does-not-match queries per month (first and last, partial, months left out)")
g4 = q[q.query_category == "GL or cost centre"].groupby(q.raised_date.dt.to_period("M")).size()
cf("c.gl.gl_or_cc_per_month", round(float(g4.iloc[1:-1].mean()), 1), "GL or cost-centre queries per month")
w = q[q.category_clean == "WO balance or validity"].days_open.dropna()
cf("c.woq.closed", len(w)); cf("c.woq.le7_pct", round(100 * (w <= 7).mean(), 1), "% of work-order queries closed within 7 days of being raised")
cf("c.woq.le14_pct", round(100 * (w <= 14).mean(), 1)); cf("c.woq.gt30_pct", round(100 * (w > 30).mean(), 1), "% open longer than 30 days")
cf("c.woq.median", float(w.median())); cf("c.woq.p90", float(w.quantile(0.9))); cf("c.woq.max", int(w.max()))
# security vendors
sec = b[(b.category == "Security Manpower") & (b.doc_type == "invoice") & b.paid_date.notna()].copy()
sec["tot"] = (sec.paid_date - sec.invoice_date).dt.days
cf("c.sec.clean_median", float(sec[~sec.has_q].tot.median()), "security bills with no query: median days invoice to paid")
cf("c.sec.queried_median", float(sec[sec.has_q].tot.median()), "security bills with a query: median days")
cf("c.sec.gt60_pct", round(100 * (sec.tot > 60).mean(), 1), "% of security bills taking more than 60 days")
oc = sec[(sec.invoice_date >= "2025-10-01") & (sec.invoice_date < "2025-11-01")]
cf("c.sec.oct_mean", round(oc.tot.mean(), 1), "security bills invoiced Oct 2025: mean days"); cf("c.sec.other_months_mean", round(sec[sec.invoice_date.dt.month != 10].tot.mean(), 1))
cf("c.sec.oct_gt60", int((oc.tot > 60).sum()), "...of which over 60 days"); cf("c.sec.oct_n", len(oc))
sv = b[b.category == "Security Manpower"].groupby("vendor_id").agg(props=("property_code", "nunique"), ms=("msme_status", "first"))
cf("c.sec.vendors", len(sv)); cf("c.sec.vendor_max_properties", int(sv.props.max()), "most properties any security vendor serves")
cf("c.sec.vendors_msme_blank", int((sv.ms == "Unknown").sum()))
cf("c.sec.queries", int((q.category == "Security Manpower").sum())); cf("c.sec.wo_queries", int(((q.category == "Security Manpower") & (q.category_clean == "WO balance or validity")).sum()))
ig = q[q.rule_id == "R05"].merge(b[["bill_id", "vendor_state", "property_state"]], on="bill_id")
cf("c.igst.haryana_haryana", int(((ig.vendor_state == "Haryana") & (ig.property_state == "Haryana")).sum()), "IGST queries where vendor and property are both in Haryana")
# attendance
A = DATA / "attendance-sample"
bio = pd.read_csv(A / "biometric_export.csv", dtype=str, keep_default_na=False)
gate = pd.read_csv(A / "gate_register_transcribed.csv", dtype=str, keep_default_na=False)
cl = pd.read_csv(A / "vendor_claim.csv", dtype=str)
cl["claim"] = cl.days_claimed.astype(int)
cl["bio"] = cl.person_id.map(bio.groupby("guard_id").date.nunique()).fillna(0).astype(int)
cl["gate"] = cl.person_id.map(gate.groupby("person_id").date.nunique()).fillna(0).astype(int)
cf("c.att.claim_days", int(cl.claim.sum())); cf("c.att.biometric_days", int(cl.bio.sum())); cf("c.att.gate_days", int(cl.gate.sum()))
cf("c.att.people", len(cl)); cf("c.att.claim_gt_biometric_people", int((cl.claim > cl.bio).sum()), "people whose claimed days exceed biometric days")
cf("c.att.claim_gt_gate_people", int((cl.claim > cl.gate).sum()), "people whose claimed days exceed gate-register days")
cf("c.att.claim_minus_gate_days", int((cl.claim - cl.gate).clip(lower=0).sum()), "claimed days not backed by the gate register")
cf("c.att.relievers", int(cl.person_id.str.startswith("R-").sum())); cf("c.att.relievers_in_biometric", int(((cl.bio > 0) & cl.person_id.str.startswith("R-")).sum()))
bset, gset = set(zip(bio.guard_id, bio.date)), {k for k in zip(gate.person_id, gate.date) if k[0].startswith("G")}
cf("c.att.guard_days_in_gate_not_biometric", len(gset - bset), "guard-days in the gate register with no biometric punch")
# the December housekeeping case (commercial executive and procurement both describe it)
hk = b[(b.category == "Housekeeping Manpower") & (b.property_type == "Residential Society")].merge(
    q[q.category_clean == "WO balance or validity"][["bill_id", "resolved_date"]].rename(columns={"resolved_date": "q_res"}), on="bill_id")
case = hk[(hk.desk_received_date == "2026-01-05") & hk.q_res.between("2026-02-11", "2026-02-14")]
cf("c.case.december_housekeeping_matches", len(case), "bills matching the described December housekeeping case (desk 5 Jan 2026, work-order query closed 11 to 14 Feb)")
# claims on the property checklist
p_cov = q.rule_id.isin(["R08", "R13", "R17", "R20", "R21", "R22", "R23"])
cf("c.q.on_property_checklist_items", int(p_cov.sum()), "queries on items the property checklist P1 to P9 already requires")
cf("c.q.on_property_checklist_items_pct", round(100 * p_cov.mean(), 1))
cf("c.dup.bills_in_same_vendor_invoice_pairs", int(b.f_dup_vendor_invoice.sum())); cf("c.dup.pct_of_bills", round(100 * b.f_dup_vendor_invoice.mean(), 2))
ov = pd.read_csv(OUT / "stage_times.csv").query("dimension == 'overall'").set_index("stage_order").cal_mean
cf("c.typing.share_of_central_ap", round(100 * ov[6] / (ov[5] + ov[6] + ov[7]), 1),
   "AP verification (no query open) as % of the days a bill spends in central AP: queue + verify + query")
cf("c.ho.central_ap_plus_treasury", round(float(ov[5] + ov[6] + ov[7] + ov[8]), 2), "mean days from head-office receipt to paid: central AP stages plus the payment run")
cf("c.prop.courier_plus_property", round(float(ov[2] + ov[3] + ov[4]), 2), "mean days in the property's check, signature and courier stages")
cf("c.igst.inter_state", int(len(ig) - (ig.vendor_state == ig.property_state).sum()), "IGST queries where the extract says vendor and property are in different states")
cf("c.att.claim_minus_biometric_days", int((cl.claim - cl.bio).clip(lower=0).sum()), "claimed days not backed by biometric punches")
cf("c.wo.over_dec_share_of_feb_pct", round(100 * c["c.wo.over_approved_by_dec"][0] / c["c.wo.over_approved_by_feb"][0], 1),
   "% of the work orders past approved value by 28 Feb that were already past it on 31 Dec")
cf("c.sec.wo_queries_pct", round(100 * c["c.sec.wo_queries"][0] / c["c.sec.queries"][0], 1), "% of queries on security bills that are work-order queries")

pd.DataFrame([dict(id=k, value=v_, description=d_) for k, (v_, d_) in c.items() if v_ is not None]).to_csv(OUT / "figures_claims_tested.csv", index=False)

# ------------------------------------------------------------------ lookup of every figure used in the evidence
SRC, F = {}, {}
for fname, script in [("figures.csv", "clean.py"), ("figures_stage_times.csv", "02_stage_times.py"),
                      ("figures_query_forensics.csv", "04_query_forensics.py"), ("figures_claims_tested.csv", "05_claims_tested.py")]:
    for r in pd.read_csv(OUT / fname, keep_default_na=False).itertuples():
        F[r.id] = r.value
        SRC[r.id] = script
ledger = {}
for line in (ROOT / "notes" / "understanding.md").read_text(encoding="utf-8").splitlines():
    if re.match(r"^\| L\d+ \|", line):
        p = [s.strip() for s in line.strip().strip("|").split(" | ")]
        ledger[p[0]] = dict(id=p[0], claim=p[1], who=p[2], source=p[3])
assert len(ledger) == 57
SUPP = {
    "S1": dict(id="S1", claim="One of them is very senior, she has been here twelve years. She takes the big properties and anything complicated. The other four share the rest.", who="AP lead", source="transcripts/02-central-ap-lead.md"),
    "S2": dict(id="S2", claim="Monday and Tuesday are heavy because the Friday packets are waiting.", who="AP lead", source="transcripts/02-central-ap-lead.md"),
    "S3": dict(id="S3", claim="Month start is worst.", who="AP lead", source="transcripts/02-central-ap-lead.md"),
}
_tx = re.sub(r"\s+", " ", (ROOT / "pack/context/transcripts/02-central-ap-lead.md").read_text(encoding="utf-8").replace("*", ""))
for s_ in SUPP.values():
    assert s_["claim"] in _tx, s_["claim"]

used: list[str] = []


def n(i, fmt="{:g}"):
    used.append(i)
    return fmt.format(float(F[i]))


pct = lambda i: n(i, "{:.1f}%")           # value already a percentage
sh = lambda i: "{:.1f}%".format(100 * float(n(i)))  # value is a fraction
sh0 = lambda i: "{:.0f}%".format(100 * float(n(i)))
d1 = lambda i: n(i, "{:.1f}")
d0 = lambda i: n(i, "{:,.0f}")

CONF, PART, REF, NT = "CONFIRMED", "PARTLY", "REFUTED", "NOT TESTABLE"
R, R_ids = {}, {}


def claim(i, verdict, text):
    R[i] = (verdict, text)
    R_ids[i] = list(dict.fromkeys(used))
    used.clear()


claim("L1", REF, f"A bill takes a mean of {d1('overall.s99.cal_mean')} days from invoice date to paid (median {d0('policy.all.invoice.median')}, p90 {d0('policy.all.invoice.p90')}); "
      f"from the desk date it is {d1('policy.all.desk_received.mean')}. Only {pct('policy.all.invoice.pct_in_cfo_band_45_to_50')} of bills land in the 45 to 50 band. "
      f"What survives is 'sometimes more': {pct('policy.all.invoice.pct_over_45')} take over 45 days and {pct('policy.all.invoice.pct_over_60')} over 60. "
      f"Invoices dated to 31 Jan 2026, which have all had time to be paid, give the same picture (mean {d1('policy.matured.invoice.mean')}).")
claim("L2", PART, f"Head office, from receipt to paid (central AP plus the payment run), holds {d1('c.ho.central_ap_plus_treasury')} of the {d1('overall.s99.cal_mean')} days, about half. "
      f"The other half is before head office: vendor to desk {d1('side.1.cal_mean')}, property {d1('side.2.cal_mean')}, courier {d1('side.4.cal_mean')}. "
      f"Inside central AP the biggest piece is the queue before a verifier picks the bill up ({d1('overall.s05.cal_mean')} days), not the work ({d1('overall.s06.cal_mean')}).")
claim("L3", REF, f"{d0('share.bills_with_query')} of {d0('share.bills')} bills have a query: {pct('share.bills_with_query_pct')}, about 1 in 7.6, not 1 in 5. No invoice month exceeds {pct('month.pct_max')}.")
claim("L4", PART, f"By the text of the query the fix sits with the vendor in {pct('side.vendor.primary_pct')} of cases, the largest single side but not a majority. "
      f"Where the text names no alternative owner only {pct('side.vendor.min_pct')} are vendor-side; it reaches {pct('side.vendor.max_pct')} only if every ambiguous query is given to the vendor.")
claim("L5", PART, f"Late payment exists, but its size depends on the clock. Of Micro or Small bills paid, {pct('policy.micro.invoice.pct_over_45')} took over 45 days from the invoice date, "
      f"{pct('policy.micro.desk_received.pct_over_45')} from the desk date and {pct('policy.micro.property_verified.pct_over_45')} from property verification. "
      f"{d0('policy.micro.invoice.n_unpaid')} Micro or Small invoices are still unpaid, {d0('policy.micro.invoice.n_unpaid_already_over_45')} already past 45 days from the invoice date. The tax consequence itself is not in the data.")
claim("L6", PART, f"{d0('msme.vendors_blank')} of {d0('msme.vendors_total')} vendors ({pct('msme.vendors_blank_pct')}) have a blank MSME status, covering {d0('msme.bills_unknown')} bills. "
      "The blanks are real; that they arose because nobody updated the master is not testable.")
claim("L7", CONF, f"None of the {d0('c.packet.posted_bills')} posted bills was posted before its packet reached head office ({d0('c.packet.posted_before_ho_received')} exceptions), and {d0('queries.other_hard_copy_text')} "
      "queries hold a bill because only a scan has arrived. That fits a practice of waiting for the paper; whether it is required by rule or law is not in the data.")
claim("L8", CONF, f"Bills with no query go from AP pick-up to posting in a mean of {d1('c.ho.clean_pick_to_post_mean')} days (median {d0('c.ho.clean_pick_to_post_median')}, longest {d0('c.ho.clean_pick_to_post_max')}). "
      f"From the day the packet arrives it is a median of {d0('c.ho.recv_to_post_clean_median')} days, because of the queue.")
claim("L9", NT, f"The data has dates, not effort. Elapsed pick-to-posting time for bills with no query is a median of {d0('c.ho.clean_pick_to_post_median')} day, consistent with it but saying nothing about minutes.")
claim("L10", PART, f"AP's own verification is {d1('overall.s06.cal_mean')} days of {d1('overall.s99.cal_mean')} ({sh('overall.s06.share')}). But the queue before a verifier starts is {d1('overall.s05.cal_mean')} days, the largest single wait, "
      f"and one verifier carries {pct('c.ver.AP-1.share_pct')} of the bills. What arrives also matters ({pct('share.bills_with_query_pct')} of bills have a query, adding {d1('added.s99')} days each), so AP is fast once it starts, but 'never our speed' ignores the queue.")
claim("L11", PART, f"Typing cannot be measured, only bounded. Active verification is {d1('overall.s06.cal_mean')} days, {pct('c.typing.share_of_central_ap')} of the days a bill spends in central AP, so typing is at most that. "
      f"Queries ({d1('added.days_on_overall_mean')} days on the overall mean) and the queue ({d1('overall.s05.cal_mean')} days) are larger. 'About ten percent' is the right order of magnitude as elapsed time; effort is not in the data.")
claim("L12", PART, f"Every one of the {d0('c.packet.received_bills')} packets received is recorded as reaching head office on a Friday ({d0('weekday.ho_received_not_friday')} on any other day), so 'mostly Friday' is confirmed. "
      "No packet is recorded as arriving on a Monday, so 'sometimes Monday' is not in the data.")
claim("L13", CONF, f"Work order, GL / cost centre and service entry / GRN queries are {d0('side.ap_lead_three_categories')} of {d0('q.rows')} ({pct('side.ap_lead_three_categories_pct')}). "
      f"Property, procurement and head office together are {pct('side.company_side_primary_pct')} on the primary reading and {pct('side.company_side_min_pct')} where the text gives no alternative owner.")
claim("L14", PART, f"{d0('rules.other_queries')} queries ({pct('queries.category_other_pct')}) are labelled Other: a modest share, though {d0('rules.other_relabelled')} of them carry a text that names a real category.")
claim("L15", REF, f"PF/ESIC challan queries have a median of {d0('claim.missing_challan_median_days')} days to resolve, not a week.")
claim("L16", PART, f"Work-order queries have a median of {d0('c.woq.median')} days to resolve, p90 {d0('c.woq.p90')}, longest {d0('c.woq.max')}. {pct('c.woq.gt30_pct')} run past 30 days, so a month happens but is not typical.")
claim("L17", NT, "The query log holds one row per bill (no bill has two), so a stop-at-the-first-error sequence cannot be seen.")
claim("L18", PART, f"IGST-on-intra-state queries ({d0('ev.igst.queries')}) and wrong-rate queries ({d0('ev.taxrate.queries')}, all '12 instead of 18') exist. But the extract puts vendor and property in the same state for only {d0('ev.igst.master_says_same_state')} of the {d0('ev.igst.queries')} IGST queries.")
claim("L19", NT, "A legal question, not a data question (see notes/understanding.md, section 4).")
claim("L20", PART, f"The head's own step is quick: {pct('c.prop.sign_step_le2_pct')} are signed within 2 days of verification (median {d0('c.prop.sign_step_median')}, longest {d0('c.prop.sign_step_max')}). "
      f"But a bill is signed a mean of {d1('c.prop.desk_to_signed_mean')} days after the desk logs it (median {d0('c.prop.desk_to_signed_median')}); only {pct('c.prop.desk_to_signed_le2_pct')} are signed within 2 days of arrival, "
      f"and it then takes {d1('overall.s04.cal_mean')} more days to reach head office.")
claim("L21", PART, f"From receipt to posting a bill spends a median of {d0('c.ho.recv_to_post_median')} days at head office (mean {d1('c.ho.recv_to_post_mean')}). "
      f"{pct('c.ho.recv_to_post_gt14_pct')} take over 14 days and {pct('c.ho.recv_to_post_gt28_pct')} over 28; bills with a query have a median of {d0('c.ho.recv_to_post_queried_median')}. 'Weeks' is true for roughly a quarter, not typically.")
claim("L22", PART, f"The courier is a fixed wait of {d0('c.courier.lag_min')} to {d0('c.courier.lag_max')} days (mean {d1('overall.s04.cal_mean')}, {sh('overall.s04.share')} of the total). "
      f"It is smaller than central AP ({d1('side.5.cal_mean')} days) but not 'a few days here and there': property plus courier is {d1('c.prop.courier_plus_property')} days.")
claim("L23", PART, f"{d0('c.q.on_property_checklist_items')} queries ({pct('c.q.on_property_checklist_items_pct')}) are on items the property checklist already requires (GSTIN, company name, rate, attendance signature, PF/ESIC, gate stamp, service report). "
      "The rest are head-office-only checks or problems the property could not know. The data cannot tell a repeated question from a check the property missed.")
claim("L24", NT, "No field records which vendor a packet was logged under.")
claim("L25", CONF, f"{d0('c.wo.crossed_approved_value')} work orders ({pct('wo.billed_gt_approved_pct')}) are billed past their approved value, and {d0('c.wo.crossed_before_valid_to')} of them ({pct('c.wo.crossed_before_valid_to_pct')}) passed it before their validity ended. "
      f"That it comes from added guards is not testable, and manpower is not special: the share runs {pct('c.wo.overbilled_pct_min_category')} to {pct('c.wo.overbilled_pct_max_category')} across categories (security {pct('c.wo.overbilled_pct_security')}, housekeeping {pct('c.wo.overbilled_pct_housekeeping')}).")
claim("L26", CONF, f"All {d0('c.packet.received_bills')} packets received reach head office on a Friday, and the lag from the head's signature is set entirely by the weekday of signing ({d0('c.courier.weekdays_with_a_single_lag')} of 7 weekdays have exactly one lag). "
      f"Signed on a Wednesday it takes {d0('c.courier.lag_signed_wednesday')} days, on a Thursday {d0('c.courier.lag_signed_thursday')}: the Thursday cut-off is real, and a bill signed on a Thursday waits for the following week's courier.")
claim("L27", REF, f"The head signs within {d0('c.prop.sign_step_max')} days of verification on every bill (median {d0('c.prop.sign_step_median')}), faster than a once-or-twice-a-week batch would allow. "
      f"Caution: {pct('c.prop.signed_on_weekend_pct')} of signature dates fall on a Saturday or Sunday, so the register's signing dates should not be over-read.")
claim("L28", NT, "Nothing records when anyone noticed a work order running out.")
claim("L29", CONF, f"Work orders per property run from {d0('wo.per_property_min')} to {d0('wo.per_property_max')} (median {d0('wo.per_property_median')}).")
claim("L30", CONF, f"All {d0('c.att.relievers')} relievers claimed on the bill are absent from the biometric file ({d0('c.att.relievers_in_biometric')} present) and appear in the gate register ({d0('attendance.gate_rows_reliever')} gate rows).")
claim("L31", NT, "The attendance files identify people by ID (G101, R-901), not by name, so spelling differences cannot be seen.")
claim("L32", NT, f"Hours are not in the data. The size of the problem in the February sample: {d0('c.att.claim_gt_biometric_people')} of {d0('c.att.people')} people claim more days than biometric shows, "
      f"but only {d0('c.att.claim_gt_gate_people')} claim more than the gate register shows. A three-way match leaves {d0('c.att.claim_gt_gate_people')} people to review.")
claim("L33", NT, f"The data has no amendment date, so the amendment step cannot be timed. The whole query cycle (which includes the paper) closes within 7 days for {pct('c.woq.le7_pct')} of work-order queries and within 14 for {pct('c.woq.le14_pct')}; the median is {d0('c.woq.median')}.")
claim("L34", NT, f"No bill in the data matches the described case (housekeeping, residential, desk 5 Jan 2026, work-order query closed 11 to 14 Feb): {d0('c.case.december_housekeeping_matches')} matches. The query log also holds one query per bill, whereas the case had three.")
claim("L35", PART, f"{d0('c.wo.expiry_query_orders_on_a_60day_report')} of the {d0('ev.expiry_queries')} orders behind an expiry query would have been on a 'next 60 days' list run on the 1st of a month since April 2025, so expiry is predictable. "
      f"The bills reached the desk a median of {d0('c.wo.expiry_days_between_expiry_and_desk_median')} days after expiry, and {d0('wo.bills_after_valid_to')} bills are dated after their order's expiry. Whether anyone opens the report is not in the data.")
claim("L36", REF, f"There are {d1('c.gl.queries_per_month')} 'GL does not match' queries a month, not two or three ({d1('c.gl.gl_or_cc_per_month')} a month if cost-centre queries are included). They are raised on bills, which may follow older orders, so the comparison is approximate.")
claim("L37", NT, f"Amendment requests are not in the data. Proxy: work-order queries raised 8 to 15 Feb 2026 number {d0('wo_cluster.feb2026_week2_count')}, against a mean of {d1('wo_cluster.mean_4day_count')} in any 4 days; no February spike.")
claim("L38", PART, f"{d0('c.wo.over_approved_by_dec')} work orders were already past their approved value by 31 Dec 2025 and {d0('c.wo.over_approved_by_feb')} by 28 Feb: {d0('c.wo.crossed_in_jan_feb')} crossed in January and February. "
      f"Crossings ran at most {d0('c.wo.crossings_per_month_apr_sep_max')} a month from April to September and at least {d0('c.wo.crossings_per_month_oct_feb_min')} a month from October, which fits balances being eaten from the festival months. "
      f"But {pct('c.wo.over_dec_share_of_feb_pct')} of those over by February were already over in December.")
claim("L39", PART, f"Median validity is {d0('c.wo.duration_median_days')} days (about 17 months); {pct('c.wo.duration_ge300_pct')} are at least 300 days but only {pct('c.wo.duration_330_400_pct')} are 330 to 400 days. They are for a year or more, and the extract may show extended dates.")
claim("L40", PART, "Same evidence as L6.")
claim("L41", CONF, f"Security bills with no query take a median of {d0('c.sec.clean_median')} days from invoice to paid, about five weeks. Bills with a query take a median of {d1('c.sec.queried_median')}, and {pct('c.sec.gt60_pct')} of all security bills take over 60 days.")
claim("L42", NT, f"No security vendor in the data serves six properties (the most is {d0('c.sec.vendor_max_properties')}), so he cannot be identified. The situation he describes does exist: {d0('c.sec.vendors_msme_blank')} of {d0('c.sec.vendors')} security vendors have a blank MSME status.")
claim("L43", PART, f"{d0('c.igst.haryana_haryana')} of the {d0('ev.igst.queries')} IGST queries are on bills where vendor and property are both in Haryana, his exact case. For the other {d0('c.igst.inter_state')} the extract says the supply is inter-state.")
claim("L44", CONF, f"Work-order queries are {d0('c.sec.wo_queries')} of {d0('c.sec.queries')} on security bills ({pct('c.sec.wo_queries_pct')}) and {d0('side.procurement.primary')} of all {d0('q.rows')} queries.")
claim("L45", PART, f"In the February sample vendors claim {d0('c.att.claim_days')} days against {d0('c.att.biometric_days')} in the biometric file and {d0('c.att.gate_days')} in the gate register. "
      f"A property that trusts biometric alone would cut {d0('c.att.claim_minus_biometric_days')} days; against the gate register only {d0('c.att.claim_minus_gate_days')}. Whether cuts are made is not in the data.")
claim("L46", PART, f"{d0('c.sec.oct_gt60')} of {d0('c.sec.oct_n')} security bills invoiced in October 2025 took over 60 days, so 'two months' happens. But October is no worse than other months (mean {d1('c.sec.oct_mean')} against {d1('c.sec.other_months_mean')} days).")
claim("L47", NT, "There is no call log. The survey's 'three times per bill' is the only figure.")
claim("L48", NT, "A past pilot's accuracy; not in the pack. Our own reader can be measured on the 40 inbox bills.")
claim("L49", CONF, f"AP verification with no query open is {d1('overall.s06.cal_mean')} days of {d1('overall.s99.cal_mean')} ({sh('overall.s06.share')}). Removing it entirely would save at most that. "
      f"The days are in waiting: {sh0('overall.s97.share')} of the total.")
claim("L50", CONF, f"After fixing formats the register covers {d0('property_code.distinct_clean')} properties, but as typed it holds {d0('property_code.distinct_raw')} different property_code strings and {d0('property_code.non_canonical_rows')} rows needed fixing. The merged-registers problem is visible.")
claim("L51", PART, f"The extract holds vendor_master ({d0('rows.sap.vendor_master')} rows), work_orders ({d0('rows.sap.work_orders')}), properties ({d0('rows.sap.properties')}), posted_invoices ({d0('rows.sap.posted_invoices')}) and the empty parsed_bill ({d0('rows.sap.parsed_bill')}). "
      "None is a service-entry table, although the IT head says service entries can be read over RFC. Reading is approved; the extract is narrower than described.")
claim("L52", NT, "Not testable. The survey puts portal preference at 9%.")
claim("L53", NT, "The data records dates, not what vendors were told.")
claim("L54", CONF, f"Queries are raised a mean of {d1('timing.days_desk_to_raised.mean')} days after the bill reaches the desk (median {d0('timing.days_desk_to_raised.median')}, never sooner than {d0('timing.min_desk_to_raised')}), and {d1('timing.days_ho_received_to_raised.mean')} days after head office receives it.")
claim("L55", PART, f"{d0('c.dup.bills_in_same_vendor_invoice_pairs')} bills ({d1('c.dup.pct_of_bills')}%) share a vendor and invoice number with another bill, and {d0('ev.dup_queries')} queries are raised as duplicates. Where a bill was delivered cannot be seen, so the survey's 33% of vendors cannot be compared.")
claim("L56", NT, "The register has no paid-amount column.")
claim("L57", PART, "Same evidence as L5: the policy limit is breached for a share of bills that depends on which date starts the clock.")
claim("S1", PART, f"One verifier does carry the load: AP-1 handled {pct('c.ver.AP-1.share_pct')} of bills ({d0('c.ver.AP-1.bills')}), the other four {pct('c.ver.AP-2.share_pct')}, {pct('c.ver.AP-3.share_pct')}, {pct('c.ver.AP-4.share_pct')} and {pct('c.ver.AP-5.share_pct')}. "
      f"But not by property: all {d0('c.ver.properties_served_by_all_five')} of {d0('c.ver.properties')} properties are served by all five verifiers, AP-1 is the main one at {d0('c.ver.properties_where_AP1_is_main')} of them ({pct('c.ver.AP1_min_share_in_a_property_pct')} to {pct('c.ver.AP1_max_share_in_a_property_pct')} share), "
      f"and the property mix and query rate are much the same ({pct('c.ver.AP-1.query_pct')} of AP-1's bills have a query against {pct('c.ver.AP-2.query_pct')} to {pct('c.ver.AP-4.query_pct')}). "
      f"AP-1's bills wait {d1('c.ver.AP-1.queue_days')} days for pick-up against {d1('c.ver.other_queue_min')} to {d1('c.ver.other_queue_max')} for the others. The data does not say AP-1 is the senior verifier.")
claim("S2", PART, f"Pick-ups are busiest early in the week ({d0('c.load.picked_tuesday')} on Tuesdays, {d0('c.load.picked_monday')} on Mondays, against a mean of {d0('c.load.picked_mean_per_weekday')} a weekday and {d0('c.load.picked_saturday')} on Saturdays), but modestly, and bills are picked up on all seven days.")
claim("S3", REF, f"Head office receives {d0('c.load.per_friday_days_1-7')} and {d0('c.load.per_friday_days_8-14')} bills per Friday in the first two weeks of the month and {d0('c.load.per_friday_days_15-21')} and {d0('c.load.per_friday_days_22-31')} in the second half; "
      f"manpower is {pct('c.load.manpower_share_received_days_1-14')} of arrivals in the first half and {pct('c.load.manpower_share_received_days_15-31')} in the second. Manpower bills are invoiced early ({pct('c.load.invoiced_first10_manpower_pct')} of bills dated the 1st to 10th) but take two to three weeks to arrive. "
      f"Waiting time for a verifier hardly varies ({d1('c.load.queue_days_received_1-14')} against {d1('c.load.queue_days_received_15-31')} days).")

assert set(R) == set(ledger) | set(SUPP), set(ledger) | set(SUPP) ^ set(R)
R_ids["L40"], R_ids["L57"] = R_ids["L6"], R_ids["L5"]  # "same evidence as" claims share the figures

# Basis of the evidence shown in each row:
#   measured              a direct count or statistic on the thing the claim states
#   estimated from proxy  the number is a stand-in for something the data does not record (elapsed days for effort, text rules for cause,
#                         a simulated report window, ...) and rests on a stated assumption
#   reported only         nothing in the pack bears on it; the claim, or a survey figure, is all there is
M, E, RO = "measured", "estimated from proxy", "reported only"
BASIS = {
    "L1": M, "L2": M, "L3": M, "L4": E, "L5": M, "L6": M, "L7": E, "L8": M, "L9": RO, "L10": E, "L11": E, "L12": M, "L13": E, "L14": M,
    "L15": M, "L16": E, "L17": RO, "L18": E, "L19": RO, "L20": M, "L21": M, "L22": M, "L23": E, "L24": RO, "L25": M, "L26": M, "L27": E,
    "L28": RO, "L29": M, "L30": M, "L31": RO, "L32": E, "L33": E, "L34": M, "L35": E, "L36": E, "L37": E, "L38": E, "L39": M, "L40": M,
    "L41": M, "L42": M, "L43": M, "L44": M, "L45": E, "L46": M, "L47": RO, "L48": RO, "L49": E, "L50": M, "L51": M, "L52": RO, "L53": RO,
    "L54": M, "L55": E, "L56": RO, "L57": M, "S1": M, "S2": M, "S3": M,
}
assert set(BASIS) == set(R), set(BASIS) ^ set(R)
rows = []
for i in list(ledger) + list(SUPP):
    base = ledger.get(i) or SUPP[i]
    verdict, text = R[i]
    scripts = sorted({SRC[k] for k in R_ids[i]})
    rows.append(dict(id=i, claim=base["claim"] if base["claim"].startswith('"') else '"' + base["claim"] + '"', who=base["who"], source=base["source"],
                     verdict=verdict, basis=BASIS[i], evidence=text, figure_ids=", ".join(R_ids[i]),
                     scripts=", ".join("analysis/" + s for s in scripts) if scripts else "none (nothing in the pack)"))
res = pd.DataFrame(rows)
res.to_csv(OUT / "claims_tested.csv", index=False)
cnt = res.verdict.value_counts()
print(cnt.to_string())
print(res[["id", "verdict", "scripts"]].to_string(index=False))

# ------------------------------------------------------------------ the readable version
order9 = [("L1", "45 to 50 days"), ("L3", "1 in 5 bills queried"), ("L2", "Time is lost at head office"), ("L11", "Typing is about 10% of AP time"),
          ("L20", "Bills leave the property in 1 to 2 days"), ("L26", "Weekly courier"), ("S1", "AP load by verifier"),
          ("L33", "Amendments take a week once paper is in"), ("L49", "OCR fixed typing, which was not the slow part")]
badge = {CONF: "CONFIRMED", PART: "PARTLY", REF: "REFUTED", NT: "NOT TESTABLE"}
esc = lambda s: str(s).replace("|", "\\|")
bcnt = res.basis.value_counts()
nt = res[res.verdict == NT]
ten = [i for i in nt.id if res.set_index("id").loc[i, "figure_ids"] == ""]   # the claims with no number from the data
six = [i for i in nt.id if i not in ten]
used.clear()

# ---- the ten with no number: is there an honest proxy?
PROXY = {
    "L17": ("No",
            f"The log holds {d0('q.rows')} queries on {d0('q.rows')} bills (repeats: {d0('multi.bills_with_more_than_one_query')}), and AP raises each one a mean {d1('timing.days_pick_to_raised.mean')} day after picking the bill up. "
            "That fits 'stops at the first error' and fits 'checks everything in a day' equally, so it cannot separate them. "
            f"Only a sensitivity can be shown, not an estimate: if a share f of queried bills needed a second round as long as the first, the overall mean would rise by f x {d1('query.mean_days_among_queried')} days x {sh('query.share_of_bills')} = {'%.2f' % (float(F['query.mean_days_among_queried']) * float(F['query.share_of_bills']))} x f days "
            f"(0.27 days for every 10 percentage points). The {sh('query.share_of_bills')} is the share of the {d0('pop.invoices_analysed')} paid invoices that had a query, the population the {d1('overall.s99.cal_mean')}-day mean covers; "
            f"across all {d0('share.bills')} bills the rate is {pct('share.bills_with_query_pct')}. The 10 points is a unit, not a finding.",
            "Every query round per bill, not just the last: AP's own Excel of open queries (the AP lead keeps one) and the query emails, with bill id, round number, date raised, date resolved, reason.",
            "AP lead; central AP verifiers"),
    "L19": ("No",
            "A legal and audit question. Nothing in the pack records what the law or internal audit requires; the payment policy says only that records are kept 'for the period required under GST law'.",
            "A written view from the client's GST or tax adviser, and from internal audit, on whether the original bill must be in hand before posting or only on file afterwards, with the clause relied on.",
            "CFO; internal audit; external tax adviser"),
    "L24": ("No",
            f"The register holds the tracker number given at the desk, not the one head office logged. Every bill's courier gap is set by its signing weekday ({d0('c.courier.weekdays_with_a_single_lag')} of 7 weekdays have exactly one gap), so a mislogged packet would not show as an outlier.",
            "The courier docket register at the property and head office's packet receipt log, both with tracker numbers; for the DG AMC case described, the October and November bill ids.",
            "Property facility desk; central AP; the property head's executive"),
    "L28": ("No",
            f"Nothing records when anyone noticed a work order was running out. The data can only show that a warning was possible: {d0('c.wo.crossed_approved_value')} orders passed their approved value, {d0('c.wo.crossed_before_valid_to')} of them before their validity ended. That is predictability, not discovery.",
            "The SAP log of failed service-entry postings with date, work order and message, for the year; the commercial executives' own trackers; procurement's amendment-request emails with dates.",
            "IT (SAP support partner); commercial executives; procurement"),
    "L31": ("No",
            f"The attendance files hold IDs (G101, R-901), not names, for {d0('attendance.claim_people')} people. Spelling cannot appear.",
            "Photos or scans of the original gate-register pages and the agency's claim sheet for the same month, with names; the biometric master list with registered names.",
            "Security supervisor; commercial executive; the security agency"),
    "L47": ("No",
            "The pack has no call, email or visit counts. The only figures are the survey's 'three times per bill' (document figure) and the agency owner's three or four (interview). Both are reported.",
            "Call logs for central AP and treasury lines, the property facility-desk visitor log, the CFO's EA notebook of escalations, WhatsApp Business inbound counts if any, for three months.",
            "Central AP lead; treasury; CFO's office; property facility desks"),
    "L48": ("No",
            "The pilot's accuracy is not in the pack. Running our reader on the 40 inbox bills would measure a different system and would not bound the pilot's figure.",
            "The pilot's staging-table extract next to the values finally posted, per field, and its acceptance or closure report.",
            "IT head; the OCR vendor"),
    "L52": ("No",
            "A forecast of behaviour. The survey (document figures: 9% prefer a portal, 12% already use one and find it hard) is reported preference, not adoption.",
            "Monthly active use after the employee self-service portal went live, which the IT head cites as the analogue; vendors' usage of other clients' portals if they will share it.",
            "IT head; procurement (vendor survey owner)"),
    "L53": ("No",
            "A perception. The survey's 71% (document figure) is the only number and cannot be checked against records.",
            "The raw survey file (212 responses, question wording, vendor size) and any log of status enquiries.",
            "Procurement (ran the survey); central AP and facility desks (enquiry logs)"),
    "L56": ("No",
            f"The register holds amount and GST but no paid amount. The {d0('amount.credit_notes')} credit notes cannot be matched to invoices (no link field), so set-offs cannot be reconstructed either.",
            "The payment-run file or bank remittance advice per bill: amount paid, TDS deducted, any set-off or credit-note adjustment, for the year.",
            "Treasury; central AP"),
}
assert set(PROXY) == set(ten), set(PROXY) ^ set(ten)
# ---- data to request, for every NOT TESTABLE claim (the ten above, then the six that carry only context numbers)
ASK = {
    "L33": ("The SAP change history of work orders (date, user, field changed: validity, value, rate) for the year, and procurement's tracker sheet with, per amendment: request received, RWA letter received, budget approval, note signed, SAP amendment made.",
            "Procurement; IT", "1", "Times the amendment alone, separate from the paper wait"),
    "L37": ("Procurement's inbox or sheet of amendment requests for February 2026 with dates received.", "Procurement", "1", "Whether the February cluster was real, and how many requests arrive per month"),
    "L34": ("The work-order number or bill id of the December housekeeping case, so it can be traced in SAP and in the register.", "Commercial executive; procurement", "1", "A fully documented example of the amendment chain"),
    "L9": ("A two-week time-and-motion sample with the five verifiers, or SAP posting-session timestamps (screen opened, document saved) per invoice for a month.", "Central AP lead; IT", "1", "Minutes per bill, and so the true share of AP effort that is typing (L9, L10, L11, L49)"),
    "L32": ("A time log or observed sample from one commercial executive during the first week of a month, with the three attendance sources for that month.", "Commercial executive", "2", "Hours spent on attendance matching"),
    "L42": ("The vendor code of the agency, its Udyam certificate email to procurement with the date sent, and the vendor master change history for that code.", "Procurement; the agency", "3", "Whether a certificate sent was ever recorded"),
}
ASK.update({
    "L17": (PROXY["L17"][2], PROXY["L17"][3], "1", "Whether serial queries exist and what they cost"),
    "L19": (PROXY["L19"][2], PROXY["L19"][3], "1", "Whether a scan-first process is allowed (the main design question)"),
    "L24": (PROXY["L24"][2], PROXY["L24"][3], "3", "How often packets are misfiled"),
    "L28": (PROXY["L28"][2], PROXY["L28"][3], "2", "How late work-order exhaustion is discovered"),
    "L31": (PROXY["L31"][2], PROXY["L31"][3], "3", "Whether name matching is needed in the attendance tool"),
    "L47": (PROXY["L47"][2], PROXY["L47"][3], "2", "Status-enquiry volume, and so the value of a status update"),
    "L48": (PROXY["L48"][2], PROXY["L48"][3], "2", "A baseline reader accuracy to beat"),
    "L52": (PROXY["L52"][2], PROXY["L52"][3], "3", "Portal versus messaging"),
    "L53": (PROXY["L53"][2], PROXY["L53"][3], "2", "How strong the vendor-visibility need is"),
    "L56": (PROXY["L56"][2], PROXY["L56"][3], "2", "Unexplained short payments"),
})
assert set(ASK) == set(nt.id), set(ASK) ^ set(nt.id)

md = []
md.append("# Claims tested against the data\n")
md.append("Each claim in the ledger of `notes/understanding.md` (L1 to L57) and three from the AP lead (S1 to S3) is tested against the cleaned data. "
          "The claim wording is verbatim from the ledger or the transcript. Every number comes from a script and is registered in `notes/numbers.md` under the figure ids in `analysis/out/claims_tested.csv`.\n")
md.append("```\npython analysis/clean.py\npython analysis/02_stage_times.py\npython analysis/04_query_forensics.py\npython analysis/05_claims_tested.py   # or: mingw32-make analyse\n```\n")
md.append("**Verdicts.** CONFIRMED: the data supports the central statement. PARTLY: some part holds, only a proxy can be tested, or the answer is a range. "
          "REFUTED: the data contradicts the central statement. NOT TESTABLE: the pack holds nothing that can speak to it. I added the fourth verdict rather than force a call.\n")
md.append("**Basis.** Every row says what kind of evidence its numbers are.\n")
md.append("- **measured**: a direct count or statistic on the thing the claim states.")
md.append("- **estimated from proxy**: the number stands in for something the data does not record (elapsed days for effort, a text rule for cause, a simulated report window), and rests on an assumption stated in the row.")
md.append("- **reported only**: nothing in the pack bears on it. The claim, or a survey figure, is all there is. Where a document figure is quoted it is marked as one.\n")
md.append(f"**Tally of {len(res)} claims.** Verdicts: {cnt.get(CONF, 0)} confirmed, {cnt.get(PART, 0)} partly, {cnt.get(REF, 0)} refuted, {cnt.get(NT, 0)} not testable. "
          f"Basis: {bcnt.get('measured', 0)} measured, {bcnt.get('estimated from proxy', 0)} estimated from proxy, {bcnt.get('reported only', 0)} reported only.\n")
md.append("## What this changes\n")
md.append(f"- **The CFO's two headline numbers are both too high.** A typical bill takes {d1('overall.s99.cal_mean')} days (median {d0('policy.all.invoice.median')}), not 45 to 50, and {pct('share.bills_with_query_pct')} of bills are queried, not one in five. His 'sometimes more' is true: {pct('policy.all.invoice.pct_over_45')} take over 45 days.")
md.append(f"- **Head office holds about half the days, but waiting is most of it.** Of the {d1('overall.s99.cal_mean')} days, {sh0('overall.s97.share')} is waiting and {sh0('overall.s98.share')} is a person working on the bill. Verification itself is {d1('overall.s06.cal_mean')} days, so reading bills faster could save at most that, which is the IT head's point about the earlier OCR pilot. This rests on elapsed time standing in for effort, so it is a proxy until AP time data is seen (Questions for the client, L9).")
md.append(f"- **The weekly courier is a hard schedule.** Every packet arrives on a Friday and the lag is fixed by the weekday of signing: a Wednesday signature arrives in {d0('c.courier.lag_signed_wednesday')} days, a Thursday signature in {d0('c.courier.lag_signed_thursday')}. That is a lever that needs no AI.")
md.append(f"- **One verifier carries {pct('c.ver.AP-1.share_pct')} of the bills** and their queue is {d1('c.ver.AP-1.queue_days')} days against about {d1('c.ver.other_queue_min')} for the others, at every property.")
md.append(f"- **The work-order and amendment stories cannot be settled from the pack.** There is no amendment date, one query per bill, and nothing on who read the 60-day report. What the data does show is that {d0('c.wo.crossed_approved_value')} orders ran past approved value, usually before they expired.\n")
md.append("## The nine claims you asked about\n")
md.append("| Claim | Who | Verdict | Basis | What the data says | Figures from |")
md.append("|---|---|---|---|---|---|")
for i, label in order9:
    r = res[res.id == i].iloc[0]
    md.append(f"| **{label}.** {esc(r.claim)} ({i}) | {r.who} | **{badge[r.verdict]}** | {r.basis} | {esc(r.evidence)} | {esc(r.scripts.replace('analysis/', ''))} |")
md.append("\n## Every claim in the ledger\n")
md.append("| ID | Claim | Who | Verdict | Basis | What the data says | Figures from |")
md.append("|---|---|---|---|---|---|---|")
for r in res.itertuples():
    md.append(f"| {r.id} | {esc(r.claim)} | {r.who} | **{badge[r.verdict]}** | {r.basis} | {esc(r.evidence)} | {esc(r.scripts.replace('analysis/', ''))} |")
md.append(f"\n## The {len(ten)} claims with no number from the data: is there an honest proxy?\n")
md.append(f"{len(nt)} claims are NOT TESTABLE. {len(six)} of them ({', '.join(six)}) carry a context number from the pack and are covered in the next section. "
          f"The other {len(ten)} have no number at all. For each I asked whether anything in the pack could bound the claim without inventing a figure. "
          "None can, so all stay NOT TESTABLE and every row below is **reported only**. The last column names what is needed instead.\n")
md.append("| ID | Claim | Honest proxy in the pack? | What I tried, with the arithmetic and assumption | Data needed (exact) | Basis |")
md.append("|---|---|---|---|---|---|")
for i in ten:
    r = res[res.id == i].iloc[0]
    p = PROXY[i]
    md.append(f"| {i} | {esc(r.claim)} | **{p[0]}** | {esc(p[1])} | {esc(p[2])} | reported only |")
md.append("\n## Questions for the client\n")
md.append("What to request for each NOT TESTABLE claim. Priority 1 would change what we build; 2 would sharpen the numbers in the deck; 3 is background.\n")
md.append("| Priority | ID | Claim | Data to request | From | What it lets us test |")
md.append("|---|---|---|---|---|---|")
for i in sorted(ASK, key=lambda k: (ASK[k][2], int(k[1:]))):
    r = res[res.id == i].iloc[0]
    a = ASK[i]
    md.append(f"| {a[2]} | {i} | {esc(r.claim)} | {esc(a[0])} | {esc(a[1])} | {esc(a[3])} |")
md.append("\nThe same requests would also move other claims from *estimated from proxy* to *measured*:\n")
md.append("- **AP time data (L9)** would settle L10, L11 and L49, which today rest on elapsed days standing in for effort.")
md.append("- **The amendment log (L33, L37)** would settle L16, L35, L36 and L38, which today use queries and invoice totals as stand-ins for amendments and orders.")
md.append("- **The property head's signing log** would settle L27, which today uses the lag from verification to signature.")
md.append("- **The facility desk's receipt log by channel** would settle L55, which today uses repeated invoice numbers as a stand-in for a bill delivered to several places.")
md.append("\n## Notes\n")
md.append("- **Clock.** Where a claim does not say when the clock starts, the figure uses the invoice date and the desk date side by side.")
md.append("- **Proxies.** Elapsed days stand in for effort wherever a claim is about time spent (L9, L10, L11, L32, L49). They give an upper bound, not a measurement.")
md.append("- **Signing and posting dates.** Signature dates and posting dates are spread across all seven days of the week, which makes weekday claims about them unreliable (data-audit D15). Weekday tests use the receipt date (always a Friday) and the payment date.")
md.append("- **Extract limits.** The SAP extract has no service entries, work-order lines or amendment history; claims that depend on those are NOT TESTABLE rather than guessed.")
(ROOT / "notes" / "claims-tested.md").write_text("\n".join(md) + "\n", encoding="utf-8")
res.to_csv(OUT / "claims_tested.csv", index=False)
print("wrote notes/claims-tested.md;", len(ten), "claims with no number;", len(six), "with a context number")
print(bcnt.to_string())
