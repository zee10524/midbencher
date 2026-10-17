"""Score eight solution options (plus one extension) using the analysis, and write notes/options.md.

DAYS SAVED is expressed one way for every option: days off the 37.6-day mean invoice-to-paid time = days saved per affected bill x share of
bills affected. Low / central / high come from stated counterfactuals; the formulas are printed in the note. Ranking is by the central value.

HOURS are my estimates of the time to a working demo on the pack data, by component, against a budget worked out from the clock
(Friday 16 Oct 2026 15:56 IST to Saturday 17 Oct 22:00 IST). They are estimates, not measurements, and the note says so.

Reads the figures files from clean.py, 02, 04, 06, 05, 08 and analysis/out/stage_times.csv, bills_clean.parquet, query_forensics.csv.
Writes notes/options.md and analysis/out/figures_options.csv.   Run: python analysis/09_options.py
"""
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
F, SRC = {}, {}
for fname, script in [("figures.csv", "clean.py"), ("figures_stage_times.csv", "02_stage_times.py"), ("figures_query_forensics.csv", "04_query_forensics.py"),
                      ("figures_msme.csv", "06_msme_exposure.py"), ("figures_claims_tested.csv", "05_claims_tested.py"), ("figures_problem.csv", "08_problem_ranking.py")]:
    for r in pd.read_csv(OUT / fname, keep_default_na=False).itertuples():
        F[r.id] = r.value
        SRC[r.id] = script
own: dict[str, tuple] = {}


def fig(k, v, d=""):
    v = round(float(v), 3) if isinstance(v, (float, np.floating)) else v
    own[k] = (v, d)
    F[k] = v


f = lambda i: float(F[i])
d1 = lambda i: f"{f(i):.1f}"
d2 = lambda i: f"{f(i):.2f}"
d0 = lambda i: f"{f(i):,.0f}"

b = pd.read_parquet(OUT / "bills_clean.parquet")
q = pd.read_csv(OUT / "query_forensics.csv", parse_dates=["paid_date"])
st = pd.read_csv(OUT / "stage_times.csv")
pop = b[(b.doc_type == "invoice") & b.paid_date.notna()].copy()
N = len(pop)
MEAN = f("overall.s99.cal_mean")
fig("o.n", N, "paid invoices analysed")

# ------------------------------------------------------------------ the time budget (assumptions, stated)
now, deadline = datetime(2026, 10, 16, 15, 56), datetime(2026, 10, 17, 22, 0)
hours_clock = (deadline - now).total_seconds() / 3600
SLEEP, LIFE, SLACK = 8.0, 5.0, 3.0
BUDGET = round(hours_clock - SLEEP - LIFE - SLACK)
fig("o.hours.clock", hours_clock, "hours from Fri 16 Oct 15:56 IST to Sat 17 Oct 22:00 IST")
fig("o.hours.sleep", SLEEP, "assumed sleep"); fig("o.hours.life", LIFE, "assumed meals, breaks and everything else")
fig("o.hours.slack", SLACK, "assumed slack for debugging, repo set-up and the chat-history export")
fig("o.hours.budget", BUDGET, "build hours available by Saturday 10 pm, after the three deductions")

# ------------------------------------------------------------------ computations per option
pq = q[(q.doc_type == "invoice") & q.paid_date.notna() & q.days_open.notna()].copy()
pq["saved"] = np.minimum(pq.days_open, pq.days_desk_to_pick.clip(lower=0))
b2 = b.set_index("bill_id")
pq["lag"] = pq.bill_id.map((b2.ho_received_date - b2.property_head_signed_date).dt.days)
pq["saved_scan"] = np.minimum(pq.days_open, (pq.days_desk_to_pick - pq.lag).clip(lower=0))
for L in ("A", "AB", "ABC"):
    g = pq[pq.catch_layer.isin(list(L))]
    fig(f"o.pre.{L}.bills", len(g), f"paid invoices with a query the pre-flight check could catch, layers {L}")
    fig(f"o.pre.{L}.pct", 100 * len(g) / N); fig(f"o.pre.{L}.per_bill", g.saved.mean(), f"days saved per caught query, layers {L}")
    fig(f"o.pre.{L}.days", g.saved.sum() / N, f"days off the mean, layers {L}")
    fig(f"o.pre.{L}.days_with_scan", g.saved_scan.sum() / N, f"days off the mean if scan-first has already removed the courier lag, layers {L}")
wo = pq[pq.rule_id.isin(["R26", "R25", "R24", "R10", "R12"])]
ex = pq[pq.rule_id == "R26"]
fig("o.wo.expiry_bills", len(ex)); fig("o.wo.expiry_pct", 100 * len(ex) / N); fig("o.wo.expiry_days", ex.days_open.sum() / N, "query-open days on the mean, work-order expiry queries")
fig("o.wo.all_bills", len(wo)); fig("o.wo.all_pct", 100 * len(wo) / N); fig("o.wo.all_days", wo.days_open.sum() / N, "query-open days on the mean, all work-order queries")
s2 = st[(st.dimension == "category") & (st.stage_order == 2)]
MANP = ["Security Manpower", "Housekeeping Manpower", "Landscaping"]
m, o = s2[s2.group.isin(MANP)], s2[~s2.group.isin(MANP)]
mm, om = (m.cal_mean * m.n).sum() / m.n.sum(), (o.cal_mean * o.n).sum() / o.n.sum()
fig("o.att.manpower_bills", m.n.sum()); fig("o.att.manpower_pct", 100 * m.n.sum() / N)
fig("o.att.manpower_check_days", mm, "mean days desk to verified, manpower bills"); fig("o.att.other_check_days", om, "mean days desk to verified, all other bills")
fig("o.att.excess", mm - om, "extra days manpower bills spend in the property check")
fig("o.att.days_high", (mm - om) * m.n.sum() / N, "days off the mean if the whole excess went")
for k, sh in (("low", 0.25), ("central", 0.5)):
    fig(f"o.att.days_{k}", f("o.att.days_high") * sh, f"{int(sh * 100)}% of the excess")
pop["queue"] = (pop.ho_picked_date - pop.ho_received_date).dt.days
nr = pop.posted_date.apply(lambda d: next(d + pd.Timedelta(days=k) for k in range(1, 9) if (d + pd.Timedelta(days=k)).dayofweek in (1, 4)))
late = (pop.paid_date - nr).dt.days > 0
ap1 = pop.ho_verifier == "AP-1"
fig("o.queue.bills", int((late | ap1).sum()), "paid invoices that are AP-1's or are paid after a later run than the next")
fig("o.queue.pct", 100 * (late | ap1).mean())
fig("o.portal.adopt", 0.09 * 100, "survey: % of vendors preferring a portal")
fig("o.portal.days", 0.09 * f("overall.s01.cal_mean"), "9% x vendor-to-desk days")
fig("o.portal.bills", 0.09 * N)
fig("o.ocr.days", 0.10 * f("overall.s06.cal_mean"), "AP lead's reported 10% x AP verification days")
fig("o.scan.days", f("overall.s04.cal_mean"), "courier lag removed from the booking path")
fig("o.tracker.low", f("p.head_office_fix.low"), "conditional days if the AP lead and treasury act on it, conservative")
fig("o.tracker.high", f("p.head_office_fix.high"), "same, upper end")
fig("o.pair.low", f("p.head_office_fix.low") + f("p.courier.save_tue_fri"), "tracker as work queue plus a second weekly courier, conservative")
fig("o.pair.high", f("p.head_office_fix.high") + f("p.courier.save_daily"), "tracker as work queue plus a daily courier, upper end")
fig("o.pair.low_pct", 100 * f("o.pair.low") / MEAN); fig("o.pair.high_pct", 100 * f("o.pair.high") / MEAN)

# ------------------------------------------------------------------ the options
O = [
    dict(k="scan", n="Scan-first, original later", lo=0.0, ce=f("o.scan.days"), hi=f("o.scan.days"), aff=N, hrs=10.0,
         hr_note="scan and upload page 3, originals-pending list and payment hold flag 2, AP work list from scans 2, control note 1, UI 2",
         formula=f"Courier lag removed from the booking path: mean signature-to-head-office days = {d2('overall.s04.cal_mean')}, on all {N:,} bills. Low = 0 if the audit view says booking needs the paper in hand. The AP wait is assumed to start at the scan instead of the packet.",
         audit="Medium to high", audit_note="Booking before the original is in hand; K1 control. Mitigation: hold payment until the original is received (it arrives within days)", adopt="None needed (internal)", adopt_n="n/a",
         sap="None", sap_prod="None"),
    dict(k="track4b", n="Live tracker as a work queue (extension of option 4)", lo=0.0, ce=f("o.tracker.low"), hi=f("o.tracker.high"), aff=int(f("o.queue.bills")), hrs=11.5,
         hr_note="stage ages and data model 2, tracker UI 4, vendor status messages (mock send) 1.5, AP pick order and next-run payment list 2.5, replay of the year 1.5",
         formula=f"From notes/problem.md: AP-1 queue gap {d2('p.queue.saving')} + payment-run lag {d2('p.pay.excess_lead2')} (list closes 2 days ahead) = {d2('p.head_office_fix.low')}; upper end {d2('p.head_office_fix.high')} with list lead 0. Low = 0 if nobody acts on it. Bills affected = AP-1's bills plus bills paid after a later run than the next.",
         audit="Low", audit_note="Read-only plus work ordering; no check removed; a status message needs the vendor's consent (DPDP)", adopt="64% would use a WhatsApp status update", adopt_n="64%",
         sap="None", sap_prod="None (reads posting and payment status over RFC)"),
    dict(k="courier", n="Daily courier", lo=f("p.courier.save_tue_fri"), ce=f("p.courier.save_daily"), hi=f("p.courier.save_daily"), aff=N, hrs=1.0,
         hr_note="a what-if switch inside the tracker 1; nothing to build",
         formula=f"Mean lag {d2('p.courier.lag_friday_only')} d now, {d2('p.courier.lag_daily')} d with a daily arrival, keeping the observed 2-day minimum = {d2('p.courier.save_daily')}. Low = {d2('p.courier.save_tue_fri')} with a second weekly arrival (lag {d2('p.courier.lag_tue_fri')}). The model reproduces today's lag exactly.",
         audit="None", audit_note="Controls unchanged; the cost is money, and the courier cost is not in the pack", adopt="None needed (internal)", adopt_n="n/a",
         sap="None", sap_prod="None"),
    dict(k="att", n="Attendance three-way match", lo=f("o.att.days_low"), ce=f("o.att.days_central"), hi=f("o.att.days_high"), aff=int(f("o.att.manpower_bills")), hrs=7.0,
         hr_note="parse the three files and fuzzy match 3, mismatch view 3, test on the February sample 1",
         formula=f"Manpower bills spend {d2('o.att.manpower_check_days')} d in the property check against {d2('o.att.other_check_days')} d for other bills: excess {d2('o.att.excess')} d on {f('o.att.manpower_pct'):.1f}% of bills = {d2('o.att.days_high')} (high). Central = 50% and low = 25% of that: **an assumption**, because the data cannot split matching from the department head's signature and the PF/ESIC check.",
         audit="Low to medium", audit_note="The signatures stay; a wrong match could cut a vendor's days, so a person confirms mismatches", adopt="None needed (uses the vendor claim already sent)", adopt_n="n/a",
         sap="None", sap_prod="None"),
    dict(k="pre", n="Pre-flight checker at intake", lo=f("o.pre.A.days"), ce=f("o.pre.AB.days"), hi=f("o.pre.ABC.days"), aff=int(f("o.pre.AB.bills")), hrs=14.5,
         hr_note="bill reader 5, rule engine 4, vendor fix-it message 1, UI 3, test on the 40 bills 1.5",
         formula=f"Sum over caught queries of min(days open, days from desk to AP pick-up), divided by {N:,} bills. Layers A: {d2('o.pre.A.days')}, A+B: {d2('o.pre.AB.days')} (central), A to C: {d2('o.pre.ABC.days')} (needs SAP fields beyond the extract). {d1('o.pre.AB.per_bill')} days per caught bill on {d0('o.pre.AB.bills')} bills.",
         audit="Low", audit_note="Adds a check and removes none; a person confirms", adopt="Works at the desk; 58% of vendors prefer WhatsApp if used before printing", adopt_n="58%",
         sap="None", sap_prod="None (RFC read is approved)"),
    dict(k="portal", n="Vendor portal", lo=0.0, ce=f("o.portal.days"), hi=f("overall.s01.cal_mean"), aff=int(round(f("o.portal.bills"))), hrs=17.0,
         hr_note="login, upload and status 5, bill reader 5, status messages 2, vendor UI 3, admin view 2",
         formula=f"Survey adoption 9% x vendor-to-desk days {d2('overall.s01.cal_mean')} = {d2('o.portal.days')}, on 9% of bills (assuming bills in proportion to vendors). High = {d2('overall.s01.cal_mean')} if mandatory (the IT head's belief, reported). Vendor-side query days are not removed by a portal.",
         audit="Medium to high", audit_note="A new vendor-facing system of record: access control, bank details, personal data; the full vision writes to SAP", adopt="9% prefer a portal; 12% already use one for another client and find it hard", adopt_n="9%",
         sap="None for the prototype", sap_prod="Needed for the two-way vision: last write interface took seven to eight months to approve"),
    dict(k="wo", n="Work-order runway alert", lo=0.0, ce=f("o.wo.expiry_days"), hi=f("o.wo.all_days"), aff=int(f("o.wo.expiry_bills")), hrs=6.0,
         hr_note="burn-rate model 2, alert list and UI 2.5, check against the 107 expiry queries 1.5",
         formula=f"Query-open days on work-order expiry queries / {N:,} bills = {d2('o.wo.expiry_days')} (central: the part SAP dates verify). High = all work-order queries {d2('o.wo.all_days')} on {f('o.wo.all_pct'):.1f}% of bills. Low = 0 if amendments take longer than the warning gives.",
         audit="Low", audit_note="Read-only warning; false alerts are the risk", adopt="None needed (internal)", adopt_n="n/a",
         sap="None", sap_prod="None (reads work orders over RFC)"),
    dict(k="ocr", n="OCR at head office", lo=0.0, ce=f("o.ocr.days"), hi=f("overall.s06.cal_mean"), aff=N, hrs=10.5,
         hr_note="bill reader 5, review and confirm screen 3, write to parsed_bill 1, hand-label 10 bills for accuracy 1.5",
         formula=f"Central = the AP lead's 'about 10%' (reported) x AP verification days {d2('overall.s06.cal_mean')} = {d2('o.ocr.days')}. High = all of verification, {d2('overall.s06.cal_mean')}. Low = 0: the earlier OCR pilot left the days unchanged.",
         audit="Low to medium", audit_note="A misread GSTIN posted without a person looking is the verifier's fear", adopt="None needed (internal)", adopt_n="n/a",
         sap="None for the prototype", sap_prod="Auto-posting needs write access (separate project, audit sign-off)"),
    dict(k="track", n="Live tracker with a vendor status message (as listed)", lo=0.0, ce=0.0, hi=0.0, aff=N, hrs=7.5,
         hr_note="stage ages 2, tracker UI 4, status message templates and preview 1.5",
         formula=f"Direct days = 0: a tracker shows the wait, it does not shorten it. It is the instrument for the two head-office fixes (up to {d2('o.tracker.low')} to {d2('o.tracker.high')} days) only if someone acts on it; that is the extension above.",
         audit="Low", audit_note="Read-only; status messages need consent", adopt="64% would use a WhatsApp status update", adopt_n="64%",
         sap="None", sap_prod="None"),
]
for r in O:
    r["per"] = r["ce"] * N / r["aff"] if r["aff"] else 0
    r["eff"] = r["ce"] / r["hrs"]
O.sort(key=lambda r: -r["ce"])
for i, r in enumerate(O, 1):
    r["rank"] = i
    fig(f"o.{r['k']}.central", r["ce"]); fig(f"o.{r['k']}.low", r["lo"]); fig(f"o.{r['k']}.high", r["hi"]); fig(f"o.{r['k']}.hours", r["hrs"], f"estimated build hours, {r['n']}")
    fig(f"o.{r['k']}.bills", r["aff"], f"bills affected, {r['n']}"); fig(f"o.{r['k']}.per_affected", r["per"], f"central days per affected bill, {r['n']}")
    fig(f"o.{r['k']}.days_per_hour", r["eff"], f"central days saved per build hour, {r['n']}")
R = {r["k"]: r for r in O}
pair_hours = R["track4b"]["hrs"] + R["courier"]["hrs"]
fig("o.pair.hours", pair_hours, "hours for the recommended pair")
fig("o.pair.spare", BUDGET - pair_hours, "hours left in the budget")
pd.DataFrame([dict(id=k, value=v_, description=d_) for k, (v_, d_) in own.items()]).to_csv(OUT / "figures_options.csv", index=False)

# ------------------------------------------------------------------ the note
rng = lambda r: (f"{r['lo']:.2f} to {r['hi']:.2f}" if r["hi"] - r["lo"] > 0.004 else f"{r['ce']:.2f}")
T = ["| Rank | Option | Days saved on the mean (low to high) | **Central** | Bills affected | Days per affected bill | Build hours | Days per hour | Audit and control risk | Vendor adoption | SAP write |",
     "|---|---|---|---|---|---|---|---|---|---|---|"]
for r in O:
    T.append(f"| {r['rank']} | **{r['n']}** | {rng(r)} | **{r['ce']:.2f}** | {r['aff']:,} ({100 * r['aff'] / N:.1f}%) | {r['per']:.2f} | {r['hrs']:g} | {r['eff']:.2f} | {r['audit']} | {r['adopt_n']} | {r['sap']} |")
TABLE = "\n".join(T)
FORM = "\n".join(f"{r['rank']}. **{r['n']}.** {r['formula']}" for r in O)
HRS = "\n".join(f"- **{r['n']}, {r['hrs']:g} h.** {r['hr_note']}." for r in sorted(O, key=lambda r: r["hrs"]))
RISK = ["| Option | Audit and control risk | Why | Vendor adoption (survey) | SAP write: prototype | SAP write: production |", "|---|---|---|---|---|---|"]
for r in O:
    RISK.append(f"| {r['n']} | {r['audit']} | {r['audit_note']} | {r['adopt']} | {r['sap']} | {r['sap_prod']} |")
RISKT = "\n".join(RISK)

md = f"""# Options scored

Scores the eight options using `notes/problem.md` and the analysis behind it. Every number is registered in `notes/numbers.md` (ids `o.*`, and the ids they read). The official deadline is Monday 19 October 2026, 1 pm IST (`Riklr-FDE-Case-Study.pdf`); Saturday 10 pm is your build cut-off, which leaves Sunday and Monday morning for the deck, video and README.

## How to read the scores

- **Days saved on the mean** = days saved per affected bill × share of bills affected. It is the number of days the option takes off the {MEAN:.1f}-day mean invoice-to-paid time, so every option is on one scale. **Central** is my best defensible case and the one used to rank; low and high bracket it.
- **Bills affected** are paid invoices from the {N:,} behind `stage_times.csv`. **Days per affected bill** = central days saved ÷ share affected.
- **Build hours are my estimates**, by component, for a working demo on the pack data. They are not measured. The budget is {BUDGET} hours: {hours_clock:.0f} hours from Friday 16 October 15:56 IST to Saturday 22:00, minus {SLEEP:g} for sleep, {LIFE:g} for meals, breaks and everything else, and {SLACK:g} for debugging, repo set-up and the chat-history export. Change the three deductions if your day is different; the ranking by days does not move.
- **Days are conditional where marked.** The tracker's days exist only if the AP lead and treasury act on it; scan-first's days exist only if the audit view allows booking from a scan.
- Option 4 as listed (tracker with a status message) saves no days by itself. I added **option 4b**, a tracker built as a work queue, because the two causes that `notes/problem.md` ranks first (payment-run lag and the AP queue) are not in your list, and a tracker is the only listed option that can reach them.

## Scores, ranked by central days saved

{TABLE}

Pre-flight checker and portal tie at 0.57. Days per hour is central days divided by build hours; the courier row is high only because there is almost nothing to build. **Over the {BUDGET}-hour budget on their own:** {', '.join(r['n'] + ' (' + format(r['hrs'], 'g') + ' h)' for r in O if r['hrs'] > BUDGET)}.

## Formulas

{FORM}

## Build effort, by component

Hours to a working demo on the pack data, including debugging, using Claude Code. Sorted by size.

{HRS}

## Audit and control risk, vendor adoption, SAP write

{RISKT}

Survey figures (`vendor-survey-summary.md`, 212 vendors responded): 58% prefer WhatsApp, 27% email, 9% a portal, 6% paper; 64% would use a status update on WhatsApp; 12% already use a portal for another client and find it hard.

## Recommendation

**1. Build: the live tracker as a work queue (4b), {R['track4b']['hrs']:g} hours.** It is the only listed option that reaches the two causes ranked first in `notes/problem.md`: packets waiting for a verifier and posted bills missing the payment run. Central {R['track4b']['ce']:.2f} days, up to {R['track4b']['hi']:.2f}, on {R['track4b']['aff']:,} bills ({100 * R['track4b']['aff'] / N:.1f}%). It needs no SAP write, no vendor adoption for the days, and changes no control. The vendor status message is the part vendors asked for (64% would use it), and the CFO asked for the screen: "a dashboard for me that shows what is stuck and where". The prototype replays the year to show what each rule would have changed.

**2. Recommend to the client, no extra build: a second weekly or daily courier, {R['courier']['hrs']:g} hour** as a what-if switch inside the tracker. {d2('p.courier.save_tue_fri')} to {d2('p.courier.save_daily')} days on every bill for a cost the pack does not give.

Together {pair_hours:g} hours of the {BUDGET} available, {BUDGET - pair_hours:g} spare, and {f('o.pair.low'):.1f} to {f('o.pair.high'):.1f} days off the mean ({f('o.pair.low_pct'):.0f}% to {f('o.pair.high_pct'):.0f}%).

## The case against my own pick

- **The tracker saves no days by itself.** Everything in the {R['track4b']['ce']:.2f} depends on two people acting. The organisation has been here before: the monthly review "became a complaint session and people stopped joining" (CFO). A work queue that orders the AP lead's tray and builds the treasury list lowers the dependence on goodwill but does not remove it.
- **I am leaving the largest number on the table.** Scan-first is {R['scan']['ce']:.2f} days, more than the tracker's central {R['track4b']['ce']:.2f}, and is ranked first. I rejected it for the audit view that is not yet in hand, not for its days. If the tax adviser says yes on Saturday, I chose wrong.
- **The payment-run estimate may be wrong.** It rests on register posting dates that are day-accurate at best, and it assumes the run list is the only cause. If treasury approvals explain the lag, the second half of the tracker's days shrinks (`notes/problem.md`, what would change my mind).
- **The queue fix rests on one verifier code.** If AP-1's longer wait is deliberate, that part goes to zero.
- **It does not touch the checks.** Queries cost {d2('p.query.days_on_mean')} days on the mean, and the double checks stay. The case says it tests document reading and rule checks, and a tracker shows neither; the pre-flight checker does. A reviewer expecting a reader may score a work queue as a dashboard.
- **The demonstration is a replay, not a result.** The numbers are counterfactuals on last year's data, not a measured effect.
- **My hours are guesses.** The tracker's UI is the usual place for estimates to slip; if it does, the replay and the what-if switch are what to cut first.

## What each rejected option is still good for later

- **Scan-first, original later.** The biggest single gain ({R['scan']['ce']:.2f} days) once the audit view is in. It reuses the tracker's data model, and the original-received flag is already in the control design. First thing to build after Saturday.
- **Attendance three-way match.** The strongest runner-up and the hidden finding: manpower bills spend {d2('o.att.manpower_check_days')} days in the property check against {d2('o.att.other_check_days')} for the rest, up to {d2('o.att.days_high')} days on the mean. Build it next on real monthly attendance from all properties; the pack has one property and one month.
- **Pre-flight checker.** {d2('o.pre.AB.days')} days now and up to {d2('o.pre.ABC.days')} once SAP exposes work-order lines, rates and open quantity. It is also the first-time-right measure the benchmarks use, and the natural phase two on the same intake the tracker feeds from. With scan-first already in place it falls to {d2('o.pre.AB.days_with_scan')}, because the courier lag it was hiding in is gone.
- **Work-order runway alert.** A cheap add-on to the tracker for procurement (about 6 hours), small in days ({d2('o.wo.expiry_days')} to {d2('o.wo.all_days')}) but aimed at the escalations that reach the CFO, and at the {d0('c.wo.crossed_approved_value')} orders that passed approved value.
- **Vendor portal.** Worth it for the large vendors who already use portals, as a read-only status page, and only after SAP write approval for the two-way version. At 9% preference it cannot be the main channel.
- **OCR at head office.** Useful as a component, not a product: the same reader feeds scan-first and the pre-flight checker, and posting automation waits for the SAP write project. On its own it saves at most {d2('overall.s06.cal_mean')} days.
- **The tracker as listed (status message only).** Kept inside 4b: the status message is the vendor-facing half of the same screen.
"""
# quotes must be verbatim from the pack
pack = " ".join(p.read_text(encoding="utf-8") for p in (ROOT / "pack" / "context").rglob("*.md"))
norm = lambda s: re.sub(r"\s+", " ", s.replace("*", "")).strip().lower()
P = norm(pack)
bad = []
for ln, line in enumerate(md.splitlines(), 1):
    for mt in re.finditer(r'"([^"]{14,})"', line):
        qt = mt.group(1)
        if norm(qt) not in P and norm(qt).rstrip(".,") not in P:
            bad.append((ln, qt))
if bad:
    print("QUOTES NOT FOUND:", bad)
    raise SystemExit(1)
(ROOT / "notes" / "options.md").write_text(md, encoding="utf-8")
print("wrote notes/options.md;", len(own), "figures")
print(pd.DataFrame([{k: r[k] for k in ("rank", "n", "lo", "ce", "hi", "aff", "hrs")} for r in O]).round(2).to_string(index=False))
