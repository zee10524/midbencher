"""Query forensics: queries.csv against the bill register (analysis/out/bills_clean.parquet).

Writes (analysis/out/):
  query_forensics.csv          one row per query: side, rule, timing, day-one evidence, catch layer, days a day-one catch would save
  query_forensics_summary.csv  tidy summary tables (table, group, metric, value) behind notes/query-forensics.md
  figures_query_forensics.csv  headline figures with ids (picked up by register_numbers.py)

SIDE = who has to act to close the query, read from query_text (category only as a fallback). It is not "who made the
mistake": the root cause usually sits upstream of the text (a property adding scope without telling procurement shows up
as a procurement-side WO query). Where the text leaves it open, `alt_side` records the other plausible owner and
`confidence` says how clear the text is.

CATCH LAYER = the earliest point at which the condition could be known, using only the bill and SAP data:
  A  bill fields + SAP tables that are in the extract (checked against the data here)
  B  what is printed on the bill (needs the reader) + SAP master data in the extract
  C  SAP data that exists but is not in the extract (WO rates and lines, open quantity, GL master, WBS status, bank data)
  D  other documents in the packet (attendance sheet, challans, service report), not the bill or SAP
  E  not knowable on the day the bill reaches the desk (service entry not yet made, internal holds, original lost)

Run: python analysis/04_query_forensics.py   (after analysis/clean.py)
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
figs: dict[str, tuple] = {}
summ: list[dict] = []


def fig(k, v, d=""):
    figs[k] = (v, d)


def S(table, group, metric, value):
    summ.append(dict(table=table, group=group, metric=metric, value=value))


# ---------------------------------------------------------------- rules: (id, text regex, issue type, side, alt side, confidence, layer, catch rule)
RULES = [
    ("R01", r"Same invoice number already booked", "Duplicate invoice number", "vendor", "head-office", "medium", "A",
     "same vendor and invoice no. already seen at the desk"),
    ("R02", r"Cost centre on service entry belongs to a different property", "Cost centre on service entry is another property's", "property", None, "high", "E",
     "service entry does not exist on day one"),
    ("R03", r"GL on WO .* does not match the expense type", "GL on work order does not match expense type", "property", "procurement", "medium", "C",
     "needs GL-to-expense mapping, not in extract"),
    ("R04", r"WBS element closed", "WBS element closed", "head-office", None, "medium", "C",
     "needs WBS status from SAP, not in extract"),
    ("R05", r"IGST charged on an intra-state supply", "IGST charged on intra-state supply", "vendor", None, "high", "B",
     "tax type printed on bill vs vendor and property state"),
    ("R06", r"HSN/SAC code missing", "HSN/SAC missing", "vendor", None, "high", "B", "HSN/SAC printed on bill"),
    ("R07", r"Tax rate on bill is", "Wrong GST rate on bill", "vendor", None, "high", "B", "rate printed on bill vs rate for the service"),
    ("R08", r"GSTIN on bill does not match vendor master", "GSTIN differs from vendor master", "vendor", "procurement", "medium", "B",
     "GSTIN printed on bill vs vendor_master"),
    ("R09", r"Discussed with property team, on hold", "On hold, no reason recorded", "head-office", "property", "low", "E",
     "reason not recorded"),
    ("R10", r"Pls check WO bal before sending", "Work order balance (asks property to check first)", "procurement", "property", "medium", "C",
     "WO balance by period, not in extract"),
    ("R11", r"Bill amount and SE amount not matching", "Bill amount differs from service entry", "property", "vendor", "medium", "E",
     "service entry does not exist on day one"),
    ("R12", r"PO not released yet", "PO not released", "procurement", None, "high", "C", "PO release status, not in extract"),
    ("R13", r"Wrong company name on bill", "Wrong company name on bill", "vendor", None, "high", "B", "bill addressee printed on bill"),
    ("R14", r"Hard copy not received yet, only scan", "Original not received, only scan", "property", "vendor", "medium", "E",
     "depends on the courier packet arriving"),
    ("R15", r"Vendor bank details changed", "Vendor bank details changed", "vendor", "procurement", "medium", "C",
     "bank data not in extract"),
    ("R16", r"Overtime billed but not approved in WO", "Overtime billed but not in work order", "vendor", "procurement", "medium", "C",
     "needs WO line items, not in extract"),
    ("R17", r"Rate on bill is higher than WO rate", "Rate above work order rate", "vendor", "procurement", "medium", "C",
     "needs WO rate, not in extract"),
    ("R18", r"Service entry still parked", "Service entry parked", "property", None, "high", "E", "service entry does not exist on day one"),
    ("R19", r"GRN not found in SAP", "GRN not found", "property", None, "high", "E", "GRN does not exist on day one"),
    ("R20", r"Service report for the quarter not attached", "Service report missing", "vendor", "property", "medium", "D", "packet document"),
    ("R21", r"Delivery challan missing security stamp", "Challan missing gate stamp", "property", None, "high", "D", "packet document"),
    ("R22", r"PF and ESIC challan for previous month not attached", "PF/ESIC challan missing", "vendor", None, "high", "D", "packet document"),
    ("R23", r"Attendance sheet not signed by property head", "Attendance sheet unsigned", "property", None, "high", "D", "packet document"),
    ("R24", r"Quantity billed exceeds open quantity on WO", "Quantity above open WO quantity", "procurement", "vendor", "medium", "C",
     "needs open quantity, not in extract (value balance tested)"),
    ("R25", r"WO .* has no balance left for this period", "Work order has no balance", "procurement", "property", "medium", "C",
     "needs WO balance by period (value balance tested)"),
    ("R26", r"WO .* expired on \d{2}-\d{2}-\d{4}", "Work order expired before bill date", "procurement", "property", "high", "A",
     "invoice date after work-order valid_to"),
]
CAT_FALLBACK = {"Duplicate bill": "vendor", "GL or cost centre": "property", "GST": "vendor", "Rate mismatch": "vendor",
                "Service entry or GRN not posted": "property", "Supporting documents": "vendor",
                "WO balance or validity": "procurement", "Other": "head-office"}
CAT_CLEAN_OTHER = {"R10": "WO balance or validity", "R12": "WO balance or validity", "R13": "Vendor master or bill details",
                   "R15": "Vendor master or bill details", "R11": "Service entry or GRN not posted",
                   "R14": "Supporting documents", "R09": "Other"}
SIDES = ["vendor", "property", "procurement", "head-office"]

# ---------------------------------------------------------------- load and join
b = pd.read_parquet(OUT / "bills_clean.parquet")
q = pd.read_csv(ROOT / "pack" / "data" / "queries.csv", dtype=str, keep_default_na=False)
q["raised_date"] = pd.to_datetime(q.raised_date)
q["resolved_date"] = pd.to_datetime(q.resolved_date.where(q.resolved_date != ""))
n_q = len(q)
fig("q.rows", n_q, "rows in queries.csv")
m = q.merge(b, on="bill_id", how="left", validate="one_to_one")
assert m.vendor_id.notna().all(), "query without a bill"

# ---------------------------------------------------------------- classify
hits = np.array([[bool(re.search(r[1], t)) for r in RULES] for t in m.query_text])
n_hits = hits.sum(axis=1)
fig("rules.queries_matching_no_rule", int((n_hits == 0).sum()), "queries no text rule matched (category fallback used)")
fig("rules.queries_matching_two_rules", int((n_hits > 1).sum()), "queries two text rules matched")
if (n_hits > 1).any():
    raise SystemExit("ambiguous rule match")
ri = np.where(n_hits == 1, hits.argmax(axis=1), -1)
rule_df = pd.DataFrame(RULES, columns=["rule_id", "pattern", "issue_type", "side", "alt_side", "confidence", "catch_layer", "catch_rule"])
for c in rule_df.columns[2:]:
    m[c] = [rule_df.loc[i, c] if i >= 0 else None for i in ri]
m["rule_id"] = [rule_df.loc[i, "rule_id"] if i >= 0 else "fallback" for i in ri]
fb = m.rule_id == "fallback"
m.loc[fb, "side"] = m.loc[fb, "query_category"].map(CAT_FALLBACK)
m.loc[fb, ["confidence", "catch_layer"]] = ["low", "E"]
m["category_clean"] = np.where(m.query_category == "Other", m.rule_id.map(CAT_CLEAN_OTHER).fillna("Other"), m.query_category)
fig("rules.other_queries", int((m.query_category == "Other").sum()), "queries categorised Other")
fig("rules.other_relabelled", int(((m.query_category == "Other") & (m.category_clean != "Other")).sum()), "Other queries given a real category from their text")
fig("rules.other_still_other", int((m.category_clean == "Other").sum()), "queries still Other after re-labelling (no reason recorded)")

# ---------------------------------------------------------------- timing
m["open"] = m.resolved_date.isna()
m["days_open"] = (m.resolved_date - m.raised_date).dt.days
m["days_desk_to_raised"] = (m.raised_date - m.desk_received_date).dt.days
m["days_ho_received_to_raised"] = (m.raised_date - m.ho_received_date).dt.days
m["days_pick_to_raised"] = (m.raised_date - m.ho_picked_date).dt.days
m["days_resolved_to_posted"] = (m.posted_date - m.resolved_date).dt.days
m["days_desk_to_pick"] = (m.ho_picked_date - m.desk_received_date).dt.days
m["raised_month"] = m.raised_date.dt.to_period("M").astype(str)
m["invoice_month"] = m.invoice_date.dt.to_period("M").astype(str)

# ---------------------------------------------------------------- share of bills with a query
inv = b.doc_type == "invoice"
fig("share.bills", len(b), "bills in bills_clean")
fig("share.bills_with_query", n_q, "bills with a query")
fig("share.bills_with_query_pct", round(100 * n_q / len(b), 2), "% of bills with a query")
fig("share.invoices_with_query", int((m.doc_type == "invoice").sum()))
fig("share.invoices_with_query_pct", round(100 * (m.doc_type == "invoice").sum() / inv.sum(), 2))
fig("share.credit_notes_with_query", int((m.doc_type == "credit_note").sum()))
fig("share.credit_notes_with_query_pct", round(100 * (m.doc_type == "credit_note").sum() / (~inv).sum(), 2))
fig("multi.bills_with_more_than_one_query", int(q.bill_id.duplicated().sum()), "bills with more than one query row")
fig("multi.max_queries_per_bill", int(q.bill_id.value_counts().max()))
fig("open.queries", int(m.open.sum()), "queries still open at 30 Apr 2026")
fig("open.queries_pct", round(100 * m.open.mean(), 2))
for st in ("Query", "With AP", "Posted", "Paid"):
    fig(f"open.status_{st}", int((m.open & (m.status == st)).sum()), f"open queries on bills with status {st}")
fig("open.age_median_days", float((pd.Timestamp("2026-04-30") - m.loc[m.open, "raised_date"]).dt.days.median()), "median age of open queries since raised")
fig("open.age_max_days", int((pd.Timestamp("2026-04-30") - m.loc[m.open, "raised_date"]).dt.days.max()))

# ---------------------------------------------------------------- timing of a query: when it is raised and how long it lasts
for c, nm in [("days_desk_to_raised", "desk to raised"), ("days_ho_received_to_raised", "HO received to raised"),
              ("days_pick_to_raised", "AP picked to raised"), ("days_open", "open (raised to resolved), closed queries"),
              ("days_resolved_to_posted", "resolved to posted")]:
    s = m[c].dropna()
    for k, v in [("mean", s.mean()), ("median", s.median()), ("p90", s.quantile(0.9)), ("min", s.min()), ("max", s.max()), ("n", len(s))]:
        fig(f"timing.{c}.{k}", round(float(v), 2), f"{nm}: {k}")
        S("timing", c, k, round(float(v), 3))

# ---------------------------------------------------------------- days a query adds, and at which stage (paid invoices, from stage_times.csv)
st = pd.read_csv(OUT / "stage_times.csv")
hq = st[(st.dimension == "has_query") & (st.stage_order.isin(range(1, 9)) | (st.stage_order == 99))]
pv = hq.pivot_table(index=["stage_order", "stage"], columns="group", values="cal_mean").reset_index()
pv = pv.rename(columns={"query": "with_q", "no query": "no_q"})
pv["added_days"] = pv.with_q - pv.no_q
for r in pv.itertuples():
    S("query_vs_no_query_mean_cal_days", r.stage, "with_query", round(r.with_q, 3))
    S("query_vs_no_query_mean_cal_days", r.stage, "without_query", round(r.no_q, 3))
    S("query_vs_no_query_mean_cal_days", r.stage, "added_days", round(r.added_days, 3))
    fig(f"added.s{int(r.stage_order):02d}", round(float(r.added_days), 2), f"{r.stage}: extra mean calendar days for bills with a query")
nq = hq[(hq.stage_order == 99)].set_index("group").n
fig("added.n_paid_with_query", int(nq["query"]), "paid invoices with a query (stage analysis population)")
fig("added.n_paid_without_query", int(nq["no query"]))
fig("added.total_mean_with_query", round(float(pv.loc[pv.stage_order == 99, "with_q"].iloc[0]), 2))
fig("added.total_mean_without_query", round(float(pv.loc[pv.stage_order == 99, "no_q"].iloc[0]), 2))
# same comparison inside each spend category, weighted by queried bills, to remove category mix
pm = st[(st.dimension == "category") & (st.stage_order == 99)]
pop = b[(b.doc_type == "invoice") & b.paid_date.notna()].copy()
pop["tot"] = (pop.paid_date - pop.invoice_date).dt.days
pop["hq"] = pop.bill_id.isin(q.bill_id)
cat_diff = pop.groupby(["category", "hq"]).tot.mean().unstack()
w = pop[pop.hq].groupby("category").size()
fig("added.days_on_overall_mean", round(float(pv.loc[pv.stage_order == 99, "added_days"].iloc[0]) * nq["query"] / (nq["query"] + nq["no query"]), 2),
    "days the queries add to the mean invoice-to-paid time of all paid invoices (extra days x share of bills with a query)")
fig("added.total_within_category_weighted", round(float(((cat_diff[True] - cat_diff[False]) * w / w.sum()).sum()), 2),
    "extra days with a query, compared within the same spend category (weighted by queried bills)")

# ---------------------------------------------------------------- days to resolve by category / side / issue
def stats(g, key, table):
    for k, s in g:
        s = s.dropna()
        for mt, v in [("n_closed", len(s)), ("mean", s.mean()), ("median", s.median()), ("p90", s.quantile(0.9)), ("max", s.max())]:
            S(table, k, mt, round(float(v), 3))


stats(m.groupby("query_category").days_open, "query_category", "days_to_resolve_by_category")
stats(m.groupby("category_clean").days_open, "category_clean", "days_to_resolve_by_category_clean")
stats(m.groupby("side").days_open, "side", "days_to_resolve_by_side")
stats(m.groupby("issue_type").days_open, "issue_type", "days_to_resolve_by_issue")
for k, s in m.groupby("query_category").days_open:
    fig(f"resolve.{k}.median", float(s.median()), f"median days to resolve, {k}")
    fig(f"resolve.{k}.mean", round(float(s.mean()), 2), f"mean days to resolve, {k}")
    fig(f"resolve.{k}.n_open", int(m[(m.query_category == k) & m.open].shape[0]), f"open queries, {k}")
med = m.groupby("query_category").days_open.median()
fig("resolve.category_median_min", float(med.min()), "lowest category median days to resolve")
fig("resolve.category_median_max", float(med.max()), "highest category median days to resolve")
sd = m.groupby("side").days_open.median()
fig("resolve.side_median_min", float(sd.min()))
fig("resolve.side_median_max", float(sd.max()))
for k, s in m.groupby("side").days_open:
    fig(f"resolve_side.{k}.median", float(s.median()), f"median days to resolve, {k}-side")
    fig(f"resolve_side.{k}.mean", round(float(s.mean()), 2))

# ---------------------------------------------------------------- sides
sc = m.side.value_counts()
for s_ in SIDES:
    prim = int(sc.get(s_, 0))
    sure = int(((m.side == s_) & m.alt_side.isna()).sum())
    maxc = prim + int(((m.alt_side == s_)).sum())
    fig(f"side.{s_}.primary", prim, f"queries whose fix sits with the {s_} side (primary rule)")
    fig(f"side.{s_}.primary_pct", round(100 * prim / n_q, 1))
    fig(f"side.{s_}.min", sure, f"{s_}: queries where the text leaves no alternative owner")
    fig(f"side.{s_}.max", maxc, f"{s_}: primary plus queries where it is the alternative owner")
    fig(f"side.{s_}.min_pct", round(100 * sure / n_q, 1))
    fig(f"side.{s_}.max_pct", round(100 * maxc / n_q, 1))
    S("side", s_, "primary", prim); S("side", s_, "min", sure); S("side", s_, "max", maxc)
fig("side.company_side_primary", int(m.side.isin(["property", "procurement", "head-office"]).sum()), "property + procurement + head-office, primary")
fig("side.company_side_primary_pct", round(100 * m.side.isin(["property", "procurement", "head-office"]).mean(), 1))
fig("side.company_side_min", int((m.side.isin(["property", "procurement", "head-office"]) & m.alt_side.isna()).sum()),
    "company side, only queries with no alternative owner")
three = m.category_clean.isin(["WO balance or validity", "GL or cost centre", "Service entry or GRN not posted"])
fig("side.ap_lead_three_categories", int(three.sum()), "queries on work order, GL / cost centre, service entry / GRN (the AP lead's 'our own side')")
fig("side.ap_lead_three_categories_pct", round(100 * three.mean(), 1))
fig("side.company_side_min_pct", round(100 * (m.side.isin(["property", "procurement", "head-office"]) & m.alt_side.isna()).mean(), 1))
for s_ in SIDES:
    fig(f"side.{s_}.high_confidence", int(((m.side == s_) & (m.confidence == "high")).sum()), f"{s_}-side queries where the text names the actor clearly")
fig("side.confidence_high", int((m.confidence == "high").sum()), "queries where the text names the actor clearly")
fig("side.confidence_medium", int((m.confidence == "medium").sum()))
fig("side.confidence_low", int((m.confidence == "low").sum()))
for k, g in m.groupby(["side", "query_category"]).size().items():
    S("side_by_category", f"{k[0]} | {k[1]}", "n", int(g))
for k, g in m.groupby("category").side.value_counts().items():
    S("side_by_spend_category", f"{k[0]} | {k[1]}", "n", int(g))
for k, g in m.groupby("property_type").side.value_counts().items():
    S("side_by_property_type", f"{k[0]} | {k[1]}", "n", int(g))

# ---------------------------------------------------------------- duplicates against the register
key = b.vendor_id + "|" + b.invoice_no
b2 = b.assign(key=key).sort_values(["desk_received_date", "bill_id"])
b2["seen_before"] = b2.groupby("key").cumcount() > 0
b2["twin_n"] = b2.groupby("key").bill_id.transform("size")
b2["twin_same_amount"] = b2.groupby(["key", "amount_inr"]).bill_id.transform("size") > 1
m = m.merge(b2[["bill_id", "seen_before", "twin_n", "twin_same_amount"]], on="bill_id", how="left")

# ---------------------------------------------------------------- work-order checks on day one
ib = b[b.doc_type == "invoice"].sort_values(["wo_id", "desk_received_date", "bill_id"]).copy()
ib["cum"] = ib.groupby("wo_id").amount_inr.cumsum()
ib["ev_over_balance"] = ib.cum > ib.wo_approved_value_inr
m = m.merge(ib[["bill_id", "ev_over_balance"]], on="bill_id", how="left")
m["ev_expired"] = m.invoice_date > m.wo_valid_to
m["expiry_text_date"] = pd.to_datetime(m.query_text.str.extract(r"expired on (\d{2}-\d{2}-\d{4})")[0], format="%d-%m-%Y")
m["same_state"] = m.vendor_state == m.property_state


def evidence(r):
    """True/False = rule run on bill + extract; None = cannot be tested with what is in the pack."""
    i = r.rule_id
    if i == "R01":
        return bool(r.seen_before)
    if i == "R26":
        return bool(r.ev_expired)
    if i in ("R24", "R25", "R10"):
        return bool(r.ev_over_balance) if pd.notna(r.ev_over_balance) else False
    if i == "R05":
        return bool(r.same_state)
    return None


m["day_one_data_supports"] = m.apply(evidence, axis=1)
ev = m.groupby("rule_id").day_one_data_supports.agg(lambda s: (s == True).sum()), m.groupby("rule_id").size()  # noqa: E712
fig("ev.dup_queries", int((m.rule_id == "R01").sum()), "duplicate-invoice-number queries")
fig("ev.dup_twin_registered_earlier", int(m[m.rule_id == "R01"].seen_before.eq(True).sum()), "...where the same vendor+invoice no. had already reached the desk")
fig("ev.dup_twin_exists", int((m[m.rule_id == "R01"].twin_n > 1).sum()), "...where a twin exists in the register at all")
fig("ev.dup_twin_same_amount", int(m[m.rule_id == "R01"].twin_same_amount.eq(True).sum()), "...where the twin has the same amount")
fig("ev.dup_no_twin_in_register", int((m[m.rule_id == "R01"].twin_n.fillna(1) <= 1).sum()))
fig("ev.expiry_queries", int((m.rule_id == "R26").sum()), "work-order-expired queries")
fig("ev.expiry_invoice_after_valid_to", int(m[m.rule_id == "R26"].ev_expired.sum()), "...where the invoice date is after the SAP valid_to")
fig("ev.expiry_text_date_equals_valid_to", int((m[m.rule_id == "R26"].expiry_text_date == m[m.rule_id == "R26"].wo_valid_to).sum()),
    "...where the expiry date in the query text equals SAP valid_to")
for rid, nm in [("R25", "no_balance"), ("R24", "quantity"), ("R10", "wo_bal_other")]:
    s = m[m.rule_id == rid]
    fig(f"ev.{nm}.queries", len(s))
    fig(f"ev.{nm}.over_balance_on_day_one", int(s.day_one_data_supports.eq(True).sum()),
        f"...where cumulative invoices on the work order exceed approved value by this bill (SAP extract)")
    fig(f"ev.{nm}.final_billed_gt_approved", int((s.wo_billed_value_inr > s.wo_approved_value_inr).sum()))
s = m[m.rule_id.isin(["R10", "R24", "R25"])]
fig("ev.wo_balance_all.queries", len(s), "work-order balance, quantity and no-balance queries together")
fig("ev.wo_balance_all.over_balance_on_day_one", int(s.day_one_data_supports.eq(True).sum()), "...where the extract's value rule says the bill pushed the work order over its approved value")
fig("ev.over_balance_rate_all_invoices_pct", round(100 * ib.ev_over_balance.mean(), 1), "% of all invoices the same value rule would flag, queried or not")
fig("ev.over_balance_flagged_invoices", int(ib.ev_over_balance.sum()), "invoices the value rule flags")
s = m[m.rule_id == "R05"]
fig("ev.igst.queries", len(s), "queries saying IGST was charged on an intra-state supply")
fig("ev.igst.master_says_same_state", int(s.same_state.sum()), "...where vendor state equals property state in the extract")
fig("ev.igst.master_says_different_state", int((~s.same_state).sum()), "...where the extract says the supply is inter-state")
fig("ev.igst.base_rate_same_state_pct", round(100 * (b.vendor_state == b.property_state).mean(), 1), "% of all bills where vendor state equals property state")
s = m[m.rule_id == "R07"]
fig("ev.taxrate.queries", len(s), "queries saying the bill has 12% where 18% applies")
fig("ev.taxrate.register_gst_is_18pct", int(((s.gst_inr / s.amount_inr).round(2) == 0.18).sum()), "...where the register shows 18% GST")
fig("ev.taxrate.diesel_zero_gst", int((s.gst_inr == 0).sum()), "...on Diesel bills, which carry no GST in the register")

# ---------------------------------------------------------------- catch layers and days a day-one catch would save
m["catchable_days_saved"] = np.where(m.open, np.nan, np.minimum(m.days_open, m.days_desk_to_pick.clip(lower=0)))
LAY = ["A", "B", "C", "D", "E"]
LNAME = {"A": "bill + SAP extract (checked)", "B": "bill printed fields + SAP master", "C": "SAP fields not in the extract",
         "D": "packet documents", "E": "not knowable on day one"}
paid_pop = int((b.doc_type.eq("invoice") & b.paid_date.notna()).sum())
cum = []
for L in LAY:
    cum.append(L)
    s = m[m.catch_layer.isin(cum)]
    cl = s[~s.open]
    cl_paid = cl[cl.doc_type.eq("invoice") & cl.paid_date.notna()]
    k = "".join(cum)
    fig(f"layer.{L}.queries", int((m.catch_layer == L).sum()), f"queries in layer {L}: {LNAME[L]}")
    fig(f"layer.{k}.cum_queries", len(s), f"queries in layers {k} together")
    fig(f"layer.{k}.cum_pct", round(100 * len(s) / n_q, 1))
    fig(f"layer.{k}.cum_mean_days_saved_per_closed_query", round(float(cl.catchable_days_saved.mean()), 2),
        f"mean days saved per closed query, layers {k}")
    fig(f"layer.{k}.cum_days_off_mean_total", round(float(cl_paid.catchable_days_saved.sum() / paid_pop), 2),
        f"days off the mean invoice-to-paid time of {paid_pop} paid invoices, layers {k}")
    S("catch_layer_cumulative", k, "queries", len(s)); S("catch_layer_cumulative", k, "pct", round(100 * len(s) / n_q, 2))
    S("catch_layer_cumulative", k, "days_off_mean_total", round(float(cl_paid.catchable_days_saved.sum() / paid_pop), 3))
for rid, g in m.groupby("rule_id"):
    S("rules", rid, "n", len(g)); S("rules", rid, "layer", g.catch_layer.iloc[0]); S("rules", rid, "side", g.side.iloc[0])
    S("rules", rid, "evidence_true", int(g.day_one_data_supports.eq(True).sum()))
    S("rules", rid, "evidence_false", int(g.day_one_data_supports.eq(False).sum()))
    S("rules", rid, "median_days_open", float(g.days_open.median()))
fig("a_verified.queries", int(m.day_one_data_supports.eq(True).sum()), "queries where a day-one rule on bill + extract fires (duplicates seen earlier, expired WOs, over-balance, IGST same-state)")
a_v = m[(m.catch_layer == "A") & m.day_one_data_supports.eq(True)]
fig("a_verified.layerA_queries", len(a_v), "layer A queries where the rule fires on the data")
cl = a_v[~a_v.open]
fig("a_verified.layerA_days_off_mean_total", round(float(cl[cl.doc_type.eq("invoice") & cl.paid_date.notna()].catchable_days_saved.sum() / paid_pop), 2))
fig("timing.desk_to_pick_median", float(m.days_desk_to_pick.median()), "median days from desk to AP picking the bill, queried bills")
fig("timing.min_desk_to_raised", int(m.days_desk_to_raised.min()), "shortest gap from desk to a query being raised")

# ---------------------------------------------------------------- monthly pattern
b["invoice_month"] = b.invoice_date.dt.to_period("M").astype(str)
bq = b.assign(has_q=b.bill_id.isin(q.bill_id))
for mo, g in bq.groupby("invoice_month"):
    S("by_invoice_month", mo, "bills", len(g)); S("by_invoice_month", mo, "bills_with_query", int(g.has_q.sum()))
    S("by_invoice_month", mo, "pct_with_query", round(100 * g.has_q.mean(), 2))
for mo, g in m.groupby("raised_month"):
    S("by_raised_month", mo, "queries", len(g))
    for s_ in SIDES:
        S("by_raised_month", mo, f"queries_{s_}", int((g.side == s_).sum()))
    S("by_raised_month", mo, "mean_days_open", round(float(g.days_open.mean()), 2))
for mo, g in m.groupby("invoice_month"):
    S("by_invoice_month", mo, "mean_days_open", round(float(g.days_open.mean()), 2))
pm_ = bq.groupby("invoice_month").has_q.mean() * 100
fig("month.pct_min", round(float(pm_.min()), 2), "lowest monthly share of bills with a query")
fig("month.pct_max", round(float(pm_.max()), 2), "highest monthly share of bills with a query")
fig("month.pct_min_month", pm_.idxmin()); fig("month.pct_max_month", pm_.idxmax())
rm = m.groupby("raised_month").size()
fig("month.raised_max", int(rm.max()), "most queries raised in one month"); fig("month.raised_max_month", rm.idxmax())
fig("month.raised_min", int(rm.min())); fig("month.raised_min_month", rm.idxmin())
fig("month.raised_mean", round(float(rm.iloc[:-1].mean()), 1), "mean queries raised per month (all but the last, partial month)")
# amendment clusters (procurement executive: eleven or twelve requests in four days, second week of February)
wo_cat = m[(m.category_clean == "WO balance or validity")]
d_ = wo_cat.groupby("raised_date").size().reindex(pd.date_range(m.raised_date.min(), m.raised_date.max()), fill_value=0)
r4 = d_.rolling(4).sum()
fig("wo_cluster.max_4day_count", int(r4.max()), "most work-order queries raised in any 4 consecutive days")
fig("wo_cluster.max_4day_ending", str(r4.idxmax().date()))
feb = d_["2026-02-08":"2026-02-15"]
fig("wo_cluster.feb2026_week2_count", int(feb.sum()), "work-order queries raised 8 to 15 Feb 2026")
fig("wo_cluster.mean_4day_count", round(float(r4.mean()), 2), "mean work-order queries per 4 days")
fig("wo_cluster.feb2026_total", int(d_["2026-02-01":"2026-02-28"].sum()), "work-order queries raised in Feb 2026")
fig("wo_cluster.monthly_mean_wo", round(float(d_.groupby(d_.index.to_period("M")).sum().iloc[:-1].mean()), 1))
# claims from the transcripts
chall = m[m.rule_id == "R22"].days_open.median()
fig("claim.missing_challan_median_days", float(chall), "AP lead: a missing challan takes a week. Median days to resolve PF/ESIC challan queries")
fig("claim.wo_median_days", float(m[m.category_clean == "WO balance or validity"].days_open.median()),
    "AP lead: an amendment can take a month. Median days to resolve work-order queries")
for k, g in m.groupby("property_type"):
    fig(f"proptype.{k}.pct_queried", round(100 * b[b.property_type == k].bill_id.isin(q.bill_id).mean(), 2), f"% of {k} bills with a query")
for k, g in m.groupby("category"):
    fig(f"spend.{k}.queries", int(b[b.category == k].bill_id.isin(q.bill_id).sum()), f"queries on {k} bills")
    fig(f"spend.{k}.pct_queried",round(100 * b[b.category == k].bill_id.isin(q.bill_id).mean(), 2), f"% of {k} bills with a query")
for k in ["Micro", "Small", "Medium", "Not MSME", "Unknown"]:
    fig(f"msme.{k}.pct_queried", round(100 * b[b.msme_status == k].bill_id.isin(q.bill_id).mean(), 2), f"% of {k} vendors' bills with a query")

# ---------------------------------------------------------------- outputs
cols = ["query_id", "bill_id", "doc_type", "category", "property_code", "property_type", "vendor_id", "msme_status",
        "query_category", "category_clean", "rule_id", "issue_type", "side", "alt_side", "confidence", "query_text",
        "raised_date", "resolved_date", "open", "days_open", "raised_month", "invoice_month",
        "desk_received_date", "ho_received_date", "ho_picked_date", "posted_date", "paid_date",
        "days_desk_to_raised", "days_ho_received_to_raised", "days_pick_to_raised", "days_resolved_to_posted", "days_desk_to_pick",
        "catch_layer", "catch_rule", "day_one_data_supports", "catchable_days_saved"]
out = m[cols].copy()
out["day_one_data_supports"] = out.day_one_data_supports.map({True: "yes", False: "no"}).fillna("not testable here")
out.to_csv(OUT / "query_forensics.csv", index=False, date_format="%Y-%m-%d")
pd.DataFrame(summ).to_csv(OUT / "query_forensics_summary.csv", index=False)
pd.DataFrame([dict(id=k, value=v, description=d) for k, (v, d) in figs.items()]).to_csv(OUT / "figures_query_forensics.csv", index=False)
rule_df.assign(n=rule_df.rule_id.map(m.rule_id.value_counts())).to_csv(OUT / "query_rules.csv", index=False)

pd.set_option("display.width", 230, "display.max_columns", 30, "display.max_rows", 200, "display.max_colwidth", 60)
print(f"wrote {len(out)} query rows")
print(pd.DataFrame(summ).query("table in ['catch_layer_cumulative','side']").pivot_table(index=["table", "group"], columns="metric", values="value").round(2))
ff = pd.read_csv(OUT / "figures_query_forensics.csv", keep_default_na=False)
print(ff[ff.id.str.startswith(("ev.", "a_verified", "claim", "wo_cluster", "added", "month", "multi", "share", "open", "rules", "layer", "resolve."))][["id", "value"]].to_string(index=False))
