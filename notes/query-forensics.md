# Query forensics

Source: `pack/data/queries.csv` joined to `analysis/out/bills_clean.parquet` (see `notes/data-audit.md` for the cleaning). Every figure is produced by `analysis/04_query_forensics.py` and registered in `notes/numbers.md`. Per-query detail is in `analysis/out/query_forensics.csv`; summary tables are in `analysis/out/query_forensics_summary.csv`; the classification rules are in `analysis/out/query_rules.csv`.

```
python analysis/clean.py && python analysis/02_stage_times.py && python analysis/04_query_forensics.py
```

## 1. Headlines

- **1,441 of 11,000 bills (13.1%) have a query**, not the "one in five" the CFO estimated. 1,416 are invoices (13.2%) and 25 are credit notes (9.6%).
- **A query adds about 24 days** to a bill (58.8 days invoice to paid against 34.6). Nearly all of it is the query being open (21.9 days). Across all bills that is 3.0 days on the mean.
- **Where the query sits makes no difference to how long it takes.** Median days to resolve is 16 to 18 by category and 16 to 19 by side. A missing challan is not "a week" (22 days) and a work-order query is not "a month" (17).
- **No bill has more than one query** in this file, so the serial three-query case the AP lead described cannot be seen here.
- **The fix, by the text of the query, sits with the vendor in 42.7% of cases, the property in 28.2%, procurement in 23.5% and head office in 5.6%.** Many texts leave the owner open, so each side has a range (section 5). "Mostly the vendor" holds only if every ambiguous query is given to the vendor.
- **Every query was raised at least 7 days after the bill reached the desk (mean 22.3), and about one day after a verifier picked it up.** Catching on day one is therefore always earlier. How many are catchable from the bill and SAP alone: **237 (16.4%)** from the bill and the SAP tables in the extract, **454 (31.5%)** if the bill's printed fields are read, **962 (66.8%)** if SAP exposes work-order detail the extract lacks. The data proves 138 of those 962. Even catching everything catchable would take 1.2 days off the 37.6-day mean, because the fix itself still takes about 17 days.

## 2. Share of bills with a query

| Cut | Lowest | Highest |
|---|---|---|
| Invoice month | 11.7% (Jan 2026) | 14.4% (Jul 2025) |
| Property type | 11.5% (Retail Mall) | 13.8% (Office Tower) |
| Spend category | 11.9% (Water Testing) | 15.5% (DG Set AMC) |
| Vendor MSME status | 12.3% (Small) | 13.7% (Medium) |

No segment is a hotspot. Security and housekeeping lead on volume (306 and 268 queries) only because they are the most bills. 59 queries (4.1%) were still open at 30 April 2026; all are on bills with status Query, median age 25 days, oldest 174.

## 3. How many days a query adds, and where

Paid invoices, from `stage_times.csv` (1,308 with a query, 9,141 without):

| Stage | With query | Without | Added days |
|---|---|---|---|
| Vendor to facility desk | 6.2 | 6.4 | -0.1 |
| Property check and service entry | 5.5 | 5.6 | -0.1 |
| Waiting for property head's signature | 1.5 | 1.5 | 0.0 |
| Courier to head office | 5.0 | 5.0 | 0.0 |
| Queue at central AP | 9.2 | 8.8 | +0.4 |
| AP verification, no query open | 3.3 | 1.3 | **+2.0** |
| Query open | 21.9 | 0.0 | **+21.9** |
| Waiting for payment run | 6.1 | 6.0 | +0.1 |
| **Invoice to paid** | **58.8** | **34.6** | **+24.2** |

Compared within the same spend category (weighted by queried bills) the gap is 24.0 days, so it is not a mix effect. Everything before the head-office pick is unaffected, which is expected since no query exists yet.

When a query is raised:

| From | Mean | Median | p90 | Min | Max |
|---|---|---|---|---|---|
| Desk received | 22.3 | 20 | 32 | 7 | 96 |
| Head office received | 10.2 | 9 | 18 | 1 | 86 |
| AP picked the bill | 1.0 | 1 | 2 | 0 | 2 |

So a verifier raises a query almost as soon as they open the bill, and the delay before that is queue time. After a query is resolved the bill is posted 1 to 4 days later (mean 2.3).

## 4. Days to resolve

Closed queries only (59 open are excluded and are the slowest, so these are slight underestimates). Category is `query_category`, with the 74 re-labelled "Other" queries moved to their real category (section 6).

| Category | Closed | Mean | Median | p90 |
|---|---|---|---|---|
| Duplicate bill | 122 | 20.8 | 16.5 | 42.9 |
| GL or cost centre | 200 | 22.1 | 17 | 43.0 |
| GST | 197 | 22.0 | 17 | 40.4 |
| Rate mismatch | 133 | 20.1 | 16 | 37.8 |
| Service entry or GRN not posted | 130 | 21.4 | 16 | 44.0 |
| Supporting documents | 241 | 22.6 | 17 | 49.0 |
| WO balance or validity | 321 | 22.5 | 17 | 44.0 |
| Vendor master or bill details | 19 | 25.5 | 19 | 48.2 |
| Other (no reason recorded) | 19 | 20.9 | 16 | 41.0 |
| **All** | 1,382 | 21.9 | 17 | 44.0 |

By side the medians are 17 (vendor), 16 (property), 17 (procurement) and 19 (head office). By individual issue the slowest medians are PF/ESIC challan missing (22), PO not released (22, only 12 closed) and HSN/SAC missing (20); the fastest is "original not received, only scan" (10, only 7 closed). Those small groups should not be over-read.

Against the transcripts:

| Said | Source | Data |
|---|---|---|
| "A missing challan, a week." | AP lead | PF/ESIC challan queries: median 22 days |
| "That can be a month." (work-order amendment) | AP lead | Work-order queries: median 17, p90 44, longest 154 |

Procurement's "once I have all the paper, an amendment is a week" cannot be tested: the query log ends when AP's query closes, not when the amendment is made.

## 5. More than one query on a bill

None. 1,441 queries sit on 1,441 different bills. The AP lead's December housekeeping bill had three queries, so the log either keeps one row per bill or overwrites. Serial queries (stop at the first error, raise the next one later) would add days that this data cannot show, so the 21.9 days is a floor for queried bills.

## 6. Monthly pattern

By invoice month (the cohort the bill belongs to):

| Invoice month | Bills | With query | Share |
|---|---|---|---|
| 2025-04 | 940 | 123 | 13.1% |
| 2025-05 | 979 | 118 | 12.1% |
| 2025-06 | 897 | 121 | 13.5% |
| 2025-07 | 945 | 136 | 14.4% |
| 2025-08 | 940 | 126 | 13.4% |
| 2025-09 | 908 | 112 | 12.3% |
| 2025-10 | 890 | 114 | 12.8% |
| 2025-11 | 868 | 124 | 14.3% |
| 2025-12 | 926 | 123 | 13.3% |
| 2026-01 | 921 | 108 | 11.7% |
| 2026-02 | 817 | 107 | 13.1% |
| 2026-03 | 969 | 129 | 13.3% |

By month the query was raised, and by side:

| Raised in | Queries | Vendor | Property | Procurement | Head office |
|---|---|---|---|---|---|
| 2025-04 (partial) | 34 | 18 | 5 | 9 | 2 |
| 2025-05 | 119 | 43 | 40 | 30 | 6 |
| 2025-06 | 115 | 63 | 26 | 21 | 5 |
| 2025-07 | 125 | 47 | 33 | 35 | 10 |
| 2025-08 | 133 | 51 | 38 | 32 | 12 |
| 2025-09 | 126 | 54 | 37 | 29 | 6 |
| 2025-10 | 118 | 50 | 34 | 28 | 6 |
| 2025-11 | 112 | 41 | 37 | 26 | 8 |
| 2025-12 | 123 | 51 | 40 | 24 | 8 |
| 2026-01 | 122 | 48 | 42 | 29 | 3 |
| 2026-02 | 100 | 46 | 28 | 25 | 1 |
| 2026-03 | 136 | 71 | 33 | 26 | 6 |
| 2026-04 (to 30 Apr) | 78 | 32 | 14 | 24 | 8 |

The share of bills with a query is flat all year. Counts by raised month rise at the start and fall at the end only because the register starts on 1 April and stops on 30 April. Mean days open falls in the last months (13.5 days for March invoices) because slow queries were still open; do not read it as improvement.

**No February spike.** Procurement described 11 or 12 amendment requests in four days in the second week of February. In the query log, work-order queries raised 8 to 15 February 2026 number 11, against a mean of 3.6 in any four days; the busiest four days of the year had 10 and ended on 15 January. February's total (25) is below the monthly mean (26.2). Procurement's count is of requests to procurement, so the two need not match, but AP's side shows no cluster.

## 7. Which side owns each query

**Definition.** "Side" is who has to act to close the query, read from the query text, with the category used only as a fallback (it was needed for 0 queries: all 1,441 matched exactly one text rule). It is not "who made the mistake". A property that adds guards without telling procurement shows up here as a procurement-side work-order query, because procurement has to amend the order.

**Ambiguity.** Where the text leaves the owner open I record `alt_side` and a `confidence` (653 high, 768 medium, 20 low). Ranges below use the primary assignment as the low-to-point value and add the queries where that side is the alternative owner.

| Side | Primary | Share | Only where unambiguous | If every ambiguous query went here |
|---|---|---|---|---|
| Vendor | 615 | 42.7% | 223 (15.5%) | 745 (51.7%) |
| Property | 407 | 28.2% | 311 (21.6%) | 719 (49.9%) |
| Procurement | 338 | 23.5% | 12 (0.8%) | 600 (41.6%) |
| Head office | 81 | 5.6% | 61 (4.2%) | 211 (14.6%) |

- **CFO: "the root is the vendor sending a bad bill."** Vendor is the largest single side but not a majority. Property, procurement and head office together are 826 (57.3%) on the primary assignment, and at least 384 (26.6%) on texts with no alternative owner. Vendor reaches a majority only if every ambiguous case is given to it.
- **AP lead: "a big share is our own side. Work order, GL, service entry."** Those three categories are 679 queries (47.1%).
- **Head office alone fixes 5.6%.** The 81 are WBS closed (61) and holds with no reason (20).

### The rules

Matched on `query_text` (regular expression), in `RULES` at the top of `analysis/04_query_forensics.py`. The query log uses 26 text templates (work-order numbers, tracker numbers and dates vary inside them) and there is one rule per template, so every query matched exactly one rule.

| Rule | Text contains | Side | Alternative | Confidence | n |
|---|---|---|---|---|---|
| R01 | Same invoice number already booked | vendor | head-office | medium | 130 |
| R02 | Cost centre on service entry belongs to a different property | property | - | high | 76 |
| R03 | GL on WO ... does not match the expense type | property | procurement | medium | 71 |
| R04 | WBS element closed | head-office | - | medium | 61 |
| R05 | IGST charged on an intra-state supply | vendor | - | high | 55 |
| R06 | HSN/SAC code missing | vendor | - | high | 52 |
| R07 | Tax rate on bill is ... | vendor | - | high | 52 |
| R08 | GSTIN on bill does not match vendor master | vendor | procurement | medium | 46 |
| R09 | Discussed with property team, on hold | head-office | property | low | 20 |
| R10 | Pls check WO bal before sending such bills | procurement | property | medium | 18 |
| R11 | Bill amount and SE amount not matching | property | vendor | medium | 17 |
| R12 | PO not released yet | procurement | - | high | 12 |
| R13 | Wrong company name on bill | vendor | - | high | 12 |
| R14 | Hard copy not received yet, only scan | property | vendor | medium | 8 |
| R15 | Vendor bank details changed | vendor | procurement | medium | 7 |
| R16 | Overtime billed but not approved in WO | vendor | procurement | medium | 72 |
| R17 | Rate on bill is higher than WO rate | vendor | procurement | medium | 66 |
| R18 | Service entry still parked | property | - | high | 59 |
| R19 | GRN not found in SAP | property | - | high | 57 |
| R20 | Service report for the quarter not attached | vendor | property | medium | 71 |
| R21 | Delivery challan missing security stamp | property | - | high | 68 |
| R22 | PF and ESIC challan for previous month not attached | vendor | - | high | 52 |
| R23 | Attendance sheet not signed by property head | property | - | high | 51 |
| R24 | Quantity billed exceeds open quantity on WO | procurement | vendor | medium | 105 |
| R25 | WO ... has no balance left for this period | procurement | property | medium | 96 |
| R26 | WO ... expired on (date) | procurement | property | high | 107 |

Why the medium calls went the way they did:

- **Duplicate (R01).** The vendor resubmitted, or sent the same bill to two places (33% of vendors in the survey said so). The alternative is head office: the query fires on the invoice number alone (section 8).
- **GL on the work order (R03).** The text tells the commercial team to correct it, so property. The procurement executive's account is that property filled the GL on the request form and procurement released it as given, so it is genuinely shared.
- **Rate above work order, overtime (R16, R17).** The bill carries something the order does not. The procurement executive says sometimes the vendor is wrong and sometimes the order was not amended in time. Vendor first, procurement as alternative.
- **Work-order balance and quantity (R24, R25).** Closed by an amendment, which only procurement can make, even though the cause is usually scope added at the property.
- **GSTIN (R08).** Wrong on the bill, but procurement keeps the vendor master.
- **Original not received, only scan (R14).** The original travels in the property's courier packet. This is the physical-copy hold the CFO raised: head office will not proceed without the paper. It is 8 queries.

### The "Other" texts

94 queries are categorised Other (6.5%). They contain only 7 distinct texts. I read each one and applied these rules:

| Text | n | Side (alt) | Re-labelled to | Reason |
|---|---|---|---|---|
| Discussed with property team, on hold | 20 | head-office (property) | stays Other | Records a hold, names no defect. Cannot say whose fix it is. Low confidence |
| Pls check WO bal before sending such bills | 18 | procurement (property) | WO balance or validity | Same blocker as the "no balance" queries |
| Bill amount and SE amount not matching, pls check | 17 | property (vendor) | Service entry or GRN not posted | Compares the bill with the service entry, which property creates |
| PO not released yet | 12 | procurement | WO balance or validity | No order to book against |
| Wrong company name on bill, should be the property entity | 12 | vendor | Vendor master or bill details | Bill particulars (check H2) |
| Hard copy not received yet, only scan | 8 | property (vendor) | Supporting documents | Original missing from the packet |
| Vendor bank details changed, need cancelled cheque | 7 | vendor (procurement) | Vendor master or bill details | Vendor must provide the cheque; procurement updates the master |

74 of the 94 get a real category; 20 stay Other. Of the 94, 30 are procurement-side, 25 property-side, 20 head-office-side and 19 vendor-side. For every other category the original `query_category` is consistent with the text (no text appears under two categories), so the category can be trusted there.

## 8. What could have been caught on the day the bill reached the desk

**Test.** For each query: could the condition behind it have been known when the facility desk logged the bill, using only the bill and SAP data? The "bill" includes what is printed on it (needs the reader). The service entry does not yet exist on that day; property creates it later.

| Layer | What it needs | Queries | Cumulative | Share |
|---|---|---|---|---|
| A | Bill fields and SAP tables **in the extract** (checked against the data below) | 237 | 237 | 16.4% |
| B | What is printed on the bill, plus the vendor master | 217 | 454 | 31.5% |
| C | SAP data that exists but is **not in the extract** (work-order lines, rates, open quantity and period balance, GL mapping, WBS status, bank data) | 508 | 962 | 66.8% |
| D | Other documents in the packet (attendance sheet, challans, service report) | 242 | 1,204 | 83.6% |
| E | Not knowable on day one (service entry or GRN not yet made, internal holds, original in the courier) | 237 | 1,441 | 100% |

Which texts sit where:

- **A:** duplicate invoice number (130), work order expired before bill date (107).
- **B:** IGST on an intra-state supply (55), HSN/SAC missing (52), wrong GST rate (52), GSTIN differs from master (46), wrong company name (12).
- **C:** GL (71), WBS closed (61), work-order balance, no balance and quantity (219), overtime (72), rate above order (66), PO not released (12), bank details (7).
- **D:** service report (71), gate stamp (68), PF/ESIC (52), attendance unsigned (51).
- **E:** cost centre on the service entry (76), service entry parked (59), GRN not found (57), bill vs service entry amount (17), holds (20), original not received (8).

**What the data proves for layer A** (the rule run on the bill and extract at the desk date):

- **Expired work orders: 104 of 107.** The SAP `valid_to` equals the expiry date in the query text for 104, and the invoice date is after it for those 104. For 3 the text gives an earlier date than SAP, which would fit a later extension.
- **Duplicates: 34 of 130, and weakly.** 68 of the 130 have a same-vendor same-invoice-number twin in the register, and in 34 of them that twin had reached the desk first. In 62 there is no twin at all. In none of the 68 does the twin have the same amount. So a rule on invoice number alone would raise the 34 queries, but they are probably number collisions rather than double billing (see `notes/data-audit.md`, D04).
- **Proven total for layer A: 138 queries (9.6%).**

**What the data does not support:**

- **Work-order balance and quantity (layer C, 219 queries).** The extract's value rule (cumulative invoices on the order exceed its approved value) fires on only 9 of the 219. It fires on 694 invoices overall (6.5%), about the same rate as for bills with no such query, so the extract cannot reproduce these queries. They may depend on period balances and quantities in SAP that the extract does not hold. The 962 (layer A to C) is therefore an upper bound that assumes SAP read access exposes those fields.
- **IGST (layer B, 55 queries).** The query says the supply was intra-state. In the extract the vendor and property are in different states for 39 of the 55, where IGST would be correct, and in the same state for 16. Across all bills the same-state share is 36.3%, so the queries do not track the master data. Either the vendor state is wrong in the master or these queries are wrong. The pack cannot settle which.
- **GST rate (layer B, 52 queries).** All say the bill shows 12% where 18% applies. For 45 the register shows 18%; 7 are Diesel Supply bills, which carry no GST in the register at all.
- **Everything else in layer B** needs the bill itself read, and 90% accuracy on printed bills was the IT head's figure for the earlier pilot, so some would be missed.

**Days a day-one catch would save.** Assume a caught query is fixed in the time it took in practice, running while the bill travels. Then the saving per closed query is the smaller of its open days and the days from desk to the AP pick (median 20). On the 37.6-day mean invoice-to-paid time:

| Catch layers | Queries | Mean days saved per closed query | Days off the mean |
|---|---|---|---|
| A | 237 | 14.9 | 0.28 |
| A and B | 454 | 14.9 | 0.57 |
| A to C | 962 | 14.8 | 1.22 |
| A to D | 1,204 | 14.7 | 1.53 |
| All, including layer E (a ceiling, E cannot be caught) | 1,441 | 14.7 | 1.83 |
| Proven layer A only | 138 | - | 0.17 |

The queries add 3.0 days to the mean, so catching all of them cannot save more than that. The saving is smaller than the 24 extra days a queried bill carries because the fix still takes about 17 days, and only the part that overlaps with the courier and the AP queue disappears.

## 9. Things that look wrong in the data

- IGST queries on inter-state supplies (39 of 55) and a 12% to 18% rate query on 7 zero-GST diesel bills (section 8).
- 62 of the 130 duplicate queries have no twin in the register, and 63 name a masked tracker (TRK2500xx), so the twin cannot be looked up (D05, D06 in the audit).
- 18 queries are dated after the bill's recorded payment date. All 18 are inside the D03 set of bad `paid_date` values (D13).
- The work-order balance queries are not explained by the extract (section 8). If the real SAP does explain them, the extract is incomplete for this purpose.

## 10. Limits

- **Side is a judgement from the text.** I show the ranges rather than one number; the rules are in the code and `query_rules.csv` for anyone to change.
- **Day-one catch is an estimate.** The days-saved model assumes the fix takes as long as it did, and for layer B it assumes the reader reads the bill correctly.
- **Closed queries only** for resolution times and savings (59 are open).
- **One query per bill** in the log, so repeat queries are invisible.
