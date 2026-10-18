"""Rank the root causes of slow payment by days added x bills affected, and by who can fix each, then write notes/problem.md.

Population: the 10,449 paid invoices behind stage_times.csv (invoices, trustworthy paid_date). "Days on the mean" = mean days per affected bill
x share of bills affected = days the cause adds to the 37.6-day mean. It is the measure used for every row, so rows are comparable.

Two numbers per cause, and they must not be confused:
  CEILING    the whole stage or cause, all of it. What removing the cause entirely would take off.
  REMOVABLE  what a stated, data-based counterfactual takes off. Conservative end first, then the upper end.

Counterfactuals (all from the register, all assumptions stated in the note):
  AP queue         AP-1 bills wait as long as the other four verifiers' bills.
  Payment run      Every posted bill is paid at the first Tuesday or Friday run after posting plus a list lead of 2 days (conservative) or 0 days.
  Courier          A second weekly arrival (Tuesday and Friday) or a daily one, with the observed minimum lag of 2 days after signing.
  Day-one catch    From 04_query_forensics.py (layers A, A+B, A to C).
Typing and the portal get a ceiling only, because the data holds no counterfactual for either.

Writes notes/problem.md and analysis/out/figures_problem.csv.  Run: python analysis/08_problem_ranking.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
F, SRC = {}, {}
for fname, script in [("figures.csv", "clean.py"), ("figures_stage_times.csv", "02_stage_times.py"),
                      ("figures_query_forensics.csv", "04_query_forensics.py"), ("figures_msme.csv", "06_msme_exposure.py"),
                      ("figures_claims_tested.csv", "05_claims_tested.py")]:
    for r in pd.read_csv(OUT / fname, keep_default_na=False).itertuples():
        F[r.id] = r.value
        SRC[r.id] = script
own: dict[str, tuple] = {}


def fig(k, v, d=""):
    v = round(float(v), 2) if isinstance(v, (float, np.floating)) else v
    own[k] = (v, d)
    F[k] = v


def f(i):
    return float(F[i])


d1 = lambda i: f"{f(i):.1f}"
d2 = lambda i: f"{f(i):.2f}"
d0 = lambda i: f"{f(i):,.0f}"
pc = lambda i: f"{f(i):.1f}%"

b = pd.read_parquet(OUT / "bills_clean.parquet")
q = pd.read_csv(OUT / "query_forensics.csv", parse_dates=["paid_date"])
pop = b[(b.doc_type == "invoice") & b.paid_date.notna()].copy()
N = len(pop)
assert N == int(f("pop.invoices_analysed"))
fig("p.n", N, "paid invoices analysed")
MEAN = f("overall.s99.cal_mean")

# ------------------------------------------------------------------ payment run: days beyond the next Tuesday or Friday run
def first_run(d, gap):
    for k in range(gap, gap + 8):
        x = d + pd.Timedelta(days=k)
        if x.dayofweek in (1, 4):
            return x


pay_save = {}
for lead in (0, 1, 2):
    nr = pop.posted_date.apply(lambda d: first_run(d, 1 + lead))
    st = (nr - pop.posted_date).dt.days
    ex = (pop.paid_date - nr).dt.days
    fig(f"p.pay.schedule_wait_lead{lead}", st.mean(), f"mean days from posting to the first run, run list closing {lead} day(s) before the run")
    fig(f"p.pay.excess_lead{lead}", ex.clip(lower=0).mean(), f"mean days paid later than that run, run list closing {lead} day(s) before")
    fig(f"p.pay.share_late_lead{lead}", 100 * (ex > 0).mean(), f"% of bills paid later than that run, list closing {lead} day(s) before")
    pay_save[lead] = ex.clip(lower=0)
fig("p.pay.actual_wait", (pop.paid_date - pop.posted_date).dt.days.mean(), "mean days from posting to payment")
fig("p.pay.per_missed_bill", f("p.pay.excess_lead0") / (f("p.pay.share_late_lead0") / 100), "mean days late per bill that missed the next run (list lead 0)")

# ------------------------------------------------------------------ courier: second weekly arrival or daily
pop["lag"] = (pop.ho_received_date - pop.property_head_signed_date).dt.days


def arrival(d, days, minlag=2):
    for k in range(minlag, minlag + 9):
        x = d + pd.Timedelta(days=k)
        if x.dayofweek in days:
            return x


cour = {}
for name, days in [("friday_only", {4}), ("tue_fri", {1, 4}), ("mon_wed_fri", {0, 2, 4}), ("daily", set(range(7)))]:
    lag = pop.property_head_signed_date.apply(lambda d: arrival(d, days)).sub(pop.property_head_signed_date).dt.days
    cour[name] = lag
    fig(f"p.courier.lag_{name}", lag.mean(), f"mean days from signature to head office with arrivals: {name}")
assert abs(f("p.courier.lag_friday_only") - f("overall.s04.cal_mean")) < 0.01, "courier model does not reproduce the observed lag"
fig("p.courier.save_tue_fri", f("p.courier.lag_friday_only") - f("p.courier.lag_tue_fri"), "days off the mean with a second weekly arrival (Tue and Fri)")
fig("p.courier.save_daily", f("p.courier.lag_friday_only") - f("p.courier.lag_daily"), "days off the mean with a daily arrival")

# ------------------------------------------------------------------ AP queue: AP-1 against the other verifiers
pop["queue"] = (pop.ho_picked_date - pop.ho_received_date).dt.days
v = pop[pop.ho_verifier != ""]
a1, oth = v[v.ho_verifier == "AP-1"], v[v.ho_verifier != "AP-1"]
fig("p.queue.ap1_bills", len(a1), "paid invoices handled by AP-1")
fig("p.queue.ap1_share_pct", 100 * len(a1) / N, "% of paid invoices handled by AP-1")
fig("p.queue.ap1_wait", a1.queue.mean(), "mean days AP-1's bills wait for pick-up")
fig("p.queue.others_wait", oth.queue.mean(), "mean days the other four verifiers' bills wait")
fig("p.queue.gap_per_bill", a1.queue.mean() - oth.queue.mean(), "extra days AP-1's bills wait")
fig("p.queue.saving", (a1.queue.mean() - oth.queue.mean()) * len(a1) / N, "days off the mean if AP-1's bills waited like the others'")
fr = pop.groupby("ho_received_date").agg(n=("bill_id", "size"), qd=("queue", "mean"))
fr["qt"] = pd.qcut(fr.n, 4, labels=False)
fig("p.queue.wait_lightest_fridays", fr[fr.qt == 0].qd.mean(), "mean wait in the quarter of Fridays with the fewest bills")
fig("p.queue.wait_heaviest_fridays", fr[fr.qt == 3].qd.mean(), "mean wait in the quarter of Fridays with the most bills")
fig("p.queue.bills_lightest_fridays", fr[fr.qt == 0].n.mean(), "mean bills arriving on those lightest Fridays")
fig("p.queue.bills_heaviest_fridays", fr[fr.qt == 3].n.mean(), "mean bills arriving on those heaviest Fridays")

# ------------------------------------------------------------------ queries: days on the mean by owner and by cause
pq = q[(q.doc_type == "invoice") & q.paid_date.notna() & q.days_open.notna()]
fig("p.query.days_on_mean", pq.days_open.sum() / N, "query-open days added to the mean of all paid invoices")
fig("p.query.pct_bills", 100 * len(pq) / N, "% of paid invoices with a query")
for s_ in ("vendor", "property", "procurement", "head-office"):
    g = pq[pq.side == s_]
    fig(f"p.query.{s_}.days_on_mean", g.days_open.sum() / N, f"query-open days on the mean, {s_}-side")
    fig(f"p.query.{s_}.pct_bills", 100 * len(g) / N, f"% of paid invoices with a {s_}-side query")
cat = pq.groupby("category_clean").days_open.agg(["size", "sum"])
top = cat["sum"].idxmax()
fig("p.query.top_cause_days_on_mean", cat.loc[top, "sum"] / N, f"largest single query category: {top}")
fig("p.query.top_cause_pct_bills", 100 * cat.loc[top, "size"] / N, f"% of paid invoices with a {top} query")
TOP = top
fig("p.vendor_ceiling", f("overall.s01.cal_mean") + f("p.query.vendor.days_on_mean"), "vendor-to-desk days plus vendor-side query days: the most a portal could touch")
fig("p.typing.pct_of_total", 100 * f("overall.s06.cal_mean") / MEAN, "AP verification (the ceiling for typing) as % of the mean days to pay")

# ------------------------------------------------------------------ the three flow fixes together, and what they do to MSME lateness (desk clock)
low = f("p.queue.saving") + f("p.pay.excess_lead2") + f("p.courier.save_tue_fri")
high = f("p.queue.saving") + f("p.pay.excess_lead0") + f("p.courier.save_daily")
fig("p.flow.low", low, "days off the mean: AP-1 queue + payment run (list lead 2) + second weekly courier")
fig("p.flow.high", high, "days off the mean: AP-1 queue + payment run (list lead 0) + daily courier")
fig("p.flow.low_pct", 100 * low / MEAN, "same, as % of the mean"); fig("p.flow.high_pct", 100 * high / MEAN, "same, as % of the mean")
fig("p.head_office_fix.low", f("p.queue.saving") + f("p.pay.excess_lead2"), "days off the mean: AP-1 queue + payment run (list lead 2), the two proposed first")
fig("p.head_office_fix.high", f("p.queue.saving") + f("p.pay.excess_lead0"), "same, payment run with list lead 0")
fig("p.head_office_fix.low_pct", 100 * f("p.head_office_fix.low") / MEAN)
fig("p.head_office_fix.high_pct", 100 * f("p.head_office_fix.high") / MEAN)
ms = pop[pop.msme_status.isin(["Micro", "Small"])].copy()
tot = (ms.paid_date - ms.desk_received_date).dt.days
base = int((tot > 45).sum())
sv_pay = pay_save[2].reindex(ms.index)
sv_q = pd.Series(np.where(ms.ho_verifier == "AP-1", np.minimum(ms.queue, f("p.queue.gap_per_bill")), 0.0), index=ms.index)
sv_c = (pop.lag - cour["tue_fri"]).reindex(ms.index)
fig("p.msme.late_desk_base", base, "known Micro/Small paid invoices over 45 days from desk receipt")
fig("p.msme.late_desk_after_pay", int(((tot - sv_pay) > 45).sum()), "...if the payment-run fix (list lead 2) had applied")
fig("p.msme.late_desk_after_queue", int(((tot - sv_q) > 45).sum()), "...if the AP-1 queue fix had applied")
fig("p.msme.late_desk_after_both", int(((tot - sv_pay - sv_q) > 45).sum()), "...if both first fixes had applied")
fig("p.msme.late_desk_after_all3", int(((tot - sv_pay - sv_q - sv_c) > 45).sum()), "...if all three flow fixes had applied")
# the ceilings printed in the owner table below (each is a sum of registered stage means and query days), registered so that every figure in the note has an id
fig("p.owner.ap_lead.ceiling", float(F["overall.s05.cal_mean"]) + float(F["p.query.head-office.days_on_mean"]) + float(F["overall.s06.cal_mean"]), "central AP lead: days on the mean that the causes it owns could take at most (verifier wait, head-office queries, typing)")
fig("p.owner.property.ceiling", float(F["overall.s04.cal_mean"]) + float(F["overall.s03.cal_mean"]) + float(F["overall.s02.cal_mean"]) + float(F["p.query.property.days_on_mean"]), "property heads and executives: days on the mean that the causes they own could take at most (courier, signature, checks and service entry, property-side queries)")
pd.DataFrame([dict(id=k, value=v_, description=d_) for k, (v_, d_) in own.items()]).to_csv(OUT / "figures_problem.csv", index=False, lineterminator="\n")

# ------------------------------------------------------------------ the ranking
rows = [
    dict(key="queue", cause="Packet waits in the AP tray for a verifier", where="Head office, receipt to pick-up", aff=N, per=f("overall.s05.cal_mean"), ceil=f("overall.s05.cal_mean"),
         lo=f("p.queue.saving"), hi=f("p.queue.saving"), owner="Central AP lead", alone="Yes", risk="None",
         note=f"Bills handled by AP-1 ({pc('p.queue.ap1_share_pct')}) wait {d1('p.queue.ap1_wait')} d, the other four's {d1('p.queue.others_wait')} d. Load is not the driver: Fridays with {d0('p.queue.bills_lightest_fridays')} bills average {d1('p.queue.wait_lightest_fridays')} d, Fridays with {d0('p.queue.bills_heaviest_fridays')} bills {d1('p.queue.wait_heaviest_fridays')} d"),
    dict(key="vendor", cause="Vendor takes days to get the bill to the desk", where="Vendor to facility desk", aff=N, per=f("overall.s01.cal_mean"), ceil=f("overall.s01.cal_mean"),
         lo=None, hi=None, owner="Vendors (the company can only influence the intake channel)", alone="No", risk="None",
         note="No counterfactual in the data: the vendor's own time"),
    dict(key="pay", cause="Posted invoice misses the next payment run", where="Treasury, posting to paid", aff=N, per=f("overall.s08.cal_mean"), ceil=f("overall.s08.cal_mean"),
         lo=f("p.pay.excess_lead2"), hi=f("p.pay.excess_lead0"), owner="Treasury, with the AP lead for the run-list cut-off", alone="Yes", risk="Low: payment approvals unchanged, check the release control",
         note=f"The schedule needs {d1('p.pay.schedule_wait_lead0')} d on average but bills wait {d1('p.pay.actual_wait')} d; {pc('p.pay.share_late_lead0')} are paid after a later run than the next one. Low end assumes the run list closes 2 days before the run"),
    dict(key="check", cause="Property checks and service entry (work, not pure waiting)", where="Commercial executive, desk to verified", aff=N, per=f("overall.s02.cal_mean"), ceil=f("overall.s02.cal_mean"),
         lo=None, hi=None, owner="Commercial executives", alone="Yes", risk="Controls P1 to P9 sit here",
         note="Includes the hand matching of attendance (4 to 5 days a month, reported). No counterfactual in the data"),
    dict(key="courier", cause="Weekly courier to head office", where="Property head to head office", aff=N, per=f("overall.s04.cal_mean"), ceil=f("overall.s04.cal_mean"),
         lo=f("p.courier.save_tue_fri"), hi=f("p.courier.save_daily"), owner="Property heads, the courier arrangement, and audit if the paper stops being the booking trigger", alone="No: three parties and a cost", risk="Depends on the audit view of booking from a scan",
         note=f"Every packet arrives on a Friday; a bill signed on a Wednesday takes {d0('c.courier.lag_signed_wednesday')} d, on a Thursday 8 d. Low end: a second weekly arrival; high end: daily; both keep the observed 2-day minimum"),
    dict(key="query", cause="Queries (all causes together)", where="Back and forth between AP, property, vendor, procurement", aff=len(pq), per=f("query.mean_days_among_queried"), ceil=f("p.query.days_on_mean"),
         lo=f("layer.A.cum_days_off_mean_total"), hi=f("layer.ABC.cum_days_off_mean_total"), owner="Split: vendor, property, procurement, head office (rows below)", alone="No", risk="None",
         note=f"{pc('p.query.pct_bills')} of bills, {d1('query.mean_days_among_queried')} d each. Low end: day-one catch from the bill and SAP extract (layer A); high end: if SAP also exposes work-order lines, rates and open quantity (layers A to C)"),
    dict(key="typing", cause="AP verification, including any typing", where="Central AP, pick-up to posting (no query open)", aff=N, per=f("overall.s06.cal_mean"), ceil=f("overall.s06.cal_mean"),
         lo=None, hi=None, owner="Central AP, IT for any reader", alone="Yes", risk="Controls H1 to H14 sit here",
         note=f"{pc('p.typing.pct_of_total')} of the mean. This is the ceiling for typing: verification is checking as well as keying"),
    dict(key="sign", cause="Property head's signature", where="Property head, verified to signed", aff=N, per=f("overall.s03.cal_mean"), ceil=f("overall.s03.cal_mean"),
         lo=None, hi=None, owner="Property heads", alone="Yes", risk="Control P11",
         note="75% are signed within 2 days (`c.prop.sign_step_le2_pct`)"),
]
rows.sort(key=lambda r: -r["ceil"])
for i, r in enumerate(rows, 1):
    r["rank_ceiling"] = i
ev = sorted([r for r in rows if r["lo"] is not None], key=lambda r: -(r["lo"] + (r["hi"] if r["hi"] else r["lo"])) )
for i, r in enumerate(ev, 1):
    r["rank_removable"] = i
for r in rows:
    r.setdefault("rank_removable", None)
R = {r["key"]: r for r in rows}


def rng(r):
    if r["lo"] is None:
        return "no counterfactual"
    return f"{r['lo']:.2f}" if abs(r["hi"] - r["lo"]) < 0.005 else f"{r['lo']:.2f} to {r['hi']:.2f}"


tbl = ["| Rank by days × bills | Root cause | Bills affected | Days per affected bill | **Days × bills** (days on the 37.6-day mean) | Removable on evidence (days on the mean) | Rank by removable | Who can fix | Alone? | Control risk |",
       "|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    share = 100 * r["aff"] / N
    tbl.append(f"| {r['rank_ceiling']} | **{r['cause']}**<br>{r['where']} | {r['aff']:,} ({share:.1f}%) | {r['per']:.1f} | **{r['ceil']:.2f}** | {rng(r)} | {r['rank_removable'] if r['rank_removable'] else 'n/a'} | {r['owner']} | {r['alone']} | {r['risk']} |")
TABLE = "\n".join(tbl)
NOTES = "\n".join(f"- **{r['cause']}.** {r['note']}." for r in rows)

own_tbl = ["| Owner | Causes they can fix | Ceiling (days on the mean) | Removable on evidence |", "|---|---|---|---|",
           f"| **Central AP lead** | Wait for a verifier; head-office-side queries ({pc('p.query.head-office.pct_bills')} of bills); typing | {f('overall.s05.cal_mean') + f('p.query.head-office.days_on_mean') + f('overall.s06.cal_mean'):.2f} | {f('p.queue.saving'):.2f} |",
           f"| **Treasury** | Payment-run lag | {f('overall.s08.cal_mean'):.2f} | {f('p.pay.excess_lead2'):.2f} to {f('p.pay.excess_lead0'):.2f} |",
           f"| **Property heads and executives** | Courier; signature; checks and service entry; property-side queries ({pc('p.query.property.pct_bills')} of bills) | {f('overall.s04.cal_mean') + f('overall.s03.cal_mean') + f('overall.s02.cal_mean') + f('p.query.property.days_on_mean'):.2f} | {f('p.courier.save_tue_fri'):.2f} to {f('p.courier.save_daily'):.2f} (courier only) |",
           f"| **Procurement** | Work-order balance, validity and PO queries ({pc('p.query.procurement.pct_bills')} of bills) | {f('p.query.procurement.days_on_mean'):.2f} | within the query row above |",
           f"| **Vendors** | Delay to the desk; vendor-side queries ({pc('p.query.vendor.pct_bills')} of bills) | {f('overall.s01.cal_mean') + f('p.query.vendor.days_on_mean'):.2f} | not measurable |"]
OWN = "\n".join(own_tbl)

md = f"""# The problem

Built by `analysis/08_problem_ranking.py` from the paid-invoice analysis ({N:,} invoices). Every number is registered in `notes/numbers.md` (ids `p.*`, plus the figure ids they read). Rankings use measured days and the stated counterfactuals; nothing here is opinion about who is to blame.

## The biggest issue, in one sentence

**A bill is worked on for about {MEAN * f('overall.s98.share'):.0f} of its {MEAN:.0f} days and waits for the rest, and the two longest waits inside our own walls are {f('overall.s05.cal_mean'):.0f} days in the AP tray before anyone opens the packet and {f('overall.s08.cal_mean'):.0f} days after posting for a payment run that is only {f('p.pay.schedule_wait_lead0'):.0f} days away on average.**

## Solve first: two problems

1. **Posted invoices miss the next payment run** (Treasury). Bills wait {d1('p.pay.actual_wait')} days after posting; if each were paid at the first Tuesday or Friday run the wait would be {d1('p.pay.schedule_wait_lead0')} days, and even if the run list closes two days ahead it would be {d1('p.pay.schedule_wait_lead2')}. {pc('p.pay.share_late_lead0')} of bills are paid at a later run than the next. That removes **{d2('p.pay.excess_lead2')} to {d2('p.pay.excess_lead0')} days** from the mean, sits with head-office finance, and changes no control.
2. **Packets wait for a verifier** (central AP). The longest single wait, {d1('overall.s05.cal_mean')} days. AP-1 handles {pc('p.queue.ap1_share_pct')} of bills and those bills wait {d1('p.queue.gap_per_bill')} days longer than the others'. Bringing them level removes **{d2('p.queue.saving')} days** from the mean. It is not a headcount problem: the wait is {d1('p.queue.wait_lightest_fridays')} days when {d0('p.queue.bills_lightest_fridays')} bills arrive and {d1('p.queue.wait_heaviest_fridays')} when {d0('p.queue.bills_heaviest_fridays')} do, so it is how and when bills are picked up.

**Why these two.** Together they take **{d2('p.head_office_fix.low')} to {d2('p.head_office_fix.high')} days** ({pc('p.head_office_fix.low_pct')} to {pc('p.head_office_fix.high_pct')} of the mean) off the 37.6-day mean. Both sit with head-office finance (the AP lead and treasury), neither depends on vendors, property heads, the courier or an audit view, and no control is removed. The courier ties the AP queue on conservative days (1.70 against 1.65) but sits outside head office and depends on property heads and, for its best form, an audit view. Applied to the year's known Micro and Small invoices, the payment-run fix alone would have taken desk-clock late bills from {d0('p.msme.late_desk_base')} to {d0('p.msme.late_desk_after_pay')}; both fixes together to {d0('p.msme.late_desk_after_both')} (`notes/msme-exposure.md` for the clock).

## Why typing, the courier and a portal rank lower

- **Typing: ceiling {d2('overall.s06.cal_mean')} days, {pc('p.typing.pct_of_total')} of the mean.** All of AP verification, including the checks, is smaller than either first fix on its own conservative figure ({d2('p.queue.saving')} and {d2('p.pay.excess_lead2')}). Deleting typing outright changes nothing about the {100 * f('overall.s97.share'):.0f}% of the mean that is waiting. The earlier OCR pilot is the same lesson: it fixed typing and the days did not move.
- **The courier is third, not last: {d2('p.courier.save_tue_fri')} to {d2('p.courier.save_daily')} days.** A second weekly arrival takes the mean lag from {d1('p.courier.lag_friday_only')} to {d1('p.courier.lag_tue_fri')} days; a daily one to {d1('p.courier.lag_daily')}. It ranks below the first two because it needs three parties (property heads, the courier arrangement, and audit if booking from a scan replaces waiting for the paper) and a cost decision, and its best form depends on an audit view not yet obtained (`notes/research.md` section 6).
- **A portal has a ceiling and no counterfactual.** The most it could touch is the vendor-to-desk delay plus vendor-side query days, {d1('p.vendor_ceiling')} days, but the data cannot say how much it would remove, it changes no head-office wait, and it removes none of the checks that cause queries. Only 9% of surveyed vendors prefer a portal against 58% for WhatsApp; the IT head puts a bought-and-integrated portal at six to nine months, and the last write interface to SAP took seven to eight months to approve before any code (interview figures, `notes/numbers.md`). The two first fixes need no vendor adoption and no build.

## Ranking table

Days × bills is the measure for every row: days per affected bill times the share of bills affected, which is the number of days the cause adds to the {MEAN:.1f}-day mean. The ceiling is the whole stage or cause; "removable on evidence" is what a stated counterfactual would take off (conservative to upper), and is blank where the data holds no counterfactual.

{TABLE}

Notes on each row:

{NOTES}

### Who can fix each

{OWN}

Rows overlap with the table above (the query row is split by owner here), so the owner totals are not additive with it.

## How the numbers are built

- **Population and mean.** {N:,} paid invoices with a trustworthy payment date; mean {MEAN:.1f} days from invoice date to paid (`02_stage_times.py`).
- **Days on the mean** = mean days per affected bill × share of bills affected. For the query row that is {d1('query.mean_days_among_queried')} days × {pc('p.query.pct_bills')} = {d2('p.query.days_on_mean')} days (query-open days only; the full extra time on a queried bill is {d1('added.s99')} days, {d2('added.days_on_overall_mean')} on the mean including extra verification).
- **Payment run.** The first Tuesday or Friday strictly after posting, plus a list lead of 0, 1 or 2 days. The conservative case uses 2. Posting dates are day-accurate at best (data-audit D15), so the result is a mean-level estimate.
- **Courier.** Reproduced exactly from the signing weekday ({d2('p.courier.lag_friday_only')} against the observed {d2('overall.s04.cal_mean')} days) before the second weekly arrival and the daily case were applied, both keeping the 2-day minimum lag seen in the data.
- **AP queue.** AP-1 is the verifier code with the most bills; the data does not say who that is. The comparison is its bills against the other four's mean.
- **Day-one catch** is from `notes/query-forensics.md` (layers A, then A to C), which says what each layer needs.
- **MSME check.** For known Micro and Small paid invoices, each fix's days are subtracted from the desk-to-paid time and the bills still over 45 days are recounted. Blank-status vendors are left out.

## Evidence that would change my mind

| If we found | It would change the ranking by |
|---|---|
| Treasury releases are held by approvals or limits, not by the run list (for example the maker-checker chain needs three working days) | Cutting the payment fix toward its low end or to zero; AP queue becomes first |
| Posting dates in SAP differ from the register's, so the register's posted-to-paid gap is not the real wait | Re-running the payment row on SAP posting and payment-proposal timestamps; the row could grow or vanish |
| The audit or tax adviser allows booking from the scan with the original following | Courier jumps to first or second: the whole {d1('overall.s04.cal_mean')}-day wait leaves the booking path, not just {d2('p.courier.save_tue_fri')} to {d2('p.courier.save_daily')} |
| AP time sheets show verification takes far more effort than the {d1('overall.s06.cal_mean')} elapsed days suggest (for example typing above a quarter of AP time) | Typing and a reader rank much higher; the claim now rests on elapsed time standing in for effort |
| AP says AP-1's longer wait is deliberate (complex bills or a different pick-up rule) | The queue fix shrinks to the part not explained, possibly to zero |
| SAP exposes work-order lines, rates, open quantity and period balances, and a day-one rule reproduces the 219 balance queries that the extract does not | Queries rise from {d2('layer.A.cum_days_off_mean_total')} toward {d2('layer.ABC.cum_days_off_mean_total')} days removable, and procurement's share grows |
| The amendment log shows the amendment step itself takes weeks, not the {d0('c.woq.median')}-day median seen for the whole query | Work-order balance becomes a top cause and procurement an owner of the first fix |
| Delivery dates show Micro and Small bills are much later than the three clocks suggest | Weighting by MSME exposure instead of by bills; payment lag and courier gain weight because they hit every Micro and Small bill |
| Vendors would adopt a portal or WhatsApp intake that cuts the vendor-to-desk time, shown by a pilot | The portal gets a counterfactual from the pilot and may move up; today it has none |
| A property head can show a second weekly courier costs little and needs no new packet work | Courier moves to the first fix: it is a {d2('p.courier.save_tue_fri')}-day gain on the same footing as the others |
"""
(ROOT / "notes" / "problem.md").write_text(md, encoding="utf-8", newline="\n")
print("wrote notes/problem.md;", len(own), "figures")
print(pd.DataFrame([{k: r[k] for k in ("rank_ceiling", "cause", "ceil", "lo", "hi", "rank_removable")} for r in rows]).round(2).to_string(index=False))
