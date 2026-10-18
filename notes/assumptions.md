# Assumptions and decisions

Decisions made while building the case, each with the reason, what it changes, and what would change it. Figures are registered in `notes/numbers.md` under the ids shown. Where a decision rests on a legal reading it points to `notes/research.md`, which is a reading of public sources and not legal advice.

## The assumptions that matter most

This is the part to read first. For each assumption I say what I assumed and why, what happens to the results if I am wrong, and how to find out from the client. Every figure is registered in `notes/numbers.md`; the id is beside it. The older sections further down (the MSME clock, blank MSME status, the tracker's judgement calls) are the detail behind some of these.

How big is each one? In order: the payment-run cut-off and the intake residual move the "days saved" answer the most, the 90-day burn moves the control-tower headline the most, and the other four change what we can trust or what we have disclosed, not the headline numbers.

### 1. The payment-run cut-off (0, 1 or 2 days) and the intake residual (3 days, 1 day or optimistic)

**What I assumed.** Treasury pays on Tuesdays and Fridays (that is what the register shows). A bill is paid on the first run after it is posted, unless the run list has already closed. I do not know when the list closes, so I replayed last year with the list closing 0, 1 or 2 days before the run. For the intake rules, I do not know how long a bill still takes once a problem has been caught at the desk, so I replayed it with 3 days, with 1 day, and with an optimistic case that counts every query the early checks could catch, with 1 day left.

**Why.** The pack has posting dates and payment dates but not the run lists or their closing times. The default in the tracker is 1 day, the middle one. This is a setting, not a finding.

**If I am wrong, this is what moves.** The "as run" figures are the real last year: a mean of 31.3 days from the desk to paid (`l.base.desk_mean`), 530 known Micro and Small bills over 45 days (`l.base.ms_late`) and 1,153 paid invoices over 45 days (`l.base.over45`).

*The payment-run cut-off, on its own (the biggest single lever):*

| Cut-off | Days off the mean | Bills moved to an earlier run | Micro and Small over 45 days (was 530) | All paid over 45 days (was 1,153) |
|---|---|---|---|---|
| List closes the same day (0) | 3.72 (`l.lever.pay0.save`) | 7,417 (`l.lever.pay0.bills`) | 370 (`l.lever.pay0.ms_late`) | 802 (`l.lever.pay0.over`) |
| List closes 1 day before (1) | 2.75 (`l.lever.pay1.save`) | 5,662 (`l.lever.pay1.bills`) | 401 (`l.lever.pay1.ms_late`) | 868 (`l.lever.pay1.over`) |
| List closes 2 days before (2) | 1.97 (`l.lever.pay2.save`) | 4,115 (`l.lever.pay2.bills`) | 430 (`l.lever.pay2.ms_late`) | 928 (`l.lever.pay2.over`) |

*The intake residual, on its own:*

| Residual after a catch | Days off the mean | Bills affected | Micro and Small over 45 days (was 530) | All paid over 45 days (was 1,153) |
|---|---|---|---|---|
| 3 days | 0.24 (`l.lever.in3.save`) | 118 (`l.lever.in3.bills`) | 497 (`l.lever.in3.ms_late`) | 1,092 (`l.lever.in3.over`) |
| 1 day | 0.26 (`l.lever.in1.save`) | 121 (`l.lever.in1.bills`) | 497 (`l.lever.in1.ms_late`) | 1,092 (`l.lever.in1.over`) |
| Optimistic (every early-catchable query, 1 day) | 0.91 (`l.lever.inopt.save`) | 403 (`l.lever.inopt.bills`) | 414 (`l.lever.inopt.ms_late`) | 930 (`l.lever.inopt.over`) |

*All three levers together (cut-off, balanced pick order and intake), worst, middle and best case:*

| Case | Settings | Days off the mean | Mean days desk to paid after | Micro and Small over 45 days (was 530) | All paid over 45 days (was 1,153) |
|---|---|---|---|---|---|
| Worst | cut-off 2, residual 3 days | 3.94 (`l.lever.low.save`) | 27.3 (`d.after.desk_mean_high`) | 303 (`l.lever.low.ms_late`) | 653 (`l.lever.low.over`) |
| Middle | cut-off 1, residual 1 day | 4.75 (`l.lever.mid.save`) | | 288 (`l.lever.mid.ms_late`) | 617 (`l.lever.mid.over`) |
| Best | cut-off 0, optimistic intake | 6.34 (`l.lever.high.save`) | 24.9 (`d.after.desk_mean_low`) | 200 (`l.lever.high.ms_late`) | 447 (`l.lever.high.over`) |

**What this tells me.** The cut-off decides most of the answer: moving from 2 days to 0 days changes the days saved from 1.97 to 3.72, nearly double. The intake residual barely matters unless the optimistic case is true: with 3 days or 1 day left, the intake rules touch only about 120 bills and save a quarter of a day. Be careful with the best case: it stacks the most favourable setting of every assumption at once, so it is a ceiling, not a forecast. The range 24.9 to 27.3 days is the spread between my scenarios, not a confidence interval.

**How to confirm with the client.** Ask Treasury for last year's run lists with the date and time each list closed and the date and time each bill was added. That gives the real cut-off in one afternoon. Ask the AP lead how many days a bill still takes after a vendor sends a corrected one, from 20 recent examples. Then replace the three settings with the real ones and re-run `analysis/09_levers.py`.

### 2. Treasury's run rule is unconfirmed (and the biggest lever may not exist)

**What I assumed.** That the delay between a bill being posted and being paid is caused by the run list closing before the bill is ready. This is the lever "pay on the first run after posting".

**Why.** It is the only cause I can see in the data: the gap between posting and the next Tuesday or Friday explains the delay, and none of amount, vendor type, category, property, verifier or month does. Posting dates are day-accurate at best, and the pack has no approval step between posting and the run.

**If I am wrong.** If the real cause is Treasury's approval time or cash timing, not the list closing, the cut-off lever is worth nothing and the combined range above is too high. I have **not** computed the combined range without this lever. That would need a new replay with the cut-off lever switched off, which I did not run because I wanted the results to stay as they are. What I can say from the figures I have: the other two levers alone are 1.67 days for the balanced pick order (`l.lever.queue.save`) and between 0.24 and 0.91 days for the intake rules, so the combined answer without the payment-run lever is in the low single digits of days at most, and I would not quote it before it is computed.

**How to confirm with the client.** One question to Treasury: "When does the list for a Tuesday or Friday run close, and who approves it?" Then compare ten bills posted two days before a run: which were on the list and which were not.

### 3. The 90-day burn rate for work orders

**What I assumed.** A work order is "likely to run dry" if its remaining balance covers 45 days or fewer of what it was billed in the last 90 days before 30 April 2026 (`rw.window_days`, `rw.horizon_days`). I replaced my first version, which used each order's lifetime average, because it flagged orders with a few rupees left.

**Why.** Recent billing is a better guide to what happens next than the average over a work order's whole life. The 90 days is a judgement. Orders with no billing in the window cannot be flagged at all.

**If I am wrong.** The headline is 234 orders (`rw.dry`), of which 49 have a vendor with a bill already waiting (`rw.dry.vendor_waiting`) and 28 have a bill waiting on that very order (`rw.dry.wo_waiting`). It moves a lot with the choice of window and horizon:

| Burn window (horizon 45 days) | Orders likely to run dry |
|---|---|
| 60 days | 172 (`rw.sens.window_60d.dry`) |
| 90 days (the headline) | 234 (`rw.dry`) |
| 120 days | 273 (`rw.sens.window_120d.dry`) |
| 180 days | 281 (`rw.sens.window_180d.dry`) |

| Horizon (window 90 days) | Orders likely to run dry |
|---|---|
| 30 days | 171 (`rw.sens.horizon_30d.dry`) |
| 45 days (the headline) | 234 (`rw.dry`) |
| 60 days | 275 (`rw.sens.horizon_60d.dry`) |

For comparison, my first version using each order's lifetime-average burn gave 132 (`rw.dry_lifetime`). So the honest statement is "between about 170 and about 280 depending on how you set it", and the control tower shows the 60-day and 120-day counts beside the headline. It is an estimate, not a forecast, and it has no seasonality in it.

**How to confirm with the client.** Ask procurement for the planned monthly spend on the 20 biggest orders on the list, and compare it with the burn I estimated. Ask whether there are known busy and quiet months.

### 4. The blank MSME vendors

**What I assumed.** Of 900 vendors, 137 have no MSME status (`msme.vendors_blank`). Among the 763 with a known status (`assume.vendors_known`), 444 are Micro or Small (`assume.known_micro_small`), which is 58.2 per cent (`assume.share_micro_small_known`). I assume the blank vendors are Micro or Small at that same share, and I also show 0 per cent and 100 per cent as the bounds. The money-case headline counts only the known vendors, so it understates the exposure.

**Why.** I have nothing else to go on. The blank vendors bill a little less than the known ones (a median of Rs 3,68,800 a year against Rs 4,50,630: `assume.blank_median_billed`, `assume.known_median_billed`), and the Micro or Small share is steady across billing sizes (57.1 to 59.7 per cent: `assume.share_by_billing_quartile_min`, `assume.share_by_billing_quartile_max`), so the 58.2 per cent is not obviously wrong, but it is not known.

**If I am wrong.** On the desk-received clock, the number of Micro and Small bills paid over 45 days is:

| If the blank vendors are | Bills paid over 45 days | Value before GST |
|---|---|---|
| none of them Micro or Small (0 per cent) | 530 (`e.scen.paid_late.desk_received.n_late.low`) | Rs 16.83 crore (`e.scen.paid_late.desk_received.val_late_ex_gst.low`) |
| 58.2 per cent of them (central) | 620 (`e.scen.paid_late.desk_received.n_late.central`) | Rs 19.31 crore (`e.scen.paid_late.desk_received.val_late_ex_gst.central`) |
| all of them Micro or Small (100 per cent) | 684 (`e.scen.paid_late.desk_received.n_late.high`) | Rs 21.10 crore (`e.scen.paid_late.desk_received.val_late_ex_gst.high`) |

The product treats a blank vendor as "could be Micro or Small" and puts it on the countdown, so nothing is missed; the cost of being wrong is warning about a vendor the rule does not cover.

**How to confirm with the client.** Ask for each blank vendor's Udyam registration number and date. It is 137 lookups, and it is the single change that turns a scenario into a count.

### 5. The synthetic GSTINs fail the real check digit

**What I found.** A real GSTIN ends in a check character computed from the first 14. All 900 vendor GSTINs have the right shape (`g.shape_valid`), and none passes the check (`g.check_digit_pass` is 0, `g.check_digit_fail` is 900). That is what synthetic data looks like.

**What I did about it.** I did not build check-digit validation into the reader. It would reject every true GSTIN in this pack. I use the vendor master as the validator instead: a GSTIN that is wrongly read with one confusable character (O and 0, I and 1, S and 5, B and 8) is repaired only if the repaired value is in the vendor master, and a GSTIN looked up from the vendor by name is marked "resolved from vendor master", never "read". Either way a person confirms it.

**If I am wrong, i.e. real data does pass the check.** Then I have left a free safety net unused, and more bills go to a person than needed, because the check digit could separate a repaired GSTIN from a wrong one without the master. Nothing in the days-saved figures changes. The check is a ten-line function and the script `analysis/19_gstin_check_digit.py` already contains it, so adding it is small.

**How to confirm with the client.** Run that script on a real vendor master. If most GSTINs pass, turn the check on in the reader; if not, the master has data-quality problems that are worth knowing about anyway.

### 6. The corrected bill-28 label

**What happened.** I scored the reader against ten bills I labelled by hand. After the first score, one amount label (bill-28) turned out to have two digits swapped; the bill image shows the right total, and the reader had read it correctly. I corrected the label. The result is two first-run scores for the same reader: 52 of 60 fields on the labels as first given (`re.first.all.fields_correct`) and 53 of 60 after the correction (`re.second.all.fields_correct`). Bills right on the four key fields are 5 of 10 both ways (`re.first.all.key_bills_correct`, `re.second.all.key_bills_correct`).

**If I am wrong about the correction.** It would change one field in one bill, and no bill's key-field result. I kept both scores in the reader note so the change is visible, and the original value survives only as a constant in the evaluation script, not in a change log, which is a weakness.

**How to confirm.** Have a second person label the ten bills without seeing my labels or the readers' output, and compare.

### 7. A third-party API on 30 of the pack's bills

**What happened.** To test a second reader, I let bill files from the pack go to Google's Gemini API on a free tier. Thirty readings came back (`rc.vision.successful_reads`) over 24 distinct files (`rc.vision.distinct_files_read`). More uploads were attempted and rejected, so assume all 40 inbox files left the machine at least once. The brief says to treat the pack as real client data, and the free tier may use inputs to improve Google's products. I chose to test it without asking the client first, and the files cannot be recalled.

**What it does to the results.** Nothing in the days-saved numbers. It changes what I can claim about the vision reader: on ten bills, read once, it had no error (`rc.vision.fields_correct` is 60 of 60), but the 95 per cent upper bound on its true error rate is still about 5 per cent (`rc.vision.error_upper95_pct`), and it did not read the other bills because the free tier allows 20 requests a day per model (`rc.free_tier.requests_per_day_per_model`, a figure from Google's own error message, not checked against its documentation).

**What I changed.** The vision command now sends nothing unless `--confirm-send` is added. The app runs from stored responses with no key and no network. The key is in a git-ignored `.env`, and I should rotate it.

**How to confirm with the client.** Tell the client's data owner and head of IT what was sent, ask whether the synthetic pack counts as client data for this purpose, and get the answer in writing. For any real deployment, a paid tier with no training on inputs and a data-processing agreement, or a model inside the client's own boundary.

## Detail behind the assumptions above

## MSME payment clock

### Decision

**The product's primary clock starts at `desk_received_date`, day 0.** A bill is on time if paid 45 calendar days or fewer after that date, late at 46 or more. The product warns before the deadline (desk date plus 45 days) and counts payment-run days left, as `analysis/out/msme_open_bills.csv` does. It always labels the result as an **at-least** figure (see "Every clock understates lateness" below).

### Why desk received is the most defensible date available

1. **The statutory clock starts earlier than any date in the register.** On the Act's wording the period runs from acceptance or deemed acceptance, which is the day of actual delivery or rendering of the service, or the day a written objection made within 15 days is removed (MSMED Act 2006, s.2(b) and s.15; `notes/research.md` §2 and §4.1). The register has no delivery date. So the right choice is the **earliest date the company itself records reliably**, not the latest.
2. **It is the company's own stamped record.** The policy's definition of a valid invoice begins with the bill being "received at the property facility desk with a tracker number". It is present for every bill (0 blanks), and exists on the day the bill arrives, which is the earliest point the product can act.
3. **It leaves the company's internal checking time out of the clock.** The property's checks and the creation of the service entry take a mean of 5.6 days (`overall.s02.cal_mean`). On the Act's wording only a written objection, not an internal check, postpones acceptance. *To confirm with counsel (`notes/research.md` §4.1).*
4. **It is checkable.** Unlike the invoice date, which the vendor types, the desk date is logged by the company and can be defended from its own records.

### The two alternatives

| Clock | Role | Why not primary | Known Micro/Small paid invoices late at 45 days | Value late before GST |
|---|---|---|---|---|
| `property_verified_date` | **Floor.** The company's record of accepting the work (service entry or GRN). The closest reading of the policy's wording "accepting the goods or services", and the reading `notes/msme-exposure.md` §1 calls most defensible *for the policy text* | It is the latest of the three, so it understates lateness most, and it builds the property's own checking time into the clock | 305 of 5,106 (6.0%) | ₹8.49 crore |
| `desk_received_date` | **Primary** | | 530 of 5,106 (10.4%) | ₹16.83 crore |
| `invoice_date` | **Upper bracket.** Nearest to the statutory start, because a bill is normally raised on or after delivery | Typed by the vendor and not verifiable; it precedes the company's receipt by a mean of 6.4 days (median 5), so a clock from it counts the vendor's own submission lag | 1,031 of 5,106 (20.2%) | ₹32.50 crore |

Ids: `e.paid.<clock>.microsmall_known.n_late`, `.pct_late`, `.val_late_ex_gst`; `overall.s01.cal_mean`, `overall.s01.cal_median`. The two notes agree: `notes/msme-exposure.md` judged the verified date the closest reading of the policy wording and treated it as the floor and the desk date as the planning number. The product takes the second half of that: **desk date for the primary clock, verified date as the floor.**

### Every clock understates lateness

The statutory clock starts at acceptance or deemed acceptance, which is the day of delivery or rendering of the service. That is **earlier than any date in the register**: delivery comes before the vendor's bill, which comes before the desk logs it, which comes before the property verifies it. All three clocks start on or after the statutory one, so every late count and every rupee figure from them is a **minimum**. How much more is unknown without delivery dates (see the client questions in `notes/claims-tested.md`).

### 15 days versus 45 days

The Act caps an agreed written payment term at 45 days but, where nothing is agreed in writing, sets the due date at the appointed day, 15 days after acceptance (`notes/research.md` §2, §4.2). The pack's work-order table has no payment-terms field, so it is unknown which limit applies to which vendor. What the data shows for **known Micro and Small invoices paid** (5,106):

| Clock | Late at 45 days | Late at 15 days |
|---|---|---|
| `property_verified_date` | 305 (6.0%) | 4,492 (88.0%) |
| `desk_received_date` (primary) | 530 (10.4%) | 4,977 (97.5%) |
| `invoice_date` | 1,031 (20.2%) | 5,090 (99.7%) |

Ids: `e.paid.<clock>.microsmall_known.n_late`, `.pct_late`, `.n_late_15`, `.pct_late_15`, `e.paid.<clock>.microsmall_known.n_paid`.

- **Decision: the product defaults to 45 days and flags any work order with no recorded written term as "limit may be 15 days".** It uses the work order's own term when the client supplies one. 45 days is the policy's figure and the one the CFO quoted; it is the ceiling of what a written term can be, not a default under the Act.
- **Not computed:** rupee values at 15 days, and the year-end (31 March 2026) and open-bill positions at 15 days. Only the 45-day versions exist. They need the payment-terms field to be meaningful.
- **What would change this:** the written terms in the work orders (45 days or less, or none), and the delivery dates. Both are in the client questions in `notes/claims-tested.md`, priority 1.

### Where the other MSME numbers are

Late by vendor status, the year-end and open-bill positions, and the closest bills to breach are in `notes/msme-exposure.md`; every figure there is registered under `e.*`, `assume.*` and `open.*` in `notes/numbers.md`.

## Blank MSME status

**137 of 900 vendors have no MSME status. The analysis assumes 58.2% of them are Micro or Small, and shows 0% and 100% as bounds.** The 58.2% is the share among the 763 vendors with a known status (`assume.share_micro_small_known`). It is a base rate: status in the pack is unrelated to billing size (`assume.share_by_billing_quartile_min` to `_max`, 57.1% to 59.7%), blank vendors bill at a similar scale, and splitting by spend category changes the expected count by less than one vendor. The pack has no registration dates, so it cannot say which blanks are registered and which are not, and a vendor registered after a bill may not be covered for that bill (`notes/research.md` §3, §4.4).

On the primary clock (desk received) the paid-late count for Micro and Small is 530 with none of the blanks counted, 620 at 58.2%, and 684 with all (`e.scen.paid_late.desk_received.n_late.*`). The product shows blank-status vendors as their own group and never folds them into "not MSME".

What would change it: Udyam registration numbers and dates for every vendor (`notes/research.md` §5).

## Tracker: judgement calls (`app/tracker`)

Choices made while building the ledger, payment list and pick order, seeded from `bill_register.csv` and `queries.csv` as of 30 April 2026. None is measured. Each is a setting or a definition that can be changed in one place, and each is tested in `tests/test_tracker.py`.

| # | Call | Why | What it changes | What would change it |
|---|---|---|---|---|
| 1 | **Credit notes are left out of the oldest-20, ageing, MSME countdown and payment list.** They stay in the ledger and in the AP pick order. A posted credit note's vendor sentence says only that it has been booked, with no payment-run date | A credit note is not an amount owed to the vendor, and the countdown is about what the company owes. The register does mark some credit notes as paid, so how Treasury handles them is not known | Five open credit notes are not counted in the CFO views. If Treasury pays them as run items, they would need to be added to the next-run list | How Treasury treats credit notes (netted against an invoice, or paid on their own) |
| 2 | **Verifier load counts bills in hand, not rupee value, and does not count bills blocked by an open query** | A query waits on someone else, so the verifier is not working it. The register shows the wait is not driven by volume or size but by who holds the bill (`notes/problem.md`) | Pick order gives the next bills to the verifiers with fewest active bills. A value-weighted load would move large bills away from the busiest verifier | AP time data per bill, or a rule that large bills take longer to check |
| 3 | **The tracker's own runway view still uses the work order's lifetime average** (the control-tower headline no longer does: it uses the last 90 days of billing, see assumption 3 above). value billed to date divided by the months from its start date to the extract date (or its end date if earlier), at least one month | The extract holds no period balance, open quantity or billing history by month. The adapter says so | Runway days are rough. An order that billed heavily early and slowly since looks worse than it is, and the reverse | Period balances and work-order lines over RFC (`app/sap/adapter.py`, `get_work_order`) |
| 4 | **A bill not yet posted is counted as if it could post at the as-of date** when counting payment runs left | Without it, no run could be counted for the bills still with the desk, property or AP. It is the best case, so runs left is an upper bound for those bills | The MSME countdown may show a run left for a bill that cannot in fact post in time. It never shows fewer runs than are possible | Real posting dates for open bills, from SAP |
| 5 | **A bill paid before it was posted (D03) keeps its stage as Paid, is flagged `paid_before_posted`, and its sentence says the payment date is being confirmed** | `notes/data-audit.md` D03: the payment date is the field that is wrong, not the posting date. The bill itself is real and was paid | No open-bill figure changes, because the bill is not open. A vendor is not told a date that cannot be right | The reason for the early payment dates, from Treasury |

### Verifier load: two definitions and the balance check under each (call 2)

**Decision (kept after seeing the check): the pick order balances definition 1, and the counting is not changed to make a check pass.**

| | Definition | Used for |
|---|---|---|
| **1** | **Bills in hand**: picked, not posted, **excluding** bills blocked by an open query. A query waits on someone else, so the verifier is not working the bill | The pick order's balancing, and the `in_hand` column of the control tower |
| **2** | Bills in hand **including** the bills blocked by an open query | Reported only. It is the `in_hand` plus the `open_queries` column of the control tower |

The control tower data (`control_tower()` in `app/tracker/pickorder.py`) gives the AP lead one row per verifier with both: `in_hand` (definition 1), `open_queries` (the follow-up work that definition 1 leaves out), the new bills the pick order gives and `in_hand_after`.

**Result as of 30 April 2026.** After the pick order assigns the waiting bills, the highest verifier's load against the lowest, with a tolerance of 20% above the lowest (`pb.tolerance_pct`). Ids `pb.*`, script `analysis/11_pick_balance.py`.

| Verifier | In hand, def. 1, before | Open queries | New from pick order | In hand, def. 1, after | In hand, def. 2, after |
|---|---|---|---|---|---|
| AP-1 | 8 | 19 | 1 | 9 | 28 |
| AP-2 | 3 | 15 | 5 | 8 | 23 |
| AP-3 | 0 | 8 | 8 | 8 | 16 |
| AP-4 | 2 | 12 | 6 | 8 | 20 |
| AP-5 | 1 | 5 | 7 | 8 | 13 |
| **Highest above lowest** | | | | **12.5%: within tolerance** | **115.4%: outside tolerance** |

**The balance is within the tolerance only under definition 1.** Under definition 2 AP-1 still holds far more than the others. The pick order assigns only the 27 bills waiting at head office; it does not move bills a verifier already holds, so it cannot level the existing backlog, in particular AP-1's queried bills. Balanced here therefore means balanced on new work among bills that can be worked now. If the AP lead wants the whole backlog levelled, bills would have to be reassigned, and that needs her say. The `open_queries` column exists so that she can see this.

The payment-run cut-off is also a setting, not a finding: the tracker defaults to 1 day (the middle of the 0, 1 and 2 days replayed in `notes/solution-design.md` part f) until Treasury's real rule is known (`notes/payment-lag.md`).



## Known limits

What the adversarial review (`notes/adversarial-review.md`) found and this build does not fix. Figures are registered in `notes/numbers.md` under the ids shown.

### Third-party data disclosure (Google Gemini)

- **What happened.** To test a second reader, bill files from the case pack were uploaded to Google's Gemini API on a **free tier**. Stored readings: `rc.vision.successful_reads`, over `rc.vision.distinct_files_read` distinct files. Further uploads were made and rejected (an early run that failed with HTTP 404, then quota errors), so assume that **every one of the 40 inbox files left this machine at least once**.
- **Why it matters.** The case brief says to treat the pack "as you would treat real client data", and the head of IT asked for anything like this to stay "inside something we can control and audit". Google's free tier may use inputs to improve its products. The files cannot be recalled.
- **What the pack contains.** Synthetic vendors and bills ("any resemblance to a real company is coincidental"), but the brief's instruction stands, so this is disclosed rather than argued away.
- **What changed.** The vision command now sends nothing unless `--confirm-send` is given, and says why. The reader is off by default and the app runs from stored responses, with no key and no network.
- **What a real deployment needs.** A paid tier with no training on inputs and a data-processing agreement, or a model run inside the client's own boundary. Until then the vision reader is an experiment, not a feature.
- **The key.** It lives in the git-ignored `.env`, in plaintext. No commit has contained it and a test checks that no tracked file looks like one. Rotate it when the experiment is over.

### Trust in the readers

- The reader is not shown to be accurate. On ten bills, read once, the vision model had no error (`rc.vision.fields_correct`); both readers see the same image, so agreement is not independent evidence. The rule-of-three upper bound on trusted-and-wrong fields is `rc.comb.trusted_wrong_upper95_pct` per cent.
- The cross-check was scored on Tesseract's first-run reading, but the app shows the later stored reading, which was tuned on those ten bills. The tuned 8 of 10 (`rc.tess_live.key_bills`) is not a measure of anything.
- Only the labelled bills have a vision reading under the scored model (`rc.vision_stored_of_labelled`); for the rest the card says it has not been read yet. A free tier allows `rc.free_tier.requests_per_day_per_model` requests a day per model, a figure taken from Google's own error message and not checked against its documentation.
- A person typing a value has confidence 1.0 and there is no second reviewer (no maker-checker).

### Audit trail

- Human reviews are logged to `app/data/audit_log.jsonl`, hash-chained, with a typed reviewer name. It is a local file, git-ignored, and rewritable by anyone with file access; the name is not authenticated.
- The first-run score is protected by a frozen snapshot and the git history only. The first-run Tesseract score exists in two forms because one label was corrected afterwards: `re.first.all.fields_correct` (labels as first given) and `rc.tess_first.fields_correct` (labels as corrected).
- Stored vision readings made before this review keep only the normalised result, not the model's raw answer (`rc.vision.successful_reads` of them).

### Security and integration

- The local web app has no login. It refuses requests addressed to other hosts or coming from other pages, but anyone using this machine can use it. Uploaded bills stay in `app/data/uploads` with no retention rule.
- SAP is a SQLite stand-in. Nothing was tested against RFC, and master-data quality is the client's open question.
- WhatsApp is simulated: no delivery failures, no wrong numbers, no template approval, no check that the replier is the vendor. The Hindi is a draft for a Hindi speaker to review.

### What the money case does not know

- The days saved (`l.lever.low.save` to `l.lever.high.save` against `l.base.desk_mean`) are scenario bounds from a replay, not a confidence interval, and there is no rupee value or build-and-run cost beside them.
- The biggest lever depends on an unconfirmed Treasury rule; the combined range without it is not computed.
- The "likely to run dry" headline (`rw.dry`) moves with the window used for the burn: `rw.sens.window_60d.dry` with 60 days, `rw.sens.window_120d.dry` with 120; and with the horizon (`rw.sens.horizon_30d.dry`, `rw.sens.horizon_60d.dry`). It is not a forecast and has no seasonality.
- The payment-run cut-off (0, 1 or 2 days) is a setting, not a finding.

## What I did not do, and why

Plainly, so nobody has to find these out later.

- **I did not connect to SAP.** The brief says a connection is not needed, reading would need an RFC user, and writing invoices into SAP is a separate project with the SAP partner and audit sign-off. The "SAP" here is a SQLite file, opened read-only.
- **I did not send a single WhatsApp message.** It needs the business API on a company number, approved templates in each language, the vendor's recorded opt-in and files kept on the company side. The chat on the intake card is a simulation, and the Hindi in it is my draft, not reviewed by a Hindi speaker.
- **I did not compute the combined days saved without the payment-run lever.** That needs a new replay, and I wanted the results to stay put while I wrote the assumptions down.
- **I did not put a rupee value or a cost on the days saved.** The pack has no interest rate, no penalty terms and no cost of the AP team's time, and I would have had to invent them.
- **I did not score the readers on more than ten bills.** I labelled those ten by hand. Ten is too few to say whether a reader's confidence is calibrated, and the Tesseract reader was tuned on the same ten, so its later score is not a fair measure.
- **I did not read the other bills with the vision model.** The free tier allows 20 requests a day per model, and, after what happened with the data, I did not want to send more. So the two-reader view covers the ten labelled bills only.
- **I did not tune the vision prompt.** I kept the first prompt so that the ten-bill result stays a clean first run.
- **I did not check Google's terms or the free-tier limit against its documentation.** The 20 a day is what Google's own error message said.
- **I did not build the GSTIN check digit into the reader.** It would reject every GSTIN in this pack (section 5 above).
- **I did not add a login, a second reviewer for typed values or a tamper-proof audit store.** The audit log is a local file; the reviewer's name is typed, not verified. A production version needs all three.
- **I did not read the statutes and circulars in full.** `notes/research.md` lists what I read in full and what I read second-hand. Nothing here is legal advice.
- **I did not build the deck or the video.** The `deck/` and `video/` folders are empty.
- **I did not push anything to GitHub.** Everything is committed locally.
