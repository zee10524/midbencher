"""Write notes/solution-design.md: the intake-to-owner pipeline and work queue, scoped to what can be built by Saturday 10 pm.

Numbers are read by figure id from the other scripts' outputs and from analysis/out/query_rules.csv, so the note cannot drift from the analysis.
Four inbox bills were read by eye (their printed values are constants below, labelled as such) and joined to the vendor master, work orders and
register to give the expected verdicts for acceptance tests.

Writes notes/solution-design.md and analysis/out/figures_design.csv.   Run: python analysis/10_solution_design.py
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
F = {}
for fname in ["figures.csv", "figures_stage_times.csv", "figures_query_forensics.csv", "figures_msme.csv", "figures_claims_tested.csv", "figures_problem.csv", "figures_options.csv", "figures_levers.csv"]:
    for r in pd.read_csv(OUT / fname, keep_default_na=False).itertuples():
        F[r.id] = r.value
own: dict[str, tuple] = {}


def fig(k, v, d=""):
    v = round(float(v), 3) if isinstance(v, (float, np.floating)) else v
    own[k] = (v, d)
    F[k] = v


f = lambda i: float(F[i])
d1 = lambda i: f"{f(i):.1f}"
d2 = lambda i: f"{f(i):.2f}"
d0 = lambda i: f"{f(i):,.0f}"
pc = lambda i: f"{f(i):.1f}%"
MEAN = f("overall.s99.cal_mean")
qr = pd.read_csv(OUT / "query_rules.csv").set_index("rule_id").n

# ------------------------------------------------------------------ the 25 checks
# class: I = at intake from the bill + SAP extract; X = at intake but needs data not in the pack; PK = needs the rest of the packet scanned; L = not at intake
CHECKS = [
    ("P1", "Vendor name and GSTIN on the bill match the vendor master", "I", "Bill + vendor_master", ["R08"], "yes"),
    ("P2", "Bill is addressed to the correct company entity and property", "X", "Company legal entity names and GSTINs (not in the pack); the property is checkable from the work order", ["R13"], "partly"),
    ("P3", "Work order or purchase order number is on the bill", "I", "Bill; then the number must exist in SAP work orders", [], "yes"),
    ("P4", "Rate on the bill matches the work order rate", "X", "Work-order rates (the extract holds values, not rates); readable over RFC", ["R17", "R16"], "no"),
    ("P5", "Quantity, days or headcount match approved attendance or delivery", "L", "Biometric, gate register and the vendor claim: three sources that are not on the bill. The bill's own man-days can be tied to the attendance summary page if the packet is scanned", ["R11"], "no"),
    ("P6", "Attendance sheet is signed by the department head", "PK", "The attendance page. A signature or stamp can be detected; whose it is cannot", ["R23"], "stretch"),
    ("P7", "PF and ESIC challans for the previous month are attached", "PK", "The challan page and its month against the billing period", ["R22"], "stretch"),
    ("P8", "Delivery challan carries the security gate stamp", "PK", "The challan page; a stamp can be detected", ["R21"], "no"),
    ("P9", "Service report or job card is attached", "PK", "The service report page", ["R20"], "no"),
    ("P10", "Service entry or GRN is created in SAP", "L", "Created by the executive after the checks; status readable over RFC later", ["R18", "R19"], "no"),
    ("P11", "Property head has signed the packet", "L", "Happens after the property check; the tracker records the event", [], "event only"),
    ("H1", "Vendor GSTIN on the bill matches the vendor master", "I", "Same as P1; one implementation", [], "yes"),
    ("H2", "Bill is addressed to the correct company entity", "X", "Same as P2", [], "partly"),
    ("H3", "Work order or purchase order is valid on the bill date and has open balance", "I", "Bill date and number + work_orders. Validity is exact; balance only as value headroom, because period balance and open quantity are not in the extract", ["R26", "R25", "R24", "R10", "R12"], "yes"),
    ("H4", "Rate matches the work order or purchase order", "X", "Same as P4", [], "no"),
    ("H5", "Quantity matches the posted service entry or GRN", "L", "The service entry does not exist yet at intake", [], "no"),
    ("H6", "Attendance sheet is signed", "PK", "Same as P6", [], "stretch"),
    ("H7", "PF and ESIC challans for the previous month are attached", "PK", "Same as P7", [], "stretch"),
    ("H8", "Delivery challan is stamped", "PK", "Same as P8", [], "no"),
    ("H9", "Service report is attached", "PK", "Same as P9", [], "no"),
    ("H10", "GST type is correct for the place of supply", "X", "The company's GST registrations and a settled place-of-supply rule (not in the pack). The bill's three facts can be read and compared", ["R05"], "partly"),
    ("H11", "HSN or SAC code and GST rate are correct", "I", "Bill + a rate rule (18%; diesel carries none in the register)", ["R06", "R07"], "yes"),
    ("H12", "GL code and cost centre on the service entry are correct", "L", "The service entry does not exist yet; GL needs an expense-type mapping nobody holds", ["R03", "R02", "R04"], "no"),
    ("H13", "Invoice number has not been booked before for this vendor", "I", "Bill + posted_invoices + the register, ignoring the bill's own row", ["R01"], "yes"),
    ("H14", "TDS section and rate are correct", "L", "The section decided for each work order (not recorded) and year-to-date payments", [], "no"),
]
assert len(CHECKS) == 25
CLASS = {"I": "At intake, from the bill and the SAP extract", "X": "At intake, but needs data not in the pack", "PK": "Needs the rest of the packet scanned (the paper)", "L": "Not at intake: a later step or another source"}
cls_n = {k: sum(1 for c in CHECKS if c[2] == k) for k in CLASS}
for k, n_ in cls_n.items():
    fig(f"d.checks.{k}", n_, f"checks in class {k}: {CLASS[k]}")
# queries last year by class (rules are each assigned to one check)
RULE_CLASS = {}
for cid, _, k, _, rules, _ in CHECKS:
    for r in rules:
        RULE_CLASS[r] = k
unmapped = [r for r in qr.index if r not in RULE_CLASS]
for k in CLASS:
    fig(f"d.queries.{k}", int(sum(qr[r] for r, kk in RULE_CLASS.items() if kk == k)), f"queries last year on checks in class {k}")
fig("d.queries.none", int(sum(qr[r] for r in unmapped)), f"queries not tied to a checklist item ({', '.join(unmapped)})")
assert sum(own[f"d.queries.{k}"][0] for k in list(CLASS) + ["none"]) == int(f("q.rows"))
fig("d.proto.checks", sum(1 for c in CHECKS if c[5] in ("yes", "partly")), "checks the Saturday prototype runs fully or partly")

# ------------------------------------------------------------------ the four inbox bills read by eye, joined to the pack data
v = pd.read_csv(ROOT / "pack" / "data" / "vendors.csv", dtype=str, keep_default_na=False)
w = pd.read_csv(ROOT / "pack" / "data" / "work_orders.csv", dtype=str, keep_default_na=False)
b = pd.read_parquet(OUT / "bills_clean.parquet")
SAMPLES = [  # values read by eye from the images in pack/context/documents/bill-inbox
    dict(file="bill-11.pdf", gstin="09WMLCG8394Z1Z9", inv="085/25-26/730", wo="4101752", date="2025-08-02", taxable=61610.0, pos="Uttar Pradesh", tax="IGST 18%", rec="06", udyam=""),
    dict(file="packet-01-security-manpower.pdf", gstin="06EPVCF6069Z1ZZ", inv="668/25-26/138", wo="4100395", date="2026-03-04", taxable=420980.0, pos="Haryana", tax="CGST 9% + SGST 9%", rec="06", udyam=""),
    dict(file="bill-16.jpg", gstin="07QXNPN2966U1ZT", inv="751/25-26/346", wo="4100393", date="2025-11-01", taxable=86330.0, pos="Haryana", tax="IGST 18%", rec="06", udyam="Micro"),
    dict(file="packet-08-repeat-invoice.pdf", gstin="06QVLCO1204A1Z3", inv="550/25-26/340", wo="4100602", date="2025-06-04", taxable=190740.0, pos="Uttar Pradesh", tax="IGST 18%", rec="06", udyam="Micro"),
]
rows = []
for s in SAMPLES:
    vm = v[v.gstin == s["gstin"]]
    vid = vm.vendor_id.iloc[0]
    wr = w[w.wo_id == s["wo"]].iloc[0]
    same = b[(b.vendor_id == vid) & (b.invoice_no == s["inv"])].sort_values("desk_received_date")
    own_row = same[(same.amount_inr == s["taxable"]) & (same.invoice_date == pd.Timestamp(s["date"]))]
    others = same.drop(own_row.index)
    hold = float(wr.approved_value_inr) - float(wr.billed_value_inr)
    rows.append(dict(**s, vendor=vid, vname=vm.vendor_name.iloc[0], vstate=vm.state.iloc[0], master_ms=vm.msme_status.iloc[0] or "blank", wo_vendor_ok=wr.vendor_id == vid,
                     wo_valid=pd.Timestamp(wr.valid_from) <= pd.Timestamp(s["date"]) <= pd.Timestamp(wr.valid_to), prop=wr.property_code, headroom=hold,
                     own=own_row.bill_id.tolist(), others=[(r.bill_id, str(r.invoice_date.date()), r.amount_inr) for r in others.itertuples()]))
S = pd.DataFrame(rows)
fig("d.samples.read", len(S), "inbox bills read by eye and joined to the pack data")
fig("d.samples.no_text_layer", 31, "inbox PDFs checked for a text layer: none has one (every page is one embedded image)")
fig("d.inbox.files", 40, "files in the bill inbox: 10 packets and 30 single bills, 9 of them phone photos")

# ------------------------------------------------------------------ numbers for the success section and the scope
fig("d.ftr.baseline", 100 - f("share.bills_with_query_pct"), "% of bills with no query: first-time-right baseline")
fig("d.human_per_pct", f("p.n") / 100, "bills a year per percentage point of bills sent to a human look")
fig("d.human_per_day", f("p.n") / 100 / 250, "...per working day, on 250 working days")
# ------------------------------------------------------------------ part f: the levers replay is computed in 09_levers.py
LV = pd.read_csv(OUT / "levers.csv").set_index("code")
BTR = pd.read_csv(OUT / "backtest_rules.csv")

HOURS = [  # (part, what, hours now, hours in the first version of this section; None = new)
    ("a", "Data and event layer, tracker timeline from the register (one loader the backtest reuses)", 1.5, 2.0),
    ("b", "Intake screen and reader on at least 10 of the 40 bills, hand-labelled for the test (build only, styling is in polish)", 3.0, 3.5),
    ("c", "Intake checks P1/H1, P3/H3 and H13, the three-way routing, and the H11 and H10 facts", 2.5, 3.0),
    ("d", "Owner notifications: simulated WhatsApp outbox (0.6) and in-app tasks (0.4)", 1.0, 1.5),
    ("e", "Work queue and control tower: AP pick order (1.0), next-run payment list (0.5), MSME countdown (0.5), work-order runway view (0.5)", 2.5, 2.0),
    ("f", "Backtest: replay three levers (payment run, pick order, three intake rules) alone and combined, with the catch table", 2.0, 1.0),
    ("UI", "Design and polish of the three screens: intake (0.6), work queue and control tower (0.6), impact (0.3)", 1.5, 0.0),
]
fig("d.hours.must", sum(h for _, _, h, _ in HOURS), "estimated hours for the must-have slice")
fig("d.hours.old", sum(o for _, _, _, o in HOURS), "hours in the first version of the slice (13) before this change")
fig("d.hours.spare", f("o.hours.budget") - f("d.hours.must"), "hours left in the budget after the must-have slice")
HRS_T = "\n".join(f"| {k} | {t} | {h:g} | {('new' if o == 0 else f'{o:g}')} |" for k, t, h, o in HOURS)
BT_T = "\n".join(f"| {r.rule} | {r.query_rules} | {r.queries:,} | {r.caught:,} | {r.queries - r.caught:,} | {r.flagged:,} | {r.flagged_never_queried:,} |" for r in BTR.itertuples())
BT_T += f"\n| **All three** | | **{d0('l.bt.q_testable')}** | **{d0('l.bt.q_caught')}** | **{f('l.bt.q_testable') - f('l.bt.q_caught'):,.0f}** | **{d0('l.bt.flag_any')}** | |"


def lv_row(code, name):
    r = LV.loc[code]
    return f"| {name} | {r.setting} | {r.save:.2f} | {r.ms_late:,.0f} ({r.ms_pct:.1f}%) | {r.over:,.0f} | {r.p90:.0f} | {r.p90_inv:.0f} |"


LV_T = "\n".join([f"| Before (the year as it ran) | | | {d0('l.base.ms_late')} ({d1('l.base.ms_late_pct')}%) | {d0('l.base.over45')} | {d0('l.base.p90')} | {d0('l.base.p90_inv')} |"]
                  + [lv_row(c, n) for c, n in [("pay0", "1. Pay on the first run"), ("pay1", "1. Pay on the first run"), ("pay2", "1. Pay on the first run"), ("queue", "2. Balanced pick order"),
                                              ("in3", "3. Three intake rules"), ("in1", "3. Three intake rules"), ("inopt", "3. Intake, optimistic"),
                                              ("low", "**All three, low**"), ("mid", "**All three, middle**"), ("high", "**All three, high**")]])
fig("d.hours.full", f("o.pre.hours") + f("o.track4b.hours"), "hours for the full checker plus the full work queue, which do not fit")
pd.DataFrame([dict(id=k, value=v_, description=d_) for k, (v_, d_) in own.items()]).to_csv(OUT / "figures_design.csv", index=False)

# ------------------------------------------------------------------ the note
CHK = ["| ID | Check | Class | What it needs | Queries last year | Saturday prototype |", "|---|---|---|---|---|---|"]
for cid, text, k, need, rules, proto in CHECKS:
    nq = sum(int(qr[r]) for r in rules)
    CHK.append(f"| {cid} | {text} | {k} | {need} | {nq if rules else '-'} | {proto} |")
CHKT = "\n".join(CHK)
CLS = ["| Class | Meaning | Checks | Queries last year |", "|---|---|---|---|"]
for k, label in CLASS.items():
    CLS.append(f"| **{k}** | {label} | {cls_n[k]} | {d0('d.queries.' + k)} |")
CLS.append(f"| none | Not tied to a checklist item (holds, bank details, hard copy) | - | {d0('d.queries.none')} |")
CLST = "\n".join(CLS)
ST = ["| Bill | Vendor in master | Work order | Number already booked (excluding its own row) | Facts the intake checks would show | Expected route |", "|---|---|---|---|---|---|"]
for r in S.itertuples():
    oth = "; ".join(f"{t[0]} ({t[1]}, ₹{t[2]:,.0f})" for t in r.others) or "none"
    facts = f"supplier state {r.gstin[:2]}, recipient GSTIN state {r.rec}, printed place of supply {r.pos}, {r.tax}"
    if r.udyam:
        facts += f"; printed 'Udyam registered: {r.udyam}' against master '{r.master_ms}'"
    route = "Auto-clear if the reader is confident"
    if r.others:
        route = "Human look: same vendor and invoice number, different date and amount"
    if r.file.startswith("bill-11"):
        route = "Human look: tax type against place of supply (see section 5); master MSME status blank"
    if r.file.startswith("packet-08"):
        route = "Human look: place of supply; the number is reused by a later bill; at the extract date the work order is past its approved value"
    ST.append(f"| {r.file} | {r.vendor}, {r.vname}, {r.vstate}, MSME {r.master_ms} | {r.wo} for {r.prop}, valid on the bill date: {r.wo_valid}; approved less billed to date (this bill included) {'minus ' if r.headroom < 0 else ''}₹{abs(r.headroom):,.0f} | {oth} | {facts} | {route} |")
STT = "\n".join(ST)

md = f"""# Solution design: intake verdicts and a work queue

Scoped to what can be built by Saturday 17 October, 10 pm IST. Numbers are registered in `notes/numbers.md` (ids `d.*`, plus the ids they read). Where I read a bill myself, the note says so.

## 1. What it is, and how it relates to the options note

One product with two parts that share one data model:

- **Part A, intake verdicts.** When a bill arrives, read it, check it against the bill's own content and SAP data, decide **auto-clear, fix-before-sending or human look**, and tell the person who owns the fix in minutes, not after the packet has travelled.
- **Part B, work queue.** A live view of every bill's stage and age that orders the AP verifiers' trays, builds the next payment-run list, and sends the vendor a status message. This is where most of the days are (`notes/problem.md`).

`notes/options.md` recommended Part B (option 4b) plus a courier what-if, and argued that Part A has the lower days but is where the case's document-reading skill shows. This design builds both as one slice, because the verdict needs somewhere to land and the queue needs the verdict as its first event. They do not both fit in full: the full checker is {d1('o.pre.hours')} hours and the full queue {d1('o.track4b.hours')}, {d1('d.hours.full')} together, against {d0('o.hours.budget')} available. Section 9 is the slice that fits.

## 2. Who uses it, and at what moment

| Moment | Person | What they see | What they do next |
|---|---|---|---|
| The vendor's bill reaches the facility desk (or a photo arrives on WhatsApp) | Facility desk | A scan screen; within a minute a verdict on the bill | Hands the packet on if clear; if a fix is asked, tells the vendor before filing |
| The verdict is ready | Vendor | A WhatsApp message with the exact fix: `GSTIN differs from our record`, `HSN/SAC missing`, `send the PF and ESIC challan` | Corrects and resends the same day (the agency owner: "if somebody had sent one WhatsApp, I would have fixed it the same evening.") |
| The executive opens the bill | Commercial executive | The bill, the verdicts with the evidence, and the work-order headroom | Confirms or overrides a human-look item; does the checks that need the paper and the service entry |
| A work order is found expired or without balance | Procurement | A task with the work order, the shortfall, and the paper to collect (RWA letter or tenant approval, budget note) | Starts the amendment on day one instead of when the service entry fails |
| The signed packet reaches head office | AP lead | A work queue ordered by age, balanced across the five verifiers | Assigns the oldest bills first, evens the load |
| A bill is posted | Treasury | The next Tuesday or Friday run list, with bills that missed the last run at the top | Pays at the next run |
| Monday morning | CFO | The twenty oldest bills, where each sits and since when | Calls the owner. "If one screen says this bill is here since this date, the argument is over." |

## 3. Data flow: bill arrival to verdict to the owner being told

```mermaid
flowchart TD
  A[Bill arrives: desk scan of the packet or vendor photo on WhatsApp] --> B[Store the original: file, SHA-256, received-at]
  B --> C[Read: fields and a confidence per field]
  C -->|any needed field below 0.70| R[Ask the vendor to resend a clearer image]
  C --> D[Match to SAP data: vendor by GSTIN, work order, property, earlier bills]
  D --> E[Run the intake checks]
  E --> F{{Route}}
  F -->|all pass, every confidence 0.90 or more| G[Auto-clear: executive queue marked pre-checked]
  F -->|fails with confidence 0.90 or more, fix in the vendor's hands| H[Fix-before-sending: message to the vendor, copy to the executive]
  F -->|fails, fix in the company's hands| I[Task to procurement or the executive with the checklist]
  F -->|confidence 0.70 to 0.90, or owner unclear, or rule unsettled| J[Human look: evidence side by side]
  G --> K[Tracker timeline and audit log]
  H --> K
  I --> K
  J --> K
  R --> K
  K --> L[Executive checks and service entry, property head signs]
  L --> M[AP work queue by age and load, next-run payment list]
  M --> N[Verifier posts in SAP, treasury pays]
  N --> O[Days to pay computed from the event log]
```

**Events recorded for every bill** (the event log is the audit trail and the source of every metric): arrived, stored (hash), read (field confidences), checked (each check, its result, the data it used, the rule version), routed, notified (who, channel, text), acknowledged, fixed, executive verified, property head signed, packet sent or scanned to AP, picked, posted, assigned to a payment run, paid.

**Timing target, to be measured:** the owner is told within five minutes of the scan. The target is a design aim; the Saturday prototype will report what it actually takes.

**What the bills look like (checked by hand).** None of the {d0('d.samples.no_text_layer')} PDFs in the inbox has a text layer: every page is one embedded image, so no PDF can be read as text. With the nine phone photos, all {d0('d.inbox.files')} files need a reader that works on images. The printed fields are consistent: supplier name and GSTIN, invoice number and date, work order or PO, place of supply, HSN/SAC, rate, taxable value and tax lines. Two of the four bills I opened print 'Udyam registered: Micro', which gives a second source for MSME status where the master is blank (it is a claim by the vendor, to be verified, not proof).

## 4. The 25 checks: which run at intake, and which cannot without the paper

The property checklist has 11 checks (P1 to P11) and head office has 14 (H1 to H14). Eight pairs are the same check done twice (`notes/workflows.md` section 7); one implementation serves both.

{CLST}

Of the 25, **{cls_n['I']} run at intake from the bill and the SAP extract**, **{cls_n['X']} need reference data the pack does not hold**, **{cls_n['PK']} need the rest of the packet (the attendance sheet, challans and service report) and so cannot run on a bill photo alone**, and **{cls_n['L']} cannot run at intake at all** because they depend on a step that has not happened (service entry, signature) or on other sources (biometric, gate register, the TDS decision).

{CHKT}

Reading the tables:

- **Packet checks (PK) run only if the desk scans the whole packet**, which it can, because the vendor hands it over together. A vendor's WhatsApp photo of the bill alone can only get the bill-level checks, so fix-before-sending on a photo covers class I and X only.
- **P5 is not an intake check.** The bill's man-days can be tied to the attendance summary page (in the one packet I opened both read 388), but matching against biometric and the gate register is the three-way match, which is a separate option and a separate week.
- **Queries last year by class** show where an intake check could have acted: {d0('d.queries.I')} on class I items and {d0('d.queries.X')} on class X. Not all of them are catchable on day one with the extract provided: only {d0('layer.AB.cum_queries')} of {d0('q.rows')} queries ({pc('layer.AB.cum_pct')}) can be, because balance, quantity and rate need SAP fields beyond the extract (`notes/query-forensics.md`).

## 5. How confidence routes a bill

**Inputs.** The reader returns a value and a confidence between 0 and 1 for each field. Each check uses some fields; the check's confidence is the lowest confidence among them, multiplied by how certain the rule itself is (1.0 for a database lookup such as GSTIN against the master, lower for a rule that is not settled, such as place of supply).

**Starting thresholds, to be tuned on the labelled bills.** 0.90 and 0.70. They are choices, not findings; there is no accuracy figure for the reader yet.

| Situation | Route | Who is told | What they see | Why |
|---|---|---|---|---|
| Every intake check passes and every confidence is 0.90 or more | **Auto-clear** | Executive (the bill appears marked pre-checked) | Nothing to resolve | It only means no intake finding. Every later check still runs |
| A check fails, confidence 0.90 or more, and the fix is the vendor's (GSTIN differs, HSN/SAC missing, wrong company name, PF/ESIC or service report page absent, rate printed as 12 where 18 applies) | **Fix-before-sending** | Vendor by WhatsApp; executive copied | The exact fix, and why | Same-day fix, not a query three weeks later |
| A check fails, confidence 0.90 or more, and the fix is the company's (work order expired, value headroom exhausted) | **Fix-before-sending, internal** | Procurement and the executive; the vendor gets a status message only | The work order, the shortfall, and the papers to collect | The amendment starts on day one; the bill is not blocked |
| Any needed confidence between 0.70 and 0.90 | **Human look** | Executive | The field image beside the value read | A person confirms a doubtful read |
| The rule is unsettled or the owner is ambiguous: place of supply against tax type; same invoice number with a different date or amount | **Human look** | Executive (AP verifier if it is a head-office item) | All the facts side by side | The law or the data does not settle it |
| A needed field is below 0.70 | **Resend** | Vendor | `Please send a clearer photo` | No verdict is better than a wrong one |

**Two bills from the inbox show why the unsettled rows exist.** In bill-11 the supplier's GSTIN is in Uttar Pradesh, the recipient GSTIN printed is a Haryana one (state code 06), the printed place of supply is Uttar Pradesh, and the tax charged is IGST. Under a recipient-location rule that is inter-State and IGST is right; under the printed place of supply it is intra-State and IGST is wrong. `notes/research.md` section 7 explains why the rule is unsettled. The check therefore **shows the three facts and routes to a human look; it does not fail the bill.** The same recipient GSTIN appears on all four bills I opened (Noida, Gurugram and Panchkula properties), which suggests one company registration across properties; the pack does not list the company's registrations.

**Sizing the human-look queue.** Each percentage point of bills sent to a human look is {d0('d.human_per_pct')} bills a year, or {d1('d.human_per_day')} a working day on 250 days. The year's data says a finding at intake would have been available on {pc('o.pre.AB.pct')} of paid invoices (layers A and B, {d0('o.pre.AB.bills')} bills) and {pc('o.pre.ABC.pct')} if SAP also exposed work-order lines, rates and open quantity. Reader confidence will add to the human-look share; that share is the number to measure first.

**How thresholds are tuned.** By days saved per human look, not accuracy. A false auto-clear costs what a bill costs today (a query later); a false flag costs a vendor message and an executive's minutes. The labelled bills give the first estimate of the trade; the pilot gives the real one.

### Acceptance tests: four bills read by hand and joined to the pack

Printed values were read by eye from the images in `bill-inbox/` and joined to the vendor master, the work orders and the register. They are the expected results the prototype must reproduce.

{STT}

## 6. Controls that stay untouched

| Control | Source | What the product does |
|---|---|---|
| The original bill is filed at head office for GST audit | CFO: "The original bill has to be with us for GST audit."; policy: "Original bills and supporting documents are filed at head office" | Nothing changes when the paper travels or is filed. The product may show whether the original has arrived; it never replaces it |
| The property certifies the work | CFO: "The property must certify the work."; P6, P10, P11 | The executive still creates the service entry, the department head still signs the attendance, the property head still signs the packet. The product signs nothing and creates nothing in SAP |
| An RWA letter for work-order amendments | Procurement: "But without the RWA letter, audit will catch us." | The task asks for the letter on day one. It never waives it |
| All 25 checks still run in their present owners' hands | `notes/workflows.md` | Auto-clear means no intake finding, not approval. Head office still runs H1 to H14 |
| Posting in SAP is by a verifier | SAP extract spec | The product proposes entries in its own store. It writes nothing into SAP |
| Payment release is by treasury | Payment policy: runs on Tuesdays and Fridays | The product builds the list; treasury approves and pays |
| The TDS section for each order is the AP lead's decision | `transcripts/02-central-ap-lead.md` | The product stores her decision per work order and flags a bill that differs. It does not choose |
| Segregation: nobody can clear their own override | Audit practice | An override by a human look is logged with who, when and why |

## 7. What is simulated, and what a real connection needs

| Part | In the Saturday prototype | What a real connection needs |
|---|---|---|
| Bill intake | The 40 inbox files loaded through an upload screen, standing in for the desk scanner and WhatsApp | A desk scanner or phone app; for WhatsApp, the Business API inbound webhook. Download each file within hours (the media ID in a webhook lasts 7 days), hash it, and store it on the company side in India |
| The reader | A vision model reading the page images. Fallback: stored extractions for the labelled bills, marked simulated | A contract and data-protection terms with the model provider, cost per bill, and an accuracy report on the client's own bills |
| SAP reads | `sap_extract.sqlite`: vendor_master, work_orders, properties, posted_invoices | **RFC read access is approved.** Request work-order lines and rates, open quantity and period balance, service-entry status, and posting and payment status, which the extract lacks |
| SAP writes | Only the stand-in's `parsed_bill` table, as the extract spec allows | **Writing invoices needs a separate project with the SAP partner and audit sign-off**; the last write interface took seven to eight months to approve before any code (IT head). The product never posts, so the design does not depend on it |
| WhatsApp out | An outbox table and a preview of each message; nothing is sent | **WhatsApp Business API on a company-owned number, with files stored on the company side** (IT head), through a provider with a processing agreement. Approved templates, recorded opt-in, the 24-hour window, and DPDP notice and consent (core duties about May 2027). See `notes/research.md` section 9 |
| Audit trail | An append-only event table in the app's database: file hash, rule version, each check with its data, each notification, each human decision | A tamper-evident store in India, retention for the GST period (72 months), access and edit logs, and an export auditors can read |
| Users and roles | One local user | Single sign-on and roles for desk, executive, AP, procurement, treasury and the CFO |
| Payment runs | A replay on the register with a cut-off of 0, 1 or 2 days, and the next-run list in the work queue | Treasury's run lists, approval times and the written cut-off (`notes/payment-lag.md`); the product only proposes the list |
| Courier | A what-if switch for a second weekly or a daily courier (stretch) | The courier cost, not in the pack |

## 8. Success is days to pay, not field accuracy

**Primary measures:** (1) mean days from the desk logging the bill to payment, and from invoice date to payment; (2) the number and share of paid invoices over 45 days from the desk, and the same for known Micro and Small vendors; with the 90th percentile beside both. Baseline from the year: **{d1('l.base.desk_mean')} days from the desk and {d1('l.base.inv_mean')} from the invoice date**; **{d0('l.base.over45')} paid invoices ({d1('l.base.over45_pct')}%) over 45 days** and **{d0('l.base.ms_late')} known Micro and Small invoices ({d1('l.base.ms_late_pct')}% of {d0('l.n_msme_known')}) over 45 days**; p90 {d0('l.base.p90')} days from the desk and {d0('l.base.p90_inv')} from the invoice date.

**Expected effect, replayed on last year's register** (part f; conditional on the people who own each lever acting, not promised). Ranges are the settings stated in section 9:

| Lever | Owner | Days off the mean |
|---|---|---|
| Pay on the first run after posting | Treasury and the AP lead (the product builds the next-run list) | {d2('l.lever.pay2.save')} to {d2('l.lever.pay0.save')} |
| Balanced AP pick order | AP lead (the product builds the pick order) | {d2('l.lever.queue.save')} |
| Three intake rules | The product, with the desk and executive acting on the verdict | {d2('l.lever.in3.save')} to {d2('l.lever.inopt.save')} |
| **All three together** | | **{d2('l.lever.low.save')} to {d2('l.lever.high.save')}**, middle {d2('l.lever.mid.save')} |

- **Mean days from the desk:** {d1('l.base.desk_mean')} falls to **{f('l.base.desk_mean') - f('l.lever.high.save'):.1f} to {f('l.base.desk_mean') - f('l.lever.low.save'):.1f}**; from the invoice date {d1('l.base.inv_mean')} falls to {f('l.base.inv_mean') - f('l.lever.high.save'):.1f} to {f('l.base.inv_mean') - f('l.lever.low.save'):.1f}.
- **Paid invoices over 45 days:** {d0('l.base.over45')} falls to **{d0('l.lever.high.over')} to {d0('l.lever.low.over')}**. **Known Micro and Small over 45 days:** {d0('l.base.ms_late')} falls to **{d0('l.lever.high.ms_late')} to {d0('l.lever.low.ms_late')}** ({d1('l.lever.high.ms_pct')}% to {d1('l.lever.low.ms_pct')}%).
- The separate levers add up to {d2('l.lever.low.sum_alone')} to {d2('l.lever.high.sum_alone')} days; the combined replay gives {d2('l.lever.low.save')} to {d2('l.lever.high.save')}, a little more, because a bill that is posted earlier can also catch an earlier run. Nothing is counted twice.
- **Where the days are:** payment-run timing and the pick order, not the intake rules. The three intake rules the register can test move the mean by {d2('l.lever.in3.save')} to {d2('l.lever.inopt.save')} days. Queries still drive the tail (`notes/payment-lag.md`): {d0('l.chk.over45_queried')} of the {d0('l.chk.over45')} bills over 45 days had one, and removing every query would cut at most about {d1('l.chk.q_ceiling_added')} days from the mean.

**Supporting measures (each from the event log):**

| Measure | Baseline | Where it comes from |
|---|---|---|
| Bills with no query (first-time-right) | {d1('d.ftr.baseline')}% | `share.bills_with_query_pct` |
| Days a query stays open | {d1('query.mean_days_among_queried')} | query log |
| Days waiting for a verifier | {d1('overall.s05.cal_mean')} | stage times |
| Days after posting before payment | {d1('overall.s08.cal_mean')} against {d1('p.pay.schedule_wait_lead0')} if every bill made the next run | stage times and payment-run model |
| Known Micro and Small invoices late on the desk clock | {d0('e.paid.desk_received.microsmall_known.n_late')} ({pc('e.paid.desk_received.microsmall_known.pct_late')}); {d0('l.lever.high.ms_late')} to {d0('l.lever.low.ms_late')} with the three levers (part f) | `notes/msme-exposure.md`, replay in part f |

**What does not count as success:** field-level accuracy of the reader. It is reported as a diagnostic and used to set thresholds, and a project that raises it while the days stay the same has failed. The earlier OCR pilot closed green on accuracy and "nothing improved for the vendor" (IT head); "We measured accuracy. We did not measure days."

**Guardrails:** no rise in the query rate; no check dropped; the human-look queue never older than two working days; every override logged.

**How it would be proven in a pilot:** switch on a few properties first and compare their mean days to pay and their bills over 45 days with the others over the same weeks, from the event log. The Saturday demo shows the **replay on last year's register**, which is a counterfactual and is labelled as one.

## 9. Scope for Saturday 10 pm

Budget: {d0('o.hours.budget')} build hours (`notes/options.md`: 30 clock hours less sleep, life and 3 hours of slack, so the slack is already outside the 14). The slice below is **{d1('d.hours.must')} hours with nothing spare**. The spare hour of the first version ({d1('d.hours.old')} used) went to the backtest, and **the README run steps move to Sunday**, before the Monday 1 pm deadline. My estimates, not measurements.

| Part | What | Hours | First version |
|---|---|---|---|
{HRS_T}
| | **Total** | **{d1('d.hours.must')}** | **{d1('d.hours.old')}** |

**What paid for the new work.** The backtest took the spare hour (f 1.0 to 2.0). Design and polish (1.5) and the MSME countdown with the runway view (1.0, inside e) came out of the other parts: 0.5 each from a, b, c and d (2.0 in all), against 0.5 more in e, whose pick order and next-run list (which share one sort) drop from 2.0 to 1.5 and whose countdown and runway view add 1.0. In plain terms: the tracker timeline is a table, not a chart (a); the reader screen has no styling until polish (b); the H11 and H10 facts are shown as plain values with no explanation text (c); and the in-app tasks are a single list (d).

**Where the MSME countdown and the runway view are built: part e.** The countdown shows, for each open bill from a Micro or Small vendor, the days since the desk logged it, the days left to day 45 on the desk clock (`notes/assumptions.md`), and the Tuesday and Friday payment runs left before then. The runway view shows, for each work order, the days to its end date and the value headroom (approved less billed) against its average monthly billing. Both read the register and the work-order table loaded by part a, so no new data work is needed. They cost 0.5 hours each.

**The three screens.** Intake (parts b, c, d), work queue and control tower (part e, with the countdown and runway view), impact (part f).

**In the slice:** the intake screen and reader; checks P1/H1, P3/H3 and H13, plus H11 and the H10 facts; the three-way routing with the thresholds above; a simulated WhatsApp outbox and in-app tasks; the AP work queue with the next-run list, the MSME countdown and the runway view; the backtest; the audit event log.

**Stretch, only if ahead of plan:** presence checks for the attendance page and the PF and ESIC challans on the packets (P6, P7, H6, H7); the courier what-if switch.

**Cut, and why:** the attendance three-way match (separate option, one property and one month in the pack); the courier cost model; real WhatsApp and SAP; sign-in and roles; the vendor portal.

**Cut order if time runs short** (first item goes first). The next-run payment list and the AP pick order are protected, because the replay puts the days in payment-run timing and the pick order:

1. The in-app tasks in d (0.4 hours). The outbox stays.
2. H11 (0.3 hours inside c).
3. The H10 facts (0.4 hours inside c).
4. The work-order runway view in e (0.5 hours). My addition: the MSME countdown stays because it carries the exposure the CFO will ask about.

Never cut: part a, the routing in c, part f, the AP pick order and the next-run payment list in e. Taken in full, the order frees 1.6 hours.

**Order and checkpoints.** Friday evening: part a and the first five bills through the reader. Saturday morning: the reader on ten bills, the checks and routing. Saturday midday: notifications, then the work queue with the countdown and runway view. Saturday afternoon: the backtest (2 hours), then polish on the three screens. Freeze at 8 pm; 10 pm is the cut-off. Sunday: README run steps, deck and video.

**Decision rules.** If by Saturday noon the reader does not read at least 8 of the 10 labelled bills correctly on the fields the checks use, switch to stored extractions, mark the screen `reader simulated`, and spend the saved time on the queue and the backtest. If part c runs over, follow the cut order above. If any part has not started by 4 pm Saturday, cut it.

### Part f: replay three levers on the register

**What it does.** It replays the register ({d0('l.bt.raw_rows')} rows in `bill_register.csv`) as bills arriving on their desk dates, as if checked on that date. **Rows versus bills:** {d0('l.bt.dropped')} rows are exact duplicates (`notes/data-audit.md` D01), so the replay uses {d0('l.bt.bills')} distinct bills, of which {d0('l.n')} are paid invoices, and the screen says so. Three levers, each alone and then all together:

1. **Pay on the first run after posting**, with the run list closing 0, 1 or 2 days before the run. A bill that was in fact paid earlier is not moved later.
2. **A balanced AP pick order:** each AP-1 bill gets the pick-up wait of the other four verifiers at the same rank in the queue, so the AP-1 mean ({d1('l.chk.ap1_wait')} days) falls toward theirs ({d1('l.chk.others_wait')} days).
3. **The three intake rules** that the register and the SAP extract can test: duplicate invoice number (H13), work order expired on the invoice date (H3), and work order value exhausted (H3, as value headroom: invoices on the order so far in desk order, above the approved value). A caught query costs a **residual delay of 1 or 3 days** instead of the {d1('query.mean_days_among_queried')} days it stayed open on average. An optimistic setting takes every layer A and B query (`notes/query-forensics.md`), removes the {d2('l.bt.extra')} days a queried bill carries beyond the days its query stays open, and leaves a 1-day residual; that setting assumes SAP fields beyond the extract.

**Combined without double counting.** Each bill's own dates move. The pick-order and intake savings bring its posting date forward (never earlier than its desk date). The payment-run lever then pays it on the first run after the new posting date, or at the old payment date less the shift, whichever is earlier. Days are therefore not added twice; the small difference from simply adding the three is shown in section 8. In the settings that apply the payment-run lever, the run is what binds. Where it is not applied, the queue and intake days assume payment follows posting at the same gap, which is the shift model, not a Treasury fact.

**What the intake rules would have caught, against the queries actually raised:**

| Rule | Query rules | Queries last year | On bills the rule flags | Not caught | Bills flagged | Flagged, never queried |
|---|---|---|---|---|---|---|
{BT_T}

The last column is the false-alarm load: a flag with no query is a bill someone would have looked at for nothing, or a real problem nobody raised. The backtest cannot tell which. Of {d0('l.bt.q_total')} queries in all, the three rules touch {d0('l.bt.q_testable')} and the flags land on {d0('l.bt.q_caught')} of them, which is why lever 3 is small.

**Results.** Days off the mean are the same on both clocks. Counts are of the {d0('l.n')} paid invoices; Micro and Small counts are of the {d0('l.n_msme_known')} known Micro and Small ones (desk clock).

| Lever | Setting | Days off the mean | Known Micro and Small over 45 days | All paid over 45 days | p90 desk to paid | p90 invoice to paid |
|---|---|---|---|---|---|---|
{LV_T}

**Reading.** Residual 1 against 3 days gives {d2('l.lever.in1.save')} against {d2('l.lever.in3.save')} days: the two differ by about {f('l.lever.in1.save') - f('l.lever.in3.save'):.2f} because the residual is small against the {d1('query.mean_days_among_queried')} days a caught query actually cost and only {d0('l.lever.in1.bills')} bills are caught. What moves the number is how many queries the rules catch, not what a catch costs. The combined low, middle and high rows use the cut-off 2, 1 and 0 settings with residual 3, residual 1 and the optimistic intake setting.

**Dependencies to settle tonight (for the whole slice, not only part f).** A model API key for the reader, and whether sending the sample bills to an outside model is acceptable (they are fictional; a real client would need data-protection terms). If there is no key, the reader is simulated from the start.

## 10. Open risks

- **The reader is the one component that can fail the demo.** Nine of the forty files are phone photos, some skewed on a dark background; scanned PDFs add noise.
- **Place of supply is unsettled** (`notes/research.md` section 7), so H10 shows facts and does not decide.
- **The company's registrations and legal entity names are not in the pack**, so P2/H2 is partial.
- **The days depend on action by people** for the queue part, and on SAP fields beyond the extract for the upper end of the intake part.
"""
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
(ROOT / "notes" / "solution-design.md").write_text(md, encoding="utf-8")
print("wrote notes/solution-design.md;", len(own), "figures")
print(S[["file", "vendor", "master_ms", "wo_valid", "headroom", "own", "others"]].to_string(index=False))
