# Options scored

Scores the eight options using `notes/problem.md` and the analysis behind it. Every number is registered in `notes/numbers.md` (ids `o.*`, and the ids they read). The official deadline is Monday 19 October 2026, 1 pm IST (`Riklr-FDE-Case-Study.pdf`); Saturday 10 pm is your build cut-off, which leaves Sunday and Monday morning for the deck, video and README.

## How to read the scores

- **Days saved on the mean** = days saved per affected bill × share of bills affected. It is the number of days the option takes off the 37.6-day mean invoice-to-paid time, so every option is on one scale. **Central** is my best defensible case and the one used to rank; low and high bracket it.
- **Bills affected** are paid invoices from the 10,449 behind `stage_times.csv`. **Days per affected bill** = central days saved ÷ share affected.
- **Build hours are my estimates**, by component, for a working demo on the pack data. They are not measured. The budget is 14 hours: 30 hours from Friday 16 October 15:56 IST to Saturday 22:00, minus 8 for sleep, 5 for meals, breaks and everything else, and 3 for debugging, repo set-up and the chat-history export. Change the three deductions if your day is different; the ranking by days does not move.
- **Days are conditional where marked.** The tracker's days exist only if the AP lead and treasury act on it; scan-first's days exist only if the audit view allows booking from a scan.
- Option 4 as listed (tracker with a status message) saves no days by itself. I added **option 4b**, a tracker built as a work queue, because the two causes that `notes/problem.md` ranks first (payment-run lag and the AP queue) are not in your list, and a tracker is the only listed option that can reach them.

## Scores, ranked by central days saved

| Rank | Option | Days saved on the mean (low to high) | **Central** | Bills affected | Days per affected bill | Build hours | Days per hour | Audit and control risk | Vendor adoption | SAP write |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Scan-first, original later** | 0.00 to 4.98 | **4.98** | 10,449 (100.0%) | 4.98 | 10 | 0.50 | Medium to high | n/a | None |
| 2 | **Live tracker as a work queue (extension of option 4)** | 0.00 to 5.37 | **3.62** | 8,620 (82.5%) | 4.39 | 11.5 | 0.31 | Low | 64% | None |
| 3 | **Daily courier** | 1.70 to 2.98 | **2.98** | 10,449 (100.0%) | 2.98 | 1 | 2.98 | None | n/a | None |
| 4 | **Attendance three-way match** | 0.53 to 2.11 | **1.06** | 4,840 (46.3%) | 2.28 | 7 | 0.15 | Low to medium | n/a | None |
| 5 | **Pre-flight checker at intake** | 0.28 to 1.22 | **0.57** | 403 (3.9%) | 14.86 | 14.5 | 0.04 | Low | 58% | None |
| 6 | **Vendor portal** | 0.00 to 6.36 | **0.57** | 940 (9.0%) | 6.36 | 17 | 0.03 | Medium to high | 9% | None for the prototype |
| 7 | **Work-order runway alert** | 0.00 to 0.64 | **0.22** | 93 (0.9%) | 24.27 | 6 | 0.04 | Low | n/a | None |
| 8 | **OCR at head office** | 0.00 to 1.58 | **0.16** | 10,449 (100.0%) | 0.16 | 10.5 | 0.02 | Low to medium | n/a | None for the prototype |
| 9 | **Live tracker with a vendor status message (as listed)** | 0.00 | **0.00** | 10,449 (100.0%) | 0.00 | 7.5 | 0.00 | Low | 64% | None |

Pre-flight checker and portal tie at 0.57. Days per hour is central days divided by build hours; the courier row is high only because there is almost nothing to build. **Over the 14-hour budget on their own:** Pre-flight checker at intake (14.5 h), Vendor portal (17 h).

## Formulas

1. **Scan-first, original later.** Courier lag removed from the booking path: mean signature-to-head-office days = 4.98, on all 10,449 bills. Low = 0 if the audit view says booking needs the paper in hand. The AP wait is assumed to start at the scan instead of the packet.
2. **Live tracker as a work queue (extension of option 4).** From notes/problem.md: AP-1 queue gap 1.65 + payment-run lag 1.97 (list closes 2 days ahead) = 3.62; upper end 5.37 with list lead 0. Low = 0 if nobody acts on it. Bills affected = AP-1's bills plus bills paid after a later run than the next.
3. **Daily courier.** Mean lag 4.98 d now, 2.00 d with a daily arrival, keeping the observed 2-day minimum = 2.98. Low = 1.70 with a second weekly arrival (lag 3.28). The model reproduces today's lag exactly.
4. **Attendance three-way match.** Manpower bills spend 8.07 d in the property check against 3.51 d for other bills: excess 4.56 d on 46.3% of bills = 2.11 (high). Central = 50% and low = 25% of that: **an assumption**, because the data cannot split matching from the department head's signature and the PF/ESIC check.
5. **Pre-flight checker at intake.** Sum over caught queries of min(days open, days from desk to AP pick-up), divided by 10,449 bills. Layers A: 0.28, A+B: 0.57 (central), A to C: 1.22 (needs SAP fields beyond the extract). 14.8 days per caught bill on 403 bills.
6. **Vendor portal.** Survey adoption 9% x vendor-to-desk days 6.36 = 0.57, on 9% of bills (assuming bills in proportion to vendors). High = 6.36 if mandatory (the IT head's belief, reported). Vendor-side query days are not removed by a portal.
7. **Work-order runway alert.** Query-open days on work-order expiry queries / 10,449 bills = 0.22 (central: the part SAP dates verify). High = all work-order queries 0.64 on 2.9% of bills. Low = 0 if amendments take longer than the warning gives.
8. **OCR at head office.** Central = the AP lead's 'about 10%' (reported) x AP verification days 1.58 = 0.16. High = all of verification, 1.58. Low = 0: the earlier OCR pilot left the days unchanged.
9. **Live tracker with a vendor status message (as listed).** Direct days = 0: a tracker shows the wait, it does not shorten it. It is the instrument for the two head-office fixes (up to 3.62 to 5.37 days) only if someone acts on it; that is the extension above.

## Build effort, by component

Hours to a working demo on the pack data, including debugging, using Claude Code. Sorted by size.

- **Daily courier, 1 h.** a what-if switch inside the tracker 1; nothing to build.
- **Work-order runway alert, 6 h.** burn-rate model 2, alert list and UI 2.5, check against the 107 expiry queries 1.5.
- **Attendance three-way match, 7 h.** parse the three files and fuzzy match 3, mismatch view 3, test on the February sample 1.
- **Live tracker with a vendor status message (as listed), 7.5 h.** stage ages 2, tracker UI 4, status message templates and preview 1.5.
- **Scan-first, original later, 10 h.** scan and upload page 3, originals-pending list and payment hold flag 2, AP work list from scans 2, control note 1, UI 2.
- **OCR at head office, 10.5 h.** bill reader 5, review and confirm screen 3, write to parsed_bill 1, hand-label 10 bills for accuracy 1.5.
- **Live tracker as a work queue (extension of option 4), 11.5 h.** stage ages and data model 2, tracker UI 4, vendor status messages (mock send) 1.5, AP pick order and next-run payment list 2.5, replay of the year 1.5.
- **Pre-flight checker at intake, 14.5 h.** bill reader 5, rule engine 4, vendor fix-it message 1, UI 3, test on the 40 bills 1.5.
- **Vendor portal, 17 h.** login, upload and status 5, bill reader 5, status messages 2, vendor UI 3, admin view 2.

## Audit and control risk, vendor adoption, SAP write

| Option | Audit and control risk | Why | Vendor adoption (survey) | SAP write: prototype | SAP write: production |
|---|---|---|---|---|---|
| Scan-first, original later | Medium to high | Booking before the original is in hand; K1 control. Mitigation: hold payment until the original is received (it arrives within days) | None needed (internal) | None | None |
| Live tracker as a work queue (extension of option 4) | Low | Read-only plus work ordering; no check removed; a status message needs the vendor's consent (DPDP) | 64% would use a WhatsApp status update | None | None (reads posting and payment status over RFC) |
| Daily courier | None | Controls unchanged; the cost is money, and the courier cost is not in the pack | None needed (internal) | None | None |
| Attendance three-way match | Low to medium | The signatures stay; a wrong match could cut a vendor's days, so a person confirms mismatches | None needed (uses the vendor claim already sent) | None | None |
| Pre-flight checker at intake | Low | Adds a check and removes none; a person confirms | Works at the desk; 58% of vendors prefer WhatsApp if used before printing | None | None (RFC read is approved) |
| Vendor portal | Medium to high | A new vendor-facing system of record: access control, bank details, personal data; the full vision writes to SAP | 9% prefer a portal; 12% already use one for another client and find it hard | None for the prototype | Needed for the two-way vision: last write interface took seven to eight months to approve |
| Work-order runway alert | Low | Read-only warning; false alerts are the risk | None needed (internal) | None | None (reads work orders over RFC) |
| OCR at head office | Low to medium | A misread GSTIN posted without a person looking is the verifier's fear | None needed (internal) | None for the prototype | Auto-posting needs write access (separate project, audit sign-off) |
| Live tracker with a vendor status message (as listed) | Low | Read-only; status messages need consent | 64% would use a WhatsApp status update | None | None |

Survey figures (`vendor-survey-summary.md`, 212 vendors responded): 58% prefer WhatsApp, 27% email, 9% a portal, 6% paper; 64% would use a status update on WhatsApp; 12% already use a portal for another client and find it hard.

## Recommendation

**1. Build: the live tracker as a work queue (4b), 11.5 hours.** It is the only listed option that reaches the two causes ranked first in `notes/problem.md`: packets waiting for a verifier and posted bills missing the payment run. Central 3.62 days, up to 5.37, on 8,620 bills (82.5%). It needs no SAP write, no vendor adoption for the days, and changes no control. The vendor status message is the part vendors asked for (64% would use it), and the CFO asked for the screen: "a dashboard for me that shows what is stuck and where". The prototype replays the year to show what each rule would have changed.

**2. Recommend to the client, no extra build: a second weekly or daily courier, 1 hour** as a what-if switch inside the tracker. 1.70 to 2.98 days on every bill for a cost the pack does not give.

Together 12.5 hours of the 14 available, 1.5 spare, and 5.3 to 8.3 days off the mean (14% to 22%).

## The case against my own pick

- **The tracker saves no days by itself.** Everything in the 3.62 depends on two people acting. The organisation has been here before: the monthly review "became a complaint session and people stopped joining" (CFO). A work queue that orders the AP lead's tray and builds the treasury list lowers the dependence on goodwill but does not remove it.
- **I am leaving the largest number on the table.** Scan-first is 4.98 days, more than the tracker's central 3.62, and is ranked first. I rejected it for the audit view that is not yet in hand, not for its days. If the tax adviser says yes on Saturday, I chose wrong.
- **The payment-run estimate may be wrong.** It rests on register posting dates that are day-accurate at best, and it assumes the run list is the only cause. If treasury approvals explain the lag, the second half of the tracker's days shrinks (`notes/problem.md`, what would change my mind).
- **The queue fix rests on one verifier code.** If AP-1's longer wait is deliberate, that part goes to zero.
- **It does not touch the checks.** Queries cost 2.75 days on the mean, and the double checks stay. The case says it tests document reading and rule checks, and a tracker shows neither; the pre-flight checker does. A reviewer expecting a reader may score a work queue as a dashboard.
- **The demonstration is a replay, not a result.** The numbers are counterfactuals on last year's data, not a measured effect.
- **My hours are guesses.** The tracker's UI is the usual place for estimates to slip; if it does, the replay and the what-if switch are what to cut first.

## What each rejected option is still good for later

- **Scan-first, original later.** The biggest single gain (4.98 days) once the audit view is in. It reuses the tracker's data model, and the original-received flag is already in the control design. First thing to build after Saturday.
- **Attendance three-way match.** The strongest runner-up and the hidden finding: manpower bills spend 8.07 days in the property check against 3.51 for the rest, up to 2.11 days on the mean. Build it next on real monthly attendance from all properties; the pack has one property and one month.
- **Pre-flight checker.** 0.57 days now and up to 1.22 once SAP exposes work-order lines, rates and open quantity. It is also the first-time-right measure the benchmarks use, and the natural phase two on the same intake the tracker feeds from. With scan-first already in place it falls to 0.48, because the courier lag it was hiding in is gone.
- **Work-order runway alert.** A cheap add-on to the tracker for procurement (about 6 hours), small in days (0.22 to 0.64) but aimed at the escalations that reach the CFO, and at the 601 orders that passed approved value.
- **Vendor portal.** Worth it for the large vendors who already use portals, as a read-only status page, and only after SAP write approval for the two-way version. At 9% preference it cannot be the main channel.
- **OCR at head office.** Useful as a component, not a product: the same reader feeds scan-first and the pre-flight checker, and posting automation waits for the SAP write project. On its own it saves at most 1.58 days.
- **The tracker as listed (status message only).** Kept inside 4b: the status message is the vendor-facing half of the same screen.
