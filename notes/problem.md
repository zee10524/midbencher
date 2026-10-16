# The problem

Built by `analysis/08_problem_ranking.py` from the paid-invoice analysis (10,449 invoices). Every number is registered in `notes/numbers.md` (ids `p.*`, plus the figure ids they read). Rankings use measured days and the stated counterfactuals; nothing here is opinion about who is to blame.

## The biggest issue, in one sentence

**A bill is worked on for about 7 of its 38 days and waits for the rest, and the two longest waits inside our own walls are 9 days in the AP tray before anyone opens the packet and 6 days after posting for a payment run that is only 2 days away on average.**

## Solve first: two problems

1. **Posted invoices miss the next payment run** (Treasury). Bills wait 6.0 days after posting; if each were paid at the first Tuesday or Friday run the wait would be 2.3 days, and even if the run list closes two days ahead it would be 4.3. 71.0% of bills are paid at a later run than the next. That removes **1.97 to 3.72 days** from the mean, sits with head-office finance, and changes no control.
2. **Packets wait for a verifier** (central AP). The longest single wait, 8.8 days. AP-1 handles 40.4% of bills and those bills wait 4.1 days longer than the others'. Bringing them level removes **1.65 days** from the mean. It is not a headcount problem: the wait is 8.3 days when 116 bills arrive and 9.0 when 278 do, so it is how and when bills are picked up.

**Why these two.** Together they take **3.62 to 5.37 days** (9.6% to 14.3% of the mean) off the 37.6-day mean. Both sit with head-office finance (the AP lead and treasury), neither depends on vendors, property heads, the courier or an audit view, and no control is removed. The courier ties the AP queue on conservative days (1.70 against 1.65) but sits outside head office and depends on property heads and, for its best form, an audit view. Applied to the year's known Micro and Small invoices, the payment-run fix alone would have taken desk-clock late bills from 530 to 430; both fixes together to 366 (`notes/msme-exposure.md` for the clock).

## Why typing, the courier and a portal rank lower

- **Typing: ceiling 1.58 days, 4.2% of the mean.** All of AP verification, including the checks, is smaller than either first fix on its own conservative figure (1.65 and 1.97). Deleting typing outright changes nothing about the 81% of the mean that is waiting. The earlier OCR pilot is the same lesson: it fixed typing and the days did not move.
- **The courier is third, not last: 1.70 to 2.98 days.** A second weekly arrival takes the mean lag from 5.0 to 3.3 days; a daily one to 2.0. It ranks below the first two because it needs three parties (property heads, the courier arrangement, and audit if booking from a scan replaces waiting for the paper) and a cost decision, and its best form depends on an audit view not yet obtained (`notes/research.md` section 6).
- **A portal has a ceiling and no counterfactual.** The most it could touch is the vendor-to-desk delay plus vendor-side query days, 7.5 days, but the data cannot say how much it would remove, it changes no head-office wait, and it removes none of the checks that cause queries. Only 9% of surveyed vendors prefer a portal against 58% for WhatsApp; the IT head puts a bought-and-integrated portal at six to nine months, and the last write interface to SAP took seven to eight months to approve before any code (interview figures, `notes/numbers.md`). The two first fixes need no vendor adoption and no build.

## Ranking table

Days × bills is the measure for every row: days per affected bill times the share of bills affected, which is the number of days the cause adds to the 37.6-day mean. The ceiling is the whole stage or cause; "removable on evidence" is what a stated counterfactual would take off (conservative to upper), and is blank where the data holds no counterfactual.

| Rank by days × bills | Root cause | Bills affected | Days per affected bill | **Days × bills** (days on the 37.6-day mean) | Removable on evidence (days on the mean) | Rank by removable | Who can fix | Alone? | Control risk |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Packet waits in the AP tray for a verifier**<br>Head office, receipt to pick-up | 10,449 (100.0%) | 8.8 | **8.84** | 1.65 | 3 | Central AP lead | Yes | None |
| 2 | **Vendor takes days to get the bill to the desk**<br>Vendor to facility desk | 10,449 (100.0%) | 6.4 | **6.36** | no counterfactual | n/a | Vendors (the company can only influence the intake channel) | No | None |
| 3 | **Posted invoice misses the next payment run**<br>Treasury, posting to paid | 10,449 (100.0%) | 6.0 | **5.99** | 1.97 to 3.72 | 1 | Treasury, with the AP lead for the run-list cut-off | Yes | Low: payment approvals unchanged, check the release control |
| 4 | **Property checks and service entry (work, not pure waiting)**<br>Commercial executive, desk to verified | 10,449 (100.0%) | 5.6 | **5.63** | no counterfactual | n/a | Commercial executives | Yes | Controls P1 to P9 sit here |
| 5 | **Weekly courier to head office**<br>Property head to head office | 10,449 (100.0%) | 5.0 | **4.98** | 1.70 to 2.98 | 2 | Property heads, the courier arrangement, and audit if the paper stops being the booking trigger | No: three parties and a cost | Depends on the audit view of booking from a scan |
| 6 | **Queries (all causes together)**<br>Back and forth between AP, property, vendor, procurement | 1,308 (12.5%) | 21.9 | **2.75** | 0.28 to 1.22 | 4 | Split: vendor, property, procurement, head office (rows below) | No | None |
| 7 | **AP verification, including any typing**<br>Central AP, pick-up to posting (no query open) | 10,449 (100.0%) | 1.6 | **1.58** | no counterfactual | n/a | Central AP, IT for any reader | Yes | Controls H1 to H14 sit here |
| 8 | **Property head's signature**<br>Property head, verified to signed | 10,449 (100.0%) | 1.5 | **1.51** | no counterfactual | n/a | Property heads | Yes | Control P11 |

Notes on each row:

- **Packet waits in the AP tray for a verifier.** Bills handled by AP-1 (40.4%) wait 11.3 d, the other four's 7.2 d. Load is not the driver: Fridays with 116 bills average 8.3 d, Fridays with 278 bills 9.0 d.
- **Vendor takes days to get the bill to the desk.** No counterfactual in the data: the vendor's own time.
- **Posted invoice misses the next payment run.** The schedule needs 2.3 d on average but bills wait 6.0 d; 71.0% are paid after a later run than the next one. Low end assumes the run list closes 2 days before the run.
- **Property checks and service entry (work, not pure waiting).** Includes the hand matching of attendance (4 to 5 days a month, reported). No counterfactual in the data.
- **Weekly courier to head office.** Every packet arrives on a Friday; a bill signed on a Wednesday takes 2 d, on a Thursday 8 d. Low end: a second weekly arrival; high end: daily; both keep the observed 2-day minimum.
- **Queries (all causes together).** 12.5% of bills, 21.9 d each. Low end: day-one catch from the bill and SAP extract (layer A); high end: if SAP also exposes work-order lines, rates and open quantity (layers A to C).
- **AP verification, including any typing.** 4.2% of the mean. This is the ceiling for typing: verification is checking as well as keying.
- **Property head's signature.** 75% are signed within 2 days (`c.prop.sign_step_le2_pct`).

### Who can fix each

| Owner | Causes they can fix | Ceiling (days on the mean) | Removable on evidence |
|---|---|---|---|
| **Central AP lead** | Wait for a verifier; head-office-side queries (0.7% of bills); typing | 10.59 | 1.65 |
| **Treasury** | Payment-run lag | 5.99 | 1.97 to 3.72 |
| **Property heads and executives** | Courier; signature; checks and service entry; property-side queries (3.6% of bills) | 12.89 | 1.70 to 2.98 (courier only) |
| **Procurement** | Work-order balance, validity and PO queries (2.9% of bills) | 0.64 | within the query row above |
| **Vendors** | Delay to the desk; vendor-side queries (5.3% of bills) | 7.53 | not measurable |

Rows overlap with the table above (the query row is split by owner here), so the owner totals are not additive with it.

## How the numbers are built

- **Population and mean.** 10,449 paid invoices with a trustworthy payment date; mean 37.6 days from invoice date to paid (`02_stage_times.py`).
- **Days on the mean** = mean days per affected bill × share of bills affected. For the query row that is 21.9 days × 12.5% = 2.75 days (query-open days only; the full extra time on a queried bill is 24.2 days, 3.02 on the mean including extra verification).
- **Payment run.** The first Tuesday or Friday strictly after posting, plus a list lead of 0, 1 or 2 days. The conservative case uses 2. Posting dates are day-accurate at best (data-audit D15), so the result is a mean-level estimate.
- **Courier.** Reproduced exactly from the signing weekday (4.98 against the observed 4.98 days) before the second weekly arrival and the daily case were applied, both keeping the 2-day minimum lag seen in the data.
- **AP queue.** AP-1 is the verifier code with the most bills; the data does not say who that is. The comparison is its bills against the other four's mean.
- **Day-one catch** is from `notes/query-forensics.md` (layers A, then A to C), which says what each layer needs.
- **MSME check.** For known Micro and Small paid invoices, each fix's days are subtracted from the desk-to-paid time and the bills still over 45 days are recounted. Blank-status vendors are left out.

## Evidence that would change my mind

| If we found | It would change the ranking by |
|---|---|
| Treasury releases are held by approvals or limits, not by the run list (for example the maker-checker chain needs three working days) | Cutting the payment fix toward its low end or to zero; AP queue becomes first |
| Posting dates in SAP differ from the register's, so the register's posted-to-paid gap is not the real wait | Re-running the payment row on SAP posting and payment-proposal timestamps; the row could grow or vanish |
| The audit or tax adviser allows booking from the scan with the original following | Courier jumps to first or second: the whole 5.0-day wait leaves the booking path, not just 1.70 to 2.98 |
| AP time sheets show verification takes far more effort than the 1.6 elapsed days suggest (for example typing above a quarter of AP time) | Typing and a reader rank much higher; the claim now rests on elapsed time standing in for effort |
| AP says AP-1's longer wait is deliberate (complex bills or a different pick-up rule) | The queue fix shrinks to the part not explained, possibly to zero |
| SAP exposes work-order lines, rates, open quantity and period balances, and a day-one rule reproduces the 219 balance queries that the extract does not | Queries rise from 0.28 toward 1.22 days removable, and procurement's share grows |
| The amendment log shows the amendment step itself takes weeks, not the 17-day median seen for the whole query | Work-order balance becomes a top cause and procurement an owner of the first fix |
| Delivery dates show Micro and Small bills are much later than the three clocks suggest | Weighting by MSME exposure instead of by bills; payment lag and courier gain weight because they hit every Micro and Small bill |
| Vendors would adopt a portal or WhatsApp intake that cuts the vendor-to-desk time, shown by a pilot | The portal gets a counterfactual from the pilot and may move up; today it has none |
| A property head can show a second weekly courier costs little and needs no new packet work | Courier moves to the first fix: it is a 1.70-day gain on the same footing as the others |
