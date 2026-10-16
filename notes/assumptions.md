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
