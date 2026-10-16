# Data audit: pack/data and sap_extract.sqlite

Every figure on this page is produced by `analysis/clean.py` and listed in `notes/numbers.md` under its id (shown in brackets where useful). Row-level detail is in `analysis/out/`.

```
python analysis/clean.py            # or: mingw32-make analyse
python analysis/register_numbers.py # refreshes notes/numbers.md
python analysis/01_profile.py       # column-by-column profile, analysis/out/profile.md
```

| Output | What it holds |
|---|---|
| `analysis/out/bills_clean.parquet` | 11,000 bills, joined to vendor, property and work order, with `f_*` flag columns |
| `analysis/out/exclusions.csv` | Every row removed from the register: source row, CSV line, bill_id, reason, the row it duplicates |
| `analysis/out/changes.csv` | Every value changed: row, column, old, new, rule |
| `analysis/out/issues.csv` | One line per check that found something |
| `analysis/out/vendor_near_duplicates.csv` | Vendor name pairs for a human to rule on |

## 1. Summary

- The register has **220 exact duplicate rows**, **683 property codes in the wrong format** and **113 payment dates that cannot be right**. Those are the three that change what we can compute. Everything else is flagged, not removed.
- Row accounting: **11,220 rows in, 220 excluded (all logged), 11,000 out.** 796 values changed (683 property codes plus 113 payment dates), all logged.
- Referential integrity is clean once property codes are fixed. Status never contradicts the dates. Several things that look like defects are not (section 5).
- Two findings are about the client's process, not the data: work orders billed past their validity or value (D08, D10), and a vendor master that is blank on MSME status for 137 vendors (D07).

## 2. What is in the data

| File / table | Rows | Notes |
|---|---|---|
| `bill_register.csv` | 11,220 [rows.bill_register] | 19 columns [bill_register.columns]. 11,000 distinct `bill_id` [bill_register.rows_after_dedup]. Blank dates after dedup: `ho_received` 4, `ho_picked` 31, `posted` 104, `paid` 185. These blanks match the five statuses exactly (section 3). |
| `vendors.csv` | 900 | Unique `vendor_id` and `gstin`. `msme_status` blank for 137 [msme.vendors_blank]. |
| `properties.csv` | 38 | 28 residential, 8 office, 2 mall. `units_or_sqft` is units for residential and square feet for the rest, so do not compare across types. |
| `work_orders.csv` | 2,092 | No blanks. Each has at least one bill. 41 to 77 orders per property, median 55 [wo.per_property_median]. |
| `queries.csv` | 1,441 | Exactly one query per queried bill. 59 open [queries.open]. |
| `attendance-sample/biometric_export.csv` | 352 | 14 guards, 28 days. |
| `attendance-sample/gate_register_transcribed.csv` | 384 | 21 reliever rows. |
| `attendance-sample/vendor_claim.csv` | 17 | 14 guards and 3 relievers. |
| sqlite `vendor_master`, `work_orders`, `properties` | 900, 2,092, 38 | **Identical, cell for cell, to the CSVs of the same name** [sap.*_csv_cells_differ = 0]. They add nothing new. |
| sqlite `posted_invoices` | 11,075 | 10,856 distinct bills. 219 rows are exact duplicates (D11). |
| sqlite `parsed_bill` | 0 | Empty by design. This is where the reader writes. |

## 3. Integrity checks that passed

| Check | Result |
|---|---|
| Bill `vendor_id` in `vendors.csv` | 0 missing |
| Bill `wo_id` in `work_orders.csv` | 0 missing |
| Bill `property_code` in `properties.csv` | 0 missing after D02 fix |
| Bill vendor equals its work order's vendor | 0 differ |
| Bill property equals its work order's property | **683 differ as typed, 0 differ after D02.** The "property differs from work order" worry is formatting, not real. |
| Bill category equals work order category and vendor category | 0 differ |
| Work order cost centre is `CC-` plus its property | 0 differ |
| Date order along the pipeline (invoice, desk, property verified, head signed, HO received, HO picked, posted) | 0 violations |
| Date order posted then paid | **113 violations (D03)** |
| Any date after 30 April 2026 | 0 |
| Posted without being picked, paid without being posted | 0 |
| `ho_verifier` set exactly when `ho_picked_date` is set | 0 exceptions |
| Status derived from dates and open queries versus recorded `status` | **0 of 11,000 contradict** |
| Open queries versus bills with status Query | 59 and 59, same bills |
| Every query's `bill_id` exists; no bill has two queries | 0 missing, 0 repeats |
| Query raised before packet reached HO, resolved before raised, raised or resolved after posting | 0, 0, 0 |
| `raised_by` equals the bill's verifier | 0 differ |
| Posted invoices vs register: vendor, invoice no, date, amount, GST, work order, posted date | 0 mismatches on the bills that are in both |
| Invoices negative or zero; credit notes positive or zero; GST sign opposite to amount | 0, 0, 0 |
| GSTIN format; duplicate GSTIN; normalised duplicate vendor name; GSTIN state prefix versus state | 0, 0, 0, 0 |
| Age of open bills at 30 April 2026 | In Transit at most 6 days since signing; With AP at most 55 since HO receipt; Query at most 188. Nothing impossibly old. |

## 4. Problems found

"Rows" counts bills (or the stated table rows) after dedup unless noted. Actions: **drop** removes the row and logs it; **fix** changes a value and logs it; **flag** keeps everything and sets a column or lists it.

| ID | Where | Problem | Rows | Action | Why |
|---|---|---|---|---|---|
| D01 | bill_register | Row identical to an earlier row in all 19 columns | 220 | **Drop** (logged in `exclusions.csv`, with the row it duplicates) | Same tracker number and same content. After dropping them, `billed_value_inr` on all 2,092 work orders equals the sum of their invoices; with them left in only 1,893 do. So they are not real bills, and keeping them would overstate spend. |
| D02 | bill_register | `property_code` not exactly as in `properties.csv`: lower case (340), space instead of hyphen (225), leading or trailing space (118); some rows have two of these | 683 | **Fix** (logged in `changes.csv`; original kept in `property_code_raw`) | Every one maps to a single property after trim, upper-case and hyphen. Unfixed, 38 properties look like 150 and 683 bills fail to join to their work order. The script stops if any code cannot be mapped. |
| D03 | bill_register | `paid_date` earlier than `posted_date` | 113 | **Flag, and blank `paid_date`** (original in `paid_date_raw`; logged) | In all 113 the payment is also before the invoice date and before the packet reached head office, and 77 fall on a day that is not a Tuesday or Friday (the payment-run days). Every other paid row, 10,702 of them, is on a Tuesday or Friday. So `paid_date` is the wrong field here, not `posted_date`. The gap to posting ranges 17 to 120 days, median 40. All have status Paid; 3 are credit notes. The other dates in the row are consistent, so the bill stays in. |
| D04 | bill_register | Same `vendor_id` and `invoice_no` on two different bills | 68 pairs (136 bills) | **Flag** (`f_dup_vendor_invoice`); keep both | No pair has the same amount; 29 pairs differ in property and 29 in work order; only 1 pair has the same invoice date. These look like invoice-number reuse, not double billing. The one same-date pair (`f_dup_vendor_invoice_same_date`, 2 bills) is the only one that deserves a person's look. No invoice number is shared across vendors, so a bare vendor-plus-invoice-number check (H13) trips on all 68 and needs amount and date to dismiss them. |
| D05 | queries | Query category is Duplicate bill but the bill has no same-vendor same-invoice twin in the register | 62 of 130 | **Flag** | The other 68 sit on the D04 pairs. For these 62 either the twin was never registered or the verifier matched on something we do not have. Cannot be resolved from the data. |
| D06 | queries | `query_text` names the earlier tracker with its last digits masked (TRK2500xx) | 63 | **Flag** | The bill it points to cannot be looked up. |
| D07 | vendors, sqlite vendor_master | `msme_status` blank | 137 vendors (15.2%); 1,620 bills (14.7%) | **Flag** (bills carry `msme_status = Unknown` and `f_msme_unknown`) | It cannot be inferred. The 45-day rule applies to Micro and Small only (256 and 188 vendors). The CFO said he could not trust the master. MSME exposure must be a range: known Micro and Small, plus an "unknown, could be" line. |
| D08 | bill_register + work_orders | Invoice dated after the work order's `valid_to` | 702 bills (6.4%) | **Flag** (`f_invoice_after_wo_expiry`) | 661 of them were paid and only 104 drew an expiry query (107 such queries exist in total). Median 79 days past expiry. Either `valid_to` in the extract is stale (amendments not reflected) or the check is applied unevenly. The data cannot say which, so `valid_to` alone should not drive a hard block. |
| D09 | work_orders | `valid_to` earlier than `valid_from` | 2 orders (12 bills) | **Flag** (`f_wo_validity_inverted`) | Dates cannot be repaired from the data. Skip these in validity checks. |
| D10 | work_orders | `billed_value_inr` above `approved_value_inr` | 601 orders (28.7%), 3,144 bills | **Flag** (`f_wo_overbilled`) | Billed is at most 1.175 times approved, median 1.082 times. This is real process signal (it is the "balance" failure the procurement executive described), not a data error. Keep it. |
| D11 | sqlite posted_invoices | Row identical to an earlier row | 219 | **Drop** in any SAP-side join (the file itself is read-only) | Mirrors D01. Deduplicate before joining or posted counts are inflated. |
| D12 | register vs sqlite | Register has a `posted_date` but `posted_invoices` has no row | 40 | **Flag** (`f_posted_not_in_sap`) | All 40 have status Paid. The SAP extract is incomplete or the register date is wrong; not resolvable here. Do not treat `posted_invoices` as the whole truth. |
| D13 | queries | `raised_date` after the bill's (raw) `paid_date` | 18 | **Flag** (`f_query_raised_after_paid`) | A query cannot follow payment. All 18 are inside D03, which is further evidence that `paid_date` is the wrong field there. |
| D14 | queries | `query_category` is Other | 94 (6.5%) | **Flag; re-label from `query_text` in the analysis, not here** | Only 7 distinct texts. They include 18 work-order-balance texts, 12 "PO not released", 17 service-entry-amount mismatches and 8 "hard copy not received, only scan". The AP lead warned about Other. No text appears under more than one category, so for the other categories `query_category` is reliable. |
| D15 | bill_register | `posted_date` on a Saturday or Sunday | 2,864 (0.263 of posted) | **Flag** (do not use for weekday analysis) | Posting dates spread over all seven days (1,451 Saturdays, 1,413 Sundays), while `ho_received_date` is always a Friday and valid `paid_date` is always a Tuesday or Friday. Trust `posted_date` to the day, not the weekday. |
| D16 | vendors | Vendor name with a repeated word (for example "Ojas Ojas Traders") | 16 | **Flag** | Cosmetic. IDs and GSTINs are unique. |
| D17 | vendors | Name similarity above 0.9 to another vendor, ignoring Pvt, Ltd and similar | 36 pairs | **Flag for review; do not merge** | No two vendors share a GSTIN or a normalised name. The pairs differ in one word (for example Ojas versus Tejas Elevator Care). 7 also share state and category; they are listed in `vendor_near_duplicates.csv`. |
| D18 | vendors | One vendor with no bills and no work orders | 1 | **Keep** | Harmless. |
| D19 | attendance-sample | Biometric `punch_out` blank | 24 | **Flag** | Forgotten punch-outs, as the commercial executive said. The day still counts as present when matching. |

Counting all flag columns, 4,839 of 11,000 bills (44.0%) carry at least one flag. Without the MSME flag, 3,863 (35.1%) do. Flags are meant to be used as filters, not as a reason to distrust the bill.

## 5. Looked like problems, are not

- **GST is zero on 1,088 rows. All of them are Diesel Supply, and no Diesel Supply row has GST.** Every other row is at 18% (rounded to two decimals); no other rate appears. Treat it as a category rule. A consequence: the register cannot show the "12 percent where it should be 18" error the AP lead mentioned. That has to come from the bill-inbox.
- **`ho_received_date` is a Friday on every row.** This is consistent with the weekly Thursday courier in the transcripts, and means a bill signed just after a pickup waits for the next one.
- **`billed_value_inr` excludes credit notes.** It equals the invoice-only sum on all 2,092 orders. Do not net credit notes against it when testing balance.
- **The 4 In Transit bills** were signed 1 to 6 days before 30 April 2026. Normal.
- **14 "With AP" bills already have a picked date.** They are mid-verification, with no open query, so status is right.
- **Invoice numbers have the format `NNN/25-26/NNN`** on every row; the first part is the vendor's number. The three-digit suffix repeats within a vendor, which is why D04 happens.

## 6. Row accounting

| Step | Rows |
|---|---|
| `bill_register.csv` | 11,220 |
| Removed as exact duplicates (D01) | 220 |
| Kept (`bills_clean.parquet`) | 11,000 |
| Values changed (D02 683, D03 113) | 796 |

The script raises an error if rows in do not equal rows out plus rows logged, if a `bill_id` is still duplicated after D01, or if a property code cannot be mapped. It never drops quietly.

## 7. Rules for the analysis that follows

1. **Days to pay** uses the cleaned `paid_date`. The 113 D03 rows are left out of payment-timing statistics (say so, with n). Their earlier stages are still valid and stay in the stage-by-stage view.
2. **MSME** exposure is reported as three groups: known Micro or Small, known Medium or Not MSME, Unknown. Never fold Unknown into "not MSME".
3. **Work orders:** use `f_invoice_after_wo_expiry` and `f_wo_overbilled` as evidence of a balance problem, but state the D08 caveat each time. Skip `f_wo_validity_inverted` rows.
4. **SAP-side joins:** deduplicate `posted_invoices` first (D11) and expect 40 gaps (D12).
5. **Query causes** come from re-labelled `query_text` (D14), not `query_category`.
6. **Duplicates:** the 220 are gone. The 68 D04 pairs stay in the counts; do not call them duplicates in the deck without the caveat above.
7. **Weekdays:** use them for `ho_received_date` and `paid_date` only (D15).

## 8. Not tested

- **Tax type** (CGST/SGST versus IGST) and **rate by line:** the register has only total GST. These need the 40 bills in the inbox.
- **Credit note to invoice link:** there is no column that ties a credit note to the invoice it reverses, so 261 credit notes cannot be matched.
- **Attendance reconciliation** (claim versus biometric versus gate register): only the structure was audited here; the matching is analysis.
- **Whether `valid_to` in the extract is stale** (D08): needs the client's amendment history from SAP.
