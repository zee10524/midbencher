"""Clean the vendor-payments bill register and audit every pack data file.

Reads pack/data read-only. Writes, under analysis/out/:
  bills_clean.parquet  one row per bill_id, joined to vendor, property and work order, with flags
  exclusions.csv       every row removed from the register, with the reason and the row it duplicates
  changes.csv          every value that was changed, old and new, with the rule
  issues.csv           every data quality check that found something, with count and action
  figures.csv          every number quoted in notes/data-audit.md, with an id

Rules: nothing is dropped without a line in exclusions.csv; nothing is changed without a line in
changes.csv; everything else suspicious is flagged in a column, not removed.

Run: python analysis/clean.py
"""
from __future__ import annotations

import difflib
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "pack" / "data"
OUT = ROOT / "analysis" / "out"
OUT.mkdir(parents=True, exist_ok=True)
ASOF = pd.Timestamp("2026-04-30")  # data dictionary: status as of 30 April 2026
PAY_DAYS = {1, 4}  # Tuesday, Friday (payment policy)

figs: dict[str, tuple] = {}
issues: list[dict] = []


def fig(key: str, value, desc: str = "") -> None:
    figs[key] = (value, desc)


def issue(iid: str, table: str, check: str, rows: int, action: str, why: str) -> None:
    issues.append(dict(id=iid, table=table, check=check, rows=int(rows), action=action, why=why))


def rd(rel: str) -> pd.DataFrame:
    return pd.read_csv(DATA / rel, dtype=str, keep_default_na=False)


def dt(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.where(s != ""), format="%Y-%m-%d")


# ---------------------------------------------------------------- load
raw = rd("bill_register.csv")
raw.insert(0, "source_row", range(len(raw)))  # 0-based data row; CSV line = source_row + 2
vendors, props, wo_raw, queries = rd("vendors.csv"), rd("properties.csv"), rd("work_orders.csv"), rd("queries.csv")
bio, gate, claim = (rd(f"attendance-sample/{n}.csv") for n in
                    ("biometric_export", "gate_register_transcribed", "vendor_claim"))
con = sqlite3.connect(f"file:{(DATA / 'sap_extract.sqlite').as_posix()}?mode=ro", uri=True)
sap = {t: pd.read_sql_query(f'select * from "{t}"', con)
       for t in ("vendor_master", "work_orders", "properties", "posted_invoices", "parsed_bill")}
con.close()

for name, d in [("bill_register", raw), ("vendors", vendors), ("properties", props), ("work_orders", wo_raw),
                ("queries", queries), ("biometric_export", bio), ("gate_register_transcribed", gate),
                ("vendor_claim", claim)]:
    fig(f"rows.{name}", len(d), f"rows in {name}.csv")
for t, d in sap.items():
    fig(f"rows.sap.{t}", len(d), f"rows in sap_extract.sqlite:{t}")

# ---------------------------------------------------------------- D01 exact duplicate rows
cols = [c for c in raw.columns if c != "source_row"]
dup_mask = raw.duplicated(subset=cols, keep="first")
kept_row = raw.groupby(cols, sort=False)["source_row"].transform("first")
excl = pd.DataFrame({
    "source_row": raw.loc[dup_mask, "source_row"],
    "csv_line": raw.loc[dup_mask, "source_row"] + 2,
    "bill_id": raw.loc[dup_mask, "bill_id"],
    "reason": "D01 exact duplicate of an earlier row (all 19 columns identical)",
    "kept_source_row": kept_row[dup_mask],
})
df = raw.loc[~dup_mask].copy()
if df.bill_id.duplicated().any():
    raise SystemExit("bill_id still duplicated after removing exact duplicates; needs a decision, not a silent drop")
if len(df) + len(excl) != len(raw):
    raise SystemExit("row accounting broken")
fig("bill_register.exact_dup_rows", len(excl), "rows removed as exact duplicates")
fig("bill_register.rows_after_dedup", len(df), "rows kept")
fig("bill_register.bill_ids_in_dup_groups", excl.bill_id.nunique(), "distinct bill_ids that appeared twice")
issue("D01", "bill_register", "row identical to an earlier row in all 19 columns", len(excl), "DROP (logged)",
      "Same tracker number, same everything. After dropping them billed_value_inr on every work order equals the "
      "sum of its invoices (see D08 note), which confirms they are not real bills.")

# ---------------------------------------------------------------- types
changes: list[dict] = []
for c in [c for c in df.columns if c.endswith("_date")]:
    df[c] = dt(df[c])
for c in ("amount_inr", "gst_inr"):
    df[c] = df[c].astype(float)
df["paid_date_raw"] = df["paid_date"]

# ---------------------------------------------------------------- D02 property_code format
df["property_code_raw"] = df["property_code"]
canon = set(props.property_code)
fixed = df.property_code.str.strip().str.upper().str.replace(r"[\s_]+", "-", regex=True)
if not fixed.isin(canon).all():
    raise SystemExit("property_code that cannot be mapped to properties.csv: "
                     f"{sorted(set(fixed[~fixed.isin(canon)]))}")
chg = df.property_code != fixed
changes += [dict(source_row=r.source_row, bill_id=r.bill_id, column="property_code", old=r.property_code,
                 new=n, rule="D02 strip, upper-case, space/underscore to hyphen")
            for r, n in zip(df.loc[chg].itertuples(), fixed[chg])]
fig("property_code.non_canonical_rows_raw", int((raw.property_code != raw.property_code.str.strip().str.upper()
    .str.replace(r"[\s_]+", "-", regex=True)).sum()), "rows in the raw file (incl. duplicates)")
fig("property_code.non_canonical_rows", int(chg.sum()), "rows kept after dedup whose property_code was changed")
fig("property_code.distinct_raw", df.property_code.nunique(), "distinct property_code strings after dedup")
fig("property_code.lowercase", int((df.property_code[chg] != df.property_code[chg].str.upper()).sum()))
fig("property_code.space_instead_of_hyphen", int(df.property_code[chg].str.strip().str.contains(" ").sum()))
fig("property_code.leading_or_trailing_space", int((df.property_code[chg] != df.property_code[chg].str.strip()).sum()))
df["property_code"] = fixed
fig("property_code.distinct_clean", df.property_code.nunique(), "distinct property_code after fix (properties.csv has 38)")
issue("D02", "bill_register", "property_code not exactly a code in properties.csv (case, spaces, space for hyphen)",
      chg.sum(), "FIX (logged)", "Every one maps to exactly one of the 38 properties once trimmed, upper-cased and "
      "hyphenated; left alone, 38 properties look like 150.")

# ---------------------------------------------------------------- joins
wo = wo_raw.copy()
for c in ("valid_from", "valid_to"):
    wo[c] = pd.to_datetime(wo[c], format="%Y-%m-%d")
for c in ("approved_value_inr", "billed_value_inr"):
    wo[c] = wo[c].astype(float)
n0 = len(df)
fig("fk.vendor_missing", int((~df.vendor_id.isin(vendors.vendor_id)).sum()), "bills whose vendor_id is not in vendors.csv")
fig("fk.wo_missing", int((~df.wo_id.isin(wo.wo_id)).sum()), "bills whose wo_id is not in work_orders.csv")
fig("fk.property_missing_after_fix", int((~df.property_code.isin(canon)).sum()))
df = df.merge(vendors.rename(columns={"vendor_name": "vendor_name", "category": "vendor_category",
                                      "state": "vendor_state", "gstin": "vendor_gstin"}),
              on="vendor_id", how="left", validate="many_to_one")
df = df.merge(props.rename(columns={"property_name": "property_name", "state": "property_state",
                                    "city": "property_city"}), on="property_code", how="left", validate="many_to_one")
wo_j = wo.rename(columns={c: f"wo_{c}" for c in wo.columns if c != "wo_id"})
df = df.merge(wo_j, on="wo_id", how="left", validate="many_to_one")
assert len(df) == n0

fig("fk.bill_vendor_ne_wo_vendor", int((df.vendor_id != df.wo_vendor_id).sum()), "bills whose vendor differs from their work order's vendor")
fig("fk.bill_property_ne_wo_property_raw", int((df.property_code_raw != df.wo_property_code).sum()),
    "bills whose property_code as typed differs from the work order's (formatting only)")
fig("fk.bill_property_ne_wo_property", int((df.property_code != df.wo_property_code).sum()),
    "bills whose property differs from the work order's after D02 fix")
fig("fk.bill_category_ne_wo_category", int((df.category != df.wo_category).sum()))
fig("fk.bill_category_ne_vendor_category", int((df.category != df.vendor_category).sum()))
fig("fk.wo_costcentre_ne_property", int((wo.cost_centre != "CC-" + wo.property_code).sum()))

# ---------------------------------------------------------------- date order
order = ["invoice_date", "desk_received_date", "property_verified_date", "property_head_signed_date",
         "ho_received_date", "ho_picked_date", "posted_date", "paid_date"]
for a, b in zip(order[:-1], order[1:]):
    n = int((df[a].notna() & df[b].notna() & (df[b] < df[a])).sum())
    fig(f"dateorder.{b}_before_{a}", n, f"{b} earlier than {a}")
for c in order:
    fig(f"nulls.bill_register.{c}", int(df[c].isna().sum()), f"blank {c} after dedup")
    fig(f"future.{c}", int((df[c] > ASOF).sum()), f"{c} after 30 Apr 2026")
fig("nulls.bill_register.ho_verifier", int((df.ho_verifier == "").sum()))
fig("dateorder.posted_without_picked", int((df.posted_date.notna() & df.ho_picked_date.isna()).sum()))
fig("dateorder.paid_without_posted", int((df.paid_date.notna() & df.posted_date.isna()).sum()))
fig("dateorder.verifier_set_iff_picked", int(((df.ho_verifier != "") != df.ho_picked_date.notna()).sum()))

# ---------------------------------------------------------------- D03 paid before posted
pbp = df.paid_date < df.posted_date
fig("paid_before_posted.rows", int(pbp.sum()), "paid_date earlier than posted_date")
fig("paid_before_posted.also_before_invoice_date", int((df.paid_date < df.invoice_date).sum()))
fig("paid_before_posted.also_before_ho_received", int((df.paid_date < df.ho_received_date).sum()))
fig("paid_before_posted.status_paid", int((pbp & (df.status == "Paid")).sum()))
fig("paid_before_posted.credit_notes", int((pbp & (df.doc_type == "credit_note")).sum()))
gap = (df.posted_date - df.paid_date).dt.days[pbp]
fig("paid_before_posted.gap_min_days", int(gap.min()))
fig("paid_before_posted.gap_median_days", float(gap.median()))
fig("paid_before_posted.gap_max_days", int(gap.max()))
offday = df.paid_date.notna() & ~df.paid_date.dt.dayofweek.isin(PAY_DAYS)
fig("paid.on_non_payment_day", int(offday.sum()), "paid_date not a Tuesday or Friday")
fig("paid.on_non_payment_day_within_D03", int((offday & pbp).sum()))
fig("paid.on_payment_day_when_valid", int((df.paid_date.notna() & ~pbp & df.paid_date.dt.dayofweek.isin(PAY_DAYS)).sum()))
fig("paid.valid_rows", int((df.paid_date.notna() & ~pbp).sum()), "paid rows whose paid_date is not in D03")
changes += [dict(source_row=r.source_row, bill_id=r.bill_id, column="paid_date", old=str(r.paid_date.date()),
                 new="", rule="D03 paid_date before posted_date, invoice_date and HO receipt; set blank in "
                 "paid_date, original kept in paid_date_raw")
            for r in df.loc[pbp].itertuples()]
df["f_paid_before_posted"] = pbp
df.loc[pbp, "paid_date"] = pd.NaT
issue("D03", "bill_register", "paid_date earlier than posted_date", pbp.sum(), "FLAG + blank paid_date (raw kept)",
      "In all 113 the payment is also before the invoice date and before the packet reached head office, so "
      "paid_date is wrong, not posted_date. 77 of them fall on a day that is not a payment-run day. "
      "The rest of the row is usable.")

# ---------------------------------------------------------------- D04 vendor+invoice_no on two bills
g = df.groupby(["vendor_id", "invoice_no"])
size = g["bill_id"].transform("size")
df["f_dup_vendor_invoice"] = size > 1
pairs = g.agg(n=("bill_id", "size"), amounts=("amount_inr", "nunique"), dates=("invoice_date", "nunique"),
              wos=("wo_id", "nunique"), props=("property_code", "nunique"))
pairs = pairs[pairs.n > 1]
fig("dup_vendor_invoice.pairs", len(pairs), "vendor+invoice_no combinations on more than one bill")
fig("dup_vendor_invoice.bills", int(df.f_dup_vendor_invoice.sum()))
fig("dup_vendor_invoice.max_bills_per_pair", int(pairs.n.max()))
fig("dup_vendor_invoice.pairs_same_amount", int((pairs.amounts == 1).sum()))
fig("dup_vendor_invoice.pairs_same_date", int((pairs.dates == 1).sum()))
fig("dup_vendor_invoice.pairs_same_date_and_amount", int(((pairs.dates == 1) & (pairs.amounts == 1)).sum()))
fig("dup_vendor_invoice.pairs_diff_property", int((pairs.props > 1).sum()))
fig("dup_vendor_invoice.pairs_diff_wo", int((pairs.wos > 1).sum()))
same_day = pairs.index[(pairs.dates == 1)]
df["f_dup_vendor_invoice_same_date"] = df.set_index(["vendor_id", "invoice_no"]).index.isin(same_day)
fig("dup_vendor_invoice.same_date_bills", int(df.f_dup_vendor_invoice_same_date.sum()))
fig("dup_vendor_invoice.bills_with_any_query", int(df.loc[df.f_dup_vendor_invoice, "bill_id"].isin(queries.bill_id).sum()))
fig("invoice_no.shared_across_vendors", int(df.groupby("invoice_no").vendor_id.nunique().gt(1).sum()))
fig("invoice_no.bad_format", int((~df.invoice_no.str.match(r"^\d{3}/25-26/\d{3}$")).sum()))
issue("D04", "bill_register", "same vendor_id and invoice_no on two different bill_ids", len(pairs),
      "FLAG (pairs, both bills kept)", "Different amount, and in all but one pair different date: look like number reuse, "
      "not double billing. The one same-date pair is the only one worth a human look. Check H13 would catch these.")

# queries versus the pair list
dq = queries[queries.query_category == "Duplicate bill"].merge(df[["bill_id", "f_dup_vendor_invoice"]], on="bill_id", how="left")
fig("dup_query.rows", len(dq), "queries categorised Duplicate bill")
fig("dup_query.on_flagged_pair", int(dq.f_dup_vendor_invoice.fillna(False).sum()))
fig("dup_query.not_on_any_pair", int((~dq.f_dup_vendor_invoice.fillna(False)).sum()),
    "Duplicate-bill queries on a bill with no vendor+invoice_no twin in the register")
fig("dup_query.masked_tracker", int(queries.query_text.str.contains(r"TRK\d+xx", regex=True).sum()),
    "query_text with a masked tracker like TRK2500xx")
issue("D05", "queries", "Duplicate-bill query on a bill with no same-vendor same-invoice twin in the register",
      (~dq.f_dup_vendor_invoice.fillna(False)).sum(), "FLAG", "Either the twin was never registered, or the AP "
      "verifier matched on something else. We cannot tell which from the data.")
issue("D06", "queries", "query_text names the earlier tracker with the last two digits masked (TRK2500xx)",
      queries.query_text.str.contains(r"TRK\d+xx", regex=True).sum(), "FLAG", "The referenced bill cannot be "
      "looked up, so these cannot be confirmed as duplicates.")

# ---------------------------------------------------------------- D07 MSME blank
fig("msme.vendors_blank", int((vendors.msme_status == "").sum()), "vendors with blank msme_status")
fig("msme.vendors_total", len(vendors))
fig("msme.vendors_micro", int((vendors.msme_status == "Micro").sum()))
fig("msme.vendors_small", int((vendors.msme_status == "Small").sum()))
fig("msme.vendors_medium", int((vendors.msme_status == "Medium").sum()))
fig("msme.vendors_not_msme", int((vendors.msme_status == "Not MSME").sum()))
df["msme_status"] = df["msme_status"].replace("", "Unknown")
df["f_msme_unknown"] = df.msme_status == "Unknown"
fig("msme.bills_unknown", int(df.f_msme_unknown.sum()), "bills (after dedup) from vendors with blank msme_status")
fig("msme.bills_unknown_amount_inr", float(df.loc[df.f_msme_unknown, "amount_inr"].sum()))
issue("D07", "vendors / vendor_master", "msme_status blank", (vendors.msme_status == "").sum(), "FLAG (value 'Unknown')",
      "Cannot be inferred. The 45-day rule applies to Micro and Small only, so exposure must be reported as a "
      "range, with unknown vendors shown separately.")

# ---------------------------------------------------------------- D08-D10 work orders
exp = df.invoice_date > df.wo_valid_to
df["f_invoice_after_wo_expiry"] = exp
fig("wo.bills_after_valid_to", int(exp.sum()), "bills dated after their work order's valid_to")
fig("wo.bills_after_valid_to_paid", int((exp & (df.status == "Paid")).sum()))
fig("wo.bills_before_valid_from", int((df.invoice_date < df.wo_valid_from).sum()))
exp_q = queries[queries.query_text.str.contains("expired on", case=False)].bill_id
fig("wo.expiry_queries", len(exp_q), "queries whose text says the work order expired")
fig("wo.bills_after_valid_to_with_expiry_query", int(df.loc[exp & df.bill_id.isin(exp_q)].shape[0]))
fig("wo.bills_after_valid_to_days_late_median", float((df.invoice_date - df.wo_valid_to).dt.days[exp].median()))
issue("D08", "bill_register + work_orders", "invoice_date after the work order's valid_to", exp.sum(),
      "FLAG", "661 of these were paid and only 104 drew an expiry query. Either valid_to in the extract is stale "
      "(amendments not reflected) or the check is applied unevenly. Cannot tell which from the data, so do not use "
      "valid_to alone as ground truth for a hard block.")

inv = wo.valid_to < wo.valid_from
fig("wo.valid_to_before_valid_from", int(inv.sum()), "work orders with valid_to earlier than valid_from")
df["f_wo_validity_inverted"] = df.wo_valid_to < df.wo_valid_from
fig("wo.bills_on_inverted_wo", int(df.f_wo_validity_inverted.sum()))
issue("D09", "work_orders", "valid_to earlier than valid_from", inv.sum(), "FLAG (exclude from validity checks)",
      "Dates cannot be repaired from the data. 12 bills sit on these two orders; they are kept and carry "
      "f_wo_validity_inverted so expiry checks skip them.")

over = wo.billed_value_inr > wo.approved_value_inr
fig("wo.billed_gt_approved", int(over.sum()), "work orders billed above approved value")
ratio = (wo.billed_value_inr / wo.approved_value_inr)[over]
fig("wo.billed_gt_approved_max_ratio", round(float(ratio.max()), 3))
fig("wo.billed_gt_approved_median_ratio", round(float(ratio.median()), 3))
df["f_wo_overbilled"] = df.wo_billed_value_inr > df.wo_approved_value_inr
fig("wo.bills_on_overbilled_wo", int(df.f_wo_overbilled.sum()))
fig("wo.approved_le_zero", int((wo.approved_value_inr <= 0).sum()))
fig("wo.per_property_median", float(wo.groupby("property_code").size().median()))
fig("wo.per_property_max", int(wo.groupby("property_code").size().max()))
fig("wo.per_property_min", int(wo.groupby("property_code").size().min()))
issue("D10", "work_orders", "billed_value_inr above approved_value_inr", over.sum(), "FLAG",
      "Real signal (work orders overrun), not a data error. Keep, and use it for the balance check.")

inv_sum = df[df.doc_type == "invoice"].groupby("wo_id").amount_inr.sum()
raw_sum = raw[raw.doc_type == "invoice"].assign(a=lambda x: x.amount_inr.astype(float)).groupby("wo_id").a.sum()
w2 = wo.set_index("wo_id")
fig("wo.billed_eq_invoice_sum_dedup", int(((w2.billed_value_inr - inv_sum.reindex(w2.index).fillna(0)).abs() <= 1).sum()),
    "work orders whose billed_value_inr equals the sum of invoices (credit notes excluded) after dedup")
fig("wo.billed_eq_invoice_sum_raw", int(((w2.billed_value_inr - raw_sum.reindex(w2.index).fillna(0)).abs() <= 1).sum()),
    "same, if the 220 duplicate rows are left in")
fig("wo.without_any_bill", int((~wo.wo_id.isin(df.wo_id)).sum()))

# ---------------------------------------------------------------- D11-D12 SAP
pi = sap["posted_invoices"]
pi_dup = pi.duplicated(keep="first")
fig("sap.posted_invoices_exact_dup_rows", int(pi_dup.sum()), "posted_invoices rows identical to an earlier row")
fig("sap.posted_invoices_distinct_bills", pi[~pi_dup].bill_id.nunique())
pid = pi[~pi_dup]
fig("sap.posted_not_in_register", int((~pid.bill_id.isin(df.bill_id)).sum()))
fig("sap.unposted_bills_in_posted_invoices", int(pid.bill_id.isin(df.loc[df.posted_date.isna(), "bill_id"]).sum()))
miss = df.posted_date.notna() & ~df.bill_id.isin(pid.bill_id)
fig("sap.register_posted_missing_from_sap", int(miss.sum()), "register has a posted_date, SAP posted_invoices has no row")
fig("sap.register_posted_missing_from_sap_status_paid", int((miss & (df.status == "Paid")).sum()))
fig("sap.register_posted_total", int(df.posted_date.notna().sum()))
jj = pid.merge(df, on="bill_id", suffixes=("_sap", ""))
for c in ("vendor_id", "invoice_no", "wo_id"):
    fig(f"sap.mismatch_{c}", int((jj[f"{c}_sap"] != jj[c]).sum()))
fig("sap.mismatch_invoice_date", int((pd.to_datetime(jj.invoice_date_sap) != jj.invoice_date).sum()))
fig("sap.mismatch_posted_date", int((pd.to_datetime(jj.posted_date_sap) != jj.posted_date).sum()))
fig("sap.mismatch_amount", int((jj.amount_inr_sap.astype(float) != jj.amount_inr).sum()))
fig("sap.mismatch_gst", int((jj.gst_inr_sap.astype(float) != jj.gst_inr).sum()))
df["f_posted_not_in_sap"] = miss


def same(a: pd.DataFrame, b: pd.DataFrame, key: str) -> int:
    def norm(x: pd.DataFrame) -> pd.DataFrame:
        return x.astype(str).apply(lambda s: s.str.replace(r"\.0$", "", regex=True)).sort_values(key).reset_index(drop=True)
    return int((norm(a[sorted(a.columns)]) != norm(b[sorted(a.columns)])).sum().sum())


fig("sap.vendor_master_vs_vendors_csv_cells_differ", same(sap["vendor_master"], vendors, "vendor_id"))
fig("sap.work_orders_vs_csv_cells_differ", same(sap["work_orders"], wo_raw, "wo_id"))
fig("sap.properties_vs_csv_cells_differ", same(sap["properties"], props, "property_code"))
fig("sap.parsed_bill_rows", len(sap["parsed_bill"]))
issue("D11", "sap posted_invoices", "row identical to an earlier row", pi_dup.sum(), "DROP in any SAP-side join",
      "Same bill_id twice with identical content; mirrors D01.")
issue("D12", "bill_register vs sap posted_invoices", "register has posted_date, SAP has no posted invoice",
      miss.sum(), "FLAG", "All 40 are Paid. SAP extract is incomplete or the register posted_date is wrong; "
      "not resolvable from the data. Do not treat posted_invoices as the full truth.")

# ---------------------------------------------------------------- status vs dates, queries
q = queries.copy()
q["raised_date"], q["resolved_date"] = dt(q.raised_date), dt(q.resolved_date)
open_q = q[q.resolved_date.isna()].bill_id
derived = pd.Series("In Transit", index=df.index)
derived[df.ho_received_date.notna()] = "With AP"
derived[df.bill_id.isin(open_q)] = "Query"
derived[df.posted_date.notna()] = "Posted"
derived[df.paid_date_raw.notna()] = "Paid"
fig("status.contradicts_dates", int((derived != df.status).sum()), "status differs from status derived from dates and open queries")
for s in ("In Transit", "With AP", "Query", "Posted", "Paid"):
    fig(f"status.count.{s}", int((df.status == s).sum()))
fig("status.in_transit_max_age_days", int((ASOF - df.loc[df.status == "In Transit", "property_head_signed_date"]).dt.days.max()))
fig("status.with_ap_max_age_days", int((ASOF - df.loc[df.status == "With AP", "ho_received_date"]).dt.days.max()))
fig("status.query_max_age_days", int((ASOF - df.loc[df.status == "Query", "ho_received_date"]).dt.days.max()))
fig("status.with_ap_already_picked", int(((df.status == "With AP") & df.ho_picked_date.notna()).sum()))
fig("queries.open", len(open_q))
fig("queries.open_not_status_query", int((~df.loc[df.bill_id.isin(open_q), "status"].eq("Query")).sum()))
fig("queries.bills_with_query", int(df.bill_id.isin(q.bill_id).sum()))
fig("queries.bill_fk_missing", int((~q.bill_id.isin(df.bill_id)).sum()))
fig("queries.bills_with_more_than_one", int(q.bill_id.duplicated().sum()))
fig("queries.resolved_before_raised", int((q.resolved_date < q.raised_date).sum()))
mq = q.merge(df[["bill_id", "ho_received_date", "ho_picked_date", "ho_verifier", "posted_date", "paid_date_raw"]], on="bill_id")
fig("queries.raised_before_ho_received", int((mq.raised_date < mq.ho_received_date).sum()))
fig("queries.raised_by_ne_verifier", int((mq.raised_by != mq.ho_verifier).sum()))
fig("queries.raised_after_posted", int((mq.raised_date > mq.posted_date).sum()))
fig("queries.resolved_after_posted", int((mq.resolved_date > mq.posted_date).sum()))
late_q = mq[mq.raised_date > mq.paid_date_raw].bill_id
fig("queries.raised_after_paid", len(late_q))
fig("queries.raised_after_paid_within_D03", int(df.loc[df.bill_id.isin(late_q), "f_paid_before_posted"].sum()))
df["f_query_raised_after_paid"] = df.bill_id.isin(late_q)
fig("queries.category_other", int((q.query_category == "Other").sum()), "queries categorised Other")
other_txt = q[q.query_category == "Other"].query_text
fig("queries.other_distinct_texts", other_txt.nunique())
fig("queries.other_wo_balance_text", int(other_txt.str.contains("WO bal", case=False).sum()))
fig("queries.other_po_not_released_text", int(other_txt.str.contains("PO not released", case=False).sum()))
fig("queries.other_se_amount_text", int(other_txt.str.contains("SE amount", case=False).sum()))
fig("queries.other_hard_copy_text", int(other_txt.str.contains("Hard copy", case=False).sum()))
fig("queries.other_on_hold_text", int(other_txt.str.contains("on hold", case=False).sum()))
fig("queries.other_company_name_text", int(other_txt.str.contains("company name", case=False).sum()))
fig("queries.other_bank_details_text", int(other_txt.str.contains("bank details", case=False).sum()))
tmpl = q.query_text.str.replace(r"TRK\d+x*|V\d+|\b\d{7}\b|[\d/\-]+", "#", regex=True)
fig("queries.templates", tmpl.nunique(), "distinct query texts after masking numbers")
fig("queries.templates_in_more_than_one_category", int((q.assign(t=tmpl).groupby("t").query_category.nunique() > 1).sum()))
issue("D13", "queries", "raised_date after the paid_date on the bill", len(late_q), "FLAG", "A query cannot follow payment. "
      "All 18 sit inside the D03 set, which is more evidence that paid_date is the wrong field there.")
issue("D14", "queries", "query_category is Other", (q.query_category == "Other").sum(), "FLAG; re-label from query_text in analysis",
      "7 fixed texts, so they can be mapped by rule. Do not trust query_category for cause analysis (AP lead warned of this).")

# ---------------------------------------------------------------- weekday patterns
fig("weekday.ho_received_not_friday", int((df.ho_received_date.dt.dayofweek.dropna() != 4).sum()))
fig("weekday.posted_on_saturday", int((df.posted_date.dt.dayofweek == 5).sum()))
fig("weekday.posted_on_sunday", int((df.posted_date.dt.dayofweek == 6).sum()))
fig("weekday.posted_weekend_share", round(float(df.posted_date.dt.dayofweek.dropna().ge(5).mean()), 3))
issue("D15", "bill_register", "posted_date on a Saturday or Sunday",
      int((df.posted_date.dt.dayofweek >= 5).sum()), "FLAG (do not use for weekday analysis)",
      "Spread roughly evenly over all seven days while ho_received is always a Friday and valid paid_date is a Tuesday or Friday. "
      "Treat posted_date as day-accurate at best.")

# ---------------------------------------------------------------- amounts and GST
ok_rate = (df.gst_inr / df.amount_inr).round(2)
fig("gst.rate_18pct_rows", int((ok_rate == 0.18).sum()))
fig("gst.rate_zero_rows", int((df.gst_inr == 0).sum()))
fig("gst.rate_zero_all_diesel", bool((df.loc[df.gst_inr == 0, "category"] == "Diesel Supply").all()))
fig("gst.diesel_rows_nonzero_gst", int(((df.category == "Diesel Supply") & (df.gst_inr != 0)).sum()))
fig("gst.rate_other_rows", int((~ok_rate.isin([0.18, 0.0])).sum()))
fig("amount.invoice_negative_or_zero", int(((df.doc_type == "invoice") & (df.amount_inr <= 0)).sum()))
fig("amount.credit_note_positive_or_zero", int(((df.doc_type == "credit_note") & (df.amount_inr >= 0)).sum()))
fig("amount.credit_notes", int((df.doc_type == "credit_note").sum()))
fig("amount.invoice_min", float(df.loc[df.doc_type == "invoice", "amount_inr"].min()))
fig("amount.invoice_max", float(df.loc[df.doc_type == "invoice", "amount_inr"].max()))
fig("amount.credit_note_min", float(df.loc[df.doc_type == "credit_note", "amount_inr"].min()))
fig("amount.credit_note_max", float(df.loc[df.doc_type == "credit_note", "amount_inr"].max()))
fig("amount.gst_sign_differs_nonzero", int((((df.gst_inr > 0) & (df.amount_inr < 0)) | ((df.gst_inr < 0) & (df.amount_inr > 0))).sum()))

# ---------------------------------------------------------------- vendors
fig("vendors.gstin_bad_format", int((~vendors.gstin.str.match(r"^\d{2}[A-Z]{5}\d{4}[A-Z]\dZ[A-Z0-9]$")).sum()))
fig("vendors.gstin_duplicate", int(vendors.gstin.duplicated().sum()))
fig("vendors.name_duplicate_normalised", int(vendors.vendor_name.str.lower().str.replace(r"\W", "", regex=True).duplicated().sum()))
code = {"03": "Punjab", "06": "Haryana", "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh"}
fig("vendors.gstin_state_prefix_ne_state", int((vendors.gstin.str[:2].map(code) != vendors.state).sum()))
fig("vendors.no_bills", int((~vendors.vendor_id.isin(df.vendor_id)).sum()))
fig("vendors.no_work_orders", int((~vendors.vendor_id.isin(wo.vendor_id)).sum()))
rep = vendors.vendor_name.apply(lambda s: len(s.split()) != len({w.lower() for w in s.split()}))
fig("vendors.name_repeated_word", int(rep.sum()), "vendor names with a word repeated, e.g. 'Ojas Ojas Traders'")
core = (vendors.vendor_name.str.lower().str.replace(r"\b(pvt|ltd|llp|private|limited|enterprises|services|solutions)\b", "", regex=True)
        .str.replace(r"\s+", " ", regex=True).str.strip().tolist())
near = []
for i in range(len(core)):
    for j in range(i + 1, len(core)):
        if abs(len(core[i]) - len(core[j])) <= 4 and difflib.SequenceMatcher(None, core[i], core[j]).ratio() > 0.9:
            near.append((vendors.vendor_id[i], vendors.vendor_id[j]))
fig("vendors.near_duplicate_name_pairs", len(near), "pairs with name similarity above 0.9 once suffixes are removed")
nv = vendors.set_index("vendor_id")
fig("vendors.near_pairs_same_state_and_category",
    sum((nv.state[a] == nv.state[b]) and (nv.category[a] == nv.category[b]) for a, b in near))
pd.DataFrame([dict(vendor_a=a, name_a=nv.vendor_name[a], vendor_b=b, name_b=nv.vendor_name[b],
                   same_state=nv.state[a] == nv.state[b], same_category=nv.category[a] == nv.category[b])
              for a, b in near]).to_csv(OUT / "vendor_near_duplicates.csv", index=False)
issue("D16", "vendors", "vendor_name has a repeated word (e.g. Ojas Ojas Traders)", rep.sum(), "FLAG", "Cosmetic; ids and GSTINs are unique.")
issue("D17", "vendors", "name similarity above 0.9 to another vendor (suffixes ignored)", len(near), "FLAG for review, do not merge",
      "No two vendors share a GSTIN or a normalised name. These pairs differ in one word (for example Ojas vs Tejas "
      "Elevator Care); 7 also share state and category and are listed in vendor_near_duplicates.csv for a human to rule on.")
issue("D18", "vendors", "vendor with no bills and no work orders", int((~vendors.vendor_id.isin(df.vendor_id)).sum()), "KEEP", "Harmless.")

# ---------------------------------------------------------------- properties
fig("properties.residential", int((props.property_type == "Residential Society").sum()))
fig("properties.office", int((props.property_type == "Office Tower").sum()))
fig("properties.mall", int((props.property_type == "Retail Mall").sum()))

# ---------------------------------------------------------------- attendance
fig("attendance.biometric_blank_punch_out", int((bio.punch_out == "").sum()))
fig("attendance.biometric_guards", bio.guard_id.nunique())
fig("attendance.biometric_days", bio.date.nunique())
fig("attendance.biometric_missing_guard_days", bio.guard_id.nunique() * bio.date.nunique() - len(bio))
fig("attendance.biometric_duplicate_guard_day", int(bio.duplicated(["date", "guard_id"]).sum()))
fig("attendance.gate_rows", len(gate))
fig("attendance.gate_rows_reliever", int(gate.person_id.str.startswith("R-").sum()))
fig("attendance.gate_remarks_reliever", int(gate.remarks.str.startswith("Reliever").sum()))
fig("attendance.claim_people", len(claim))
fig("attendance.claim_relievers_not_in_biometric", int((~claim.person_id.isin(bio.guard_id)).sum()))
fig("attendance.gate_duplicate", int(gate.duplicated(["date", "person_id", "shift"]).sum()))
issue("D19", "attendance-sample", "biometric punch_out blank", (bio.punch_out == "").sum(), "FLAG",
      "Forgotten punch-outs, as the commercial executive described; the day still counts as present for matching.")

# ---------------------------------------------------------------- flags summary and outputs
flag_cols = [c for c in df.columns if c.startswith("f_")]
df["n_flags"] = df[flag_cols].sum(axis=1)
for c in flag_cols:
    fig(f"flag.{c}", int(df[c].sum()))
fig("flag.bills_with_any_flag", int((df.n_flags > 0).sum()))
fig("flag.bills_with_no_flag", int((df.n_flags == 0).sum()))
fig("flag.excl_f_msme_unknown_bills_with_any_flag", int((df[[c for c in flag_cols if c != "f_msme_unknown"]].sum(axis=1) > 0).sum()))

fig("bill_register.columns", len(cols), "columns in bill_register.csv")
fig("msme.vendors_blank_pct", round(100 * (vendors.msme_status == "").mean(), 1), "% of vendors with blank msme_status")
fig("msme.bills_unknown_pct", round(100 * df.f_msme_unknown.mean(), 1), "% of bills from vendors with blank msme_status")
fig("wo.bills_after_valid_to_pct", round(100 * df.f_invoice_after_wo_expiry.mean(), 1), "% of bills dated after WO valid_to")
fig("wo.billed_gt_approved_pct", round(100 * over.mean(), 1), "% of work orders billed above approved value")
fig("queries.category_other_pct", round(100 * (q.query_category == "Other").mean(), 1), "% of queries categorised Other")
fig("weekday.posted_weekend_count", int((df.posted_date.dt.dayofweek >= 5).sum()), "posted_date on Saturday or Sunday")
fig("flag.bills_with_any_flag_pct",round(100 * (df.n_flags > 0).mean(), 1))
fig("flag.bills_any_flag_excl_msme_pct", round(100 * (df[[c for c in flag_cols if c != "f_msme_unknown"]].sum(axis=1) > 0).mean(), 1))
fig("out.rows_in", len(raw))
fig("out.rows_excluded", len(excl))
fig("out.rows_out", len(df))
fig("out.values_changed", len(changes))

df = df.drop(columns=["source_row"]).reset_index(drop=True)
df.to_parquet(OUT / "bills_clean.parquet", index=False)
excl.to_csv(OUT / "exclusions.csv", index=False)
pd.DataFrame(changes).to_csv(OUT / "changes.csv", index=False)
pd.DataFrame(issues).to_csv(OUT / "issues.csv", index=False)
pd.DataFrame([dict(id=k, value=v, description=d) for k, (v, d) in figs.items()]).to_csv(OUT / "figures.csv", index=False)

assert len(raw) == len(df) + len(excl), "rows lost without a log entry"
print(f"in={len(raw)} excluded={len(excl)} out={len(df)} values_changed={len(changes)}")
print(f"wrote {OUT / 'bills_clean.parquet'}")
print(pd.DataFrame(issues)[["id", "table", "rows", "action"]].to_string(index=False))
