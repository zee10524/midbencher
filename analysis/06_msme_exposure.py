"""MSME late-payment exposure, from analysis/out/bills_clean.parquet.

Data only. No legal conclusions: the legal reading and its sources are in notes/research.md.

CLOCK DEFINITION (stated once, used everywhere)
  Day 0 is the clock-start date. A bill is paid within 45 days if paid_date - start <= 45 calendar days,
  late if it is 46 or more. Three starts are shown, in the order they happen to a bill:
    invoice_date            the date on the vendor's bill (bracket: closest to when the service was rendered)
    desk_received_date      the facility desk logs the bill
    property_verified_date  the commercial executive finishes checks and creates the service entry / GRN
  The payment policy says the 45 days run from "accepting the goods or services". The service entry / GRN is the
  company's own record of accepting, so property_verified_date is the closest to the policy wording.

POPULATION   invoices only (credit notes are excluded). Paid analysis uses invoices with a trustworthy paid_date
             (the 110 invoices in data-audit D03 have no usable payment date and are counted separately).
VALUE        amount_inr (before GST) and amount_inr + gst_inr.
STATUS       Micro, Small, Medium, Not MSME, Unknown (blank in the vendor master).
BLANKS       No honest way to know. Three cases: none are Micro/Small (low), the share found among vendors with a known
             status (central), all are (high). See the figures for why the central share is used.

Writes (analysis/out/): msme_exposure.csv, msme_open_bills.csv, figures_msme.csv, and notes/msme-exposure.md.
Run: python analysis/06_msme_exposure.py   (after analysis/clean.py)
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
ASOF = pd.Timestamp("2026-04-30")      # status date in the data dictionary
FYE = pd.Timestamp("2026-03-31")       # end of the financial year the bills belong to
LIMIT = 45
CLOCKS = {"invoice_date": "invoice date", "desk_received_date": "desk received", "property_verified_date": "property verified"}
GROUPS = ["Micro", "Small", "Medium", "Not MSME", "Unknown"]
KEY = {"Micro": "micro", "Small": "small", "Medium": "medium", "Not MSME": "notmsme", "Unknown": "unknown"}
figs: dict[str, tuple] = {}
rows: list[dict] = []


def fig(k, v, d=""):
    figs[k] = (v, d)


b = pd.read_parquet(OUT / "bills_clean.parquet")
inv = b[b.doc_type == "invoice"].copy()
inv["gross"] = inv.amount_inr + inv.gst_inr
fig("pop.invoices", len(inv), "invoices (credit notes excluded)")
fig("pop.credit_notes_excluded", int((b.doc_type != "invoice").sum()))
paid = inv[inv.paid_date.notna()]
bad_date = inv[inv.f_paid_before_posted]
open_ = inv[inv.paid_date_raw.isna()]
fig("pop.paid_analysed", len(paid), "invoices with a trustworthy payment date")
fig("pop.paid_date_unusable", len(bad_date), "invoices whose payment date is unusable (D03)")
fig("pop.open", len(open_), "invoices unpaid at 30 Apr 2026")
assert len(paid) + len(bad_date) + len(open_) == len(inv)

# ---------------------------------------------------------------- the blank-status assumption
v = pd.read_csv(ROOT / "pack" / "data" / "vendors.csv", dtype=str, keep_default_na=False)
known = v[v.msme_status != ""]
ms_known = known.msme_status.isin(["Micro", "Small"])
P = float(ms_known.mean())
fig("assume.vendors_blank", int((v.msme_status == "").sum()), "vendors with blank MSME status")
fig("assume.vendors_known", len(known), "vendors with a known status")
fig("assume.known_micro_small", int(ms_known.sum()), "known vendors that are Micro or Small")
fig("assume.share_micro_small_known", round(100 * P, 1), "% of known-status vendors that are Micro or Small (the central assumption)")
va = inv.groupby("vendor_id").amount_inr.sum().rename("billed")
kk = known.merge(va, left_on="vendor_id", right_index=True, how="left").fillna({"billed": 0})
kk["q"] = pd.qcut(kk.billed, 4, labels=False)
qs = kk.groupby("q").msme_status.apply(lambda s: 100 * s.isin(["Micro", "Small"]).mean())
fig("assume.share_by_billing_quartile_min", round(float(qs.min()), 1), "lowest Micro/Small share across four billing-size quartiles of known vendors")
fig("assume.share_by_billing_quartile_max", round(float(qs.max()), 1), "highest")
blank_billed = v[v.msme_status == ""].merge(va, left_on="vendor_id", right_index=True, how="left").fillna({"billed": 0}).billed
fig("assume.blank_median_billed", float(blank_billed.median()), "median yearly billing of blank-status vendors (INR)")
fig("assume.known_median_billed", float(kk.billed.median()), "median yearly billing of known-status vendors (INR)")
cat_share = known.assign(ms=ms_known).groupby("category").ms.mean()
blanks_by_cat = v[v.msme_status == ""].groupby("category").size()
strat = float((blanks_by_cat * cat_share.reindex(blanks_by_cat.index)).sum())
fig("assume.expected_blank_micro_small_central", round(P * (v.msme_status == "").sum(), 1), "expected Micro/Small among blank vendors at the central share")
fig("assume.expected_blank_micro_small_by_category", round(strat, 1), "same, using each spend category's own known share")
fig("assume.category_share_min", round(100 * float(cat_share.min()), 1)); fig("assume.category_share_max", round(100 * float(cat_share.max()), 1))
SC = {"low": 0.0, "central": P, "high": 1.0}


# ---------------------------------------------------------------- paid late, by group and clock
def paid_stats(df, clock):
    d = (df.paid_date - df[clock]).dt.days
    late = d > LIMIT
    return dict(n_paid=len(df), val_paid_ex_gst=float(df.amount_inr.sum()), n_late=int(late.sum()),
                val_late_ex_gst=float(df.loc[late, "amount_inr"].sum()), val_late_incl_gst=float(df.loc[late, "gross"].sum()),
                n_late_60=int((d > 60).sum()), val_late_60_ex_gst=float(df.loc[d > 60, "amount_inr"].sum()),
                n_late_15=int((d > 15).sum()),
                median_days_over_limit=float((d[late] - LIMIT).median()) if late.any() else np.nan,
                mean_days_to_pay=float(d.mean()))


def add(table, group, clock, stats):
    for k, val in stats.items():
        rows.append(dict(table=table, group=group, clock=clock, metric=k, value=val))
        if table == "paid_late":
            fig(f"e.paid.{clock.replace('_date', '')}.{group}.{k}", round(float(val), 2) if pd.notna(val) else val)
    if table == "paid_late":  # shares, so every percentage quoted in the notes is a registered figure
        for k, nm in (("n_late", "pct_late"), ("n_late_15", "pct_late_15"), ("n_late_60", "pct_late_60")):
            days_ = {"pct_late": 45, "pct_late_15": 15, "pct_late_60": 60}[nm]
            fig(f"e.paid.{clock.replace('_date', '')}.{group}.{nm}", round(100 * stats[k] / stats["n_paid"], 1),
                f"% of {group} paid invoices paid more than {days_} days after {clock}")


for c in CLOCKS:
    for g in GROUPS:
        add("paid_late", KEY[g], c, paid_stats(paid[paid.msme_status == g], c))
    ms = paid[paid.msme_status.isin(["Micro", "Small"])]
    add("paid_late", "microsmall_known", c, paid_stats(ms, c))
    add("paid_late", "all_statuses", c, paid_stats(paid, c))

for c in CLOCKS:  # spread of the late share across the five statuses
    ck = c.replace("_date", "")
    ss = [figs[f"e.paid.{ck}.{g}.pct_late"][0] for g in ("micro", "small", "unknown", "medium", "notmsme")]
    fig(f"e.paid.{ck}.status_pct_late_min", min(ss), f"lowest share paid over 45 days across the five statuses, clock {c}")
    fig(f"e.paid.{ck}.status_pct_late_max", max(ss), f"highest share, clock {c}")
for c in CLOCKS:  # what a 15-day limit would show (used only in notes/research.md, which explains when it could apply)
    k = f"e.paid.{c.replace('_date', '')}.microsmall_known."
    fig(f"e.sens15.{c.replace('_date', '')}.pct_late_over_15", round(100 * figs[k + "n_late_15"][0] / figs[k + "n_paid"][0], 1),
        f"% of known Micro/Small paid invoices paid more than 15 days after {c}")


# ---------------------------------------------------------------- unpaid and past 45 days at year end (31 Mar 2026) and now (30 Apr 2026)
def snap(df, clock, at):
    """invoices not yet paid on `at` and past 45 days from the clock start on `at`. Payment date unusable rows are left out."""
    started = df[df[clock] <= at]
    unpaid = started[started.paid_date.isna() | (started.paid_date > at)]
    unpaid = unpaid[~unpaid.f_paid_before_posted]
    past = unpaid[(at - unpaid[clock]).dt.days > LIMIT]
    return dict(n_unpaid=len(unpaid), n_past45=len(past), val_past45_ex_gst=float(past.amount_inr.sum()), val_past45_incl_gst=float(past.gross.sum()))


for at, tag in [(FYE, "ye"), (ASOF, "now")]:
    for c in CLOCKS:
        for g in GROUPS:
            s = snap(inv[inv.msme_status == g], c, at)
            for k, val in s.items():
                rows.append(dict(table=f"unpaid_{tag}", group=KEY[g], clock=c, metric=k, value=val))
                fig(f"e.{tag}.{c.replace('_date', '')}.{KEY[g]}.{k}", round(val, 2))
        s = snap(inv[inv.msme_status.isin(["Micro", "Small"])], c, at)
        for k, val in s.items():
            rows.append(dict(table=f"unpaid_{tag}", group="microsmall_known", clock=c, metric=k, value=val))
            fig(f"e.{tag}.{c.replace('_date', '')}.microsmall_known.{k}", round(val, 2))

# paid date unusable
for g in GROUPS:
    s = bad_date[bad_date.msme_status == g]
    rows.append(dict(table="paid_date_unusable", group=KEY[g], clock="", metric="n", value=len(s)))
    rows.append(dict(table="paid_date_unusable", group=KEY[g], clock="", metric="val_ex_gst", value=float(s.amount_inr.sum())))
    fig(f"e.d03.{KEY[g]}.n", len(s)); fig(f"e.d03.{KEY[g]}.val_ex_gst", round(float(s.amount_inr.sum()), 0))

# ---------------------------------------------------------------- scenarios for the blank vendors
R = pd.DataFrame(rows)
def val(table, group, clock, metric):
    s = R[(R.table == table) & (R.group == group) & (R.clock == clock) & (R.metric == metric)].value
    return float(s.iloc[0])
scen_rows = []
for c in CLOCKS:
    for table, metrics in [("paid_late", ["n_late", "val_late_ex_gst", "val_late_incl_gst"]), ("unpaid_ye", ["n_past45", "val_past45_ex_gst", "val_past45_incl_gst"]),
                           ("unpaid_now", ["n_past45", "val_past45_ex_gst", "val_past45_incl_gst"])]:
        for m in metrics:
            known_v = val(table, "microsmall_known", c, m)
            blank_v = val(table, "unknown", c, m)
            for sc, p in SC.items():
                x = known_v + p * blank_v
                scen_rows.append(dict(table=f"scenario_{table}", group=sc, clock=c, metric=m, value=x))
                fig(f"e.scen.{table}.{c.replace('_date', '')}.{m}.{sc}", round(x, 1))
S_ = pd.DataFrame(scen_rows)
pd.concat([R, S_], ignore_index=True).to_csv(OUT / "msme_exposure.csv", index=False, lineterminator="\n")

# ---------------------------------------------------------------- the open bills nearest to 45 days
o = open_.copy()
o["limit_applies"] = np.where(o.msme_status.isin(["Micro", "Small"]), "45 days (Micro/Small)",
                     np.where(o.msme_status == "Unknown", "45 days if Micro/Small (status blank)", "not 45 days (60-day policy)"))
for c, short in [("invoice_date", "inv"), ("desk_received_date", "desk"), ("property_verified_date", "ver")]:
    o[f"age_{short}"] = (ASOF - o[c]).dt.days
    o[f"deadline_{short}"] = o[c] + pd.Timedelta(days=LIMIT)
    o[f"days_left_{short}"] = LIMIT - o[f"age_{short}"]
runs = pd.date_range(ASOF + pd.Timedelta(days=1), periods=120, freq="D")
runs = runs[runs.dayofweek.isin([1, 4])]  # Tuesday, Friday payment runs
o["runs_left_before_desk_deadline"] = [int((runs <= d).sum()) for d in o.deadline_desk]
o["runs_left_before_ver_deadline"] = [int((runs <= d).sum()) for d in o.deadline_ver]
o["payable_now"] = o.status.eq("Posted")
cols = ["bill_id", "vendor_id", "vendor_name", "msme_status", "limit_applies", "property_code", "category", "status", "payable_now", "amount_inr", "gst_inr", "gross",
        "invoice_date", "desk_received_date", "property_verified_date", "age_desk", "days_left_desk", "deadline_desk", "runs_left_before_desk_deadline",
        "age_ver", "days_left_ver", "deadline_ver", "runs_left_before_ver_deadline", "age_inv", "days_left_inv"]
o = o.sort_values(["days_left_desk", "bill_id"])
o[cols].to_csv(OUT / "msme_open_bills.csv", index=False, date_format="%Y-%m-%d", lineterminator="\n")
ms_open = o[o.msme_status.isin(["Micro", "Small", "Unknown"])]
for g in ("Micro", "Small", "Unknown"):
    s = o[o.msme_status == g]
    fig(f"open.{KEY[g]}.n", len(s), f"open invoices, {g}")
    fig(f"open.{KEY[g]}.n_breached_desk", int((s.days_left_desk < 0).sum()), f"...already past 45 days from desk receipt")
    fig(f"open.{KEY[g]}.n_breached_ver", int((s.days_left_ver < 0).sum()), "...already past 45 days from property verification")
    fig(f"open.{KEY[g]}.n_within14_desk", int(s.days_left_desk.between(0, 14).sum()), "...not yet past, 14 days or fewer left (desk clock)")
    fig(f"open.{KEY[g]}.n_within14_ver", int(s.days_left_ver.between(0, 14).sum()))
    fig(f"open.{KEY[g]}.n_posted", int(s.payable_now.sum()), "...with status Posted, so treasury can pay them")
fig("open.ms_unknown.n", len(ms_open), "open Micro, Small and Unknown invoices")
near = ms_open[ms_open.days_left_desk >= 0]
fig("open.ms_unknown.n_not_yet_breached_desk", len(near)); fig("open.ms_unknown.n_no_run_left_desk", int((near.runs_left_before_desk_deadline == 0).sum()),
    "not yet past 45 days from desk, but no Tuesday or Friday payment run left before the deadline")
fig("open.ms_unknown.n_not_yet_breached_posted", int(near.payable_now.sum()), "...of those not yet past, with status Posted")
fig("open.ms_unknown.near_max_days_left", int(near.days_left_desk.max()))
fig("open.next_run", str(runs[0].date()), "first payment run after 30 Apr 2026")
pd.DataFrame([dict(id=k, value=v_, description=d_) for k, (v_, d_) in figs.items()]).to_csv(OUT / "figures_msme.csv", index=False, lineterminator="\n")

# ---------------------------------------------------------------- the readable note (numbers read from the figures above)
F = {k: v_[0] for k, v_ in figs.items()}
cr = lambda x: f"{x / 1e7:,.2f}"          # INR to crore
n0 = lambda x: f"{float(x):,.0f}"
p1 = lambda x: f"{float(x):.1f}%"


def pc(clock, g, k):
    return F[f"e.paid.{clock}.{g}.{k}"]


def tab_paid(clock):
    lines = ["| Vendor status | Paid invoices | Paid late (over 45 days) | Share late | Value late before GST (₹ crore) | Value late incl. GST (₹ crore) | Median days over the limit |",
             "|---|---|---|---|---|---|---|"]
    for g in ["micro", "small", "unknown", "medium", "notmsme"]:
        nm = {"micro": "Micro", "small": "Small", "unknown": "Blank (unknown)", "medium": "Medium", "notmsme": "Not MSME"}[g]
        lines.append(f"| {nm} | {n0(pc(clock, g, 'n_paid'))} | {n0(pc(clock, g, 'n_late'))} | {p1(100 * pc(clock, g, 'n_late') / pc(clock, g, 'n_paid'))} | "
                     f"{cr(pc(clock, g, 'val_late_ex_gst'))} | {cr(pc(clock, g, 'val_late_incl_gst'))} | {pc(clock, g, 'median_days_over_limit'):g} |")
    k = "microsmall_known"
    lines.append(f"| **Micro + Small (known)** | {n0(pc(clock, k, 'n_paid'))} | **{n0(pc(clock, k, 'n_late'))}** | {p1(100 * pc(clock, k, 'n_late') / pc(clock, k, 'n_paid'))} | "
                 f"**{cr(pc(clock, k, 'val_late_ex_gst'))}** | **{cr(pc(clock, k, 'val_late_incl_gst'))}** | {pc(clock, k, 'median_days_over_limit'):g} |")
    return "\n".join(lines)


def scen_line(table, clock, m_n, m_v, m_g):
    out = []
    for sc, lab in [("low", "0% of blanks"), ("central", f"{P * 100:.1f}% of blanks"), ("high", "100% of blanks")]:
        out.append(f"| {lab} | {n0(F[f'e.scen.{table}.{clock}.{m_n}.{sc}'])} | {cr(F[f'e.scen.{table}.{clock}.{m_v}.{sc}'])} | {cr(F[f'e.scen.{table}.{clock}.{m_g}.{sc}'])} |")
    return "\n".join(out)


md = []
md.append("# MSME late-payment exposure\n")
md.append("Data only, from `analysis/06_msme_exposure.py` (figure ids `e.*` and `assume.*`, `open.*` in `notes/numbers.md`). "
          "This note makes no legal finding; the legal reading and its sources are in `notes/research.md`. "
          "All amounts are rupees, shown in crore (1 crore = 10 million), for **invoices only** (credit notes excluded), bills dated 1 April 2025 to 31 March 2026, status at 30 April 2026.\n")
md.append("```\npython analysis/clean.py\npython analysis/06_msme_exposure.py   # or: mingw32-make analyse\n```\n")
md.append("## 1. The clock, stated explicitly\n")
md.append(f"- **Day 0 is the clock-start date. A bill is paid within 45 days if payment is 45 calendar days or fewer after day 0, and late if it is 46 or more.** Calendar days, no holiday adjustment.\n"
          "- **The payment policy says the 45 days run from accepting the goods or services.** The register has no delivery or acceptance date, so three stand-ins are shown in the order they occur to a bill:\n")
md.append("| Clock start | What the data dictionary says it is | Relation to acceptance |\n|---|---|---|")
md.append("| `invoice_date` | Date on the vendor's bill | Before or on the day the bill reaches the company. Not acceptance; shown as a bracket |")
md.append("| `desk_received_date` | Date the facility desk logged the bill | The company has the bill, not yet accepted the work |")
md.append("| `property_verified_date` | Date the commercial executive finished checks and created the service entry or GRN | The company's own record of accepting the goods or services |")
md.append("\n**Which is more defensible?** `property_verified_date`, as the reading of the policy's word 'accepting': the service entry or GRN is where the company records that the work or goods were accepted. "
          "It is also the latest of the three, so it gives the smallest late count. If acceptance is dated earlier than the service entry, the verified-date figures are a floor and the desk-date figures sit nearer the truth; "
          "the point at which acceptance is dated is a question for the client's advisers (see `notes/research.md`). I therefore headline both and treat the verified-date result as the floor and the desk-date result as the planning number.\n")
md.append("## 2. Paid late, by vendor status\n")
md.append(f"Paid invoices with a trustworthy payment date: {n0(F['pop.paid_analysed'])}. Another {n0(F['pop.paid_date_unusable'])} are marked Paid but their payment date is impossible (data-audit D03) and are not counted; their count is given below the tables. Medium and Not MSME vendors are shown for reference only: the 45-day figure is not their limit.\n")
md.append("### From `property_verified_date` (nearest to 'acceptance')\n")
md.append(tab_paid("property_verified"))
md.append("\n### From `desk_received_date`\n")
md.append(tab_paid("desk_received"))
md.append("\n### From `invoice_date` (bracket)\n")
md.append(tab_paid("invoice"))
sh_ = lambda c: [100 * pc(c, g, "n_late") / pc(c, g, "n_paid") for g in ["micro", "small", "unknown", "medium", "notmsme"]]
md.append(f"\nValue late is the sum of invoice amounts paid more than 45 days after the clock start. The late share is similar across the five statuses: "
          f"{min(sh_('property_verified')):.1f}% to {max(sh_('property_verified')):.1f}% from property verified, {min(sh_('desk_received')):.1f}% to {max(sh_('desk_received')):.1f}% from desk received, "
          f"{min(sh_('invoice')):.1f}% to {max(sh_('invoice')):.1f}% from invoice date, so Micro and Small vendors are not paid on a different footing from the rest. "
          f"{n0(F['e.d03.micro.n'] + F['e.d03.small.n'] + F['e.d03.unknown.n'])} of the unusable-date invoices belong to Micro, Small or blank-status vendors, worth ₹{cr(F['e.d03.micro.val_ex_gst'] + F['e.d03.small.val_ex_gst'] + F['e.d03.unknown.val_ex_gst'])} crore before GST.\n")
md.append("## 3. Still unpaid and past 45 days\n")
md.append("Two snapshots of invoices not yet paid and already past 45 days from the clock start: at 31 March 2026 (the end of the financial year the bills belong to) and at 30 April 2026 (the data cut-off). Invoices with an unusable payment date are left out.\n")
for tag, label in [("ye", "At 31 March 2026"), ("now", "At 30 April 2026")]:
    md.append(f"### {label}\n")
    md.append("| Clock | Micro | Small | Blank | Micro + Small (known): bills | Value before GST (₹ crore) | Value incl. GST (₹ crore) |\n|---|---|---|---|---|---|---|")
    for c, lab in [("property_verified", "property verified"), ("desk_received", "desk received"), ("invoice", "invoice date")]:
        g = lambda gr, k: F[f"e.{tag}.{c}.{gr}.{k}"]
        md.append(f"| {lab} | {n0(g('micro', 'n_past45'))} | {n0(g('small', 'n_past45'))} | {n0(g('unknown', 'n_past45'))} | **{n0(g('microsmall_known', 'n_past45'))}** | "
                  f"{cr(g('microsmall_known', 'val_past45_ex_gst'))} | {cr(g('microsmall_known', 'val_past45_incl_gst'))} |")
    md.append("")
md.append("## 4. Blank-status vendors: the assumption\n")
md.append(f"{n0(F['assume.vendors_blank'])} of 900 vendors have no MSME status. Nothing in the pack says how many are Micro or Small, so three cases are shown.\n")
md.append(f"- **Central: {F['assume.share_micro_small_known']:.1f}% of blank vendors are Micro or Small.** It is the share among the {n0(F['assume.vendors_known'])} vendors with a known status ({n0(F['assume.known_micro_small'])} Micro or Small). "
          f"Why this and not another figure: MSME status in the pack is unrelated to how much a vendor bills (the Micro/Small share is {F['assume.share_by_billing_quartile_min']:.1f}% to {F['assume.share_by_billing_quartile_max']:.1f}% in every billing quartile), "
          f"so there is no size signal to separate blanks from the rest; blank vendors bill a median of ₹{n0(F['assume.blank_median_billed'])} a year against ₹{n0(F['assume.known_median_billed'])} for known vendors, somewhat lower but the same scale; "
          f"and the share by spend category ({F['assume.category_share_min']:.0f}% to {F['assume.category_share_max']:.0f}%) gives {F['assume.expected_blank_micro_small_by_category']:.0f} expected Micro/Small blanks against {F['assume.expected_blank_micro_small_central']:.0f} at the overall share, so category changes little.")
md.append("- **Low: none are.** The known-status figures stand alone.")
md.append("- **High: all are.** This is the ceiling.")
md.append("- **What could move it.** The CFO and the procurement executive both said some vendors registered after they began trading with the company and the master was never updated, which would push the true share above the base rate; "
          "a vendor registered later than a bill may not count for that bill (see `notes/research.md`), which would push it below. The pack has no registration dates, so the central case is a base rate, not a finding.\n")
md.append("Exposure under the three cases (expected values; each blank vendor is either Micro/Small or not, so these are averages over the assumption):\n")
for table, clock, lab, mn, mv, mg in [("paid_late", "property_verified", "Paid late, from property verified", "n_late", "val_late_ex_gst", "val_late_incl_gst"),
                                      ("paid_late", "desk_received", "Paid late, from desk received", "n_late", "val_late_ex_gst", "val_late_incl_gst"),
                                      ("ye", "property_verified", "Unpaid and past 45 days at 31 Mar 2026, from property verified", "n_past45", "val_past45_ex_gst", "val_past45_incl_gst"),
                                      ("ye", "desk_received", "Unpaid and past 45 days at 31 Mar 2026, from desk received", "n_past45", "val_past45_ex_gst", "val_past45_incl_gst")]:
    t = "paid_late" if table == "paid_late" else "unpaid_ye"
    md.append(f"**{lab}**\n")
    md.append("| Blanks treated as Micro/Small | Bills | Value before GST (₹ crore) | Value incl. GST (₹ crore) |\n|---|---|---|---|")
    md.append(scen_line(t, clock, mn, mv, mg))
    md.append("")
md.append("## 5. Open bills closest to breaching 45 days, as of 30 April 2026\n")
md.append(f"Open invoices for Micro, Small and blank-status vendors: {n0(F['open.micro.n'] + F['open.small.n'] + F['open.unknown.n'])} "
          f"({n0(F['open.micro.n'])} Micro, {n0(F['open.small.n'])} Small, {n0(F['open.unknown.n'])} blank). Counted from the desk date, {n0(F['open.micro.n_breached_desk'] + F['open.small.n_breached_desk'] + F['open.unknown.n_breached_desk'])} are already past 45 days "
          f"({n0(F['open.micro.n_breached_ver'] + F['open.small.n_breached_ver'] + F['open.unknown.n_breached_ver'])} counted from property verification); {n0(F['open.ms_unknown.n_not_yet_breached_desk'])} are not yet past. "
          f"Of those, {n0(F['open.ms_unknown.n_not_yet_breached_posted'])} have status Posted and can be paid; the rest are still with AP, in query or in transit and cannot be paid at the next run whatever treasury does. "
          f"The next payment run is {F['open.next_run']} (Tuesdays and Fridays). The full list, with the ages on all three clocks, is `analysis/out/msme_open_bills.csv`.\n")
md.append("Ranked by days left on the desk clock (the earlier deadline). 'Runs left' counts Tuesday and Friday runs from 1 May up to the deadline; 0 means no run remains before the bill passes 45 days.\n")
md.append("| Bill | Vendor | Status of vendor | Bill status | Value incl. GST (₹) | Desk received | Days left (desk) | Deadline (desk) | Runs left | Days left (verified) |\n|---|---|---|---|---|---|---|---|---|---|")
for r in near.head(25).itertuples():
    md.append(f"| {r.bill_id} | {r.vendor_id} | {r.msme_status} | {r.status} | {r.gross:,.0f} | {r.desk_received_date.date()} | {r.days_left_desk} | {r.deadline_desk.date()} | {r.runs_left_before_desk_deadline} | {r.days_left_ver} |")
md.append(f"\nOf the not-yet-breached bills, {n0(F['open.ms_unknown.n_no_run_left_desk'])} have no payment run left before their desk-clock deadline.\n")
md.append("## 6. What this does and does not show\n")
md.append("- **The register has no delivery date and no payment-terms field.** The three clocks bracket the answer; they do not replace the date the policy names.")
md.append("- **The blank-status share is an assumption**, not a measurement (section 4). The known-status results do not depend on it.")
md.append("- **Value is invoice value.** It is not the amount of any tax or interest; it is the size of the bills involved.")
md.append("- **Unusable payment dates.** 110 invoices marked Paid cannot be placed on any clock (data-audit D03).")
(ROOT / "notes" / "msme-exposure.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
print("wrote notes/msme-exposure.md")
print(S_.pivot_table(index=["table", "metric"], columns=["clock", "group"], values="value").round(0).to_string())
