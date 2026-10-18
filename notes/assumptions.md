# Assumptions and decisions

Decisions made while building the case, each with the reason, what it changes, and what would change it. Figures are registered in `notes/numbers.md` under the ids shown. Where a decision rests on a legal reading it points to `notes/research.md`, which is a reading of public sources and not legal advice.

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
| 3 | **Runway burn is the work order's lifetime average**: value billed to date divided by the months from its start date to the extract date (or its end date if earlier), at least one month | The extract holds no period balance, open quantity or billing history by month. The adapter says so | Runway days are rough. An order that billed heavily early and slowly since looks worse than it is, and the reverse | Period balances and work-order lines over RFC (`app/sap/adapter.py`, `get_work_order`) |
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
