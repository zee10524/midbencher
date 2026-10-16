# MSME late-payment exposure

Data only, from `analysis/06_msme_exposure.py` (figure ids `e.*` and `assume.*`, `open.*` in `notes/numbers.md`). This note makes no legal finding; the legal reading and its sources are in `notes/research.md`. All amounts are rupees, shown in crore (1 crore = 10 million), for **invoices only** (credit notes excluded), bills dated 1 April 2025 to 31 March 2026, status at 30 April 2026.

```
python analysis/clean.py
python analysis/06_msme_exposure.py   # or: mingw32-make analyse
```

## 1. The clock, stated explicitly

- **Day 0 is the clock-start date. A bill is paid within 45 days if payment is 45 calendar days or fewer after day 0, and late if it is 46 or more.** Calendar days, no holiday adjustment.
- **The payment policy says the 45 days run from accepting the goods or services.** The register has no delivery or acceptance date, so three stand-ins are shown in the order they occur to a bill:

| Clock start | What the data dictionary says it is | Relation to acceptance |
|---|---|---|
| `invoice_date` | Date on the vendor's bill | Before or on the day the bill reaches the company. Not acceptance; shown as a bracket |
| `desk_received_date` | Date the facility desk logged the bill | The company has the bill, not yet accepted the work |
| `property_verified_date` | Date the commercial executive finished checks and created the service entry or GRN | The company's own record of accepting the goods or services |

**Which is more defensible?** `property_verified_date`, as the reading of the policy's word 'accepting': the service entry or GRN is where the company records that the work or goods were accepted. It is also the latest of the three, so it gives the smallest late count. If acceptance is dated earlier than the service entry, the verified-date figures are a floor and the desk-date figures sit nearer the truth; the point at which acceptance is dated is a question for the client's advisers (see `notes/research.md`). I therefore headline both and treat the verified-date result as the floor and the desk-date result as the planning number.

## 2. Paid late, by vendor status

Paid invoices with a trustworthy payment date: 10,449. Another 110 are marked Paid but their payment date is impossible (data-audit D03) and are not counted; their count is given below the tables. Medium and Not MSME vendors are shown for reference only: the 45-day figure is not their limit.

### From `property_verified_date` (nearest to 'acceptance')

| Vendor status | Paid invoices | Paid late (over 45 days) | Share late | Value late before GST (₹ crore) | Value late incl. GST (₹ crore) | Median days over the limit |
|---|---|---|---|---|---|---|
| Micro | 3,041 | 198 | 6.5% | 5.21 | 6.08 | 13 |
| Small | 2,065 | 107 | 5.2% | 3.28 | 3.83 | 12 |
| Blank (unknown) | 1,532 | 99 | 6.5% | 2.55 | 2.94 | 9 |
| Medium | 893 | 54 | 6.0% | 1.26 | 1.45 | 9.5 |
| Not MSME | 2,918 | 208 | 7.1% | 6.05 | 7.02 | 11 |
| **Micro + Small (known)** | 5,106 | **305** | 6.0% | **8.49** | **9.90** | 12 |

### From `desk_received_date`

| Vendor status | Paid invoices | Paid late (over 45 days) | Share late | Value late before GST (₹ crore) | Value late incl. GST (₹ crore) | Median days over the limit |
|---|---|---|---|---|---|---|
| Micro | 3,041 | 337 | 11.1% | 10.52 | 12.32 | 9 |
| Small | 2,065 | 193 | 9.3% | 6.31 | 7.40 | 9 |
| Blank (unknown) | 1,532 | 154 | 10.1% | 4.26 | 4.95 | 9 |
| Medium | 893 | 97 | 10.9% | 2.83 | 3.29 | 8 |
| Not MSME | 2,918 | 372 | 12.7% | 12.94 | 15.15 | 9 |
| **Micro + Small (known)** | 5,106 | **530** | 10.4% | **16.83** | **19.72** | 9 |

### From `invoice_date` (bracket)

| Vendor status | Paid invoices | Paid late (over 45 days) | Share late | Value late before GST (₹ crore) | Value late incl. GST (₹ crore) | Median days over the limit |
|---|---|---|---|---|---|---|
| Micro | 3,041 | 620 | 20.4% | 19.26 | 22.50 | 9 |
| Small | 2,065 | 411 | 19.9% | 13.25 | 15.53 | 9 |
| Blank (unknown) | 1,532 | 291 | 19.0% | 9.08 | 10.57 | 8 |
| Medium | 893 | 171 | 19.1% | 5.09 | 5.94 | 9 |
| Not MSME | 2,918 | 629 | 21.6% | 20.62 | 24.09 | 10 |
| **Micro + Small (known)** | 5,106 | **1,031** | 20.2% | **32.50** | **38.02** | 9 |

Value late is the sum of invoice amounts paid more than 45 days after the clock start. The late share is similar across the five statuses: 5.2% to 7.1% from property verified, 9.3% to 12.7% from desk received, 19.0% to 21.6% from invoice date, so Micro and Small vendors are not paid on a different footing from the rest. 74 of the unusable-date invoices belong to Micro, Small or blank-status vendors, worth ₹2.29 crore before GST.

## 3. Still unpaid and past 45 days

Two snapshots of invoices not yet paid and already past 45 days from the clock start: at 31 March 2026 (the end of the financial year the bills belong to) and at 30 April 2026 (the data cut-off). Invoices with an unusable payment date are left out.

### At 31 March 2026

| Clock | Micro | Small | Blank | Micro + Small (known): bills | Value before GST (₹ crore) | Value incl. GST (₹ crore) |
|---|---|---|---|---|---|---|
| property verified | 10 | 3 | 6 | **13** | 0.52 | 0.61 |
| desk received | 16 | 9 | 12 | **25** | 1.06 | 1.24 |
| invoice date | 22 | 17 | 13 | **39** | 1.68 | 1.95 |

### At 30 April 2026

| Clock | Micro | Small | Blank | Micro + Small (known): bills | Value before GST (₹ crore) | Value incl. GST (₹ crore) |
|---|---|---|---|---|---|---|
| property verified | 9 | 8 | 6 | **17** | 0.78 | 0.92 |
| desk received | 17 | 13 | 10 | **30** | 1.37 | 1.59 |
| invoice date | 26 | 17 | 12 | **43** | 1.79 | 2.09 |

## 4. Blank-status vendors: the assumption

137 of 900 vendors have no MSME status. Nothing in the pack says how many are Micro or Small, so three cases are shown.

- **Central: 58.2% of blank vendors are Micro or Small.** It is the share among the 763 vendors with a known status (444 Micro or Small). Why this and not another figure: MSME status in the pack is unrelated to how much a vendor bills (the Micro/Small share is 57.1% to 59.7% in every billing quartile), so there is no size signal to separate blanks from the rest; blank vendors bill a median of ₹368,800 a year against ₹450,630 for known vendors, somewhat lower but the same scale; and the share by spend category (49% to 68%) gives 80 expected Micro/Small blanks against 80 at the overall share, so category changes little.
- **Low: none are.** The known-status figures stand alone.
- **High: all are.** This is the ceiling.
- **What could move it.** The CFO and the procurement executive both said some vendors registered after they began trading with the company and the master was never updated, which would push the true share above the base rate; a vendor registered later than a bill may not count for that bill (see `notes/research.md`), which would push it below. The pack has no registration dates, so the central case is a base rate, not a finding.

Exposure under the three cases (expected values; each blank vendor is either Micro/Small or not, so these are averages over the assumption):

**Paid late, from property verified**

| Blanks treated as Micro/Small | Bills | Value before GST (₹ crore) | Value incl. GST (₹ crore) |
|---|---|---|---|
| 0% of blanks | 305 | 8.49 | 9.90 |
| 58.2% of blanks | 363 | 9.98 | 11.62 |
| 100% of blanks | 404 | 11.04 | 12.85 |

**Paid late, from desk received**

| Blanks treated as Micro/Small | Bills | Value before GST (₹ crore) | Value incl. GST (₹ crore) |
|---|---|---|---|
| 0% of blanks | 530 | 16.83 | 19.72 |
| 58.2% of blanks | 620 | 19.31 | 22.60 |
| 100% of blanks | 684 | 21.10 | 24.67 |

**Unpaid and past 45 days at 31 Mar 2026, from property verified**

| Blanks treated as Micro/Small | Bills | Value before GST (₹ crore) | Value incl. GST (₹ crore) |
|---|---|---|---|
| 0% of blanks | 13 | 0.52 | 0.61 |
| 58.2% of blanks | 16 | 0.62 | 0.72 |
| 100% of blanks | 19 | 0.69 | 0.80 |

**Unpaid and past 45 days at 31 Mar 2026, from desk received**

| Blanks treated as Micro/Small | Bills | Value before GST (₹ crore) | Value incl. GST (₹ crore) |
|---|---|---|---|
| 0% of blanks | 25 | 1.06 | 1.24 |
| 58.2% of blanks | 32 | 1.26 | 1.48 |
| 100% of blanks | 37 | 1.41 | 1.65 |

## 5. Open bills closest to breaching 45 days, as of 30 April 2026

Open invoices for Micro, Small and blank-status vendors: 119 (54 Micro, 34 Small, 31 blank). Counted from the desk date, 40 are already past 45 days (23 counted from property verification); 79 are not yet past. Of those, 43 have status Posted and can be paid; the rest are still with AP, in query or in transit and cannot be paid at the next run whatever treasury does. The next payment run is 2026-05-01 (Tuesdays and Fridays). The full list, with the ages on all three clocks, is `analysis/out/msme_open_bills.csv`.

Ranked by days left on the desk clock (the earlier deadline). 'Runs left' counts Tuesday and Friday runs from 1 May up to the deadline; 0 means no run remains before the bill passes 45 days.

| Bill | Vendor | Status of vendor | Bill status | Value incl. GST (₹) | Desk received | Days left (desk) | Deadline (desk) | Runs left | Days left (verified) |
|---|---|---|---|---|---|---|---|---|---|
| TRK257381 | V10393 | Micro | With AP | 1,219,117 | 2026-03-16 | 0 | 2026-04-30 | 0 | 15 |
| TRK257687 | V10350 | Unknown | With AP | 260,426 | 2026-03-16 | 0 | 2026-04-30 | 0 | 34 |
| TRK250695 | V10327 | Micro | Query | 941,734 | 2026-03-17 | 1 | 2026-05-01 | 1 | 10 |
| TRK253479 | V10351 | Micro | Posted | 103,930 | 2026-03-17 | 1 | 2026-05-01 | 1 | 3 |
| TRK260036 | V10459 | Small | Posted | 78,706 | 2026-03-17 | 1 | 2026-05-01 | 1 | 4 |
| TRK251891 | V10885 | Small | Posted | 15,387 | 2026-03-19 | 3 | 2026-05-03 | 1 | 8 |
| TRK252276 | V10801 | Unknown | With AP | 36,238 | 2026-03-19 | 3 | 2026-05-03 | 1 | 24 |
| TRK254854 | V10173 | Small | Query | 445,096 | 2026-03-19 | 3 | 2026-05-03 | 1 | 14 |
| TRK255575 | V10531 | Micro | With AP | 129,540 | 2026-03-19 | 3 | 2026-05-03 | 1 | 9 |
| TRK257307 | V10072 | Small | Query | 9,641 | 2026-03-19 | 3 | 2026-05-03 | 1 | 5 |
| TRK254534 | V10182 | Unknown | With AP | 23,612 | 2026-03-21 | 5 | 2026-05-05 | 2 | 7 |
| TRK257394 | V10810 | Small | Query | 7,682 | 2026-03-22 | 6 | 2026-05-06 | 2 | 9 |
| TRK258357 | V10886 | Micro | With AP | 160,291 | 2026-03-23 | 7 | 2026-05-07 | 2 | 9 |
| TRK251099 | V10221 | Small | Posted | 122,024 | 2026-03-24 | 8 | 2026-05-08 | 3 | 15 |
| TRK252747 | V10387 | Micro | Posted | 197,414 | 2026-03-24 | 8 | 2026-05-08 | 3 | 10 |
| TRK257317 | V10081 | Micro | With AP | 33,123 | 2026-03-24 | 8 | 2026-05-08 | 3 | 10 |
| TRK259810 | V10559 | Micro | With AP | 48,581 | 2026-03-24 | 8 | 2026-05-08 | 3 | 9 |
| TRK251472 | V10123 | Small | Query | 28,945 | 2026-03-25 | 9 | 2026-05-09 | 3 | 19 |
| TRK253395 | V10805 | Micro | Query | 4,637 | 2026-03-25 | 9 | 2026-05-09 | 3 | 11 |
| TRK256854 | V10300 | Micro | Posted | 9,263 | 2026-03-25 | 9 | 2026-05-09 | 3 | 14 |
| TRK258527 | V10680 | Small | Posted | 86,506 | 2026-03-25 | 9 | 2026-05-09 | 3 | 13 |
| TRK260789 | V10096 | Micro | Posted | 155,570 | 2026-03-25 | 9 | 2026-05-09 | 3 | 12 |
| TRK253038 | V10132 | Micro | Query | 10,219 | 2026-03-26 | 10 | 2026-05-10 | 3 | 11 |
| TRK254725 | V10790 | Small | Posted | 17,842 | 2026-03-26 | 10 | 2026-05-10 | 3 | 14 |
| TRK255706 | V10132 | Micro | Query | 20,107 | 2026-03-26 | 10 | 2026-05-10 | 3 | 14 |

Of the not-yet-breached bills, 2 have no payment run left before their desk-clock deadline.

## 6. What this does and does not show

- **The register has no delivery date and no payment-terms field.** The three clocks bracket the answer; they do not replace the date the policy names.
- **The blank-status share is an assumption**, not a measurement (section 4). The known-status results do not depend on it.
- **Value is invoice value.** It is not the amount of any tax or interest; it is the size of the bills involved.
- **Unusable payment dates.** 110 invoices marked Paid cannot be placed on any clock (data-audit D03).
