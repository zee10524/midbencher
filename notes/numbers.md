# Numbers register

**Rule: every figure used anywhere (README, deck, video, app, notes) must be listed here with the script and command that produced it.**

Figures from `analysis/clean.py` are generated into the block below. Add hand-run figures from other scripts here:

| Figure | Value | Script | Command | Date |
|---|---|---|---|---|
| Vendors who say they do not know where their bill is | 71% | none: document figure, not computed | `pack/context/documents/vendor-survey-summary.md` | |
| Vendors who say queries come late | 48% | none: document figure | same file | |
| Vendors who say the same bill is delivered to several places | 33% | none: document figure | same file | |
| Vendors who prefer a web portal | 9% | none: document figure | same file | |
| Vendors who already use another client's portal and find it hard | 12% | none: document figure | same file | |
| Vendors who prefer WhatsApp | 58% | none: document figure | same file | |
| Vendors who prefer email | 27% | none: document figure | same file | |
| Vendors who prefer paper at the property | 6% | none: document figure | same file | |
| Vendors who would use a status update sent on WhatsApp | 64% | none: document figure | same file | |
| Survey responses | 212 of about 900 vendors | none: document figure | same file | |
| Status calls per bill, average | 3 | none: document figure | same file | |
| Calls per bill, agency owner | three or four | none: interview figure | `pack/context/transcripts/05-security-agency-owner.md` | |
| Earlier OCR pilot accuracy on main fields | about 90% | none: interview figure | `pack/context/transcripts/06-it-head.md` | |
| Bills in the inbox | 40 | none: pack fact | `pack/BRIEF.md` | |
| Portal bought and integrated with SAP | six to nine months | none: interview figure | `pack/context/transcripts/06-it-head.md` | |
| Last SAP write interface, approval before code | seven, eight months | none: interview figure | same file | |
| MSME and other payment limits | 45 days, 60 days | none: policy document | `pack/context/documents/payment-policy.md` | |
| CFO's days to pay and share queried | 45 to 50 days; 1 in 5 | none: interview figures | `pack/context/transcripts/01-cfo.md` | |
| AP lead's typing share and per-bill time | about 10%; 10 to 15 minutes | none: interview figures | `pack/context/transcripts/02-central-ap-lead.md` | |

<!-- BEGIN clean.py -->

### Figures from `analysis/clean.py` (used in notes/data-audit.md)

Script: `analysis/clean.py`. Output: `analysis/out/figures.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| rows.bill_register | 11220 | rows in bill_register.csv |
| rows.vendors | 900 | rows in vendors.csv |
| rows.properties | 38 | rows in properties.csv |
| rows.work_orders | 2092 | rows in work_orders.csv |
| rows.queries | 1441 | rows in queries.csv |
| rows.biometric_export | 352 | rows in biometric_export.csv |
| rows.gate_register_transcribed | 384 | rows in gate_register_transcribed.csv |
| rows.vendor_claim | 17 | rows in vendor_claim.csv |
| rows.sap.vendor_master | 900 | rows in sap_extract.sqlite:vendor_master |
| rows.sap.work_orders | 2092 | rows in sap_extract.sqlite:work_orders |
| rows.sap.properties | 38 | rows in sap_extract.sqlite:properties |
| rows.sap.posted_invoices | 11075 | rows in sap_extract.sqlite:posted_invoices |
| rows.sap.parsed_bill | 0 | rows in sap_extract.sqlite:parsed_bill |
| bill_register.exact_dup_rows | 220 | rows removed as exact duplicates |
| bill_register.rows_after_dedup | 11000 | rows kept |
| bill_register.bill_ids_in_dup_groups | 220 | distinct bill_ids that appeared twice |
| property_code.non_canonical_rows_raw | 694 | rows in the raw file (incl. duplicates) |
| property_code.non_canonical_rows | 683 | rows kept after dedup whose property_code was changed |
| property_code.distinct_raw | 150 | distinct property_code strings after dedup |
| property_code.lowercase | 340 |  |
| property_code.space_instead_of_hyphen | 225 |  |
| property_code.leading_or_trailing_space | 118 |  |
| property_code.distinct_clean | 38 | distinct property_code after fix (properties.csv has 38) |
| fk.vendor_missing | 0 | bills whose vendor_id is not in vendors.csv |
| fk.wo_missing | 0 | bills whose wo_id is not in work_orders.csv |
| fk.property_missing_after_fix | 0 |  |
| fk.bill_vendor_ne_wo_vendor | 0 | bills whose vendor differs from their work order's vendor |
| fk.bill_property_ne_wo_property_raw | 683 | bills whose property_code as typed differs from the work order's (formatting only) |
| fk.bill_property_ne_wo_property | 0 | bills whose property differs from the work order's after D02 fix |
| fk.bill_category_ne_wo_category | 0 |  |
| fk.bill_category_ne_vendor_category | 0 |  |
| fk.wo_costcentre_ne_property | 0 |  |
| dateorder.desk_received_date_before_invoice_date | 0 | desk_received_date earlier than invoice_date |
| dateorder.property_verified_date_before_desk_received_date | 0 | property_verified_date earlier than desk_received_date |
| dateorder.property_head_signed_date_before_property_verified_date | 0 | property_head_signed_date earlier than property_verified_date |
| dateorder.ho_received_date_before_property_head_signed_date | 0 | ho_received_date earlier than property_head_signed_date |
| dateorder.ho_picked_date_before_ho_received_date | 0 | ho_picked_date earlier than ho_received_date |
| dateorder.posted_date_before_ho_picked_date | 0 | posted_date earlier than ho_picked_date |
| dateorder.paid_date_before_posted_date | 113 | paid_date earlier than posted_date |
| nulls.bill_register.invoice_date | 0 | blank invoice_date after dedup |
| future.invoice_date | 0 | invoice_date after 30 Apr 2026 |
| nulls.bill_register.desk_received_date | 0 | blank desk_received_date after dedup |
| future.desk_received_date | 0 | desk_received_date after 30 Apr 2026 |
| nulls.bill_register.property_verified_date | 0 | blank property_verified_date after dedup |
| future.property_verified_date | 0 | property_verified_date after 30 Apr 2026 |
| nulls.bill_register.property_head_signed_date | 0 | blank property_head_signed_date after dedup |
| future.property_head_signed_date | 0 | property_head_signed_date after 30 Apr 2026 |
| nulls.bill_register.ho_received_date | 4 | blank ho_received_date after dedup |
| future.ho_received_date | 0 | ho_received_date after 30 Apr 2026 |
| nulls.bill_register.ho_picked_date | 31 | blank ho_picked_date after dedup |
| future.ho_picked_date | 0 | ho_picked_date after 30 Apr 2026 |
| nulls.bill_register.posted_date | 104 | blank posted_date after dedup |
| future.posted_date | 0 | posted_date after 30 Apr 2026 |
| nulls.bill_register.paid_date | 185 | blank paid_date after dedup |
| future.paid_date | 0 | paid_date after 30 Apr 2026 |
| nulls.bill_register.ho_verifier | 31 |  |
| dateorder.posted_without_picked | 0 |  |
| dateorder.paid_without_posted | 0 |  |
| dateorder.verifier_set_iff_picked | 0 |  |
| paid_before_posted.rows | 113 | paid_date earlier than posted_date |
| paid_before_posted.also_before_invoice_date | 113 |  |
| paid_before_posted.also_before_ho_received | 113 |  |
| paid_before_posted.status_paid | 113 |  |
| paid_before_posted.credit_notes | 3 |  |
| paid_before_posted.gap_min_days | 17 |  |
| paid_before_posted.gap_median_days | 40.0 |  |
| paid_before_posted.gap_max_days | 120 |  |
| paid.on_non_payment_day | 77 | paid_date not a Tuesday or Friday |
| paid.on_non_payment_day_within_D03 | 77 |  |
| paid.on_payment_day_when_valid | 10702 |  |
| paid.valid_rows | 10702 | paid rows whose paid_date is not in D03 |
| dup_vendor_invoice.pairs | 68 | vendor+invoice_no combinations on more than one bill |
| dup_vendor_invoice.bills | 136 |  |
| dup_vendor_invoice.max_bills_per_pair | 2 |  |
| dup_vendor_invoice.pairs_same_amount | 0 |  |
| dup_vendor_invoice.pairs_same_date | 1 |  |
| dup_vendor_invoice.pairs_same_date_and_amount | 0 |  |
| dup_vendor_invoice.pairs_diff_property | 29 |  |
| dup_vendor_invoice.pairs_diff_wo | 29 |  |
| dup_vendor_invoice.same_date_bills | 2 |  |
| dup_vendor_invoice.bills_with_any_query | 72 |  |
| invoice_no.shared_across_vendors | 0 |  |
| invoice_no.bad_format | 0 |  |
| dup_query.rows | 130 | queries categorised Duplicate bill |
| dup_query.on_flagged_pair | 68 |  |
| dup_query.not_on_any_pair | 62 | Duplicate-bill queries on a bill with no vendor+invoice_no twin in the register |
| dup_query.masked_tracker | 63 | query_text with a masked tracker like TRK2500xx |
| msme.vendors_blank | 137 | vendors with blank msme_status |
| msme.vendors_total | 900 |  |
| msme.vendors_micro | 256 |  |
| msme.vendors_small | 188 |  |
| msme.vendors_medium | 75 |  |
| msme.vendors_not_msme | 244 |  |
| msme.bills_unknown | 1620 | bills (after dedup) from vendors with blank msme_status |
| msme.bills_unknown_amount_inr | 414011276.0 |  |
| wo.bills_after_valid_to | 702 | bills dated after their work order's valid_to |
| wo.bills_after_valid_to_paid | 661 |  |
| wo.bills_before_valid_from | 0 |  |
| wo.expiry_queries | 107 | queries whose text says the work order expired |
| wo.bills_after_valid_to_with_expiry_query | 104 |  |
| wo.bills_after_valid_to_days_late_median | 79.0 |  |
| wo.valid_to_before_valid_from | 2 | work orders with valid_to earlier than valid_from |
| wo.bills_on_inverted_wo | 12 |  |
| wo.billed_gt_approved | 601 | work orders billed above approved value |
| wo.billed_gt_approved_max_ratio | 1.175 |  |
| wo.billed_gt_approved_median_ratio | 1.082 |  |
| wo.bills_on_overbilled_wo | 3144 |  |
| wo.approved_le_zero | 0 |  |
| wo.per_property_median | 55.0 |  |
| wo.per_property_max | 77 |  |
| wo.per_property_min | 41 |  |
| wo.billed_eq_invoice_sum_dedup | 2092 | work orders whose billed_value_inr equals the sum of invoices (credit notes excluded) after dedup |
| wo.billed_eq_invoice_sum_raw | 1893 | same, if the 220 duplicate rows are left in |
| wo.without_any_bill | 0 |  |
| sap.posted_invoices_exact_dup_rows | 219 | posted_invoices rows identical to an earlier row |
| sap.posted_invoices_distinct_bills | 10856 |  |
| sap.posted_not_in_register | 0 |  |
| sap.unposted_bills_in_posted_invoices | 0 |  |
| sap.register_posted_missing_from_sap | 40 | register has a posted_date, SAP posted_invoices has no row |
| sap.register_posted_missing_from_sap_status_paid | 40 |  |
| sap.register_posted_total | 10896 |  |
| sap.mismatch_vendor_id | 0 |  |
| sap.mismatch_invoice_no | 0 |  |
| sap.mismatch_wo_id | 0 |  |
| sap.mismatch_invoice_date | 0 |  |
| sap.mismatch_posted_date | 0 |  |
| sap.mismatch_amount | 0 |  |
| sap.mismatch_gst | 0 |  |
| sap.vendor_master_vs_vendors_csv_cells_differ | 0 |  |
| sap.work_orders_vs_csv_cells_differ | 0 |  |
| sap.properties_vs_csv_cells_differ | 0 |  |
| sap.parsed_bill_rows | 0 |  |
| status.contradicts_dates | 0 | status differs from status derived from dates and open queries |
| status.count.In Transit | 4 |  |
| status.count.With AP | 41 |  |
| status.count.Query | 59 |  |
| status.count.Posted | 81 |  |
| status.count.Paid | 10815 |  |
| status.in_transit_max_age_days | 6 |  |
| status.with_ap_max_age_days | 55 |  |
| status.query_max_age_days | 188 |  |
| status.with_ap_already_picked | 14 |  |
| queries.open | 59 |  |
| queries.open_not_status_query | 0 |  |
| queries.bills_with_query | 1441 |  |
| queries.bill_fk_missing | 0 |  |
| queries.bills_with_more_than_one | 0 |  |
| queries.resolved_before_raised | 0 |  |
| queries.raised_before_ho_received | 0 |  |
| queries.raised_by_ne_verifier | 0 |  |
| queries.raised_after_posted | 0 |  |
| queries.resolved_after_posted | 0 |  |
| queries.raised_after_paid | 18 |  |
| queries.raised_after_paid_within_D03 | 18 |  |
| queries.category_other | 94 | queries categorised Other |
| queries.other_distinct_texts | 7 |  |
| queries.other_wo_balance_text | 18 |  |
| queries.other_po_not_released_text | 12 |  |
| queries.other_se_amount_text | 17 |  |
| queries.other_hard_copy_text | 8 |  |
| queries.other_on_hold_text | 20 |  |
| queries.other_company_name_text | 12 |  |
| queries.other_bank_details_text | 7 |  |
| queries.templates | 26 | distinct query texts after masking numbers |
| queries.templates_in_more_than_one_category | 0 |  |
| weekday.ho_received_not_friday | 0 |  |
| weekday.posted_on_saturday | 1451 |  |
| weekday.posted_on_sunday | 1413 |  |
| weekday.posted_weekend_share | 0.263 |  |
| gst.rate_18pct_rows | 9912 |  |
| gst.rate_zero_rows | 1088 |  |
| gst.rate_zero_all_diesel | True |  |
| gst.diesel_rows_nonzero_gst | 0 |  |
| gst.rate_other_rows | 0 |  |
| amount.invoice_negative_or_zero | 0 |  |
| amount.credit_note_positive_or_zero | 0 |  |
| amount.credit_notes | 261 |  |
| amount.invoice_min | 3000.0 |  |
| amount.invoice_max | 1398460.0 |  |
| amount.credit_note_min | -452960.0 |  |
| amount.credit_note_max | -206.0 |  |
| amount.gst_sign_differs_nonzero | 0 |  |
| vendors.gstin_bad_format | 0 |  |
| vendors.gstin_duplicate | 0 |  |
| vendors.name_duplicate_normalised | 0 |  |
| vendors.gstin_state_prefix_ne_state | 0 |  |
| vendors.no_bills | 1 |  |
| vendors.no_work_orders | 1 |  |
| vendors.name_repeated_word | 16 | vendor names with a word repeated, e.g. 'Ojas Ojas Traders' |
| vendors.near_duplicate_name_pairs | 36 | pairs with name similarity above 0.9 once suffixes are removed |
| vendors.near_pairs_same_state_and_category | 7 |  |
| properties.residential | 28 |  |
| properties.office | 8 |  |
| properties.mall | 2 |  |
| attendance.biometric_blank_punch_out | 24 |  |
| attendance.biometric_guards | 14 |  |
| attendance.biometric_days | 28 |  |
| attendance.biometric_missing_guard_days | 40 |  |
| attendance.biometric_duplicate_guard_day | 0 |  |
| attendance.gate_rows | 384 |  |
| attendance.gate_rows_reliever | 21 |  |
| attendance.gate_remarks_reliever | 21 |  |
| attendance.claim_people | 17 |  |
| attendance.claim_relievers_not_in_biometric | 3 |  |
| attendance.gate_duplicate | 0 |  |
| flag.f_paid_before_posted | 113 |  |
| flag.f_dup_vendor_invoice | 136 |  |
| flag.f_dup_vendor_invoice_same_date | 2 |  |
| flag.f_msme_unknown | 1620 |  |
| flag.f_invoice_after_wo_expiry | 702 |  |
| flag.f_wo_validity_inverted | 12 |  |
| flag.f_wo_overbilled | 3144 |  |
| flag.f_posted_not_in_sap | 40 |  |
| flag.f_query_raised_after_paid | 18 |  |
| flag.bills_with_any_flag | 4839 |  |
| flag.bills_with_no_flag | 6161 |  |
| flag.excl_f_msme_unknown_bills_with_any_flag | 3863 |  |
| bill_register.columns | 19 | columns in bill_register.csv |
| msme.vendors_blank_pct | 15.2 | % of vendors with blank msme_status |
| msme.bills_unknown_pct | 14.7 | % of bills from vendors with blank msme_status |
| wo.bills_after_valid_to_pct | 6.4 | % of bills dated after WO valid_to |
| wo.billed_gt_approved_pct | 28.7 | % of work orders billed above approved value |
| queries.category_other_pct | 6.5 | % of queries categorised Other |
| weekday.posted_weekend_count | 2864 | posted_date on Saturday or Sunday |
| flag.bills_with_any_flag_pct | 44.0 |  |
| flag.bills_any_flag_excl_msme_pct | 35.1 |  |
| out.rows_in | 11220 |  |
| out.rows_excluded | 220 |  |
| out.rows_out | 11000 |  |
| out.values_changed | 796 |  |

<!-- END clean.py -->

<!-- BEGIN 02_stage_times.py -->

### Figures from `analysis/02_stage_times.py` (used in stage_times.csv, policy_compliance.csv, stage_times_chart.png. Every row of stage_times.csv and policy_compliance.csv is also a figure: same script, same command)

Script: `analysis/02_stage_times.py`. Output: `analysis/out/figures_stage_times.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
python -I analysis/02_stage_times.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| pop.bills_in_clean | 11000.0 | bills in bills_clean.parquet |
| pop.credit_notes_excluded | 261.0 | credit notes, not a payment of a bill |
| pop.invoices_unpaid_excluded | 180.0 | invoices with no paid_date: still in the pipeline |
| pop.invoices_bad_paid_date_excluded | 110.0 | invoices in D03: paid_date unusable |
| pop.invoices_analysed | 10449.0 | paid invoices with a trustworthy paid_date |
| query.clipped_to_window | 0.0 | queries that fell outside the pick..post window and were clipped |
| query.bills_with_query | 1308.0 | analysed invoices that had a query |
| overall.s01.cal_mean | 6.36 | Vendor to facility desk: cal_mean |
| overall.s01.cal_median | 5.0 | Vendor to facility desk: cal_median |
| overall.s01.cal_p90 | 12.0 | Vendor to facility desk: cal_p90 |
| overall.s01.wd_mean | 4.53 | Vendor to facility desk: wd_mean |
| overall.s01.wd_median | 4.0 | Vendor to facility desk: wd_median |
| overall.s01.wd_p90 | 9.0 | Vendor to facility desk: wd_p90 |
| overall.s01.share | 0.1689 | Vendor to facility desk: share of mean calendar days |
| overall.s02.cal_mean | 5.63 | Property check and service entry: cal_mean |
| overall.s02.cal_median | 4.0 | Property check and service entry: cal_median |
| overall.s02.cal_p90 | 11.0 | Property check and service entry: cal_p90 |
| overall.s02.wd_mean | 4.02 | Property check and service entry: wd_mean |
| overall.s02.wd_median | 3.0 | Property check and service entry: wd_median |
| overall.s02.wd_p90 | 8.0 | Property check and service entry: wd_p90 |
| overall.s02.share | 0.1495 | Property check and service entry: share of mean calendar days |
| overall.s03.cal_mean | 1.51 | Waiting for property head's signature: cal_mean |
| overall.s03.cal_median | 2.0 | Waiting for property head's signature: cal_median |
| overall.s03.cal_p90 | 3.0 | Waiting for property head's signature: cal_p90 |
| overall.s03.wd_mean | 1.08 | Waiting for property head's signature: wd_mean |
| overall.s03.wd_median | 1.0 | Waiting for property head's signature: wd_median |
| overall.s03.wd_p90 | 3.0 | Waiting for property head's signature: wd_p90 |
| overall.s03.share | 0.0402 | Waiting for property head's signature: share of mean calendar days |
| overall.s04.cal_mean | 4.98 | Courier to head office: cal_mean |
| overall.s04.cal_median | 5.0 | Courier to head office: cal_median |
| overall.s04.cal_p90 | 8.0 | Courier to head office: cal_p90 |
| overall.s04.wd_mean | 3.99 | Courier to head office: wd_mean |
| overall.s04.wd_median | 4.0 | Courier to head office: wd_median |
| overall.s04.wd_p90 | 6.0 | Courier to head office: wd_p90 |
| overall.s04.share | 0.1322 | Courier to head office: share of mean calendar days |
| overall.s05.cal_mean | 8.84 | Queue at central AP: cal_mean |
| overall.s05.cal_median | 7.0 | Queue at central AP: cal_median |
| overall.s05.cal_p90 | 16.0 | Queue at central AP: cal_p90 |
| overall.s05.wd_mean | 5.84 | Queue at central AP: wd_mean |
| overall.s05.wd_median | 5.0 | Queue at central AP: wd_median |
| overall.s05.wd_p90 | 11.0 | Queue at central AP: wd_p90 |
| overall.s05.share | 0.235 | Queue at central AP: share of mean calendar days |
| overall.s06.cal_mean | 1.58 | AP verification, no query open: cal_mean |
| overall.s06.cal_median | 1.0 | AP verification, no query open: cal_median |
| overall.s06.cal_p90 | 3.0 | AP verification, no query open: cal_p90 |
| overall.s06.wd_mean | 1.17 | AP verification, no query open: wd_mean |
| overall.s06.wd_median | 1.0 | AP verification, no query open: wd_median |
| overall.s06.wd_p90 | 2.0 | AP verification, no query open: wd_p90 |
| overall.s06.share | 0.0421 | AP verification, no query open: share of mean calendar days |
| overall.s07.cal_mean | 2.75 | Query open: cal_mean |
| overall.s07.cal_median | 0.0 | Query open: cal_median |
| overall.s07.cal_p90 | 9.0 | Query open: cal_p90 |
| overall.s07.wd_mean | 1.96 | Query open: wd_mean |
| overall.s07.wd_median | 0.0 | Query open: wd_median |
| overall.s07.wd_p90 | 6.0 | Query open: wd_p90 |
| overall.s07.share | 0.0729 | Query open: share of mean calendar days |
| overall.s08.cal_mean | 5.99 | Waiting for payment run: cal_mean |
| overall.s08.cal_median | 5.0 | Waiting for payment run: cal_median |
| overall.s08.cal_p90 | 10.0 | Waiting for payment run: cal_p90 |
| overall.s08.wd_mean | 4.22 | Waiting for payment run: wd_mean |
| overall.s08.wd_median | 4.0 | Waiting for payment run: wd_median |
| overall.s08.wd_p90 | 7.0 | Waiting for payment run: wd_p90 |
| overall.s08.share | 0.1592 | Waiting for payment run: share of mean calendar days |
| overall.s97.cal_mean | 30.43 | Total waiting: cal_mean |
| overall.s97.cal_median | 27.0 | Total waiting: cal_median |
| overall.s97.cal_p90 | 46.0 | Total waiting: cal_p90 |
| overall.s97.wd_mean | 21.63 | Total waiting: wd_mean |
| overall.s97.wd_median | 20.0 | Total waiting: wd_median |
| overall.s97.wd_p90 | 33.0 | Total waiting: wd_p90 |
| overall.s97.share | 0.8085 | Total waiting: share of mean calendar days |
| overall.s98.cal_mean | 7.21 | Total worked: cal_mean |
| overall.s98.cal_median | 6.0 | Total worked: cal_median |
| overall.s98.cal_p90 | 13.0 | Total worked: cal_p90 |
| overall.s98.wd_mean | 5.19 | Total worked: wd_mean |
| overall.s98.wd_median | 5.0 | Total worked: wd_median |
| overall.s98.wd_p90 | 9.0 | Total worked: wd_p90 |
| overall.s98.share | 0.1915 | Total worked: share of mean calendar days |
| overall.s99.cal_mean | 37.64 | Total invoice to paid: cal_mean |
| overall.s99.cal_median | 35.0 | Total invoice to paid: cal_median |
| overall.s99.cal_p90 | 54.0 | Total invoice to paid: cal_p90 |
| overall.s99.wd_mean | 26.82 | Total invoice to paid: wd_mean |
| overall.s99.wd_median | 25.0 | Total invoice to paid: wd_median |
| overall.s99.wd_p90 | 39.0 | Total invoice to paid: wd_p90 |
| overall.s99.share | 1.0 | Total invoice to paid: share of mean calendar days |
| side.1.cal_mean | 6.36 | mean calendar days with: Vendor (to the desk) |
| side.1.share | 0.1689 | share of mean total with: Vendor (to the desk) |
| side.2.cal_mean | 7.14 | mean calendar days with: Property (check, signature) |
| side.2.share | 0.1897 | share of mean total with: Property (check, signature) |
| side.4.cal_mean | 4.98 | mean calendar days with: Courier |
| side.4.share | 0.1322 | share of mean total with: Courier |
| side.5.cal_mean | 13.17 | mean calendar days with: Central AP (queue, verify, query) |
| side.5.share | 0.35 | share of mean total with: Central AP (queue, verify, query) |
| side.8.cal_mean | 5.99 | mean calendar days with: Treasury (payment run) |
| side.8.share | 0.1592 | share of mean total with: Treasury (payment run) |
| query.mean_days_among_queried | 21.93 | mean calendar days a query was open, on bills that had one |
| query.share_of_bills | 0.1252 | share of analysed invoices that had a query |
| policy.micro.invoice.n_paid | 5106.0 | Micro or Small, clock from invoice_date: n_paid |
| policy.micro.invoice.mean | 37.48 | Micro or Small, clock from invoice_date: mean |
| policy.micro.invoice.median | 34.0 | Micro or Small, clock from invoice_date: median |
| policy.micro.invoice.p90 | 54.0 | Micro or Small, clock from invoice_date: p90 |
| policy.micro.invoice.pct_over_45 | 20.19 | Micro or Small, clock from invoice_date: pct_over_45 |
| policy.micro.invoice.pct_over_60 | 6.15 | Micro or Small, clock from invoice_date: pct_over_60 |
| policy.micro.invoice.pct_in_cfo_band_45_to_50 | 8.56 | Micro or Small, clock from invoice_date: pct_in_cfo_band_45_to_50 |
| policy.micro.invoice.n_unpaid | 88.0 | Micro or Small, clock from invoice_date: n_unpaid |
| policy.micro.invoice.n_unpaid_already_over_45 | 43.0 | Micro or Small, clock from invoice_date: n_unpaid_already_over_45 |
| policy.micro.invoice.n_unpaid_already_over_60 | 9.0 | Micro or Small, clock from invoice_date: n_unpaid_already_over_60 |
| policy.micro.desk_received.n_paid | 5106.0 | Micro or Small, clock from desk_received_date: n_paid |
| policy.micro.desk_received.mean | 31.06 | Micro or Small, clock from desk_received_date: mean |
| policy.micro.desk_received.median | 28.0 | Micro or Small, clock from desk_received_date: median |
| policy.micro.desk_received.p90 | 46.0 | Micro or Small, clock from desk_received_date: p90 |
| policy.micro.desk_received.pct_over_45 | 10.38 | Micro or Small, clock from desk_received_date: pct_over_45 |
| policy.micro.desk_received.pct_over_60 | 3.41 | Micro or Small, clock from desk_received_date: pct_over_60 |
| policy.micro.desk_received.pct_in_cfo_band_45_to_50 | 4.43 | Micro or Small, clock from desk_received_date: pct_in_cfo_band_45_to_50 |
| policy.micro.desk_received.n_unpaid | 88.0 | Micro or Small, clock from desk_received_date: n_unpaid |
| policy.micro.desk_received.n_unpaid_already_over_45 | 30.0 | Micro or Small, clock from desk_received_date: n_unpaid_already_over_45 |
| policy.micro.desk_received.n_unpaid_already_over_60 | 8.0 | Micro or Small, clock from desk_received_date: n_unpaid_already_over_60 |
| policy.micro.property_verified.n_paid | 5106.0 | Micro or Small, clock from property_verified_date: n_paid |
| policy.micro.property_verified.mean | 25.3 | Micro or Small, clock from property_verified_date: mean |
| policy.micro.property_verified.median | 22.0 | Micro or Small, clock from property_verified_date: median |
| policy.micro.property_verified.p90 | 39.0 | Micro or Small, clock from property_verified_date: p90 |
| policy.micro.property_verified.pct_over_45 | 5.97 | Micro or Small, clock from property_verified_date: pct_over_45 |
| policy.micro.property_verified.pct_over_60 | 2.47 | Micro or Small, clock from property_verified_date: pct_over_60 |
| policy.micro.property_verified.pct_in_cfo_band_45_to_50 | 2.21 | Micro or Small, clock from property_verified_date: pct_in_cfo_band_45_to_50 |
| policy.micro.property_verified.n_unpaid | 88.0 | Micro or Small, clock from property_verified_date: n_unpaid |
| policy.micro.property_verified.n_unpaid_already_over_45 | 17.0 | Micro or Small, clock from property_verified_date: n_unpaid_already_over_45 |
| policy.micro.property_verified.n_unpaid_already_over_60 | 7.0 | Micro or Small, clock from property_verified_date: n_unpaid_already_over_60 |
| policy.medium.invoice.n_paid | 3811.0 | Medium or Not MSME, clock from invoice_date: n_paid |
| policy.medium.invoice.mean | 38.05 | Medium or Not MSME, clock from invoice_date: mean |
| policy.medium.invoice.median | 35.0 | Medium or Not MSME, clock from invoice_date: median |
| policy.medium.invoice.p90 | 56.0 | Medium or Not MSME, clock from invoice_date: p90 |
| policy.medium.invoice.pct_over_45 | 20.99 | Medium or Not MSME, clock from invoice_date: pct_over_45 |
| policy.medium.invoice.pct_over_60 | 6.9 | Medium or Not MSME, clock from invoice_date: pct_over_60 |
| policy.medium.invoice.pct_in_cfo_band_45_to_50 | 8.4 | Medium or Not MSME, clock from invoice_date: pct_in_cfo_band_45_to_50 |
| policy.medium.invoice.n_unpaid | 61.0 | Medium or Not MSME, clock from invoice_date: n_unpaid |
| policy.medium.invoice.n_unpaid_already_over_45 | 30.0 | Medium or Not MSME, clock from invoice_date: n_unpaid_already_over_45 |
| policy.medium.invoice.n_unpaid_already_over_60 | 8.0 | Medium or Not MSME, clock from invoice_date: n_unpaid_already_over_60 |
| policy.medium.desk_received.n_paid | 3811.0 | Medium or Not MSME, clock from desk_received_date: n_paid |
| policy.medium.desk_received.mean | 31.69 | Medium or Not MSME, clock from desk_received_date: mean |
| policy.medium.desk_received.median | 28.0 | Medium or Not MSME, clock from desk_received_date: median |
| policy.medium.desk_received.p90 | 48.0 | Medium or Not MSME, clock from desk_received_date: p90 |
| policy.medium.desk_received.pct_over_45 | 12.31 | Medium or Not MSME, clock from desk_received_date: pct_over_45 |
| policy.medium.desk_received.pct_over_60 | 3.8 | Medium or Not MSME, clock from desk_received_date: pct_over_60 |
| policy.medium.desk_received.pct_in_cfo_band_45_to_50 | 5.12 | Medium or Not MSME, clock from desk_received_date: pct_in_cfo_band_45_to_50 |
| policy.medium.desk_received.n_unpaid | 61.0 | Medium or Not MSME, clock from desk_received_date: n_unpaid |
| policy.medium.desk_received.n_unpaid_already_over_45 | 19.0 | Medium or Not MSME, clock from desk_received_date: n_unpaid_already_over_45 |
| policy.medium.desk_received.n_unpaid_already_over_60 | 6.0 | Medium or Not MSME, clock from desk_received_date: n_unpaid_already_over_60 |
| policy.medium.property_verified.n_paid | 3811.0 | Medium or Not MSME, clock from property_verified_date: n_paid |
| policy.medium.property_verified.mean | 26.16 | Medium or Not MSME, clock from property_verified_date: mean |
| policy.medium.property_verified.median | 23.0 | Medium or Not MSME, clock from property_verified_date: median |
| policy.medium.property_verified.p90 | 41.0 | Medium or Not MSME, clock from property_verified_date: p90 |
| policy.medium.property_verified.pct_over_45 | 6.87 | Medium or Not MSME, clock from property_verified_date: pct_over_45 |
| policy.medium.property_verified.pct_over_60 | 2.57 | Medium or Not MSME, clock from property_verified_date: pct_over_60 |
| policy.medium.property_verified.pct_in_cfo_band_45_to_50 | 2.65 | Medium or Not MSME, clock from property_verified_date: pct_in_cfo_band_45_to_50 |
| policy.medium.property_verified.n_unpaid | 61.0 | Medium or Not MSME, clock from property_verified_date: n_unpaid |
| policy.medium.property_verified.n_unpaid_already_over_45 | 11.0 | Medium or Not MSME, clock from property_verified_date: n_unpaid_already_over_45 |
| policy.medium.property_verified.n_unpaid_already_over_60 | 4.0 | Medium or Not MSME, clock from property_verified_date: n_unpaid_already_over_60 |
| policy.unknown.invoice.n_paid | 1532.0 | Unknown, clock from invoice_date: n_paid |
| policy.unknown.invoice.mean | 37.15 | Unknown, clock from invoice_date: mean |
| policy.unknown.invoice.median | 34.0 | Unknown, clock from invoice_date: median |
| policy.unknown.invoice.p90 | 53.0 | Unknown, clock from invoice_date: p90 |
| policy.unknown.invoice.pct_over_45 | 18.99 | Unknown, clock from invoice_date: pct_over_45 |
| policy.unknown.invoice.pct_over_60 | 5.87 | Unknown, clock from invoice_date: pct_over_60 |
| policy.unknown.invoice.pct_in_cfo_band_45_to_50 | 9.27 | Unknown, clock from invoice_date: pct_in_cfo_band_45_to_50 |
| policy.unknown.invoice.n_unpaid | 31.0 | Unknown, clock from invoice_date: n_unpaid |
| policy.unknown.invoice.n_unpaid_already_over_45 | 12.0 | Unknown, clock from invoice_date: n_unpaid_already_over_45 |
| policy.unknown.invoice.n_unpaid_already_over_60 | 5.0 | Unknown, clock from invoice_date: n_unpaid_already_over_60 |
| policy.unknown.desk_received.n_paid | 1532.0 | Unknown, clock from desk_received_date: n_paid |
| policy.unknown.desk_received.mean | 31.04 | Unknown, clock from desk_received_date: mean |
| policy.unknown.desk_received.median | 28.0 | Unknown, clock from desk_received_date: median |
| policy.unknown.desk_received.p90 | 45.9 | Unknown, clock from desk_received_date: p90 |
| policy.unknown.desk_received.pct_over_45 | 10.05 | Unknown, clock from desk_received_date: pct_over_45 |
| policy.unknown.desk_received.pct_over_60 | 3.39 | Unknown, clock from desk_received_date: pct_over_60 |
| policy.unknown.desk_received.pct_in_cfo_band_45_to_50 | 3.66 | Unknown, clock from desk_received_date: pct_in_cfo_band_45_to_50 |
| policy.unknown.desk_received.n_unpaid | 31.0 | Unknown, clock from desk_received_date: n_unpaid |
| policy.unknown.desk_received.n_unpaid_already_over_45 | 10.0 | Unknown, clock from desk_received_date: n_unpaid_already_over_45 |
| policy.unknown.desk_received.n_unpaid_already_over_60 | 4.0 | Unknown, clock from desk_received_date: n_unpaid_already_over_60 |
| policy.unknown.property_verified.n_paid | 1532.0 | Unknown, clock from property_verified_date: n_paid |
| policy.unknown.property_verified.mean | 25.61 | Unknown, clock from property_verified_date: mean |
| policy.unknown.property_verified.median | 22.0 | Unknown, clock from property_verified_date: median |
| policy.unknown.property_verified.p90 | 39.0 | Unknown, clock from property_verified_date: p90 |
| policy.unknown.property_verified.pct_over_45 | 6.46 | Unknown, clock from property_verified_date: pct_over_45 |
| policy.unknown.property_verified.pct_over_60 | 2.28 | Unknown, clock from property_verified_date: pct_over_60 |
| policy.unknown.property_verified.pct_in_cfo_band_45_to_50 | 2.81 | Unknown, clock from property_verified_date: pct_in_cfo_band_45_to_50 |
| policy.unknown.property_verified.n_unpaid | 31.0 | Unknown, clock from property_verified_date: n_unpaid |
| policy.unknown.property_verified.n_unpaid_already_over_45 | 6.0 | Unknown, clock from property_verified_date: n_unpaid_already_over_45 |
| policy.unknown.property_verified.n_unpaid_already_over_60 | 4.0 | Unknown, clock from property_verified_date: n_unpaid_already_over_60 |
| policy.all.invoice.n_paid | 10449.0 | All, clock from invoice_date: n_paid |
| policy.all.invoice.mean | 37.64 | All, clock from invoice_date: mean |
| policy.all.invoice.median | 35.0 | All, clock from invoice_date: median |
| policy.all.invoice.p90 | 54.0 | All, clock from invoice_date: p90 |
| policy.all.invoice.pct_over_45 | 20.31 | All, clock from invoice_date: pct_over_45 |
| policy.all.invoice.pct_over_60 | 6.38 | All, clock from invoice_date: pct_over_60 |
| policy.all.invoice.pct_in_cfo_band_45_to_50 | 8.6 | All, clock from invoice_date: pct_in_cfo_band_45_to_50 |
| policy.all.invoice.n_unpaid | 180.0 | All, clock from invoice_date: n_unpaid |
| policy.all.invoice.n_unpaid_already_over_45 | 85.0 | All, clock from invoice_date: n_unpaid_already_over_45 |
| policy.all.invoice.n_unpaid_already_over_60 | 22.0 | All, clock from invoice_date: n_unpaid_already_over_60 |
| policy.all.desk_received.n_paid | 10449.0 | All, clock from desk_received_date: n_paid |
| policy.all.desk_received.mean | 31.28 | All, clock from desk_received_date: mean |
| policy.all.desk_received.median | 28.0 | All, clock from desk_received_date: median |
| policy.all.desk_received.p90 | 47.0 | All, clock from desk_received_date: p90 |
| policy.all.desk_received.pct_over_45 | 11.03 | All, clock from desk_received_date: pct_over_45 |
| policy.all.desk_received.pct_over_60 | 3.55 | All, clock from desk_received_date: pct_over_60 |
| policy.all.desk_received.pct_in_cfo_band_45_to_50 | 4.57 | All, clock from desk_received_date: pct_in_cfo_band_45_to_50 |
| policy.all.desk_received.n_unpaid | 180.0 | All, clock from desk_received_date: n_unpaid |
| policy.all.desk_received.n_unpaid_already_over_45 | 59.0 | All, clock from desk_received_date: n_unpaid_already_over_45 |
| policy.all.desk_received.n_unpaid_already_over_60 | 18.0 | All, clock from desk_received_date: n_unpaid_already_over_60 |
| policy.all.property_verified.n_paid | 10449.0 | All, clock from property_verified_date: n_paid |
| policy.all.property_verified.mean | 25.66 | All, clock from property_verified_date: mean |
| policy.all.property_verified.median | 22.0 | All, clock from property_verified_date: median |
| policy.all.property_verified.p90 | 40.0 | All, clock from property_verified_date: p90 |
| policy.all.property_verified.pct_over_45 | 6.37 | All, clock from property_verified_date: pct_over_45 |
| policy.all.property_verified.pct_over_60 | 2.48 | All, clock from property_verified_date: pct_over_60 |
| policy.all.property_verified.pct_in_cfo_band_45_to_50 | 2.46 | All, clock from property_verified_date: pct_in_cfo_band_45_to_50 |
| policy.all.property_verified.n_unpaid | 180.0 | All, clock from property_verified_date: n_unpaid |
| policy.all.property_verified.n_unpaid_already_over_45 | 34.0 | All, clock from property_verified_date: n_unpaid_already_over_45 |
| policy.all.property_verified.n_unpaid_already_over_60 | 15.0 | All, clock from property_verified_date: n_unpaid_already_over_60 |
| policy.matured.invoice.n_paid | 8888.0 | All, invoiced to 31 Jan 2026, clock from invoice_date: n_paid |
| policy.matured.invoice.mean | 38.13 | All, invoiced to 31 Jan 2026, clock from invoice_date: mean |
| policy.matured.invoice.median | 35.0 | All, invoiced to 31 Jan 2026, clock from invoice_date: median |
| policy.matured.invoice.p90 | 56.0 | All, invoiced to 31 Jan 2026, clock from invoice_date: p90 |
| policy.matured.invoice.pct_over_45 | 21.3 | All, invoiced to 31 Jan 2026, clock from invoice_date: pct_over_45 |
| policy.matured.invoice.pct_over_60 | 7.08 | All, invoiced to 31 Jan 2026, clock from invoice_date: pct_over_60 |
| policy.matured.invoice.pct_in_cfo_band_45_to_50 | 8.8 | All, invoiced to 31 Jan 2026, clock from invoice_date: pct_in_cfo_band_45_to_50 |
| policy.matured.invoice.n_unpaid | 5.0 | All, invoiced to 31 Jan 2026, clock from invoice_date: n_unpaid |
| policy.matured.invoice.n_unpaid_already_over_45 | 5.0 | All, invoiced to 31 Jan 2026, clock from invoice_date: n_unpaid_already_over_45 |
| policy.matured.invoice.n_unpaid_already_over_60 | 5.0 | All, invoiced to 31 Jan 2026, clock from invoice_date: n_unpaid_already_over_60 |
| policy.matured.desk_received.n_paid | 8888.0 | All, invoiced to 31 Jan 2026, clock from desk_received_date: n_paid |
| policy.matured.desk_received.mean | 31.7 | All, invoiced to 31 Jan 2026, clock from desk_received_date: mean |
| policy.matured.desk_received.median | 28.0 | All, invoiced to 31 Jan 2026, clock from desk_received_date: median |
| policy.matured.desk_received.p90 | 48.0 | All, invoiced to 31 Jan 2026, clock from desk_received_date: p90 |
| policy.matured.desk_received.pct_over_45 | 11.81 | All, invoiced to 31 Jan 2026, clock from desk_received_date: pct_over_45 |
| policy.matured.desk_received.pct_over_60 | 3.98 | All, invoiced to 31 Jan 2026, clock from desk_received_date: pct_over_60 |
| policy.matured.desk_received.pct_in_cfo_band_45_to_50 | 4.7 | All, invoiced to 31 Jan 2026, clock from desk_received_date: pct_in_cfo_band_45_to_50 |
| policy.matured.desk_received.n_unpaid | 5.0 | All, invoiced to 31 Jan 2026, clock from desk_received_date: n_unpaid |
| policy.matured.desk_received.n_unpaid_already_over_45 | 5.0 | All, invoiced to 31 Jan 2026, clock from desk_received_date: n_unpaid_already_over_45 |
| policy.matured.desk_received.n_unpaid_already_over_60 | 5.0 | All, invoiced to 31 Jan 2026, clock from desk_received_date: n_unpaid_already_over_60 |
| policy.matured.property_verified.n_paid | 8888.0 | All, invoiced to 31 Jan 2026, clock from property_verified_date: n_paid |
| policy.matured.property_verified.mean | 26.03 | All, invoiced to 31 Jan 2026, clock from property_verified_date: mean |
| policy.matured.property_verified.median | 23.0 | All, invoiced to 31 Jan 2026, clock from property_verified_date: median |
| policy.matured.property_verified.p90 | 41.0 | All, invoiced to 31 Jan 2026, clock from property_verified_date: p90 |
| policy.matured.property_verified.pct_over_45 | 7.07 | All, invoiced to 31 Jan 2026, clock from property_verified_date: pct_over_45 |
| policy.matured.property_verified.pct_over_60 | 2.81 | All, invoiced to 31 Jan 2026, clock from property_verified_date: pct_over_60 |
| policy.matured.property_verified.pct_in_cfo_band_45_to_50 | 2.72 | All, invoiced to 31 Jan 2026, clock from property_verified_date: pct_in_cfo_band_45_to_50 |
| policy.matured.property_verified.n_unpaid | 5.0 | All, invoiced to 31 Jan 2026, clock from property_verified_date: n_unpaid |
| policy.matured.property_verified.n_unpaid_already_over_45 | 5.0 | All, invoiced to 31 Jan 2026, clock from property_verified_date: n_unpaid_already_over_45 |
| policy.matured.property_verified.n_unpaid_already_over_60 | 5.0 | All, invoiced to 31 Jan 2026, clock from property_verified_date: n_unpaid_already_over_60 |

<!-- END 02_stage_times.py -->

<!-- BEGIN 04_query_forensics.py -->

### Figures from `analysis/04_query_forensics.py` (used in notes/query-forensics.md, query_forensics.csv. Every row of query_forensics.csv, query_forensics_summary.csv and query_rules.csv is also a figure: same script, same command)

Script: `analysis/04_query_forensics.py`. Output: `analysis/out/figures_query_forensics.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
python -I analysis/02_stage_times.py
python -I analysis/04_query_forensics.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| q.rows | 1441 | rows in queries.csv |
| rules.queries_matching_no_rule | 0 | queries no text rule matched (category fallback used) |
| rules.queries_matching_two_rules | 0 | queries two text rules matched |
| rules.other_queries | 94 | queries categorised Other |
| rules.other_relabelled | 74 | Other queries given a real category from their text |
| rules.other_still_other | 20 | queries still Other after re-labelling (no reason recorded) |
| share.bills | 11000 | bills in bills_clean |
| share.bills_with_query | 1441 | bills with a query |
| share.bills_with_query_pct | 13.1 | % of bills with a query |
| share.invoices_with_query | 1416 |  |
| share.invoices_with_query_pct | 13.19 |  |
| share.credit_notes_with_query | 25 |  |
| share.credit_notes_with_query_pct | 9.58 |  |
| multi.bills_with_more_than_one_query | 0 | bills with more than one query row |
| multi.max_queries_per_bill | 1 |  |
| open.queries | 59 | queries still open at 30 Apr 2026 |
| open.queries_pct | 4.09 |  |
| open.status_Query | 59 | open queries on bills with status Query |
| open.status_With AP | 0 | open queries on bills with status With AP |
| open.status_Posted | 0 | open queries on bills with status Posted |
| open.status_Paid | 0 | open queries on bills with status Paid |
| open.age_median_days | 25.0 | median age of open queries since raised |
| open.age_max_days | 174 |  |
| timing.days_desk_to_raised.mean | 22.25 | desk to raised: mean |
| timing.days_desk_to_raised.median | 20.0 | desk to raised: median |
| timing.days_desk_to_raised.p90 | 32.0 | desk to raised: p90 |
| timing.days_desk_to_raised.min | 7.0 | desk to raised: min |
| timing.days_desk_to_raised.max | 96.0 | desk to raised: max |
| timing.days_desk_to_raised.n | 1441.0 | desk to raised: n |
| timing.days_ho_received_to_raised.mean | 10.21 | HO received to raised: mean |
| timing.days_ho_received_to_raised.median | 9.0 | HO received to raised: median |
| timing.days_ho_received_to_raised.p90 | 18.0 | HO received to raised: p90 |
| timing.days_ho_received_to_raised.min | 1.0 | HO received to raised: min |
| timing.days_ho_received_to_raised.max | 86.0 | HO received to raised: max |
| timing.days_ho_received_to_raised.n | 1441.0 | HO received to raised: n |
| timing.days_pick_to_raised.mean | 1.0 | AP picked to raised: mean |
| timing.days_pick_to_raised.median | 1.0 | AP picked to raised: median |
| timing.days_pick_to_raised.p90 | 2.0 | AP picked to raised: p90 |
| timing.days_pick_to_raised.min | 0.0 | AP picked to raised: min |
| timing.days_pick_to_raised.max | 2.0 | AP picked to raised: max |
| timing.days_pick_to_raised.n | 1441.0 | AP picked to raised: n |
| timing.days_open.mean | 21.92 | open (raised to resolved), closed queries: mean |
| timing.days_open.median | 17.0 | open (raised to resolved), closed queries: median |
| timing.days_open.p90 | 44.0 | open (raised to resolved), closed queries: p90 |
| timing.days_open.min | 2.0 | open (raised to resolved), closed queries: min |
| timing.days_open.max | 154.0 | open (raised to resolved), closed queries: max |
| timing.days_open.n | 1382.0 | open (raised to resolved), closed queries: n |
| timing.days_resolved_to_posted.mean | 2.3 | resolved to posted: mean |
| timing.days_resolved_to_posted.median | 2.0 | resolved to posted: median |
| timing.days_resolved_to_posted.p90 | 4.0 | resolved to posted: p90 |
| timing.days_resolved_to_posted.min | 1.0 | resolved to posted: min |
| timing.days_resolved_to_posted.max | 4.0 | resolved to posted: max |
| timing.days_resolved_to_posted.n | 1375.0 | resolved to posted: n |
| added.s01 | -0.14 | Vendor to facility desk: extra mean calendar days for bills with a query |
| added.s02 | -0.1 | Property check and service entry: extra mean calendar days for bills with a query |
| added.s03 | -0.01 | Waiting for property head's signature: extra mean calendar days for bills with a query |
| added.s04 | 0.04 | Courier to head office: extra mean calendar days for bills with a query |
| added.s05 | 0.41 | Queue at central AP: extra mean calendar days for bills with a query |
| added.s06 | 1.96 | AP verification, no query open: extra mean calendar days for bills with a query |
| added.s07 | 21.93 | Query open: extra mean calendar days for bills with a query |
| added.s08 | 0.07 | Waiting for payment run: extra mean calendar days for bills with a query |
| added.s99 | 24.16 | Total invoice to paid: extra mean calendar days for bills with a query |
| added.n_paid_with_query | 1308 | paid invoices with a query (stage analysis population) |
| added.n_paid_without_query | 9141 |  |
| added.total_mean_with_query | 58.78 |  |
| added.total_mean_without_query | 34.62 |  |
| added.days_on_overall_mean | 3.02 | days the queries add to the mean invoice-to-paid time of all paid invoices (extra days x share of bills with a query) |
| added.total_within_category_weighted | 24.0 | extra days with a query, compared within the same spend category (weighted by queried bills) |
| resolve.Duplicate bill.median | 16.5 | median days to resolve, Duplicate bill |
| resolve.Duplicate bill.mean | 20.79 | mean days to resolve, Duplicate bill |
| resolve.Duplicate bill.n_open | 8 | open queries, Duplicate bill |
| resolve.GL or cost centre.median | 17.0 | median days to resolve, GL or cost centre |
| resolve.GL or cost centre.mean | 22.14 | mean days to resolve, GL or cost centre |
| resolve.GL or cost centre.n_open | 8 | open queries, GL or cost centre |
| resolve.GST.median | 17.0 | median days to resolve, GST |
| resolve.GST.mean | 22.03 | mean days to resolve, GST |
| resolve.GST.n_open | 8 | open queries, GST |
| resolve.Other.median | 18.0 | median days to resolve, Other |
| resolve.Other.mean | 22.15 | mean days to resolve, Other |
| resolve.Other.n_open | 5 | open queries, Other |
| resolve.Rate mismatch.median | 16.0 | median days to resolve, Rate mismatch |
| resolve.Rate mismatch.mean | 20.05 | mean days to resolve, Rate mismatch |
| resolve.Rate mismatch.n_open | 5 | open queries, Rate mismatch |
| resolve.Service entry or GRN not posted.median | 16.0 | median days to resolve, Service entry or GRN not posted |
| resolve.Service entry or GRN not posted.mean | 20.82 | mean days to resolve, Service entry or GRN not posted |
| resolve.Service entry or GRN not posted.n_open | 1 | open queries, Service entry or GRN not posted |
| resolve.Supporting documents.median | 17.5 | median days to resolve, Supporting documents |
| resolve.Supporting documents.mean | 22.88 | mean days to resolve, Supporting documents |
| resolve.Supporting documents.n_open | 8 | open queries, Supporting documents |
| resolve.WO balance or validity.median | 16.0 | median days to resolve, WO balance or validity |
| resolve.WO balance or validity.mean | 22.63 | mean days to resolve, WO balance or validity |
| resolve.WO balance or validity.n_open | 16 | open queries, WO balance or validity |
| resolve.category_median_min | 16.0 | lowest category median days to resolve |
| resolve.category_median_max | 18.0 | highest category median days to resolve |
| resolve.side_median_min | 16.0 |  |
| resolve.side_median_max | 19.0 |  |
| resolve_side.head-office.median | 19.0 | median days to resolve, head-office-side |
| resolve_side.head-office.mean | 23.55 |  |
| resolve_side.procurement.median | 17.0 | median days to resolve, procurement-side |
| resolve_side.procurement.mean | 22.5 |  |
| resolve_side.property.median | 16.0 | median days to resolve, property-side |
| resolve_side.property.mean | 21.15 |  |
| resolve_side.vendor.median | 17.0 | median days to resolve, vendor-side |
| resolve_side.vendor.mean | 21.91 |  |
| side.vendor.primary | 615 | queries whose fix sits with the vendor side (primary rule) |
| side.vendor.primary_pct | 42.7 |  |
| side.vendor.min | 223 | vendor: queries where the text leaves no alternative owner |
| side.vendor.max | 745 | vendor: primary plus queries where it is the alternative owner |
| side.vendor.min_pct | 15.5 |  |
| side.vendor.max_pct | 51.7 |  |
| side.property.primary | 407 | queries whose fix sits with the property side (primary rule) |
| side.property.primary_pct | 28.2 |  |
| side.property.min | 311 | property: queries where the text leaves no alternative owner |
| side.property.max | 719 | property: primary plus queries where it is the alternative owner |
| side.property.min_pct | 21.6 |  |
| side.property.max_pct | 49.9 |  |
| side.procurement.primary | 338 | queries whose fix sits with the procurement side (primary rule) |
| side.procurement.primary_pct | 23.5 |  |
| side.procurement.min | 12 | procurement: queries where the text leaves no alternative owner |
| side.procurement.max | 600 | procurement: primary plus queries where it is the alternative owner |
| side.procurement.min_pct | 0.8 |  |
| side.procurement.max_pct | 41.6 |  |
| side.head-office.primary | 81 | queries whose fix sits with the head-office side (primary rule) |
| side.head-office.primary_pct | 5.6 |  |
| side.head-office.min | 61 | head-office: queries where the text leaves no alternative owner |
| side.head-office.max | 211 | head-office: primary plus queries where it is the alternative owner |
| side.head-office.min_pct | 4.2 |  |
| side.head-office.max_pct | 14.6 |  |
| side.company_side_primary | 826 | property + procurement + head-office, primary |
| side.company_side_primary_pct | 57.3 |  |
| side.company_side_min | 384 | company side, only queries with no alternative owner |
| side.ap_lead_three_categories | 679 | queries on work order, GL / cost centre, service entry / GRN (the AP lead's 'our own side') |
| side.ap_lead_three_categories_pct | 47.1 |  |
| side.company_side_min_pct | 26.6 |  |
| side.vendor.high_confidence | 223 | vendor-side queries where the text names the actor clearly |
| side.property.high_confidence | 311 | property-side queries where the text names the actor clearly |
| side.procurement.high_confidence | 119 | procurement-side queries where the text names the actor clearly |
| side.head-office.high_confidence | 0 | head-office-side queries where the text names the actor clearly |
| side.confidence_high | 653 | queries where the text names the actor clearly |
| side.confidence_medium | 768 |  |
| side.confidence_low | 20 |  |
| ev.dup_queries | 130 | duplicate-invoice-number queries |
| ev.dup_twin_registered_earlier | 34 | ...where the same vendor+invoice no. had already reached the desk |
| ev.dup_twin_exists | 68 | ...where a twin exists in the register at all |
| ev.dup_twin_same_amount | 0 | ...where the twin has the same amount |
| ev.dup_no_twin_in_register | 62 |  |
| ev.expiry_queries | 107 | work-order-expired queries |
| ev.expiry_invoice_after_valid_to | 104 | ...where the invoice date is after the SAP valid_to |
| ev.expiry_text_date_equals_valid_to | 104 | ...where the expiry date in the query text equals SAP valid_to |
| ev.no_balance.queries | 96 |  |
| ev.no_balance.over_balance_on_day_one | 5 | ...where cumulative invoices on the work order exceed approved value by this bill (SAP extract) |
| ev.no_balance.final_billed_gt_approved | 25 |  |
| ev.quantity.queries | 105 |  |
| ev.quantity.over_balance_on_day_one | 3 | ...where cumulative invoices on the work order exceed approved value by this bill (SAP extract) |
| ev.quantity.final_billed_gt_approved | 24 |  |
| ev.wo_bal_other.queries | 18 |  |
| ev.wo_bal_other.over_balance_on_day_one | 1 | ...where cumulative invoices on the work order exceed approved value by this bill (SAP extract) |
| ev.wo_bal_other.final_billed_gt_approved | 7 |  |
| ev.wo_balance_all.queries | 219 | work-order balance, quantity and no-balance queries together |
| ev.wo_balance_all.over_balance_on_day_one | 9 | ...where the extract's value rule says the bill pushed the work order over its approved value |
| ev.over_balance_rate_all_invoices_pct | 6.5 | % of all invoices the same value rule would flag, queried or not |
| ev.over_balance_flagged_invoices | 694 | invoices the value rule flags |
| ev.igst.queries | 55 | queries saying IGST was charged on an intra-state supply |
| ev.igst.master_says_same_state | 16 | ...where vendor state equals property state in the extract |
| ev.igst.master_says_different_state | 39 | ...where the extract says the supply is inter-state |
| ev.igst.base_rate_same_state_pct | 36.3 | % of all bills where vendor state equals property state |
| ev.taxrate.queries | 52 | queries saying the bill has 12% where 18% applies |
| ev.taxrate.register_gst_is_18pct | 45 | ...where the register shows 18% GST |
| ev.taxrate.diesel_zero_gst | 7 | ...on Diesel bills, which carry no GST in the register |
| layer.A.queries | 237 | queries in layer A: bill + SAP extract (checked) |
| layer.A.cum_queries | 237 | queries in layers A together |
| layer.A.cum_pct | 16.4 |  |
| layer.A.cum_mean_days_saved_per_closed_query | 14.86 | mean days saved per closed query, layers A |
| layer.A.cum_days_off_mean_total | 0.28 | days off the mean invoice-to-paid time of 10449 paid invoices, layers A |
| layer.B.queries | 217 | queries in layer B: bill printed fields + SAP master |
| layer.AB.cum_queries | 454 | queries in layers AB together |
| layer.AB.cum_pct | 31.5 |  |
| layer.AB.cum_mean_days_saved_per_closed_query | 14.87 | mean days saved per closed query, layers AB |
| layer.AB.cum_days_off_mean_total | 0.57 | days off the mean invoice-to-paid time of 10449 paid invoices, layers AB |
| layer.C.queries | 508 | queries in layer C: SAP fields not in the extract |
| layer.ABC.cum_queries | 962 | queries in layers ABC together |
| layer.ABC.cum_pct | 66.8 |  |
| layer.ABC.cum_mean_days_saved_per_closed_query | 14.75 | mean days saved per closed query, layers ABC |
| layer.ABC.cum_days_off_mean_total | 1.22 | days off the mean invoice-to-paid time of 10449 paid invoices, layers ABC |
| layer.D.queries | 242 | queries in layer D: packet documents |
| layer.ABCD.cum_queries | 1204 | queries in layers ABCD together |
| layer.ABCD.cum_pct | 83.6 |  |
| layer.ABCD.cum_mean_days_saved_per_closed_query | 14.71 | mean days saved per closed query, layers ABCD |
| layer.ABCD.cum_days_off_mean_total | 1.53 | days off the mean invoice-to-paid time of 10449 paid invoices, layers ABCD |
| layer.E.queries | 237 | queries in layer E: not knowable on day one |
| layer.ABCDE.cum_queries | 1441 | queries in layers ABCDE together |
| layer.ABCDE.cum_pct | 100.0 |  |
| layer.ABCDE.cum_mean_days_saved_per_closed_query | 14.65 | mean days saved per closed query, layers ABCDE |
| layer.ABCDE.cum_days_off_mean_total | 1.83 | days off the mean invoice-to-paid time of 10449 paid invoices, layers ABCDE |
| a_verified.queries | 163 | queries where a day-one rule on bill + extract fires (duplicates seen earlier, expired WOs, over-balance, IGST same-state) |
| a_verified.layerA_queries | 138 | layer A queries where the rule fires on the data |
| a_verified.layerA_days_off_mean_total | 0.17 |  |
| timing.desk_to_pick_median | 20.0 | median days from desk to AP picking the bill, queried bills |
| timing.min_desk_to_raised | 7 | shortest gap from desk to a query being raised |
| month.pct_min | 11.73 | lowest monthly share of bills with a query |
| month.pct_max | 14.39 | highest monthly share of bills with a query |
| month.pct_min_month | 2026-01 |  |
| month.pct_max_month | 2025-07 |  |
| month.raised_max | 136 | most queries raised in one month |
| month.raised_max_month | 2026-03 |  |
| month.raised_min | 34 |  |
| month.raised_min_month | 2025-04 |  |
| month.raised_mean | 113.6 | mean queries raised per month (all but the last, partial month) |
| wo_cluster.max_4day_count | 10 | most work-order queries raised in any 4 consecutive days |
| wo_cluster.max_4day_ending | 2026-01-15 |  |
| wo_cluster.feb2026_week2_count | 11 | work-order queries raised 8 to 15 Feb 2026 |
| wo_cluster.mean_4day_count | 3.58 | mean work-order queries per 4 days |
| wo_cluster.feb2026_total | 25 | work-order queries raised in Feb 2026 |
| wo_cluster.monthly_mean_wo | 26.2 |  |
| claim.missing_challan_median_days | 22.0 | AP lead: a missing challan takes a week. Median days to resolve PF/ESIC challan queries |
| claim.wo_median_days | 17.0 | AP lead: an amendment can take a month. Median days to resolve work-order queries |
| proptype.Office Tower.pct_queried | 13.83 | % of Office Tower bills with a query |
| proptype.Residential Society.pct_queried | 12.99 | % of Residential Society bills with a query |
| proptype.Retail Mall.pct_queried | 11.49 | % of Retail Mall bills with a query |
| spend.Cleaning Material.queries | 158 | queries on Cleaning Material bills |
| spend.Cleaning Material.pct_queried | 12.66 | % of Cleaning Material bills with a query |
| spend.DG Set AMC.queries | 80 | queries on DG Set AMC bills |
| spend.DG Set AMC.pct_queried | 15.5 | % of DG Set AMC bills with a query |
| spend.Diesel Supply.queries | 132 | queries on Diesel Supply bills |
| spend.Diesel Supply.pct_queried | 12.13 | % of Diesel Supply bills with a query |
| spend.Fire AMC.queries | 69 | queries on Fire AMC bills |
| spend.Fire AMC.pct_queried | 12.8 | % of Fire AMC bills with a query |
| spend.Housekeeping Manpower.queries | 268 | queries on Housekeeping Manpower bills |
| spend.Housekeeping Manpower.pct_queried | 13.43 | % of Housekeeping Manpower bills with a query |
| spend.Landscaping.queries | 121 | queries on Landscaping bills |
| spend.Landscaping.pct_queried | 13.64 | % of Landscaping bills with a query |
| spend.Lift AMC.queries | 85 | queries on Lift AMC bills |
| spend.Lift AMC.pct_queried | 12.32 | % of Lift AMC bills with a query |
| spend.Pest Control.queries | 77 | queries on Pest Control bills |
| spend.Pest Control.pct_queried | 12.09 | % of Pest Control bills with a query |
| spend.Repairs and Maintenance.queries | 80 | queries on Repairs and Maintenance bills |
| spend.Repairs and Maintenance.pct_queried | 11.99 | % of Repairs and Maintenance bills with a query |
| spend.Security Manpower.queries | 306 | queries on Security Manpower bills |
| spend.Security Manpower.pct_queried | 13.99 | % of Security Manpower bills with a query |
| spend.Water Testing.queries | 65 | queries on Water Testing bills |
| spend.Water Testing.pct_queried | 11.93 | % of Water Testing bills with a query |
| msme.Micro.pct_queried | 12.83 | % of Micro vendors' bills with a query |
| msme.Small.pct_queried | 12.34 | % of Small vendors' bills with a query |
| msme.Medium.pct_queried | 13.7 | % of Medium vendors' bills with a query |
| msme.Not MSME.pct_queried | 13.59 | % of Not MSME vendors' bills with a query |
| msme.Unknown.pct_queried | 13.4 | % of Unknown vendors' bills with a query |

<!-- END 04_query_forensics.py -->

<!-- BEGIN 05_claims_tested.py -->

### Figures from `analysis/05_claims_tested.py` (used in notes/claims-tested.md, claims_tested.csv. The other numbers in claims-tested.md are read from the figure ids named in claims_tested.csv (clean.py, 02_stage_times.py, 04_query_forensics.py and 06_msme_exposure.py))

Script: `analysis/05_claims_tested.py`. Output: `analysis/out/figures_claims_tested.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
python -I analysis/02_stage_times.py
python -I analysis/04_query_forensics.py
python -I analysis/06_msme_exposure.py
python -I analysis/05_claims_tested.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| c.courier.weekdays_with_a_single_lag | 7.0 | signing weekdays on which every bill took the same number of days to reach head office |
| c.courier.lag_signed_wednesday | 2.0 | days from head's signature to HO receipt when signed on a Wednesday |
| c.courier.lag_signed_thursday | 8.0 | days from head's signature to HO receipt when signed on a Thursday |
| c.courier.lag_signed_friday | 7.0 | days from head's signature to HO receipt when signed on a Friday |
| c.courier.lag_min | 2.0 |  |
| c.courier.lag_max | 8.0 |  |
| c.packet.posted_before_ho_received | 0.0 | bills posted before the packet reached head office |
| c.packet.posted_bills | 10896.0 |  |
| c.packet.received_bills | 10996.0 | bills whose packet has a head-office receipt date |
| c.prop.desk_to_signed_mean | 7.14 | days from desk to head's signature, mean |
| c.prop.desk_to_signed_median | 6.0 |  |
| c.prop.desk_to_signed_p90 | 13.0 |  |
| c.prop.sign_step_mean | 1.52 | days from verified to head's signature, mean |
| c.prop.sign_step_median | 2.0 |  |
| c.prop.sign_step_max | 3.0 |  |
| c.prop.sign_step_le2_pct | 75.3 | % signed within 2 days of verification |
| c.prop.desk_to_ho_mean | 12.12 | days from desk to head-office receipt, mean |
| c.prop.desk_to_signed_le2_pct | 6.7 | % of bills leaving property (signed) within 2 days of the desk |
| c.prop.signed_on_weekend_pct | 28.4 | % of signatures dated Saturday or Sunday |
| c.ho.recv_to_post_mean | 13.2 | days at head office from receipt to posting, mean |
| c.ho.recv_to_post_median | 9.0 |  |
| c.ho.recv_to_post_gt14_pct | 26.9 | % of posted bills more than 14 days from HO receipt to posting |
| c.ho.recv_to_post_gt21_pct | 14.6 |  |
| c.ho.recv_to_post_gt28_pct | 8.4 |  |
| c.ho.recv_to_post_queried_median | 30.0 | same, bills with a query |
| c.ho.recv_to_post_queried_mean | 34.5 |  |
| c.ho.recv_to_post_clean_median | 9.0 | same, bills with no query |
| c.ho.recv_to_post_clean_gt14_pct | 17.2 |  |
| c.ho.recv_to_pick_gt14_pct | 13.5 | % of picked bills that waited more than 14 days for a verifier |
| c.ho.clean_pick_to_post_mean | 1.34 | days from pick to posting, bills with no query, mean |
| c.ho.clean_pick_to_post_median | 1.0 |  |
| c.ho.clean_pick_to_post_max | 3.0 |  |
| c.ver.AP-1.bills | 4421.0 | bills handled by AP-1 |
| c.ver.AP-1.share_pct | 40.3 |  |
| c.ver.AP-1.queue_days | 11.29 | mean days waiting for AP-1 to pick up |
| c.ver.AP-1.query_pct | 14.0 | % of AP-1's bills with a query |
| c.ver.AP-1.mean_amount | 268374.0 | mean bill amount for AP-1 |
| c.ver.AP-1.residential_pct | 73.9 |  |
| c.ver.AP-2.bills | 2167.0 | bills handled by AP-2 |
| c.ver.AP-2.share_pct | 19.8 |  |
| c.ver.AP-2.queue_days | 7.18 | mean days waiting for AP-2 to pick up |
| c.ver.AP-2.query_pct | 11.1 | % of AP-2's bills with a query |
| c.ver.AP-2.mean_amount | 258254.0 | mean bill amount for AP-2 |
| c.ver.AP-2.residential_pct | 74.5 |  |
| c.ver.AP-3.bills | 1665.0 | bills handled by AP-3 |
| c.ver.AP-3.share_pct | 15.2 |  |
| c.ver.AP-3.queue_days | 7.24 | mean days waiting for AP-3 to pick up |
| c.ver.AP-3.query_pct | 12.4 | % of AP-3's bills with a query |
| c.ver.AP-3.mean_amount | 255180.0 | mean bill amount for AP-3 |
| c.ver.AP-3.residential_pct | 73.8 |  |
| c.ver.AP-4.bills | 1610.0 | bills handled by AP-4 |
| c.ver.AP-4.share_pct | 14.7 |  |
| c.ver.AP-4.queue_days | 7.28 | mean days waiting for AP-4 to pick up |
| c.ver.AP-4.query_pct | 14.3 | % of AP-4's bills with a query |
| c.ver.AP-4.mean_amount | 248117.0 | mean bill amount for AP-4 |
| c.ver.AP-4.residential_pct | 73.8 |  |
| c.ver.AP-5.bills | 1106.0 | bills handled by AP-5 |
| c.ver.AP-5.share_pct | 10.1 |  |
| c.ver.AP-5.queue_days | 7.11 | mean days waiting for AP-5 to pick up |
| c.ver.AP-5.query_pct | 13.2 | % of AP-5's bills with a query |
| c.ver.AP-5.mean_amount | 254872.0 | mean bill amount for AP-5 |
| c.ver.AP-5.residential_pct | 75.8 |  |
| c.ver.total_with_verifier | 10969.0 |  |
| c.ver.properties_served_by_all_five | 38.0 | properties served by all five verifiers |
| c.ver.properties | 38.0 |  |
| c.ver.properties_where_AP1_is_main | 38.0 | properties where AP-1 handles the most bills |
| c.ver.AP1_min_share_in_a_property_pct | 31.0 |  |
| c.ver.AP1_max_share_in_a_property_pct | 47.1 |  |
| c.ver.other_queue_min | 7.11 |  |
| c.ver.other_queue_max | 7.28 |  |
| c.load.picked_monday | 1742.0 | bills picked up on a Monday |
| c.load.picked_tuesday | 1816.0 | bills picked up on a Tuesday |
| c.load.picked_saturday | 1240.0 | bills picked up on a Saturday |
| c.load.picked_mean_per_weekday | 1567.0 | mean bills picked up per weekday |
| c.load.per_friday_days_1-7 | 159.0 | bills reaching head office per Friday, Fridays on days 1-7 of the month |
| c.load.per_friday_days_8-14 | 137.0 | bills reaching head office per Friday, Fridays on days 8-14 of the month |
| c.load.per_friday_days_15-21 | 236.0 | bills reaching head office per Friday, Fridays on days 15-21 of the month |
| c.load.per_friday_days_22-31 | 249.0 | bills reaching head office per Friday, Fridays on days 22-31 of the month |
| c.load.manpower_share_received_days_1-14 | 25.9 | % of bills reaching HO on days 1-14 that are manpower (security, housekeeping, landscaping) |
| c.load.queue_days_received_1-14 | 8.56 |  |
| c.load.manpower_share_received_days_15-31 | 56.3 | % of bills reaching HO on days 15-31 that are manpower (security, housekeeping, landscaping) |
| c.load.queue_days_received_15-31 | 9.0 |  |
| c.load.invoiced_first10_manpower_pct | 72.4 | % of bills invoiced on days 1 to 10 that are manpower |
| c.load.invoiced_after10_manpower_pct | 0.0 |  |
| c.load.invoiced_first10_share_pct | 63.7 | % of all bills invoiced on days 1 to 10 |
| c.wo.duration_median_days | 530.0 | median validity of a work order in days |
| c.wo.duration_330_400_pct | 6.3 | % of work orders valid for 330 to 400 days |
| c.wo.duration_ge300_pct | 96.7 |  |
| c.wo.overbilled_pct_min_category | 22.7 |  |
| c.wo.overbilled_pct_max_category | 35.3 |  |
| c.wo.overbilled_pct_security | 30.7 |  |
| c.wo.overbilled_pct_housekeeping | 29.2 |  |
| c.wo.crossed_approved_value | 601.0 | work orders whose cumulative invoices pass approved value |
| c.wo.crossed_before_valid_to | 560.0 | ...before their valid_to date |
| c.wo.crossed_before_valid_to_pct | 93.2 |  |
| c.wo.over_approved_by_dec | 244.0 | work orders past approved value by invoice date 2025-12-31 |
| c.wo.over_approved_by_feb | 422.0 | work orders past approved value by invoice date 2026-02-28 |
| c.wo.crossed_in_jan_feb | 178.0 | work orders that crossed approved value during Jan and Feb 2026 |
| c.wo.crossings_per_month_apr_sep_max | 23.0 | most work orders crossing approved value in any month Apr to Sep 2025 |
| c.wo.crossings_per_month_oct_feb_min | 42.0 | fewest in any month Oct 2025 to Feb 2026 |
| c.wo.expiry_query_orders_on_a_60day_report | 93.0 | orders behind an expiry query that fall inside a 'next 60 days' list run on the 1st of a month from 1 Apr 2025 |
| c.wo.expiry_days_between_expiry_and_desk_median | 39.0 | median days from the order's expiry to the bill reaching the desk |
| c.gl.queries_per_month | 6.3 | GL-does-not-match queries per month (first and last, partial, months left out) |
| c.gl.gl_or_cc_per_month | 17.9 | GL or cost-centre queries per month |
| c.woq.closed | 321.0 |  |
| c.woq.le7_pct | 14.0 | % of work-order queries closed within 7 days of being raised |
| c.woq.le14_pct | 41.1 |  |
| c.woq.gt30_pct | 22.1 | % open longer than 30 days |
| c.woq.median | 17.0 |  |
| c.woq.p90 | 44.0 |  |
| c.woq.max | 154.0 |  |
| c.sec.clean_median | 36.0 | security bills with no query: median days invoice to paid |
| c.sec.queried_median | 56.5 | security bills with a query: median days |
| c.sec.gt60_pct | 8.1 | % of security bills taking more than 60 days |
| c.sec.oct_mean | 41.4 | security bills invoiced Oct 2025: mean days |
| c.sec.other_months_mean | 41.0 |  |
| c.sec.oct_gt60 | 12.0 | ...of which over 60 days |
| c.sec.oct_n | 167.0 |  |
| c.sec.vendors | 72.0 |  |
| c.sec.vendor_max_properties | 4.0 | most properties any security vendor serves |
| c.sec.vendors_msme_blank | 10.0 |  |
| c.sec.queries | 306.0 |  |
| c.sec.wo_queries | 69.0 |  |
| c.igst.haryana_haryana | 10.0 | IGST queries where vendor and property are both in Haryana |
| c.att.claim_days | 388.0 |  |
| c.att.biometric_days | 352.0 |  |
| c.att.gate_days | 382.0 |  |
| c.att.people | 17.0 |  |
| c.att.claim_gt_biometric_people | 11.0 | people whose claimed days exceed biometric days |
| c.att.claim_gt_gate_people | 4.0 | people whose claimed days exceed gate-register days |
| c.att.claim_minus_gate_days | 6.0 | claimed days not backed by the gate register |
| c.att.relievers | 3.0 |  |
| c.att.relievers_in_biometric | 0.0 |  |
| c.att.guard_days_in_gate_not_biometric | 11.0 | guard-days in the gate register with no biometric punch |
| c.case.december_housekeeping_matches | 0.0 | bills matching the described December housekeeping case (desk 5 Jan 2026, work-order query closed 11 to 14 Feb) |
| c.q.on_property_checklist_items | 366.0 | queries on items the property checklist P1 to P9 already requires |
| c.q.on_property_checklist_items_pct | 25.4 |  |
| c.dup.bills_in_same_vendor_invoice_pairs | 136.0 |  |
| c.dup.pct_of_bills | 1.24 |  |
| c.typing.share_of_central_ap | 12.0 | AP verification (no query open) as % of the days a bill spends in central AP: queue + verify + query |
| c.ho.central_ap_plus_treasury | 19.17 | mean days from head-office receipt to paid: central AP stages plus the payment run |
| c.prop.courier_plus_property | 12.12 | mean days in the property's check, signature and courier stages |
| c.igst.inter_state | 39.0 | IGST queries where the extract says vendor and property are in different states |
| c.att.claim_minus_biometric_days | 36.0 | claimed days not backed by biometric punches |
| c.wo.over_dec_share_of_feb_pct | 57.8 | % of the work orders past approved value by 28 Feb that were already past it on 31 Dec |
| c.sec.wo_queries_pct | 22.5 | % of queries on security bills that are work-order queries |

<!-- END 05_claims_tested.py -->

<!-- BEGIN 06_msme_exposure.py -->

### Figures from `analysis/06_msme_exposure.py` (used in notes/msme-exposure.md, notes/research.md, notes/assumptions.md. Every row of msme_exposure.csv and msme_open_bills.csv is also a figure: same script, same command)

Script: `analysis/06_msme_exposure.py`. Output: `analysis/out/figures_msme.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
python -I analysis/06_msme_exposure.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| pop.invoices | 10739 | invoices (credit notes excluded) |
| pop.credit_notes_excluded | 261 |  |
| pop.paid_analysed | 10449 | invoices with a trustworthy payment date |
| pop.paid_date_unusable | 110 | invoices whose payment date is unusable (D03) |
| pop.open | 180 | invoices unpaid at 30 Apr 2026 |
| assume.vendors_blank | 137 | vendors with blank MSME status |
| assume.vendors_known | 763 | vendors with a known status |
| assume.known_micro_small | 444 | known vendors that are Micro or Small |
| assume.share_micro_small_known | 58.2 | % of known-status vendors that are Micro or Small (the central assumption) |
| assume.share_by_billing_quartile_min | 57.1 | lowest Micro/Small share across four billing-size quartiles of known vendors |
| assume.share_by_billing_quartile_max | 59.7 | highest |
| assume.blank_median_billed | 368800.0 | median yearly billing of blank-status vendors (INR) |
| assume.known_median_billed | 450630.0 | median yearly billing of known-status vendors (INR) |
| assume.expected_blank_micro_small_central | 79.7 | expected Micro/Small among blank vendors at the central share |
| assume.expected_blank_micro_small_by_category | 79.5 | same, using each spend category's own known share |
| assume.category_share_min | 49.0 |  |
| assume.category_share_max | 67.6 |  |
| e.paid.invoice.micro.n_paid | 3041.0 |  |
| e.paid.invoice.micro.val_paid_ex_gst | 822933220.0 |  |
| e.paid.invoice.micro.n_late | 620.0 |  |
| e.paid.invoice.micro.val_late_ex_gst | 192575470.0 |  |
| e.paid.invoice.micro.val_late_incl_gst | 224987429.0 |  |
| e.paid.invoice.micro.n_late_60 | 196.0 |  |
| e.paid.invoice.micro.val_late_60_ex_gst | 59220370.0 |  |
| e.paid.invoice.micro.n_late_15 | 3029.0 |  |
| e.paid.invoice.micro.median_days_over_limit | 9.0 |  |
| e.paid.invoice.micro.mean_days_to_pay | 37.58 |  |
| e.paid.invoice.micro.pct_late | 20.4 | % of micro paid invoices paid more than 45 days after invoice_date |
| e.paid.invoice.micro.pct_late_15 | 99.6 | % of micro paid invoices paid more than 15 days after invoice_date |
| e.paid.invoice.micro.pct_late_60 | 6.4 | % of micro paid invoices paid more than 60 days after invoice_date |
| e.paid.invoice.small.n_paid | 2065.0 |  |
| e.paid.invoice.small.val_paid_ex_gst | 551882150.0 |  |
| e.paid.invoice.small.n_late | 411.0 |  |
| e.paid.invoice.small.val_late_ex_gst | 132466720.0 |  |
| e.paid.invoice.small.val_late_incl_gst | 155256677.0 |  |
| e.paid.invoice.small.n_late_60 | 118.0 |  |
| e.paid.invoice.small.val_late_60_ex_gst | 36087700.0 |  |
| e.paid.invoice.small.n_late_15 | 2061.0 |  |
| e.paid.invoice.small.median_days_over_limit | 9.0 |  |
| e.paid.invoice.small.mean_days_to_pay | 37.33 |  |
| e.paid.invoice.small.pct_late | 19.9 | % of small paid invoices paid more than 45 days after invoice_date |
| e.paid.invoice.small.pct_late_15 | 99.8 | % of small paid invoices paid more than 15 days after invoice_date |
| e.paid.invoice.small.pct_late_60 | 5.7 | % of small paid invoices paid more than 60 days after invoice_date |
| e.paid.invoice.medium.n_paid | 893.0 |  |
| e.paid.invoice.medium.val_paid_ex_gst | 232712650.0 |  |
| e.paid.invoice.medium.n_late | 171.0 |  |
| e.paid.invoice.medium.val_late_ex_gst | 50876980.0 |  |
| e.paid.invoice.medium.val_late_incl_gst | 59429347.0 |  |
| e.paid.invoice.medium.n_late_60 | 46.0 |  |
| e.paid.invoice.medium.val_late_60_ex_gst | 12461340.0 |  |
| e.paid.invoice.medium.n_late_15 | 892.0 |  |
| e.paid.invoice.medium.median_days_over_limit | 9.0 |  |
| e.paid.invoice.medium.mean_days_to_pay | 37.25 |  |
| e.paid.invoice.medium.pct_late | 19.1 | % of medium paid invoices paid more than 45 days after invoice_date |
| e.paid.invoice.medium.pct_late_15 | 99.9 | % of medium paid invoices paid more than 15 days after invoice_date |
| e.paid.invoice.medium.pct_late_60 | 5.2 | % of medium paid invoices paid more than 60 days after invoice_date |
| e.paid.invoice.notmsme.n_paid | 2918.0 |  |
| e.paid.invoice.notmsme.val_paid_ex_gst | 789241460.0 |  |
| e.paid.invoice.notmsme.n_late | 629.0 |  |
| e.paid.invoice.notmsme.val_late_ex_gst | 206154120.0 |  |
| e.paid.invoice.notmsme.val_late_incl_gst | 240947924.0 |  |
| e.paid.invoice.notmsme.n_late_60 | 217.0 |  |
| e.paid.invoice.notmsme.val_late_60_ex_gst | 70054430.0 |  |
| e.paid.invoice.notmsme.n_late_15 | 2914.0 |  |
| e.paid.invoice.notmsme.median_days_over_limit | 10.0 |  |
| e.paid.invoice.notmsme.mean_days_to_pay | 38.3 |  |
| e.paid.invoice.notmsme.pct_late | 21.6 | % of notmsme paid invoices paid more than 45 days after invoice_date |
| e.paid.invoice.notmsme.pct_late_15 | 99.9 | % of notmsme paid invoices paid more than 15 days after invoice_date |
| e.paid.invoice.notmsme.pct_late_60 | 7.4 | % of notmsme paid invoices paid more than 60 days after invoice_date |
| e.paid.invoice.unknown.n_paid | 1532.0 |  |
| e.paid.invoice.unknown.val_paid_ex_gst | 408405810.0 |  |
| e.paid.invoice.unknown.n_late | 291.0 |  |
| e.paid.invoice.unknown.val_late_ex_gst | 90783070.0 |  |
| e.paid.invoice.unknown.val_late_incl_gst | 105707276.0 |  |
| e.paid.invoice.unknown.n_late_60 | 90.0 |  |
| e.paid.invoice.unknown.val_late_60_ex_gst | 27935810.0 |  |
| e.paid.invoice.unknown.n_late_15 | 1531.0 |  |
| e.paid.invoice.unknown.median_days_over_limit | 8.0 |  |
| e.paid.invoice.unknown.mean_days_to_pay | 37.15 |  |
| e.paid.invoice.unknown.pct_late | 19.0 | % of unknown paid invoices paid more than 45 days after invoice_date |
| e.paid.invoice.unknown.pct_late_15 | 99.9 | % of unknown paid invoices paid more than 15 days after invoice_date |
| e.paid.invoice.unknown.pct_late_60 | 5.9 | % of unknown paid invoices paid more than 60 days after invoice_date |
| e.paid.invoice.microsmall_known.n_paid | 5106.0 |  |
| e.paid.invoice.microsmall_known.val_paid_ex_gst | 1374815370.0 |  |
| e.paid.invoice.microsmall_known.n_late | 1031.0 |  |
| e.paid.invoice.microsmall_known.val_late_ex_gst | 325042190.0 |  |
| e.paid.invoice.microsmall_known.val_late_incl_gst | 380244106.0 |  |
| e.paid.invoice.microsmall_known.n_late_60 | 314.0 |  |
| e.paid.invoice.microsmall_known.val_late_60_ex_gst | 95308070.0 |  |
| e.paid.invoice.microsmall_known.n_late_15 | 5090.0 |  |
| e.paid.invoice.microsmall_known.median_days_over_limit | 9.0 |  |
| e.paid.invoice.microsmall_known.mean_days_to_pay | 37.48 |  |
| e.paid.invoice.microsmall_known.pct_late | 20.2 | % of microsmall_known paid invoices paid more than 45 days after invoice_date |
| e.paid.invoice.microsmall_known.pct_late_15 | 99.7 | % of microsmall_known paid invoices paid more than 15 days after invoice_date |
| e.paid.invoice.microsmall_known.pct_late_60 | 6.1 | % of microsmall_known paid invoices paid more than 60 days after invoice_date |
| e.paid.invoice.all_statuses.n_paid | 10449.0 |  |
| e.paid.invoice.all_statuses.val_paid_ex_gst | 2805175290.0 |  |
| e.paid.invoice.all_statuses.n_late | 2122.0 |  |
| e.paid.invoice.all_statuses.val_late_ex_gst | 672856360.0 |  |
| e.paid.invoice.all_statuses.val_late_incl_gst | 786328653.0 |  |
| e.paid.invoice.all_statuses.n_late_60 | 667.0 |  |
| e.paid.invoice.all_statuses.val_late_60_ex_gst | 205759650.0 |  |
| e.paid.invoice.all_statuses.n_late_15 | 10427.0 |  |
| e.paid.invoice.all_statuses.median_days_over_limit | 9.0 |  |
| e.paid.invoice.all_statuses.mean_days_to_pay | 37.64 |  |
| e.paid.invoice.all_statuses.pct_late | 20.3 | % of all_statuses paid invoices paid more than 45 days after invoice_date |
| e.paid.invoice.all_statuses.pct_late_15 | 99.8 | % of all_statuses paid invoices paid more than 15 days after invoice_date |
| e.paid.invoice.all_statuses.pct_late_60 | 6.4 | % of all_statuses paid invoices paid more than 60 days after invoice_date |
| e.paid.desk_received.micro.n_paid | 3041.0 |  |
| e.paid.desk_received.micro.val_paid_ex_gst | 822933220.0 |  |
| e.paid.desk_received.micro.n_late | 337.0 |  |
| e.paid.desk_received.micro.val_late_ex_gst | 105196810.0 |  |
| e.paid.desk_received.micro.val_late_incl_gst | 123215443.0 |  |
| e.paid.desk_received.micro.n_late_60 | 114.0 |  |
| e.paid.desk_received.micro.val_late_60_ex_gst | 34236880.0 |  |
| e.paid.desk_received.micro.n_late_15 | 2957.0 |  |
| e.paid.desk_received.micro.median_days_over_limit | 9.0 |  |
| e.paid.desk_received.micro.mean_days_to_pay | 31.27 |  |
| e.paid.desk_received.micro.pct_late | 11.1 | % of micro paid invoices paid more than 45 days after desk_received_date |
| e.paid.desk_received.micro.pct_late_15 | 97.2 | % of micro paid invoices paid more than 15 days after desk_received_date |
| e.paid.desk_received.micro.pct_late_60 | 3.7 | % of micro paid invoices paid more than 60 days after desk_received_date |
| e.paid.desk_received.small.n_paid | 2065.0 |  |
| e.paid.desk_received.small.val_paid_ex_gst | 551882150.0 |  |
| e.paid.desk_received.small.n_late | 193.0 |  |
| e.paid.desk_received.small.val_late_ex_gst | 63141510.0 |  |
| e.paid.desk_received.small.val_late_incl_gst | 74012959.0 |  |
| e.paid.desk_received.small.n_late_60 | 60.0 |  |
| e.paid.desk_received.small.val_late_60_ex_gst | 20344130.0 |  |
| e.paid.desk_received.small.n_late_15 | 2020.0 |  |
| e.paid.desk_received.small.median_days_over_limit | 9.0 |  |
| e.paid.desk_received.small.mean_days_to_pay | 30.74 |  |
| e.paid.desk_received.small.pct_late | 9.3 | % of small paid invoices paid more than 45 days after desk_received_date |
| e.paid.desk_received.small.pct_late_15 | 97.8 | % of small paid invoices paid more than 15 days after desk_received_date |
| e.paid.desk_received.small.pct_late_60 | 2.9 | % of small paid invoices paid more than 60 days after desk_received_date |
| e.paid.desk_received.medium.n_paid | 893.0 |  |
| e.paid.desk_received.medium.val_paid_ex_gst | 232712650.0 |  |
| e.paid.desk_received.medium.n_late | 97.0 |  |
| e.paid.desk_received.medium.val_late_ex_gst | 28257360.0 |  |
| e.paid.desk_received.medium.val_late_incl_gst | 32946659.0 |  |
| e.paid.desk_received.medium.n_late_60 | 24.0 |  |
| e.paid.desk_received.medium.val_late_60_ex_gst | 5928050.0 |  |
| e.paid.desk_received.medium.n_late_15 | 879.0 |  |
| e.paid.desk_received.medium.median_days_over_limit | 8.0 |  |
| e.paid.desk_received.medium.mean_days_to_pay | 31.07 |  |
| e.paid.desk_received.medium.pct_late | 10.9 | % of medium paid invoices paid more than 45 days after desk_received_date |
| e.paid.desk_received.medium.pct_late_15 | 98.4 | % of medium paid invoices paid more than 15 days after desk_received_date |
| e.paid.desk_received.medium.pct_late_60 | 2.7 | % of medium paid invoices paid more than 60 days after desk_received_date |
| e.paid.desk_received.notmsme.n_paid | 2918.0 |  |
| e.paid.desk_received.notmsme.val_paid_ex_gst | 789241460.0 |  |
| e.paid.desk_received.notmsme.n_late | 372.0 |  |
| e.paid.desk_received.notmsme.val_late_ex_gst | 129414190.0 |  |
| e.paid.desk_received.notmsme.val_late_incl_gst | 151513382.0 |  |
| e.paid.desk_received.notmsme.n_late_60 | 121.0 |  |
| e.paid.desk_received.notmsme.val_late_60_ex_gst | 36191870.0 |  |
| e.paid.desk_received.notmsme.n_late_15 | 2871.0 |  |
| e.paid.desk_received.notmsme.median_days_over_limit | 9.0 |  |
| e.paid.desk_received.notmsme.mean_days_to_pay | 31.88 |  |
| e.paid.desk_received.notmsme.pct_late | 12.7 | % of notmsme paid invoices paid more than 45 days after desk_received_date |
| e.paid.desk_received.notmsme.pct_late_15 | 98.4 | % of notmsme paid invoices paid more than 15 days after desk_received_date |
| e.paid.desk_received.notmsme.pct_late_60 | 4.1 | % of notmsme paid invoices paid more than 60 days after desk_received_date |
| e.paid.desk_received.unknown.n_paid | 1532.0 |  |
| e.paid.desk_received.unknown.val_paid_ex_gst | 408405810.0 |  |
| e.paid.desk_received.unknown.n_late | 154.0 |  |
| e.paid.desk_received.unknown.val_late_ex_gst | 42637650.0 |  |
| e.paid.desk_received.unknown.val_late_incl_gst | 49499798.0 |  |
| e.paid.desk_received.unknown.n_late_60 | 52.0 |  |
| e.paid.desk_received.unknown.val_late_60_ex_gst | 16192940.0 |  |
| e.paid.desk_received.unknown.n_late_15 | 1499.0 |  |
| e.paid.desk_received.unknown.median_days_over_limit | 9.0 |  |
| e.paid.desk_received.unknown.mean_days_to_pay | 31.04 |  |
| e.paid.desk_received.unknown.pct_late | 10.1 | % of unknown paid invoices paid more than 45 days after desk_received_date |
| e.paid.desk_received.unknown.pct_late_15 | 97.8 | % of unknown paid invoices paid more than 15 days after desk_received_date |
| e.paid.desk_received.unknown.pct_late_60 | 3.4 | % of unknown paid invoices paid more than 60 days after desk_received_date |
| e.paid.desk_received.microsmall_known.n_paid | 5106.0 |  |
| e.paid.desk_received.microsmall_known.val_paid_ex_gst | 1374815370.0 |  |
| e.paid.desk_received.microsmall_known.n_late | 530.0 |  |
| e.paid.desk_received.microsmall_known.val_late_ex_gst | 168338320.0 |  |
| e.paid.desk_received.microsmall_known.val_late_incl_gst | 197228402.0 |  |
| e.paid.desk_received.microsmall_known.n_late_60 | 174.0 |  |
| e.paid.desk_received.microsmall_known.val_late_60_ex_gst | 54581010.0 |  |
| e.paid.desk_received.microsmall_known.n_late_15 | 4977.0 |  |
| e.paid.desk_received.microsmall_known.median_days_over_limit | 9.0 |  |
| e.paid.desk_received.microsmall_known.mean_days_to_pay | 31.06 |  |
| e.paid.desk_received.microsmall_known.pct_late | 10.4 | % of microsmall_known paid invoices paid more than 45 days after desk_received_date |
| e.paid.desk_received.microsmall_known.pct_late_15 | 97.5 | % of microsmall_known paid invoices paid more than 15 days after desk_received_date |
| e.paid.desk_received.microsmall_known.pct_late_60 | 3.4 | % of microsmall_known paid invoices paid more than 60 days after desk_received_date |
| e.paid.desk_received.all_statuses.n_paid | 10449.0 |  |
| e.paid.desk_received.all_statuses.val_paid_ex_gst | 2805175290.0 |  |
| e.paid.desk_received.all_statuses.n_late | 1153.0 |  |
| e.paid.desk_received.all_statuses.val_late_ex_gst | 368647520.0 |  |
| e.paid.desk_received.all_statuses.val_late_incl_gst | 431188241.0 |  |
| e.paid.desk_received.all_statuses.n_late_60 | 371.0 |  |
| e.paid.desk_received.all_statuses.val_late_60_ex_gst | 112893870.0 |  |
| e.paid.desk_received.all_statuses.n_late_15 | 10226.0 |  |
| e.paid.desk_received.all_statuses.median_days_over_limit | 9.0 |  |
| e.paid.desk_received.all_statuses.mean_days_to_pay | 31.28 |  |
| e.paid.desk_received.all_statuses.pct_late | 11.0 | % of all_statuses paid invoices paid more than 45 days after desk_received_date |
| e.paid.desk_received.all_statuses.pct_late_15 | 97.9 | % of all_statuses paid invoices paid more than 15 days after desk_received_date |
| e.paid.desk_received.all_statuses.pct_late_60 | 3.6 | % of all_statuses paid invoices paid more than 60 days after desk_received_date |
| e.paid.property_verified.micro.n_paid | 3041.0 |  |
| e.paid.property_verified.micro.val_paid_ex_gst | 822933220.0 |  |
| e.paid.property_verified.micro.n_late | 198.0 |  |
| e.paid.property_verified.micro.val_late_ex_gst | 52100470.0 |  |
| e.paid.property_verified.micro.val_late_incl_gst | 60791523.0 |  |
| e.paid.property_verified.micro.n_late_60 | 83.0 |  |
| e.paid.property_verified.micro.val_late_60_ex_gst | 22874420.0 |  |
| e.paid.property_verified.micro.n_late_15 | 2659.0 |  |
| e.paid.property_verified.micro.median_days_over_limit | 13.0 |  |
| e.paid.property_verified.micro.mean_days_to_pay | 25.57 |  |
| e.paid.property_verified.micro.pct_late | 6.5 | % of micro paid invoices paid more than 45 days after property_verified_date |
| e.paid.property_verified.micro.pct_late_15 | 87.4 | % of micro paid invoices paid more than 15 days after property_verified_date |
| e.paid.property_verified.micro.pct_late_60 | 2.7 | % of micro paid invoices paid more than 60 days after property_verified_date |
| e.paid.property_verified.small.n_paid | 2065.0 |  |
| e.paid.property_verified.small.val_paid_ex_gst | 551882150.0 |  |
| e.paid.property_verified.small.n_late | 107.0 |  |
| e.paid.property_verified.small.val_late_ex_gst | 32796120.0 |  |
| e.paid.property_verified.small.val_late_incl_gst | 38250658.0 |  |
| e.paid.property_verified.small.n_late_60 | 43.0 |  |
| e.paid.property_verified.small.val_late_60_ex_gst | 13228230.0 |  |
| e.paid.property_verified.small.n_late_15 | 1833.0 |  |
| e.paid.property_verified.small.median_days_over_limit | 12.0 |  |
| e.paid.property_verified.small.mean_days_to_pay | 24.89 |  |
| e.paid.property_verified.small.pct_late | 5.2 | % of small paid invoices paid more than 45 days after property_verified_date |
| e.paid.property_verified.small.pct_late_15 | 88.8 | % of small paid invoices paid more than 15 days after property_verified_date |
| e.paid.property_verified.small.pct_late_60 | 2.1 | % of small paid invoices paid more than 60 days after property_verified_date |
| e.paid.property_verified.medium.n_paid | 893.0 |  |
| e.paid.property_verified.medium.val_paid_ex_gst | 232712650.0 |  |
| e.paid.property_verified.medium.n_late | 54.0 |  |
| e.paid.property_verified.medium.val_late_ex_gst | 12634950.0 |  |
| e.paid.property_verified.medium.val_late_incl_gst | 14543082.0 |  |
| e.paid.property_verified.medium.n_late_60 | 15.0 |  |
| e.paid.property_verified.medium.val_late_60_ex_gst | 3784130.0 |  |
| e.paid.property_verified.medium.n_late_15 | 807.0 |  |
| e.paid.property_verified.medium.median_days_over_limit | 9.5 |  |
| e.paid.property_verified.medium.mean_days_to_pay | 25.68 |  |
| e.paid.property_verified.medium.pct_late | 6.0 | % of medium paid invoices paid more than 45 days after property_verified_date |
| e.paid.property_verified.medium.pct_late_15 | 90.4 | % of medium paid invoices paid more than 15 days after property_verified_date |
| e.paid.property_verified.medium.pct_late_60 | 1.7 | % of medium paid invoices paid more than 60 days after property_verified_date |
| e.paid.property_verified.notmsme.n_paid | 2918.0 |  |
| e.paid.property_verified.notmsme.val_paid_ex_gst | 789241460.0 |  |
| e.paid.property_verified.notmsme.n_late | 208.0 |  |
| e.paid.property_verified.notmsme.val_late_ex_gst | 60462000.0 |  |
| e.paid.property_verified.notmsme.val_late_incl_gst | 70175368.0 |  |
| e.paid.property_verified.notmsme.n_late_60 | 83.0 |  |
| e.paid.property_verified.notmsme.val_late_60_ex_gst | 20228080.0 |  |
| e.paid.property_verified.notmsme.n_late_15 | 2617.0 |  |
| e.paid.property_verified.notmsme.median_days_over_limit | 11.0 |  |
| e.paid.property_verified.notmsme.mean_days_to_pay | 26.31 |  |
| e.paid.property_verified.notmsme.pct_late | 7.1 | % of notmsme paid invoices paid more than 45 days after property_verified_date |
| e.paid.property_verified.notmsme.pct_late_15 | 89.7 | % of notmsme paid invoices paid more than 15 days after property_verified_date |
| e.paid.property_verified.notmsme.pct_late_60 | 2.8 | % of notmsme paid invoices paid more than 60 days after property_verified_date |
| e.paid.property_verified.unknown.n_paid | 1532.0 |  |
| e.paid.property_verified.unknown.val_paid_ex_gst | 408405810.0 |  |
| e.paid.property_verified.unknown.n_late | 99.0 |  |
| e.paid.property_verified.unknown.val_late_ex_gst | 25539490.0 |  |
| e.paid.property_verified.unknown.val_late_incl_gst | 29408450.0 |  |
| e.paid.property_verified.unknown.n_late_60 | 35.0 |  |
| e.paid.property_verified.unknown.val_late_60_ex_gst | 9238300.0 |  |
| e.paid.property_verified.unknown.n_late_15 | 1352.0 |  |
| e.paid.property_verified.unknown.median_days_over_limit | 9.0 |  |
| e.paid.property_verified.unknown.mean_days_to_pay | 25.61 |  |
| e.paid.property_verified.unknown.pct_late | 6.5 | % of unknown paid invoices paid more than 45 days after property_verified_date |
| e.paid.property_verified.unknown.pct_late_15 | 88.3 | % of unknown paid invoices paid more than 15 days after property_verified_date |
| e.paid.property_verified.unknown.pct_late_60 | 2.3 | % of unknown paid invoices paid more than 60 days after property_verified_date |
| e.paid.property_verified.microsmall_known.n_paid | 5106.0 |  |
| e.paid.property_verified.microsmall_known.val_paid_ex_gst | 1374815370.0 |  |
| e.paid.property_verified.microsmall_known.n_late | 305.0 |  |
| e.paid.property_verified.microsmall_known.val_late_ex_gst | 84896590.0 |  |
| e.paid.property_verified.microsmall_known.val_late_incl_gst | 99042181.0 |  |
| e.paid.property_verified.microsmall_known.n_late_60 | 126.0 |  |
| e.paid.property_verified.microsmall_known.val_late_60_ex_gst | 36102650.0 |  |
| e.paid.property_verified.microsmall_known.n_late_15 | 4492.0 |  |
| e.paid.property_verified.microsmall_known.median_days_over_limit | 12.0 |  |
| e.paid.property_verified.microsmall_known.mean_days_to_pay | 25.3 |  |
| e.paid.property_verified.microsmall_known.pct_late | 6.0 | % of microsmall_known paid invoices paid more than 45 days after property_verified_date |
| e.paid.property_verified.microsmall_known.pct_late_15 | 88.0 | % of microsmall_known paid invoices paid more than 15 days after property_verified_date |
| e.paid.property_verified.microsmall_known.pct_late_60 | 2.5 | % of microsmall_known paid invoices paid more than 60 days after property_verified_date |
| e.paid.property_verified.all_statuses.n_paid | 10449.0 |  |
| e.paid.property_verified.all_statuses.val_paid_ex_gst | 2805175290.0 |  |
| e.paid.property_verified.all_statuses.n_late | 666.0 |  |
| e.paid.property_verified.all_statuses.val_late_ex_gst | 183533030.0 |  |
| e.paid.property_verified.all_statuses.val_late_incl_gst | 213169081.0 |  |
| e.paid.property_verified.all_statuses.n_late_60 | 259.0 |  |
| e.paid.property_verified.all_statuses.val_late_60_ex_gst | 69353160.0 |  |
| e.paid.property_verified.all_statuses.n_late_15 | 9268.0 |  |
| e.paid.property_verified.all_statuses.median_days_over_limit | 11.0 |  |
| e.paid.property_verified.all_statuses.mean_days_to_pay | 25.66 |  |
| e.paid.property_verified.all_statuses.pct_late | 6.4 | % of all_statuses paid invoices paid more than 45 days after property_verified_date |
| e.paid.property_verified.all_statuses.pct_late_15 | 88.7 | % of all_statuses paid invoices paid more than 15 days after property_verified_date |
| e.paid.property_verified.all_statuses.pct_late_60 | 2.5 | % of all_statuses paid invoices paid more than 60 days after property_verified_date |
| e.paid.invoice.status_pct_late_min | 19.0 | lowest share paid over 45 days across the five statuses, clock invoice_date |
| e.paid.invoice.status_pct_late_max | 21.6 | highest share, clock invoice_date |
| e.paid.desk_received.status_pct_late_min | 9.3 | lowest share paid over 45 days across the five statuses, clock desk_received_date |
| e.paid.desk_received.status_pct_late_max | 12.7 | highest share, clock desk_received_date |
| e.paid.property_verified.status_pct_late_min | 5.2 | lowest share paid over 45 days across the five statuses, clock property_verified_date |
| e.paid.property_verified.status_pct_late_max | 7.1 | highest share, clock property_verified_date |
| e.sens15.invoice.pct_late_over_15 | 99.7 | % of known Micro/Small paid invoices paid more than 15 days after invoice_date |
| e.sens15.desk_received.pct_late_over_15 | 97.5 | % of known Micro/Small paid invoices paid more than 15 days after desk_received_date |
| e.sens15.property_verified.pct_late_over_15 | 88.0 | % of known Micro/Small paid invoices paid more than 15 days after property_verified_date |
| e.ye.invoice.micro.n_unpaid | 285 |  |
| e.ye.invoice.micro.n_past45 | 22 |  |
| e.ye.invoice.micro.val_past45_ex_gst | 6963060.0 |  |
| e.ye.invoice.micro.val_past45_incl_gst | 8126767.0 |  |
| e.ye.invoice.small.n_unpaid | 193 |  |
| e.ye.invoice.small.n_past45 | 17 |  |
| e.ye.invoice.small.val_past45_ex_gst | 9811570.0 |  |
| e.ye.invoice.small.val_past45_incl_gst | 11364106.0 |  |
| e.ye.invoice.medium.n_unpaid | 73 |  |
| e.ye.invoice.medium.n_past45 | 7 |  |
| e.ye.invoice.medium.val_past45_ex_gst | 1322900.0 |  |
| e.ye.invoice.medium.val_past45_incl_gst | 1561021.0 |  |
| e.ye.invoice.notmsme.n_unpaid | 260 |  |
| e.ye.invoice.notmsme.n_past45 | 25 |  |
| e.ye.invoice.notmsme.val_past45_ex_gst | 5555420.0 |  |
| e.ye.invoice.notmsme.val_past45_incl_gst | 6535255.0 |  |
| e.ye.invoice.unknown.n_unpaid | 144 |  |
| e.ye.invoice.unknown.n_past45 | 13 |  |
| e.ye.invoice.unknown.val_past45_ex_gst | 4026080.0 |  |
| e.ye.invoice.unknown.val_past45_incl_gst | 4556627.0 |  |
| e.ye.invoice.microsmall_known.n_unpaid | 478 |  |
| e.ye.invoice.microsmall_known.n_past45 | 39 |  |
| e.ye.invoice.microsmall_known.val_past45_ex_gst | 16774630.0 |  |
| e.ye.invoice.microsmall_known.val_past45_incl_gst | 19490873.0 |  |
| e.ye.desk_received.micro.n_unpaid | 260 |  |
| e.ye.desk_received.micro.n_past45 | 16 |  |
| e.ye.desk_received.micro.val_past45_ex_gst | 5286070.0 |  |
| e.ye.desk_received.micro.val_past45_incl_gst | 6237563.0 |  |
| e.ye.desk_received.small.n_unpaid | 178 |  |
| e.ye.desk_received.small.n_past45 | 9 |  |
| e.ye.desk_received.small.val_past45_ex_gst | 5289500.0 |  |
| e.ye.desk_received.small.val_past45_incl_gst | 6159289.0 |  |
| e.ye.desk_received.medium.n_unpaid | 62 |  |
| e.ye.desk_received.medium.n_past45 | 3 |  |
| e.ye.desk_received.medium.val_past45_ex_gst | 919450.0 |  |
| e.ye.desk_received.medium.val_past45_incl_gst | 1084950.0 |  |
| e.ye.desk_received.notmsme.n_unpaid | 232 |  |
| e.ye.desk_received.notmsme.n_past45 | 18 |  |
| e.ye.desk_received.notmsme.val_past45_ex_gst | 3996800.0 |  |
| e.ye.desk_received.notmsme.val_past45_incl_gst | 4696083.0 |  |
| e.ye.desk_received.unknown.n_unpaid | 126 |  |
| e.ye.desk_received.unknown.n_past45 | 12 |  |
| e.ye.desk_received.unknown.val_past45_ex_gst | 3559760.0 |  |
| e.ye.desk_received.unknown.val_past45_incl_gst | 4090307.0 |  |
| e.ye.desk_received.microsmall_known.n_unpaid | 438 |  |
| e.ye.desk_received.microsmall_known.n_past45 | 25 |  |
| e.ye.desk_received.microsmall_known.val_past45_ex_gst | 10575570.0 |  |
| e.ye.desk_received.microsmall_known.val_past45_incl_gst | 12396852.0 |  |
| e.ye.property_verified.micro.n_unpaid | 232 |  |
| e.ye.property_verified.micro.n_past45 | 10 |  |
| e.ye.property_verified.micro.val_past45_ex_gst | 2579630.0 |  |
| e.ye.property_verified.micro.val_past45_incl_gst | 3043964.0 |  |
| e.ye.property_verified.small.n_unpaid | 157 |  |
| e.ye.property_verified.small.n_past45 | 3 |  |
| e.ye.property_verified.small.val_past45_ex_gst | 2605870.0 |  |
| e.ye.property_verified.small.val_past45_incl_gst | 3074927.0 |  |
| e.ye.property_verified.medium.n_unpaid | 59 |  |
| e.ye.property_verified.medium.n_past45 | 2 |  |
| e.ye.property_verified.medium.val_past45_ex_gst | 23260.0 |  |
| e.ye.property_verified.medium.val_past45_incl_gst | 27446.0 |  |
| e.ye.property_verified.notmsme.n_unpaid | 212 |  |
| e.ye.property_verified.notmsme.n_past45 | 9 |  |
| e.ye.property_verified.notmsme.val_past45_ex_gst | 769020.0 |  |
| e.ye.property_verified.notmsme.val_past45_incl_gst | 907443.0 |  |
| e.ye.property_verified.unknown.n_unpaid | 115 |  |
| e.ye.property_verified.unknown.n_past45 | 6 |  |
| e.ye.property_verified.unknown.val_past45_ex_gst | 1729440.0 |  |
| e.ye.property_verified.unknown.val_past45_incl_gst | 1930529.0 |  |
| e.ye.property_verified.microsmall_known.n_unpaid | 389 |  |
| e.ye.property_verified.microsmall_known.n_past45 | 13 |  |
| e.ye.property_verified.microsmall_known.val_past45_ex_gst | 5185500.0 |  |
| e.ye.property_verified.microsmall_known.val_past45_incl_gst | 6118891.0 |  |
| e.now.invoice.micro.n_unpaid | 54 |  |
| e.now.invoice.micro.n_past45 | 26 |  |
| e.now.invoice.micro.val_past45_ex_gst | 11183520.0 |  |
| e.now.invoice.micro.val_past45_incl_gst | 12965394.0 |  |
| e.now.invoice.small.n_unpaid | 34 |  |
| e.now.invoice.small.n_past45 | 17 |  |
| e.now.invoice.small.val_past45_ex_gst | 6689180.0 |  |
| e.now.invoice.small.val_past45_incl_gst | 7893233.0 |  |
| e.now.invoice.medium.n_unpaid | 10 |  |
| e.now.invoice.medium.n_past45 | 4 |  |
| e.now.invoice.medium.val_past45_ex_gst | 1137200.0 |  |
| e.now.invoice.medium.val_past45_incl_gst | 1341896.0 |  |
| e.now.invoice.notmsme.n_unpaid | 51 |  |
| e.now.invoice.notmsme.n_past45 | 26 |  |
| e.now.invoice.notmsme.val_past45_ex_gst | 7191960.0 |  |
| e.now.invoice.notmsme.val_past45_incl_gst | 8454374.0 |  |
| e.now.invoice.unknown.n_unpaid | 31 |  |
| e.now.invoice.unknown.n_past45 | 12 |  |
| e.now.invoice.unknown.val_past45_ex_gst | 2687570.0 |  |
| e.now.invoice.unknown.val_past45_incl_gst | 3059171.0 |  |
| e.now.invoice.microsmall_known.n_unpaid | 88 |  |
| e.now.invoice.microsmall_known.n_past45 | 43 |  |
| e.now.invoice.microsmall_known.val_past45_ex_gst | 17872700.0 |  |
| e.now.invoice.microsmall_known.val_past45_incl_gst | 20858627.0 |  |
| e.now.desk_received.micro.n_unpaid | 54 |  |
| e.now.desk_received.micro.n_past45 | 17 |  |
| e.now.desk_received.micro.val_past45_ex_gst | 7468630.0 |  |
| e.now.desk_received.micro.val_past45_incl_gst | 8600532.0 |  |
| e.now.desk_received.small.n_unpaid | 34 |  |
| e.now.desk_received.small.n_past45 | 13 |  |
| e.now.desk_received.small.val_past45_ex_gst | 6221990.0 |  |
| e.now.desk_received.small.val_past45_incl_gst | 7341948.0 |  |
| e.now.desk_received.medium.n_unpaid | 10 |  |
| e.now.desk_received.medium.n_past45 | 3 |  |
| e.now.desk_received.medium.val_past45_ex_gst | 1021990.0 |  |
| e.now.desk_received.medium.val_past45_incl_gst | 1205948.0 |  |
| e.now.desk_received.notmsme.n_unpaid | 51 |  |
| e.now.desk_received.notmsme.n_past45 | 16 |  |
| e.now.desk_received.notmsme.val_past45_ex_gst | 4800160.0 |  |
| e.now.desk_received.notmsme.val_past45_incl_gst | 5632050.0 |  |
| e.now.desk_received.unknown.n_unpaid | 31 |  |
| e.now.desk_received.unknown.n_past45 | 10 |  |
| e.now.desk_received.unknown.val_past45_ex_gst | 2436160.0 |  |
| e.now.desk_received.unknown.val_past45_incl_gst | 2762507.0 |  |
| e.now.desk_received.microsmall_known.n_unpaid | 88 |  |
| e.now.desk_received.microsmall_known.n_past45 | 30 |  |
| e.now.desk_received.microsmall_known.val_past45_ex_gst | 13690620.0 |  |
| e.now.desk_received.microsmall_known.val_past45_incl_gst | 15942480.0 |  |
| e.now.property_verified.micro.n_unpaid | 54 |  |
| e.now.property_verified.micro.n_past45 | 9 |  |
| e.now.property_verified.micro.val_past45_ex_gst | 3588820.0 |  |
| e.now.property_verified.micro.val_past45_incl_gst | 4145164.0 |  |
| e.now.property_verified.small.n_unpaid | 34 |  |
| e.now.property_verified.small.n_past45 | 8 |  |
| e.now.property_verified.small.val_past45_ex_gst | 4255520.0 |  |
| e.now.property_verified.small.val_past45_incl_gst | 5021513.0 |  |
| e.now.property_verified.medium.n_unpaid | 10 |  |
| e.now.property_verified.medium.n_past45 | 2 |  |
| e.now.property_verified.medium.val_past45_ex_gst | 648430.0 |  |
| e.now.property_verified.medium.val_past45_incl_gst | 765147.0 |  |
| e.now.property_verified.notmsme.n_unpaid | 51 |  |
| e.now.property_verified.notmsme.n_past45 | 9 |  |
| e.now.property_verified.notmsme.val_past45_ex_gst | 1466810.0 |  |
| e.now.property_verified.notmsme.val_past45_incl_gst | 1698698.0 |  |
| e.now.property_verified.unknown.n_unpaid | 31 |  |
| e.now.property_verified.unknown.n_past45 | 6 |  |
| e.now.property_verified.unknown.val_past45_ex_gst | 1110740.0 |  |
| e.now.property_verified.unknown.val_past45_incl_gst | 1229160.0 |  |
| e.now.property_verified.microsmall_known.n_unpaid | 88 |  |
| e.now.property_verified.microsmall_known.n_past45 | 17 |  |
| e.now.property_verified.microsmall_known.val_past45_ex_gst | 7844340.0 |  |
| e.now.property_verified.microsmall_known.val_past45_incl_gst | 9166677.0 |  |
| e.d03.micro.n | 40 |  |
| e.d03.micro.val_ex_gst | 11981880.0 |  |
| e.d03.small.n | 22 |  |
| e.d03.small.val_ex_gst | 6165200.0 |  |
| e.d03.medium.n | 11 |  |
| e.d03.medium.val_ex_gst | 2887790.0 |  |
| e.d03.notmsme.n | 25 |  |
| e.d03.notmsme.val_ex_gst | 5784460.0 |  |
| e.d03.unknown.n | 12 |  |
| e.d03.unknown.val_ex_gst | 4800680.0 |  |
| e.scen.paid_late.invoice.n_late.low | 1031.0 |  |
| e.scen.paid_late.invoice.n_late.central | 1200.3 |  |
| e.scen.paid_late.invoice.n_late.high | 1322.0 |  |
| e.scen.paid_late.invoice.val_late_ex_gst.low | 325042190.0 |  |
| e.scen.paid_late.invoice.val_late_ex_gst.central | 377870083.9 |  |
| e.scen.paid_late.invoice.val_late_ex_gst.high | 415825260.0 |  |
| e.scen.paid_late.invoice.val_late_incl_gst.low | 380244106.0 |  |
| e.scen.paid_late.invoice.val_late_incl_gst.central | 441756596.9 |  |
| e.scen.paid_late.invoice.val_late_incl_gst.high | 485951382.0 |  |
| e.scen.unpaid_ye.invoice.n_past45.low | 39.0 |  |
| e.scen.unpaid_ye.invoice.n_past45.central | 46.6 |  |
| e.scen.unpaid_ye.invoice.n_past45.high | 52.0 |  |
| e.scen.unpaid_ye.invoice.val_past45_ex_gst.low | 16774630.0 |  |
| e.scen.unpaid_ye.invoice.val_past45_ex_gst.central | 19117460.3 |  |
| e.scen.unpaid_ye.invoice.val_past45_ex_gst.high | 20800710.0 |  |
| e.scen.unpaid_ye.invoice.val_past45_incl_gst.low | 19490873.0 |  |
| e.scen.unpaid_ye.invoice.val_past45_incl_gst.central | 22142435.8 |  |
| e.scen.unpaid_ye.invoice.val_past45_incl_gst.high | 24047500.0 |  |
| e.scen.unpaid_now.invoice.n_past45.low | 43.0 |  |
| e.scen.unpaid_now.invoice.n_past45.central | 50.0 |  |
| e.scen.unpaid_now.invoice.n_past45.high | 55.0 |  |
| e.scen.unpaid_now.invoice.val_past45_ex_gst.low | 17872700.0 |  |
| e.scen.unpaid_now.invoice.val_past45_ex_gst.central | 19436633.3 |  |
| e.scen.unpaid_now.invoice.val_past45_ex_gst.high | 20560270.0 |  |
| e.scen.unpaid_now.invoice.val_past45_incl_gst.low | 20858627.0 |  |
| e.scen.unpaid_now.invoice.val_past45_incl_gst.central | 22638799.9 |  |
| e.scen.unpaid_now.invoice.val_past45_incl_gst.high | 23917798.0 |  |
| e.scen.paid_late.desk_received.n_late.low | 530.0 |  |
| e.scen.paid_late.desk_received.n_late.central | 619.6 |  |
| e.scen.paid_late.desk_received.n_late.high | 684.0 |  |
| e.scen.paid_late.desk_received.val_late_ex_gst.low | 168338320.0 |  |
| e.scen.paid_late.desk_received.val_late_ex_gst.central | 193149744.1 |  |
| e.scen.paid_late.desk_received.val_late_ex_gst.high | 210975970.0 |  |
| e.scen.paid_late.desk_received.val_late_incl_gst.low | 197228402.0 |  |
| e.scen.paid_late.desk_received.val_late_incl_gst.central | 226033002.7 |  |
| e.scen.paid_late.desk_received.val_late_incl_gst.high | 246728200.0 |  |
| e.scen.unpaid_ye.desk_received.n_past45.low | 25.0 |  |
| e.scen.unpaid_ye.desk_received.n_past45.central | 32.0 |  |
| e.scen.unpaid_ye.desk_received.n_past45.high | 37.0 |  |
| e.scen.unpaid_ye.desk_received.val_past45_ex_gst.low | 10575570.0 |  |
| e.scen.unpaid_ye.desk_received.val_past45_ex_gst.central | 12647042.4 |  |
| e.scen.unpaid_ye.desk_received.val_past45_ex_gst.high | 14135330.0 |  |
| e.scen.unpaid_ye.desk_received.val_past45_incl_gst.low | 12396852.0 |  |
| e.scen.unpaid_ye.desk_received.val_past45_incl_gst.central | 14777056.9 |  |
| e.scen.unpaid_ye.desk_received.val_past45_incl_gst.high | 16487159.0 |  |
| e.scen.unpaid_now.desk_received.n_past45.low | 30.0 |  |
| e.scen.unpaid_now.desk_received.n_past45.central | 35.8 |  |
| e.scen.unpaid_now.desk_received.n_past45.high | 40.0 |  |
| e.scen.unpaid_now.desk_received.val_past45_ex_gst.low | 13690620.0 |  |
| e.scen.unpaid_now.desk_received.val_past45_ex_gst.central | 15108254.4 |  |
| e.scen.unpaid_now.desk_received.val_past45_ex_gst.high | 16126780.0 |  |
| e.scen.unpaid_now.desk_received.val_past45_incl_gst.low | 15942480.0 |  |
| e.scen.unpaid_now.desk_received.val_past45_incl_gst.central | 17550020.1 |  |
| e.scen.unpaid_now.desk_received.val_past45_incl_gst.high | 18704987.0 |  |
| e.scen.paid_late.property_verified.n_late.low | 305.0 |  |
| e.scen.paid_late.property_verified.n_late.central | 362.6 |  |
| e.scen.paid_late.property_verified.n_late.high | 404.0 |  |
| e.scen.paid_late.property_verified.val_late_ex_gst.low | 84896590.0 |  |
| e.scen.paid_late.property_verified.val_late_ex_gst.central | 99758364.0 |  |
| e.scen.paid_late.property_verified.val_late_ex_gst.high | 110436080.0 |  |
| e.scen.paid_late.property_verified.val_late_incl_gst.low | 99042181.0 |  |
| e.scen.paid_late.property_verified.val_late_incl_gst.central | 116155355.0 |  |
| e.scen.paid_late.property_verified.val_late_incl_gst.high | 128450631.0 |  |
| e.scen.unpaid_ye.property_verified.n_past45.low | 13.0 |  |
| e.scen.unpaid_ye.property_verified.n_past45.central | 16.5 |  |
| e.scen.unpaid_ye.property_verified.n_past45.high | 19.0 |  |
| e.scen.unpaid_ye.property_verified.val_past45_ex_gst.low | 5185500.0 |  |
| e.scen.unpaid_ye.property_verified.val_past45_ex_gst.central | 6191884.5 |  |
| e.scen.unpaid_ye.property_verified.val_past45_ex_gst.high | 6914940.0 |  |
| e.scen.unpaid_ye.property_verified.val_past45_incl_gst.low | 6118891.0 |  |
| e.scen.unpaid_ye.property_verified.val_past45_incl_gst.central | 7242291.9 |  |
| e.scen.unpaid_ye.property_verified.val_past45_incl_gst.high | 8049420.0 |  |
| e.scen.unpaid_now.property_verified.n_past45.low | 17.0 |  |
| e.scen.unpaid_now.property_verified.n_past45.central | 20.5 |  |
| e.scen.unpaid_now.property_verified.n_past45.high | 23.0 |  |
| e.scen.unpaid_now.property_verified.val_past45_ex_gst.low | 7844340.0 |  |
| e.scen.unpaid_now.property_verified.val_past45_ex_gst.central | 8490694.6 |  |
| e.scen.unpaid_now.property_verified.val_past45_ex_gst.high | 8955080.0 |  |
| e.scen.unpaid_now.property_verified.val_past45_incl_gst.low | 9166677.0 |  |
| e.scen.unpaid_now.property_verified.val_past45_incl_gst.central | 9881941.8 |  |
| e.scen.unpaid_now.property_verified.val_past45_incl_gst.high | 10395837.0 |  |
| open.micro.n | 54 | open invoices, Micro |
| open.micro.n_breached_desk | 17 | ...already past 45 days from desk receipt |
| open.micro.n_breached_ver | 9 | ...already past 45 days from property verification |
| open.micro.n_within14_desk | 19 | ...not yet past, 14 days or fewer left (desk clock) |
| open.micro.n_within14_ver | 21 |  |
| open.micro.n_posted | 23 | ...with status Posted, so treasury can pay them |
| open.small.n | 34 | open invoices, Small |
| open.small.n_breached_desk | 13 | ...already past 45 days from desk receipt |
| open.small.n_breached_ver | 8 | ...already past 45 days from property verification |
| open.small.n_within14_desk | 13 | ...not yet past, 14 days or fewer left (desk clock) |
| open.small.n_within14_ver | 11 |  |
| open.small.n_posted | 21 | ...with status Posted, so treasury can pay them |
| open.unknown.n | 31 | open invoices, Unknown |
| open.unknown.n_breached_desk | 10 | ...already past 45 days from desk receipt |
| open.unknown.n_breached_ver | 6 | ...already past 45 days from property verification |
| open.unknown.n_within14_desk | 6 | ...not yet past, 14 days or fewer left (desk clock) |
| open.unknown.n_within14_ver | 6 |  |
| open.unknown.n_posted | 11 | ...with status Posted, so treasury can pay them |
| open.ms_unknown.n | 119 | open Micro, Small and Unknown invoices |
| open.ms_unknown.n_not_yet_breached_desk | 79 |  |
| open.ms_unknown.n_no_run_left_desk | 2 | not yet past 45 days from desk, but no Tuesday or Friday payment run left before the deadline |
| open.ms_unknown.n_not_yet_breached_posted | 43 | ...of those not yet past, with status Posted |
| open.ms_unknown.near_max_days_left | 37 |  |
| open.next_run | 2026-05-01 | first payment run after 30 Apr 2026 |

<!-- END 06_msme_exposure.py -->

<!-- BEGIN 07_workflow_map.py -->

### Figures from `analysis/07_workflow_map.py` (used in notes/workflows.md and notes/workflows/swimlane.mmd. The other numbers in workflows.md are read by figure id from the other scripts' figures files)

Script: `analysis/07_workflow_map.py`. Output: `analysis/out/figures_workflows.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
python -I analysis/02_stage_times.py
python -I analysis/04_query_forensics.py
python -I analysis/06_msme_exposure.py
python -I analysis/05_claims_tested.py
python -I analysis/07_workflow_map.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| w.dup.P1H1.queries | 46 | queries raised by head office on P1/H1 items (rule R08) |
| w.dup.P2H2.queries | 12 | queries raised by head office on P2/H2 items (rule R13) |
| w.dup.P4H4.queries | 66 | queries raised by head office on P4/H4 items (rule R17) |
| w.dup.P5H5.queries | 17 | queries raised by head office on P5/H5 items (rule R11) |
| w.dup.P6H6.queries | 51 | queries raised by head office on P6/H6 items (rule R23) |
| w.dup.P7H7.queries | 52 | queries raised by head office on P7/H7 items (rule R22) |
| w.dup.P8H8.queries | 68 | queries raised by head office on P8/H8 items (rule R21) |
| w.dup.P9H9.queries | 71 | queries raised by head office on P9/H9 items (rule R20) |
| w.dup.queries_total | 383 | queries on items the property checklist already requires |
| w.dup.pairs | 8 | checks that appear on both the property and the head-office checklist |
| w.q.gl | 71 | queries under rule R03 |
| w.q.costcentre | 76 | queries under rule R02 |
| w.q.wbs | 61 | queries under rule R04 |
| w.q.wo_expired | 107 | queries under rule R26 |
| w.q.wo_balance | 96 | queries under rule R25 |
| w.q.wo_quantity | 105 | queries under rule R24 |
| w.q.wo_bal_other | 18 | queries under rule R10 |
| w.q.po_not_released | 12 | queries under rule R12 |
| w.q.rate_agreed_by_phone | 66 | queries under rule R17 |
| w.q.overtime | 72 | queries under rule R16 |
| w.q.wo_all | 338 | work-order balance, quantity, expiry and PO queries together |
| w.diagram.messages | 32 | numbered arrows in the swimlane |

<!-- END 07_workflow_map.py -->

<!-- BEGIN 08_problem_ranking.py -->

### Figures from `analysis/08_problem_ranking.py` (used in notes/problem.md. The other numbers in problem.md are read by figure id from the other scripts' figures files)

Script: `analysis/08_problem_ranking.py`. Output: `analysis/out/figures_problem.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
python -I analysis/02_stage_times.py
python -I analysis/04_query_forensics.py
python -I analysis/06_msme_exposure.py
python -I analysis/05_claims_tested.py
python -I analysis/08_problem_ranking.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| p.n | 10449.0 | paid invoices analysed |
| p.pay.schedule_wait_lead0 | 2.28 | mean days from posting to the first run, run list closing 0 day(s) before the run |
| p.pay.excess_lead0 | 3.72 | mean days paid later than that run, run list closing 0 day(s) before |
| p.pay.share_late_lead0 | 70.98 | % of bills paid later than that run, list closing 0 day(s) before |
| p.pay.schedule_wait_lead1 | 3.3 | mean days from posting to the first run, run list closing 1 day(s) before the run |
| p.pay.excess_lead1 | 2.75 | mean days paid later than that run, run list closing 1 day(s) before |
| p.pay.share_late_lead1 | 54.19 | % of bills paid later than that run, list closing 1 day(s) before |
| p.pay.schedule_wait_lead2 | 4.31 | mean days from posting to the first run, run list closing 2 day(s) before the run |
| p.pay.excess_lead2 | 1.97 | mean days paid later than that run, run list closing 2 day(s) before |
| p.pay.share_late_lead2 | 39.38 | % of bills paid later than that run, list closing 2 day(s) before |
| p.pay.actual_wait | 5.99 | mean days from posting to payment |
| p.pay.per_missed_bill | 5.24 | mean days late per bill that missed the next run (list lead 0) |
| p.courier.lag_friday_only | 4.98 | mean days from signature to head office with arrivals: friday_only |
| p.courier.lag_tue_fri | 3.28 | mean days from signature to head office with arrivals: tue_fri |
| p.courier.lag_mon_wed_fri | 2.72 | mean days from signature to head office with arrivals: mon_wed_fri |
| p.courier.lag_daily | 2.0 | mean days from signature to head office with arrivals: daily |
| p.courier.save_tue_fri | 1.7 | days off the mean with a second weekly arrival (Tue and Fri) |
| p.courier.save_daily | 2.98 | days off the mean with a daily arrival |
| p.queue.ap1_bills | 4223.0 | paid invoices handled by AP-1 |
| p.queue.ap1_share_pct | 40.42 | % of paid invoices handled by AP-1 |
| p.queue.ap1_wait | 11.27 | mean days AP-1's bills wait for pick-up |
| p.queue.others_wait | 7.2 | mean days the other four verifiers' bills wait |
| p.queue.gap_per_bill | 4.07 | extra days AP-1's bills wait |
| p.queue.saving | 1.65 | days off the mean if AP-1's bills waited like the others' |
| p.queue.wait_lightest_fridays | 8.32 | mean wait in the quarter of Fridays with the fewest bills |
| p.queue.wait_heaviest_fridays | 9.0 | mean wait in the quarter of Fridays with the most bills |
| p.queue.bills_lightest_fridays | 116.07 | mean bills arriving on those lightest Fridays |
| p.queue.bills_heaviest_fridays | 278.43 | mean bills arriving on those heaviest Fridays |
| p.query.days_on_mean | 2.75 | query-open days added to the mean of all paid invoices |
| p.query.pct_bills | 12.52 | % of paid invoices with a query |
| p.query.vendor.days_on_mean | 1.17 | query-open days on the mean, vendor-side |
| p.query.vendor.pct_bills | 5.32 | % of paid invoices with a vendor-side query |
| p.query.property.days_on_mean | 0.77 | query-open days on the mean, property-side |
| p.query.property.pct_bills | 3.62 | % of paid invoices with a property-side query |
| p.query.procurement.days_on_mean | 0.64 | query-open days on the mean, procurement-side |
| p.query.procurement.pct_bills | 2.87 | % of paid invoices with a procurement-side query |
| p.query.head-office.days_on_mean | 0.17 | query-open days on the mean, head-office-side |
| p.query.head-office.pct_bills | 0.71 | % of paid invoices with a head-office-side query |
| p.query.top_cause_days_on_mean | 0.64 | largest single query category: WO balance or validity |
| p.query.top_cause_pct_bills | 2.87 | % of paid invoices with a WO balance or validity query |
| p.vendor_ceiling | 7.53 | vendor-to-desk days plus vendor-side query days: the most a portal could touch |
| p.typing.pct_of_total | 4.2 | AP verification (the ceiling for typing) as % of the mean days to pay |
| p.flow.low | 5.32 | days off the mean: AP-1 queue + payment run (list lead 2) + second weekly courier |
| p.flow.high | 8.35 | days off the mean: AP-1 queue + payment run (list lead 0) + daily courier |
| p.flow.low_pct | 14.13 | same, as % of the mean |
| p.flow.high_pct | 22.18 | same, as % of the mean |
| p.head_office_fix.low | 3.62 | days off the mean: AP-1 queue + payment run (list lead 2), the two proposed first |
| p.head_office_fix.high | 5.37 | same, payment run with list lead 0 |
| p.head_office_fix.low_pct | 9.62 |  |
| p.head_office_fix.high_pct | 14.27 |  |
| p.msme.late_desk_base | 530.0 | known Micro/Small paid invoices over 45 days from desk receipt |
| p.msme.late_desk_after_pay | 430.0 | ...if the payment-run fix (list lead 2) had applied |
| p.msme.late_desk_after_queue | 447.0 | ...if the AP-1 queue fix had applied |
| p.msme.late_desk_after_both | 366.0 | ...if both first fixes had applied |
| p.msme.late_desk_after_all3 | 315.0 | ...if all three flow fixes had applied |
| p.owner.ap_lead.ceiling | 10.59 | central AP lead: days on the mean that the causes it owns could take at most (verifier wait, head-office queries, typing) |
| p.owner.property.ceiling | 12.89 | property heads and executives: days on the mean that the causes they own could take at most (courier, signature, checks and service entry, property-side queries) |

<!-- END 08_problem_ranking.py -->

<!-- BEGIN 09_options.py -->

### Figures from `analysis/09_options.py` (used in notes/options.md. Build hours are my estimates and the time budget is an assumption, both stated in the note; the other numbers are read by figure id from the other scripts' figures files)

Script: `analysis/09_options.py`. Output: `analysis/out/figures_options.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
python -I analysis/02_stage_times.py
python -I analysis/04_query_forensics.py
python -I analysis/06_msme_exposure.py
python -I analysis/05_claims_tested.py
python -I analysis/08_problem_ranking.py
python -I analysis/09_options.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| o.n | 10449.0 | paid invoices analysed |
| o.hours.clock | 30.067 | hours from Fri 16 Oct 15:56 IST to Sat 17 Oct 22:00 IST |
| o.hours.sleep | 8.0 | assumed sleep |
| o.hours.life | 5.0 | assumed meals, breaks and everything else |
| o.hours.slack | 3.0 | assumed slack for debugging, repo set-up and the chat-history export |
| o.hours.budget | 14.0 | build hours available by Saturday 10 pm, after the three deductions |
| o.pre.A.bills | 201.0 | paid invoices with a query the pre-flight check could catch, layers A |
| o.pre.A.pct | 1.924 |  |
| o.pre.A.per_bill | 14.771 | days saved per caught query, layers A |
| o.pre.A.days | 0.284 | days off the mean, layers A |
| o.pre.A.days_with_scan | 0.238 | days off the mean if scan-first has already removed the courier lag, layers A |
| o.pre.AB.bills | 403.0 | paid invoices with a query the pre-flight check could catch, layers AB |
| o.pre.AB.pct | 3.857 |  |
| o.pre.AB.per_bill | 14.849 | days saved per caught query, layers AB |
| o.pre.AB.days | 0.573 | days off the mean, layers AB |
| o.pre.AB.days_with_scan | 0.478 | days off the mean if scan-first has already removed the courier lag, layers AB |
| o.pre.ABC.bills | 865.0 | paid invoices with a query the pre-flight check could catch, layers ABC |
| o.pre.ABC.pct | 8.278 |  |
| o.pre.ABC.per_bill | 14.749 | days saved per caught query, layers ABC |
| o.pre.ABC.days | 1.221 | days off the mean, layers ABC |
| o.pre.ABC.days_with_scan | 1.019 | days off the mean if scan-first has already removed the courier lag, layers ABC |
| o.wo.expiry_bills | 93.0 |  |
| o.wo.expiry_pct | 0.89 |  |
| o.wo.expiry_days | 0.216 | query-open days on the mean, work-order expiry queries |
| o.wo.all_bills | 300.0 |  |
| o.wo.all_pct | 2.871 |  |
| o.wo.all_days | 0.638 | query-open days on the mean, all work-order queries |
| o.att.manpower_bills | 4840.0 |  |
| o.att.manpower_pct | 46.32 |  |
| o.att.manpower_check_days | 8.075 | mean days desk to verified, manpower bills |
| o.att.other_check_days | 3.513 | mean days desk to verified, all other bills |
| o.att.excess | 4.562 | extra days manpower bills spend in the property check |
| o.att.days_high | 2.113 | days off the mean if the whole excess went |
| o.att.days_low | 0.528 | 25% of the excess |
| o.att.days_central | 1.056 | 50% of the excess |
| o.queue.bills | 8620.0 | paid invoices that are AP-1's or are paid after a later run than the next |
| o.queue.pct | 82.496 |  |
| o.portal.adopt | 9.0 | survey: % of vendors preferring a portal |
| o.portal.days | 0.572 | 9% x vendor-to-desk days |
| o.portal.bills | 940.0 | bills affected, Vendor portal |
| o.ocr.days | 0.158 | AP lead's reported 10% x AP verification days |
| o.scan.days | 4.98 | courier lag removed from the booking path |
| o.tracker.low | 3.62 | conditional days if the AP lead and treasury act on it, conservative |
| o.tracker.high | 5.37 | same, upper end |
| o.pair.low | 5.32 | tracker as work queue plus a second weekly courier, conservative |
| o.pair.high | 8.35 | tracker as work queue plus a daily courier, upper end |
| o.pair.low_pct | 14.134 |  |
| o.pair.high_pct | 22.184 |  |
| o.scan.central | 4.98 |  |
| o.scan.low | 0.0 |  |
| o.scan.high | 4.98 |  |
| o.scan.hours | 10.0 | estimated build hours, Scan-first, original later |
| o.scan.bills | 10449.0 | bills affected, Scan-first, original later |
| o.scan.per_affected | 4.98 | central days per affected bill, Scan-first, original later |
| o.scan.days_per_hour | 0.498 | central days saved per build hour, Scan-first, original later |
| o.track4b.central | 3.62 |  |
| o.track4b.low | 0.0 |  |
| o.track4b.high | 5.37 |  |
| o.track4b.hours | 11.5 | estimated build hours, Live tracker as a work queue (extension of option 4) |
| o.track4b.bills | 8620.0 | bills affected, Live tracker as a work queue (extension of option 4) |
| o.track4b.per_affected | 4.388 | central days per affected bill, Live tracker as a work queue (extension of option 4) |
| o.track4b.days_per_hour | 0.315 | central days saved per build hour, Live tracker as a work queue (extension of option 4) |
| o.courier.central | 2.98 |  |
| o.courier.low | 1.7 |  |
| o.courier.high | 2.98 |  |
| o.courier.hours | 1.0 | estimated build hours, Daily courier |
| o.courier.bills | 10449.0 | bills affected, Daily courier |
| o.courier.per_affected | 2.98 | central days per affected bill, Daily courier |
| o.courier.days_per_hour | 2.98 | central days saved per build hour, Daily courier |
| o.att.central | 1.056 |  |
| o.att.low | 0.528 |  |
| o.att.high | 2.113 |  |
| o.att.hours | 7.0 | estimated build hours, Attendance three-way match |
| o.att.bills | 4840.0 | bills affected, Attendance three-way match |
| o.att.per_affected | 2.28 | central days per affected bill, Attendance three-way match |
| o.att.days_per_hour | 0.151 | central days saved per build hour, Attendance three-way match |
| o.pre.central | 0.573 |  |
| o.pre.low | 0.284 |  |
| o.pre.high | 1.221 |  |
| o.pre.hours | 14.5 | estimated build hours, Pre-flight checker at intake |
| o.pre.bills | 403.0 | bills affected, Pre-flight checker at intake |
| o.pre.per_affected | 14.857 | central days per affected bill, Pre-flight checker at intake |
| o.pre.days_per_hour | 0.04 | central days saved per build hour, Pre-flight checker at intake |
| o.portal.central | 0.572 |  |
| o.portal.low | 0.0 |  |
| o.portal.high | 6.36 |  |
| o.portal.hours | 17.0 | estimated build hours, Vendor portal |
| o.portal.per_affected | 6.358 | central days per affected bill, Vendor portal |
| o.portal.days_per_hour | 0.034 | central days saved per build hour, Vendor portal |
| o.wo.central | 0.216 |  |
| o.wo.low | 0.0 |  |
| o.wo.high | 0.638 |  |
| o.wo.hours | 6.0 | estimated build hours, Work-order runway alert |
| o.wo.bills | 93.0 | bills affected, Work-order runway alert |
| o.wo.per_affected | 24.269 | central days per affected bill, Work-order runway alert |
| o.wo.days_per_hour | 0.036 | central days saved per build hour, Work-order runway alert |
| o.ocr.central | 0.158 |  |
| o.ocr.low | 0.0 |  |
| o.ocr.high | 1.58 |  |
| o.ocr.hours | 10.5 | estimated build hours, OCR at head office |
| o.ocr.bills | 10449.0 | bills affected, OCR at head office |
| o.ocr.per_affected | 0.158 | central days per affected bill, OCR at head office |
| o.ocr.days_per_hour | 0.015 | central days saved per build hour, OCR at head office |
| o.track.central | 0.0 |  |
| o.track.low | 0.0 |  |
| o.track.high | 0.0 |  |
| o.track.hours | 7.5 | estimated build hours, Live tracker with a vendor status message (as listed) |
| o.track.bills | 10449.0 | bills affected, Live tracker with a vendor status message (as listed) |
| o.track.per_affected | 0.0 | central days per affected bill, Live tracker with a vendor status message (as listed) |
| o.track.days_per_hour | 0.0 | central days saved per build hour, Live tracker with a vendor status message (as listed) |
| o.pair.hours | 12.5 | hours for the recommended pair |
| o.pair.spare | 1.5 | hours left in the budget |

<!-- END 09_options.py -->

<!-- BEGIN 10_solution_design.py -->

### Figures from `analysis/10_solution_design.py` (used in notes/solution-design.md. The check classes and build hours are my judgement and estimates, stated in the note; four inbox bills were read by eye)

Script: `analysis/10_solution_design.py`. Output: `analysis/out/figures_design.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
python -I analysis/02_stage_times.py
python -I analysis/04_query_forensics.py
python -I analysis/06_msme_exposure.py
python -I analysis/05_claims_tested.py
python -I analysis/08_problem_ranking.py
python -I analysis/09_levers.py
python -I analysis/09_options.py
python -I analysis/10_solution_design.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| d.checks.I | 6.0 | checks in class I: At intake, from the bill and the SAP extract |
| d.checks.X | 5.0 | checks in class X: At intake, but needs data not in the pack |
| d.checks.PK | 8.0 | checks in class PK: Needs the rest of the packet scanned (the paper) |
| d.checks.L | 6.0 | checks in class L: Not at intake: a later step or another source |
| d.queries.I | 618.0 | queries last year on checks in class I |
| d.queries.X | 205.0 | queries last year on checks in class X |
| d.queries.PK | 242.0 | queries last year on checks in class PK |
| d.queries.L | 341.0 | queries last year on checks in class L |
| d.queries.none | 35.0 | queries not tied to a checklist item (R09, R14, R15) |
| d.proto.checks | 9.0 | checks the Saturday prototype runs fully or partly |
| d.samples.read | 4.0 | inbox bills read by eye and joined to the pack data |
| d.samples.no_text_layer | 31.0 | inbox PDFs checked for a text layer: none has one (every page is one embedded image) |
| d.inbox.files | 40.0 | files in the bill inbox: 10 packets and 30 single bills, 9 of them phone photos |
| d.ftr.baseline | 86.9 | % of bills with no query: first-time-right baseline |
| d.human_per_pct | 104.49 | bills a year per percentage point of bills sent to a human look |
| d.human_per_day | 0.418 | ...per working day, on 250 working days |
| d.hours.must | 14.0 | estimated hours for the must-have slice |
| d.hours.old | 13.0 | hours in the first version of the slice (13) before this change |
| d.hours.spare | 0.0 | hours left in the budget after the must-have slice |
| d.after.desk_mean_low | 24.944 | mean days from the desk after all three levers, best case (before minus the high saving) |
| d.after.desk_mean_high | 27.348 | mean days from the desk after all three levers, worst case (before minus the low saving) |
| d.after.inv_mean_low | 31.301 | mean days from the invoice date after all three levers, best case |
| d.after.inv_mean_high | 33.705 | mean days from the invoice date after all three levers, worst case |
| d.hours.full | 26.0 | hours for the full checker plus the full work queue, which do not fit |

<!-- END 10_solution_design.py -->

<!-- BEGIN 09_levers.py -->

### Figures from `analysis/09_levers.py` (used in notes/payment-lag.md and notes/solution-design.md (part f). The replay is backtest/replay.py, called by this script; every value in backtest/out/impact.csv and confusion.csv is one of these figures (l.lever.*, l.base.*, l.cf.*, l.impact.*, l.assume.*, l.live.*): same script, same command. Every row of levers.csv, lag_factors.csv, lag_first_run.csv and backtest_rules.csv is also a figure: same script, same command)

Script: `analysis/09_levers.py`. Output: `analysis/out/figures_levers.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
python -I analysis/02_stage_times.py
python -I analysis/04_query_forensics.py
python -I analysis/06_msme_exposure.py
python -I analysis/05_claims_tested.py
python -I analysis/08_problem_ranking.py
python -I analysis/09_levers.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| l.n | 10449.0 | paid invoices analysed |
| l.n_msme_known | 5106.0 | known Micro and Small paid invoices |
| l.chk.paid_on_run_pct | 100.0 | % of paid invoices paid on a Tuesday or a Friday |
| l.chk.run_wait | 2.278 | mean days from posting to the next Tuesday or Friday run |
| l.chk.actual_wait | 5.994 | mean days from posting to payment |
| l.chk.first_run_pct | 29.017 | % of paid invoices paid on or before the first run after posting |
| l.chk.ap1_share | 40.415 | AP-1's share of paid invoices (%) |
| l.chk.ap1_wait | 11.272 | mean days from head-office receipt to pick-up, AP-1 |
| l.chk.others_wait | 7.198 | mean days from head-office receipt to pick-up, the other four verifiers |
| l.chk.ap1_saving | 1.647 | days off the mean if each AP-1 bill waited the others' mean |
| l.chk.queried_pct | 12.518 | % of paid invoices with a query |
| l.chk.q_ceiling_open | 2.746 | days off the mean if every query's open days vanished (ceiling) |
| l.chk.q_ceiling_added | 3.024 | days off the mean if queried bills lost the extra days they carry over unqueried bills (the 24.2 extra, same category) |
| l.chk.q_diff_means | 3.025 | days off the mean if queried bills were as fast as unqueried bills (invoice clock) |
| l.chk.over45 | 1153.0 | paid invoices over 45 days from the desk date |
| l.chk.over45_queried | 754.0 | ...of which had a query |
| l.chk.over45_queried_pct | 65.395 | ...% of them |
| l.chk.over45_share_among_queried | 57.645 | % of queried bills over 45 days |
| l.chk.over45_share_among_unqueried | 4.365 | % of unqueried bills over 45 days |
| l.chk.over45_if_no_queries | 468.0 | bills still over 45 days if every query's open days were removed |
| l.chk.mean_over45_queried_removed | 28.539 | mean desk-to-paid days with every query's open days removed |
| l.lag.missed_0 | 29.008 | % of paid invoices that missed 0 runs after the first one open to them |
| l.lag.missed_1 | 46.579 | % of paid invoices that missed 1 runs after the first one open to them |
| l.lag.missed_2 | 17.466 | % of paid invoices that missed 2 runs after the first one open to them |
| l.lag.missed_3 | 6.938 | % of paid invoices that missed 3+ runs after the first one open to them |
| l.lag.mean_runs_missed | 1.056 | mean runs missed after the first one open to the bill |
| l.lag.days_per_run | 3.519 | mean days added per missed run |
| l.lag.gap.adj_eta2 | 0.114 | share of the spread in days past the first run explained by gap to the run (days) (adjusted for the number of groups) |
| l.lag.gap.lowest | 1.928 | lowest group mean of days past the first run, gap to the run (days) |
| l.lag.gap.highest | 5.192 | highest group mean of days past the first run, gap to the run (days) |
| l.lag.dow.adj_eta2 | 0.114 | share of the spread in days past the first run explained by posting weekday (adjusted for the number of groups) |
| l.lag.dow.lowest | 1.928 | lowest group mean of days past the first run, posting weekday |
| l.lag.dow.highest | 5.262 | highest group mean of days past the first run, posting weekday |
| l.lag.amount.adj_eta2 | -0.0 | share of the spread in days past the first run explained by amount (fifths) (adjusted for the number of groups) |
| l.lag.amount.lowest | 3.681 | lowest group mean of days past the first run, amount (fifths) |
| l.lag.amount.highest | 3.769 | highest group mean of days past the first run, amount (fifths) |
| l.lag.msme.adj_eta2 | 0.0 | share of the spread in days past the first run explained by msme status (adjusted for the number of groups) |
| l.lag.msme.lowest | 3.617 | lowest group mean of days past the first run, msme status |
| l.lag.msme.highest | 3.856 | highest group mean of days past the first run, msme status |
| l.lag.verifier.adj_eta2 | 0.0 | share of the spread in days past the first run explained by verifier (adjusted for the number of groups) |
| l.lag.verifier.lowest | 3.574 | lowest group mean of days past the first run, verifier |
| l.lag.verifier.highest | 3.766 | highest group mean of days past the first run, verifier |
| l.lag.category.adj_eta2 | -0.001 | share of the spread in days past the first run explained by spend category (adjusted for the number of groups) |
| l.lag.category.lowest | 3.595 | lowest group mean of days past the first run, spend category |
| l.lag.category.highest | 3.813 | highest group mean of days past the first run, spend category |
| l.lag.ptype.adj_eta2 | 0.0 | share of the spread in days past the first run explained by property type (adjusted for the number of groups) |
| l.lag.ptype.lowest | 3.494 | lowest group mean of days past the first run, property type |
| l.lag.ptype.highest | 3.755 | highest group mean of days past the first run, property type |
| l.lag.property.adj_eta2 | 0.001 | share of the spread in days past the first run explained by property (adjusted for the number of groups) |
| l.lag.property.lowest | 3.296 | lowest group mean of days past the first run, property |
| l.lag.property.highest | 4.288 | highest group mean of days past the first run, property |
| l.lag.vendor.adj_eta2 | -0.004 | share of the spread in days past the first run explained by vendor (adjusted for the number of groups) |
| l.lag.vendor.lowest | 2.727 | lowest group mean of days past the first run, vendor |
| l.lag.vendor.highest | 4.833 | highest group mean of days past the first run, vendor |
| l.lag.month.adj_eta2 | 0.001 | share of the spread in days past the first run explained by posting month (adjusted for the number of groups) |
| l.lag.month.lowest | 3.296 | lowest group mean of days past the first run, posting month |
| l.lag.month.highest | 3.919 | highest group mean of days past the first run, posting month |
| l.lag.gap1.n | 3009.0 | paid invoices whose first open run is 1 days after posting |
| l.lag.gap1.first_pct | 5.218 | % of them paid on that first run |
| l.lag.gap1.excess | 5.192 | mean days past that run |
| l.lag.gap2.n | 2993.0 | paid invoices whose first open run is 2 days after posting |
| l.lag.gap2.first_pct | 23.154 | % of them paid on that first run |
| l.lag.gap2.excess | 4.0 | mean days past that run |
| l.lag.gap3.n | 2984.0 | paid invoices whose first open run is 3 days after posting |
| l.lag.gap3.first_pct | 43.968 | % of them paid on that first run |
| l.lag.gap3.excess | 2.82 | mean days past that run |
| l.lag.gap4.n | 1463.0 | paid invoices whose first open run is 4 days after posting |
| l.lag.gap4.first_pct | 59.467 | % of them paid on that first run |
| l.lag.gap4.excess | 1.928 | mean days past that run |
| l.lag.runs_n | 108.0 | payment run dates in the register |
| l.lag.bills_per_run_mean | 96.75 | mean paid invoices per run date |
| l.lag.bills_per_run_tue | 110.907 | mean paid invoices per Tuesday run |
| l.lag.bills_per_run_fri | 82.593 | mean paid invoices per Friday run |
| l.lag.tue_share | 57.316 | % of paid invoices paid on a Tuesday |
| l.bt.dup.queries | 130.0 | backtest, Duplicate invoice number for the vendor (H13): queries |
| l.bt.dup.caught | 34.0 | backtest, Duplicate invoice number for the vendor (H13): caught |
| l.bt.dup.flagged | 68.0 | backtest, Duplicate invoice number for the vendor (H13): flagged |
| l.bt.dup.flagged_never_queried | 31.0 | backtest, Duplicate invoice number for the vendor (H13): flagged never queried |
| l.bt.exp.queries | 107.0 | backtest, Work order expired on the invoice date (H3): queries |
| l.bt.exp.caught | 102.0 | backtest, Work order expired on the invoice date (H3): caught |
| l.bt.exp.flagged | 690.0 | backtest, Work order expired on the invoice date (H3): flagged |
| l.bt.exp.flagged_never_queried | 506.0 | backtest, Work order expired on the invoice date (H3): flagged never queried |
| l.bt.bal.queries | 219.0 | backtest, Work order value exhausted (H3, as value headroom): queries |
| l.bt.bal.caught | 9.0 | backtest, Work order value exhausted (H3, as value headroom): caught |
| l.bt.bal.flagged | 694.0 | backtest, Work order value exhausted (H3, as value headroom): flagged |
| l.bt.bal.flagged_never_queried | 611.0 | backtest, Work order value exhausted (H3, as value headroom): flagged never queried |
| l.bt.raw_rows | 11220.0 | rows in bill_register.csv |
| l.bt.bills | 11000.0 | distinct bills replayed (raw rows less the exact duplicate rows, data-audit D01) |
| l.bt.dropped | 220.0 | exact duplicate rows removed before the replay |
| l.bt.flag_any | 1392.0 | bills flagged by at least one of the three rules |
| l.bt.flag_any_pct | 12.655 | % of replayed bills flagged by at least one rule |
| l.bt.q_total | 1441.0 | queries last year, all rules |
| l.bt.q_testable | 456.0 | queries on the rules the backtest can test |
| l.bt.q_caught | 145.0 | of those, on bills flagged on the desk date |
| l.bt.extra | 2.23 | days a queried bill carries beyond the days its query stays open |
| l.bt.n_caught_paid | 121.0 | queries on paid invoices that the three rules would have caught |
| l.cf.dup.tp | 34.0 | confusion, bills, Duplicate invoice number for the vendor (H13): flagged and queried for this cause |
| l.cf.dup.fp | 34.0 | confusion, bills, Duplicate invoice number for the vendor (H13): flagged, not queried for this cause |
| l.cf.dup.fn | 96.0 | confusion, bills, Duplicate invoice number for the vendor (H13): queried for this cause, not flagged |
| l.cf.dup.tn | 10836.0 | confusion, bills, Duplicate invoice number for the vendor (H13): neither |
| l.cf.dup.precision_pct | 50.0 | Duplicate invoice number for the vendor (H13): % of flagged bills that really had a query for this cause |
| l.cf.dup.recall_pct | 26.154 | Duplicate invoice number for the vendor (H13): % of bills with a query for this cause that were flagged on day 0 |
| l.cf.exp.tp | 102.0 | confusion, bills, Work order expired on the invoice date (H3): flagged and queried for this cause |
| l.cf.exp.fp | 588.0 | confusion, bills, Work order expired on the invoice date (H3): flagged, not queried for this cause |
| l.cf.exp.fn | 5.0 | confusion, bills, Work order expired on the invoice date (H3): queried for this cause, not flagged |
| l.cf.exp.tn | 10305.0 | confusion, bills, Work order expired on the invoice date (H3): neither |
| l.cf.exp.precision_pct | 14.783 | Work order expired on the invoice date (H3): % of flagged bills that really had a query for this cause |
| l.cf.exp.recall_pct | 95.327 | Work order expired on the invoice date (H3): % of bills with a query for this cause that were flagged on day 0 |
| l.cf.bal.tp | 9.0 | confusion, bills, Work order value exhausted (H3, as value headroom): flagged and queried for this cause |
| l.cf.bal.fp | 685.0 | confusion, bills, Work order value exhausted (H3, as value headroom): flagged, not queried for this cause |
| l.cf.bal.fn | 210.0 | confusion, bills, Work order value exhausted (H3, as value headroom): queried for this cause, not flagged |
| l.cf.bal.tn | 10096.0 | confusion, bills, Work order value exhausted (H3, as value headroom): neither |
| l.cf.bal.precision_pct | 1.297 | Work order value exhausted (H3, as value headroom): % of flagged bills that really had a query for this cause |
| l.cf.bal.recall_pct | 4.11 | Work order value exhausted (H3, as value headroom): % of bills with a query for this cause that were flagged on day 0 |
| l.cf.any.tp | 160.0 | confusion, bills, Any of the three rules: flagged and queried for this cause |
| l.cf.any.fp | 1232.0 | confusion, bills, Any of the three rules: flagged, not queried for this cause |
| l.cf.any.fn | 296.0 | confusion, bills, Any of the three rules: queried for this cause, not flagged |
| l.cf.any.tn | 9312.0 | confusion, bills, Any of the three rules: neither |
| l.cf.any.precision_pct | 11.494 | Any of the three rules: % of flagged bills that really had a query for this cause |
| l.cf.any.recall_pct | 35.088 | Any of the three rules: % of bills with a query for this cause that were flagged on day 0 |
| l.impact.no_flag_pct | 87.345 | Share of bills with no flag from the three rules we can test; AP still runs all other checks on these bills (%) |
| l.assume.calls_per_bill | 3.0 | ASSUMPTION: vendor status calls per bill (vendor survey, about 3) |
| l.impact.calls_ceiling | 33000.0 | Vendor calls a year, ceiling if every call were a status call that the tool removes; not an estimate (ASSUMPTION: 3 calls per bill on the replayed bills) |
| l.live.waiting | 27.0 | bills waiting at head office for AP to pick them up on 30 April 2026 (not yet picked) |
| l.lever.queue.days | 1.669 | days off the mean: AP-1's pick-up waits matched to the other verifiers' at the same rank |
| l.lever.queue.bills | 4221.0 | Balanced AP pick order, AP-1 matched to the other four: bills |
| l.base.desk_mean | 31.284 | mean days desk to paid, paid invoices, as run |
| l.base.inv_mean | 37.641 | mean days invoice to paid, paid invoices, as run |
| l.base.ms_late | 530.0 | known Micro and Small paid invoices over 45 days from the desk, as run |
| l.base.ms_late_pct | 10.38 | ...as % of known Micro and Small paid invoices |
| l.base.p90 | 47.0 | p90 days desk to paid, as run |
| l.base.p90_inv | 54.0 | p90 days invoice to paid, as run |
| l.base.over45 | 1153.0 | all paid invoices over 45 days from the desk, as run |
| l.base.over45_pct | 11.035 | ...as % of paid invoices |
| l.lever.pay0.save | 3.716 | Pay on the first run after posting, list closes the same day (cut-off 0): save |
| l.lever.pay0.ms_late | 370.0 | Pay on the first run after posting, list closes the same day (cut-off 0): ms_late |
| l.lever.pay0.ms_pct | 7.246 | Pay on the first run after posting, list closes the same day (cut-off 0): ms_pct |
| l.lever.pay0.p90 | 42.0 | Pay on the first run after posting, list closes the same day (cut-off 0): p90 |
| l.lever.pay0.p90_inv | 50.0 | Pay on the first run after posting, list closes the same day (cut-off 0): p90_inv |
| l.lever.pay0.over | 802.0 | Pay on the first run after posting, list closes the same day (cut-off 0): over |
| l.lever.pay0.bills | 7417.0 | Pay on the first run after posting, list closes the same day (cut-off 0): bills |
| l.lever.pay1.save | 2.748 | Pay on the first run after posting, list closes 1 day before (cut-off 1): save |
| l.lever.pay1.ms_late | 401.0 | Pay on the first run after posting, list closes 1 day before (cut-off 1): ms_late |
| l.lever.pay1.ms_pct | 7.854 | Pay on the first run after posting, list closes 1 day before (cut-off 1): ms_pct |
| l.lever.pay1.p90 | 43.0 | Pay on the first run after posting, list closes 1 day before (cut-off 1): p90 |
| l.lever.pay1.p90_inv | 51.0 | Pay on the first run after posting, list closes 1 day before (cut-off 1): p90_inv |
| l.lever.pay1.over | 868.0 | Pay on the first run after posting, list closes 1 day before (cut-off 1): over |
| l.lever.pay1.bills | 5662.0 | Pay on the first run after posting, list closes 1 day before (cut-off 1): bills |
| l.lever.pay2.save | 1.969 | Pay on the first run after posting, list closes 2 days before (cut-off 2): save |
| l.lever.pay2.ms_late | 430.0 | Pay on the first run after posting, list closes 2 days before (cut-off 2): ms_late |
| l.lever.pay2.ms_pct | 8.421 | Pay on the first run after posting, list closes 2 days before (cut-off 2): ms_pct |
| l.lever.pay2.p90 | 44.0 | Pay on the first run after posting, list closes 2 days before (cut-off 2): p90 |
| l.lever.pay2.p90_inv | 52.0 | Pay on the first run after posting, list closes 2 days before (cut-off 2): p90_inv |
| l.lever.pay2.over | 928.0 | Pay on the first run after posting, list closes 2 days before (cut-off 2): over |
| l.lever.pay2.bills | 4115.0 | Pay on the first run after posting, list closes 2 days before (cut-off 2): bills |
| l.lever.queue.save | 1.669 | Balanced AP pick order, AP-1 matched to the other four: save |
| l.lever.queue.ms_late | 414.0 | Balanced AP pick order, AP-1 matched to the other four: ms_late |
| l.lever.queue.ms_pct | 8.108 | Balanced AP pick order, AP-1 matched to the other four: ms_pct |
| l.lever.queue.p90 | 43.0 | Balanced AP pick order, AP-1 matched to the other four: p90 |
| l.lever.queue.p90_inv | 52.0 | Balanced AP pick order, AP-1 matched to the other four: p90_inv |
| l.lever.queue.over | 897.0 | Balanced AP pick order, AP-1 matched to the other four: over |
| l.lever.in3.save | 0.24 | Three intake rules, residual delay 3 days: save |
| l.lever.in3.ms_late | 497.0 | Three intake rules, residual delay 3 days: ms_late |
| l.lever.in3.ms_pct | 9.734 | Three intake rules, residual delay 3 days: ms_pct |
| l.lever.in3.p90 | 46.0 | Three intake rules, residual delay 3 days: p90 |
| l.lever.in3.p90_inv | 54.0 | Three intake rules, residual delay 3 days: p90_inv |
| l.lever.in3.over | 1092.0 | Three intake rules, residual delay 3 days: over |
| l.lever.in3.bills | 118.0 | Three intake rules, residual delay 3 days: bills |
| l.lever.in1.save | 0.263 | Three intake rules, residual delay 1 day: save |
| l.lever.in1.ms_late | 497.0 | Three intake rules, residual delay 1 day: ms_late |
| l.lever.in1.ms_pct | 9.734 | Three intake rules, residual delay 1 day: ms_pct |
| l.lever.in1.p90 | 46.0 | Three intake rules, residual delay 1 day: p90 |
| l.lever.in1.p90_inv | 54.0 | Three intake rules, residual delay 1 day: p90_inv |
| l.lever.in1.over | 1092.0 | Three intake rules, residual delay 1 day: over |
| l.lever.in1.bills | 121.0 | Three intake rules, residual delay 1 day: bills |
| l.lever.inopt.save | 0.912 | Intake rules, optimistic, all layer A and B queries, residual 1 day: save |
| l.lever.inopt.ms_late | 414.0 | Intake rules, optimistic, all layer A and B queries, residual 1 day: ms_late |
| l.lever.inopt.ms_pct | 8.108 | Intake rules, optimistic, all layer A and B queries, residual 1 day: ms_pct |
| l.lever.inopt.p90 | 44.0 | Intake rules, optimistic, all layer A and B queries, residual 1 day: p90 |
| l.lever.inopt.p90_inv | 52.0 | Intake rules, optimistic, all layer A and B queries, residual 1 day: p90_inv |
| l.lever.inopt.over | 930.0 | Intake rules, optimistic, all layer A and B queries, residual 1 day: over |
| l.lever.inopt.bills | 403.0 | Intake rules, optimistic, all layer A and B queries, residual 1 day: bills |
| l.lever.low.save | 3.936 | All three combined, cut-off 2, balanced order, residual 3: save |
| l.lever.low.ms_late | 303.0 | All three combined, cut-off 2, balanced order, residual 3: ms_late |
| l.lever.low.ms_pct | 5.934 | All three combined, cut-off 2, balanced order, residual 3: ms_pct |
| l.lever.low.p90 | 40.0 | All three combined, cut-off 2, balanced order, residual 3: p90 |
| l.lever.low.p90_inv | 48.0 | All three combined, cut-off 2, balanced order, residual 3: p90_inv |
| l.lever.low.over | 653.0 | All three combined, cut-off 2, balanced order, residual 3: over |
| l.lever.low.bills | 6690.0 | All three combined, cut-off 2, balanced order, residual 3: bills |
| l.lever.mid.save | 4.75 | All three combined, cut-off 1, balanced order, residual 1: save |
| l.lever.mid.ms_late | 288.0 | All three combined, cut-off 1, balanced order, residual 1: ms_late |
| l.lever.mid.ms_pct | 5.64 | All three combined, cut-off 1, balanced order, residual 1: ms_pct |
| l.lever.mid.p90 | 39.0 | All three combined, cut-off 1, balanced order, residual 1: p90 |
| l.lever.mid.p90_inv | 47.0 | All three combined, cut-off 1, balanced order, residual 1: p90_inv |
| l.lever.mid.over | 617.0 | All three combined, cut-off 1, balanced order, residual 1: over |
| l.lever.mid.bills | 7601.0 | All three combined, cut-off 1, balanced order, residual 1: bills |
| l.lever.high.save | 6.34 | All three combined, cut-off 0, balanced order, optimistic intake: save |
| l.lever.high.ms_late | 200.0 | All three combined, cut-off 0, balanced order, optimistic intake: ms_late |
| l.lever.high.ms_pct | 3.917 | All three combined, cut-off 0, balanced order, optimistic intake: ms_pct |
| l.lever.high.p90 | 37.0 | All three combined, cut-off 0, balanced order, optimistic intake: p90 |
| l.lever.high.p90_inv | 45.0 | All three combined, cut-off 0, balanced order, optimistic intake: p90_inv |
| l.lever.high.over | 447.0 | All three combined, cut-off 0, balanced order, optimistic intake: over |
| l.lever.high.bills | 8689.0 | All three combined, cut-off 0, balanced order, optimistic intake: bills |
| l.lever.low.sum_alone | 3.878 | sum of the three levers' days off the mean taken separately, low case |
| l.lever.low.overlap | -0.058 | days the separate levers count twice, low case |
| l.lever.mid.sum_alone | 4.679 | sum of the three levers' days off the mean taken separately, mid case |
| l.lever.mid.overlap | -0.071 | days the separate levers count twice, mid case |
| l.lever.high.sum_alone | 6.297 | sum of the three levers' days off the mean taken separately, high case |
| l.lever.high.overlap | -0.043 | days the separate levers count twice, high case |

<!-- END 09_levers.py -->

<!-- BEGIN 11_pick_balance.py -->

### Figures from `analysis/11_pick_balance.py` (used in notes/assumptions.md ('Tracker: judgement calls', verifier load). Reads pack/data and runs app/tracker; every row of pick_balance.csv is also a figure: same script, same command)

Script: `analysis/11_pick_balance.py`. Output: `analysis/out/figures_pickbalance.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/11_pick_balance.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| pb.tolerance_pct | 20.0 | tolerance: highest verifier load at most this % above the lowest |
| pb.waiting | 27.0 | bills waiting at head office that the pick order assigns |
| pb.AP-1.in_hand | 8.0 | AP-1: bills in hand excluding open queries (definition 1), before |
| pb.AP-1.open_queries | 19.0 | AP-1: bills blocked by an open query |
| pb.AP-1.new_from_pick_order | 1.0 | AP-1: new bills given by the pick order |
| pb.AP-1.in_hand_after | 9.0 | AP-1: bills in hand excluding open queries, after |
| pb.AP-1.def2_after | 28.0 | AP-1: bills in hand including open queries (definition 2), after |
| pb.AP-2.in_hand | 3.0 | AP-2: bills in hand excluding open queries (definition 1), before |
| pb.AP-2.open_queries | 15.0 | AP-2: bills blocked by an open query |
| pb.AP-2.new_from_pick_order | 5.0 | AP-2: new bills given by the pick order |
| pb.AP-2.in_hand_after | 8.0 | AP-2: bills in hand excluding open queries, after |
| pb.AP-2.def2_after | 23.0 | AP-2: bills in hand including open queries (definition 2), after |
| pb.AP-3.in_hand | 0.0 | AP-3: bills in hand excluding open queries (definition 1), before |
| pb.AP-3.open_queries | 8.0 | AP-3: bills blocked by an open query |
| pb.AP-3.new_from_pick_order | 8.0 | AP-3: new bills given by the pick order |
| pb.AP-3.in_hand_after | 8.0 | AP-3: bills in hand excluding open queries, after |
| pb.AP-3.def2_after | 16.0 | AP-3: bills in hand including open queries (definition 2), after |
| pb.AP-4.in_hand | 2.0 | AP-4: bills in hand excluding open queries (definition 1), before |
| pb.AP-4.open_queries | 12.0 | AP-4: bills blocked by an open query |
| pb.AP-4.new_from_pick_order | 6.0 | AP-4: new bills given by the pick order |
| pb.AP-4.in_hand_after | 8.0 | AP-4: bills in hand excluding open queries, after |
| pb.AP-4.def2_after | 20.0 | AP-4: bills in hand including open queries (definition 2), after |
| pb.AP-5.in_hand | 1.0 | AP-5: bills in hand excluding open queries (definition 1), before |
| pb.AP-5.open_queries | 5.0 | AP-5: bills blocked by an open query |
| pb.AP-5.new_from_pick_order | 7.0 | AP-5: new bills given by the pick order |
| pb.AP-5.in_hand_after | 8.0 | AP-5: bills in hand excluding open queries, after |
| pb.AP-5.def2_after | 13.0 | AP-5: bills in hand including open queries (definition 2), after |
| pb.def1.spread_pct | 12.5 | after the pick order, highest load above lowest as % of lowest, def1 (-1 = lowest is zero) |
| pb.def1.within | 1.0 | 1 if def1 is within the tolerance after the pick order, else 0 |
| pb.def2.spread_pct | 115.385 | after the pick order, highest load above lowest as % of lowest, def2 (-1 = lowest is zero) |
| pb.def2.within | 0.0 | 1 if def2 is within the tolerance after the pick order, else 0 |

<!-- END 11_pick_balance.py -->

<!-- BEGIN 12_loose_duplicates.py -->

### Figures from `analysis/12_loose_duplicates.py` (used in notes/assumptions.md and the docstring of check H13 in app/rules/checks.py. What loose duplicate matching adds on the register; the backtest and impact figures use exact matching only)

Script: `analysis/12_loose_duplicates.py`. Output: `analysis/out/figures_loose.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
python -I analysis/02_stage_times.py
python -I analysis/04_query_forensics.py
python -I analysis/12_loose_duplicates.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| ld.bills | 11000.0 | distinct bills in the register (after the exact duplicate rows are removed) |
| ld.exact.flagged | 68.0 | bills flagged by exact matching: an earlier bill of the vendor has the same invoice number as written |
| ld.loose.flagged | 68.0 | bills flagged by loose matching: same vendor, same letters and digits ignoring case, slashes, dashes and spaces |
| ld.extra.flagged | 0.0 | extra bills that loose matching flags and exact matching does not |
| ld.extra.queried_dup | 0.0 | of the extra bills, those with a duplicate-bill query (R01) |
| ld.extra.not_queried | 0.0 | of the extra bills, those with no duplicate-bill query: the false alarms |
| ld.extra.false_alarm_pct | -1.0 | false-alarm share of the extra bills, % (-1 = there are no extra bills, so the rate cannot be measured on this register) |
| ld.exact.queried_dup | 34.0 | of the exactly flagged bills, those with a duplicate-bill query (R01) |
| ld.exact.false_alarm_pct | 50.0 | false-alarm share of the exactly flagged bills, % (for comparison) |
| ld.invoice_no.nonstandard | 0.0 | bills whose invoice number is not in the form NNN/YY-YY/NNN, the only form the register uses when it is clean |
| ld.invoice_no.distinct_forms_per_loose_key | 0.0 | vendor and invoice-number keys written in more than one way |

<!-- END 12_loose_duplicates.py -->

<!-- BEGIN 13_duplicate_false_alarms.py -->

### Figures from `analysis/13_duplicate_false_alarms.py` (used in notes/duplicate-false-alarms.md. Loose near-duplicate matching run on every posted invoice in the SAP extract)

Script: `analysis/13_duplicate_false_alarms.py`. Output: `analysis/out/figures_dupalarm.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
python -I analysis/02_stage_times.py
python -I analysis/04_query_forensics.py
python -I analysis/13_duplicate_false_alarms.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| da.rows | 11075.0 | rows in posted_invoices |
| da.invoices | 10856.0 | distinct posted invoices after collapsing exact duplicate rows (D11) |
| da.flagged_loose | 120.0 | posted invoices that loose matching flags: another posted invoice of the same vendor matches on letters and digits |
| da.flagged_exact | 120.0 | posted invoices flagged by exact matching (case and whitespace normalised, as the adapter does) |
| da.flagged_extra | 0.0 | posted invoices that loose matching flags and exact matching does not |
| da.flag_rate_per_1000 | 11.054 | loose flags per 1,000 posted invoices |
| da.pairs | 60.0 | distinct flagged pairs |
| da.pairs_same_date_and_amount | 0.0 | pairs with the same invoice date and the same amount (the fail grade of check H13) |
| da.pairs_same_amount | 0.0 | pairs with the same amount |
| da.pairs_same_date | 1.0 | pairs with the same invoice date |
| da.pairs_same_wo | 34.0 | pairs on the same work order |
| da.pairs_same_text | 60.0 | pairs whose invoice numbers are written identically |
| da.confirmed | 61.0 | flagged invoices that the register shows with a duplicate-bill query (R01) |
| da.unconfirmed | 59.0 | flagged invoices with no duplicate-bill query |
| da.false_alarm_pct | 49.167 | share of flagged invoices with no duplicate-bill query, % |
| da.pairs_either_queried | 60.0 | pairs where at least one of the two invoices has a duplicate-bill query |
| da.pairs_both_queried | 1.0 | pairs where both invoices have a duplicate-bill query |
| da.pairs_one_queried | 59.0 | pairs where exactly one invoice has a duplicate-bill query |
| da.pairs_none_queried | 0.0 | pairs where neither invoice has a duplicate-bill query |
| da.intake.flagged | 60.0 | as at intake: one flag per pair, raised when the second bill of the pair arrives |
| da.intake.confirmed | 60.0 | of those, pairs with a duplicate-bill query on at least one of the two invoices |
| da.intake.false_alarms | 0.0 | of those, pairs with no duplicate-bill query on either invoice |
| da.intake.false_alarm_pct | 0.0 | share of intake flags (pairs) with no duplicate-bill query on either invoice, % |
| da.intake.rate_per_1000 | 5.527 | intake flags (pairs) per 1,000 posted invoices |
| da.queried_dup_not_flagged | 59.0 | posted invoices with a duplicate-bill query that loose matching does not flag |

<!-- END 13_duplicate_false_alarms.py -->

<!-- BEGIN 14_reader_results.py -->

### Figures from `analysis/14_reader_results.py` (used in app/reader/ (reader summary). What the reader did with the 40 inbox files; reads app/reader/cache/*.json (written by `python -m app.reader`); no label file is read)

Script: `analysis/14_reader_results.py`. Output: `analysis/out/figures_reader.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/14_reader_results.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| rd.all.files | 40 | files read (all) |
| rd.all.ok | 21 | files the reader passes with every required field at 0.90 or more and amounts that add up (all) |
| rd.all.review | 19 | files that go to review (all) |
| rd.all.review.human_look | 9 | of the review files, lowest required confidence 0.70 to 0.90 (all) |
| rd.all.review.resend | 10 | of the review files, a required field missing or below 0.70 (all) |
| rd.all.vendor_gstin.not_found | 0 | files where vendor_gstin was not found (all) |
| rd.all.vendor_gstin.below_090 | 9 | files where vendor_gstin was found with confidence below 0.90 (all) |
| rd.all.vendor_name.not_found | 0 | files where vendor_name was not found (all) |
| rd.all.vendor_name.below_090 | 0 | files where vendor_name was found with confidence below 0.90 (all) |
| rd.all.invoice_no.not_found | 1 | files where invoice_no was not found (all) |
| rd.all.invoice_no.below_090 | 1 | files where invoice_no was found with confidence below 0.90 (all) |
| rd.all.invoice_date.not_found | 1 | files where invoice_date was not found (all) |
| rd.all.invoice_date.below_090 | 0 | files where invoice_date was found with confidence below 0.90 (all) |
| rd.all.wo_id.not_found | 3 | files where wo_id was not found (all) |
| rd.all.wo_id.below_090 | 0 | files where wo_id was found with confidence below 0.90 (all) |
| rd.all.taxable.not_found | 1 | files where taxable was not found (all) |
| rd.all.taxable.below_090 | 5 | files where taxable was found with confidence below 0.90 (all) |
| rd.all.total.not_found | 1 | files where total was not found (all) |
| rd.all.total.below_090 | 5 | files where total was found with confidence below 0.90 (all) |
| rd.all.arithmetic_fail | 4 | files where taxable value plus tax does not equal the total, or a tax line does not match its rate (all) |
| rd.pdf_single.files | 21 | files read (pdf_single) |
| rd.pdf_single.ok | 13 | files the reader passes with every required field at 0.90 or more and amounts that add up (pdf_single) |
| rd.pdf_single.review | 8 | files that go to review (pdf_single) |
| rd.pdf_single.review.human_look | 4 | of the review files, lowest required confidence 0.70 to 0.90 (pdf_single) |
| rd.pdf_single.review.resend | 4 | of the review files, a required field missing or below 0.70 (pdf_single) |
| rd.pdf_single.vendor_gstin.not_found | 0 | files where vendor_gstin was not found (pdf_single) |
| rd.pdf_single.vendor_gstin.below_090 | 4 | files where vendor_gstin was found with confidence below 0.90 (pdf_single) |
| rd.pdf_single.vendor_name.not_found | 0 | files where vendor_name was not found (pdf_single) |
| rd.pdf_single.vendor_name.below_090 | 0 | files where vendor_name was found with confidence below 0.90 (pdf_single) |
| rd.pdf_single.invoice_no.not_found | 0 | files where invoice_no was not found (pdf_single) |
| rd.pdf_single.invoice_no.below_090 | 0 | files where invoice_no was found with confidence below 0.90 (pdf_single) |
| rd.pdf_single.invoice_date.not_found | 0 | files where invoice_date was not found (pdf_single) |
| rd.pdf_single.invoice_date.below_090 | 0 | files where invoice_date was found with confidence below 0.90 (pdf_single) |
| rd.pdf_single.wo_id.not_found | 3 | files where wo_id was not found (pdf_single) |
| rd.pdf_single.wo_id.below_090 | 0 | files where wo_id was found with confidence below 0.90 (pdf_single) |
| rd.pdf_single.taxable.not_found | 0 | files where taxable was not found (pdf_single) |
| rd.pdf_single.taxable.below_090 | 1 | files where taxable was found with confidence below 0.90 (pdf_single) |
| rd.pdf_single.total.not_found | 0 | files where total was not found (pdf_single) |
| rd.pdf_single.total.below_090 | 1 | files where total was found with confidence below 0.90 (pdf_single) |
| rd.pdf_single.arithmetic_fail | 1 | files where taxable value plus tax does not equal the total, or a tax line does not match its rate (pdf_single) |
| rd.pdf_packet.files | 10 | files read (pdf_packet) |
| rd.pdf_packet.ok | 8 | files the reader passes with every required field at 0.90 or more and amounts that add up (pdf_packet) |
| rd.pdf_packet.review | 2 | files that go to review (pdf_packet) |
| rd.pdf_packet.review.human_look | 2 | of the review files, lowest required confidence 0.70 to 0.90 (pdf_packet) |
| rd.pdf_packet.review.resend | 0 | of the review files, a required field missing or below 0.70 (pdf_packet) |
| rd.pdf_packet.vendor_gstin.not_found | 0 | files where vendor_gstin was not found (pdf_packet) |
| rd.pdf_packet.vendor_gstin.below_090 | 2 | files where vendor_gstin was found with confidence below 0.90 (pdf_packet) |
| rd.pdf_packet.vendor_name.not_found | 0 | files where vendor_name was not found (pdf_packet) |
| rd.pdf_packet.vendor_name.below_090 | 0 | files where vendor_name was found with confidence below 0.90 (pdf_packet) |
| rd.pdf_packet.invoice_no.not_found | 0 | files where invoice_no was not found (pdf_packet) |
| rd.pdf_packet.invoice_no.below_090 | 0 | files where invoice_no was found with confidence below 0.90 (pdf_packet) |
| rd.pdf_packet.invoice_date.not_found | 0 | files where invoice_date was not found (pdf_packet) |
| rd.pdf_packet.invoice_date.below_090 | 0 | files where invoice_date was found with confidence below 0.90 (pdf_packet) |
| rd.pdf_packet.wo_id.not_found | 0 | files where wo_id was not found (pdf_packet) |
| rd.pdf_packet.wo_id.below_090 | 0 | files where wo_id was found with confidence below 0.90 (pdf_packet) |
| rd.pdf_packet.taxable.not_found | 0 | files where taxable was not found (pdf_packet) |
| rd.pdf_packet.taxable.below_090 | 0 | files where taxable was found with confidence below 0.90 (pdf_packet) |
| rd.pdf_packet.total.not_found | 0 | files where total was not found (pdf_packet) |
| rd.pdf_packet.total.below_090 | 0 | files where total was found with confidence below 0.90 (pdf_packet) |
| rd.pdf_packet.arithmetic_fail | 0 | files where taxable value plus tax does not equal the total, or a tax line does not match its rate (pdf_packet) |
| rd.phone_photo.files | 9 | files read (phone_photo) |
| rd.phone_photo.ok | 0 | files the reader passes with every required field at 0.90 or more and amounts that add up (phone_photo) |
| rd.phone_photo.review | 9 | files that go to review (phone_photo) |
| rd.phone_photo.review.human_look | 3 | of the review files, lowest required confidence 0.70 to 0.90 (phone_photo) |
| rd.phone_photo.review.resend | 6 | of the review files, a required field missing or below 0.70 (phone_photo) |
| rd.phone_photo.vendor_gstin.not_found | 0 | files where vendor_gstin was not found (phone_photo) |
| rd.phone_photo.vendor_gstin.below_090 | 3 | files where vendor_gstin was found with confidence below 0.90 (phone_photo) |
| rd.phone_photo.vendor_name.not_found | 0 | files where vendor_name was not found (phone_photo) |
| rd.phone_photo.vendor_name.below_090 | 0 | files where vendor_name was found with confidence below 0.90 (phone_photo) |
| rd.phone_photo.invoice_no.not_found | 1 | files where invoice_no was not found (phone_photo) |
| rd.phone_photo.invoice_no.below_090 | 1 | files where invoice_no was found with confidence below 0.90 (phone_photo) |
| rd.phone_photo.invoice_date.not_found | 1 | files where invoice_date was not found (phone_photo) |
| rd.phone_photo.invoice_date.below_090 | 0 | files where invoice_date was found with confidence below 0.90 (phone_photo) |
| rd.phone_photo.wo_id.not_found | 0 | files where wo_id was not found (phone_photo) |
| rd.phone_photo.wo_id.below_090 | 0 | files where wo_id was found with confidence below 0.90 (phone_photo) |
| rd.phone_photo.taxable.not_found | 1 | files where taxable was not found (phone_photo) |
| rd.phone_photo.taxable.below_090 | 4 | files where taxable was found with confidence below 0.90 (phone_photo) |
| rd.phone_photo.total.not_found | 1 | files where total was not found (phone_photo) |
| rd.phone_photo.total.below_090 | 4 | files where total was found with confidence below 0.90 (phone_photo) |
| rd.phone_photo.arithmetic_fail | 3 | files where taxable value plus tax does not equal the total, or a tax line does not match its rate (phone_photo) |
| rd.packets.has_attendance | 2 | packets with a attendance page recognised |
| rd.packets.has_challan | 2 | packets with a challan page recognised |
| rd.packets.has_service_report | 1 | packets with a service_report page recognised |
| rd.packets.has_pf_esic | 1 | packets with a pf_esic page recognised |
| rd.packets.no_support | 5 | packets with no supporting page recognised |
| rd.credit_notes | 1 | files read as a credit note |
| rd.no_gst | 1 | files that print 'GST not applicable' |
| rd.text_layer_fast_path | 0 | files read through the pdfplumber text-layer fast path (expected 0) |
| rd.simulated | 0 | cached results marked reader simulated |

<!-- END 14_reader_results.py -->

<!-- BEGIN 15_reader_evaluation.py -->

### Figures from `analysis/15_reader_evaluation.py` (used in notes/reader-evaluation.md. FIRST-RUN score of the reader against the 10 hand-labelled bills (analysis/gold_labels.csv, read only), from the frozen analysis/reader_first_run.json)

Script: `analysis/15_reader_evaluation.py`. Output: `analysis/out/figures_reader_eval.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/15_reader_evaluation.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| re.first.pdf_single.fields_correct | 17 | first run, pdf_single: field readings correct |
| re.first.pdf_single.fields_total | 18 | first run, pdf_single: field readings scored |
| re.first.pdf_single.key_bills_correct | 2 | first run, pdf_single: bills correct on all four key fields |
| re.first.pdf_single.bills | 3 | first run, pdf_single: bills |
| re.first.pdf_single.vendor_name.correct | 3 | first run, pdf_single: vendor_name correct (of 3) |
| re.first.pdf_single.invoice_number.correct | 3 | first run, pdf_single: invoice_number correct (of 3) |
| re.first.pdf_single.invoice_date.correct | 3 | first run, pdf_single: invoice_date correct (of 3) |
| re.first.pdf_single.amount.correct | 3 | first run, pdf_single: amount correct (of 3) |
| re.first.pdf_single.gstin.correct | 2 | first run, pdf_single: gstin correct (of 3) |
| re.first.pdf_single.po_or_wo_number.correct | 3 | first run, pdf_single: po_or_wo_number correct (of 3) |
| re.first.pdf_packet.fields_correct | 17 | first run, pdf_packet: field readings correct |
| re.first.pdf_packet.fields_total | 18 | first run, pdf_packet: field readings scored |
| re.first.pdf_packet.key_bills_correct | 2 | first run, pdf_packet: bills correct on all four key fields |
| re.first.pdf_packet.bills | 3 | first run, pdf_packet: bills |
| re.first.pdf_packet.vendor_name.correct | 3 | first run, pdf_packet: vendor_name correct (of 3) |
| re.first.pdf_packet.invoice_number.correct | 3 | first run, pdf_packet: invoice_number correct (of 3) |
| re.first.pdf_packet.invoice_date.correct | 3 | first run, pdf_packet: invoice_date correct (of 3) |
| re.first.pdf_packet.amount.correct | 3 | first run, pdf_packet: amount correct (of 3) |
| re.first.pdf_packet.gstin.correct | 2 | first run, pdf_packet: gstin correct (of 3) |
| re.first.pdf_packet.po_or_wo_number.correct | 3 | first run, pdf_packet: po_or_wo_number correct (of 3) |
| re.first.phone_photo.fields_correct | 18 | first run, phone_photo: field readings correct |
| re.first.phone_photo.fields_total | 24 | first run, phone_photo: field readings scored |
| re.first.phone_photo.key_bills_correct | 1 | first run, phone_photo: bills correct on all four key fields |
| re.first.phone_photo.bills | 4 | first run, phone_photo: bills |
| re.first.phone_photo.vendor_name.correct | 4 | first run, phone_photo: vendor_name correct (of 4) |
| re.first.phone_photo.invoice_number.correct | 3 | first run, phone_photo: invoice_number correct (of 4) |
| re.first.phone_photo.invoice_date.correct | 3 | first run, phone_photo: invoice_date correct (of 4) |
| re.first.phone_photo.amount.correct | 2 | first run, phone_photo: amount correct (of 4) |
| re.first.phone_photo.gstin.correct | 2 | first run, phone_photo: gstin correct (of 4) |
| re.first.phone_photo.po_or_wo_number.correct | 4 | first run, phone_photo: po_or_wo_number correct (of 4) |
| re.first.all.fields_correct | 52 | first run, all: field readings correct |
| re.first.all.fields_total | 60 | first run, all: field readings scored |
| re.first.all.key_bills_correct | 5 | first run, all: bills correct on all four key fields |
| re.first.all.bills | 10 | first run, all: bills |
| re.first.all.vendor_name.correct | 10 | first run, all: vendor_name correct (of 10) |
| re.first.all.invoice_number.correct | 9 | first run, all: invoice_number correct (of 10) |
| re.first.all.invoice_date.correct | 9 | first run, all: invoice_date correct (of 10) |
| re.first.all.amount.correct | 8 | first run, all: amount correct (of 10) |
| re.first.all.gstin.correct | 6 | first run, all: gstin correct (of 10) |
| re.first.all.po_or_wo_number.correct | 10 | first run, all: po_or_wo_number correct (of 10) |
| re.first.cal.hi.n | 44 | first run: readings with confidence 0.90 or more |
| re.first.cal.hi.correct | 44 | first run: of those, correct |
| re.first.cal.mid.n | 8 | first run: readings with confidence 0.70 to 0.90 |
| re.first.cal.mid.correct | 6 | first run: of those, correct |
| re.first.cal.lo.n | 8 | first run: readings with confidence below 0.70 (or not read) |
| re.first.cal.lo.correct | 2 | first run: of those, correct |
| re.first.wrong_conf_070_plus | 2 | first run: wrong readings with confidence 0.70 or more |
| re.second.pdf_single.fields_correct | 17 | second score (label corrected), pdf_single: field readings correct |
| re.second.pdf_single.key_bills_correct | 2 | second score, pdf_single: bills correct on all four key fields |
| re.second.pdf_single.vendor_name.correct | 3 | second score, pdf_single: vendor_name correct |
| re.second.pdf_single.invoice_number.correct | 3 | second score, pdf_single: invoice_number correct |
| re.second.pdf_single.invoice_date.correct | 3 | second score, pdf_single: invoice_date correct |
| re.second.pdf_single.amount.correct | 3 | second score, pdf_single: amount correct |
| re.second.pdf_single.gstin.correct | 2 | second score, pdf_single: gstin correct |
| re.second.pdf_single.po_or_wo_number.correct | 3 | second score, pdf_single: po_or_wo_number correct |
| re.second.pdf_packet.fields_correct | 17 | second score (label corrected), pdf_packet: field readings correct |
| re.second.pdf_packet.key_bills_correct | 2 | second score, pdf_packet: bills correct on all four key fields |
| re.second.pdf_packet.vendor_name.correct | 3 | second score, pdf_packet: vendor_name correct |
| re.second.pdf_packet.invoice_number.correct | 3 | second score, pdf_packet: invoice_number correct |
| re.second.pdf_packet.invoice_date.correct | 3 | second score, pdf_packet: invoice_date correct |
| re.second.pdf_packet.amount.correct | 3 | second score, pdf_packet: amount correct |
| re.second.pdf_packet.gstin.correct | 2 | second score, pdf_packet: gstin correct |
| re.second.pdf_packet.po_or_wo_number.correct | 3 | second score, pdf_packet: po_or_wo_number correct |
| re.second.phone_photo.fields_correct | 19 | second score (label corrected), phone_photo: field readings correct |
| re.second.phone_photo.key_bills_correct | 1 | second score, phone_photo: bills correct on all four key fields |
| re.second.phone_photo.vendor_name.correct | 4 | second score, phone_photo: vendor_name correct |
| re.second.phone_photo.invoice_number.correct | 3 | second score, phone_photo: invoice_number correct |
| re.second.phone_photo.invoice_date.correct | 3 | second score, phone_photo: invoice_date correct |
| re.second.phone_photo.amount.correct | 3 | second score, phone_photo: amount correct |
| re.second.phone_photo.gstin.correct | 2 | second score, phone_photo: gstin correct |
| re.second.phone_photo.po_or_wo_number.correct | 4 | second score, phone_photo: po_or_wo_number correct |
| re.second.all.fields_correct | 53 | second score (label corrected), all: field readings correct |
| re.second.all.key_bills_correct | 5 | second score, all: bills correct on all four key fields |
| re.second.all.vendor_name.correct | 10 | second score, all: vendor_name correct |
| re.second.all.invoice_number.correct | 9 | second score, all: invoice_number correct |
| re.second.all.invoice_date.correct | 9 | second score, all: invoice_date correct |
| re.second.all.amount.correct | 9 | second score, all: amount correct |
| re.second.all.gstin.correct | 6 | second score, all: gstin correct |
| re.second.all.po_or_wo_number.correct | 10 | second score, all: po_or_wo_number correct |
| re.second.cal.hi.n | 44 | second score: readings with confidence 0.90 or more |
| re.second.cal.hi.correct | 44 | second score: of those, correct |
| re.second.cal.mid.n | 8 | second score: readings with confidence 0.70 to 0.90 |
| re.second.cal.mid.correct | 6 | second score: of those, correct |
| re.second.cal.lo.n | 8 | second score: readings with confidence below 0.70 (or not read) |
| re.second.cal.lo.correct | 3 | second score: of those, correct |
| re.second.wrong_conf_070_plus | 2 | second score: wrong readings with confidence 0.70 or more |
| re.first.suspect_label_errors | 1 | first run: misses where the label, not the reader, was wrong (bill-28 amount; the user has since corrected it) |
| re.post.changed | 1 | the live reader output differs from the first-run snapshot |
| re.post.pdf_single.fields_correct | 18 | post-fix (tuned on these 10 bills), pdf_single: field readings correct |
| re.post.pdf_single.key_bills_correct | 3 | post-fix (tuned on these 10 bills), pdf_single: bills correct on all four key fields |
| re.post.pdf_single.vendor_name.correct | 3 | post-fix (tuned on these 10 bills), pdf_single: vendor_name correct |
| re.post.pdf_single.invoice_number.correct | 3 | post-fix (tuned on these 10 bills), pdf_single: invoice_number correct |
| re.post.pdf_single.invoice_date.correct | 3 | post-fix (tuned on these 10 bills), pdf_single: invoice_date correct |
| re.post.pdf_single.amount.correct | 3 | post-fix (tuned on these 10 bills), pdf_single: amount correct |
| re.post.pdf_single.gstin.correct | 3 | post-fix (tuned on these 10 bills), pdf_single: gstin correct |
| re.post.pdf_single.po_or_wo_number.correct | 3 | post-fix (tuned on these 10 bills), pdf_single: po_or_wo_number correct |
| re.post.pdf_packet.fields_correct | 18 | post-fix (tuned on these 10 bills), pdf_packet: field readings correct |
| re.post.pdf_packet.key_bills_correct | 3 | post-fix (tuned on these 10 bills), pdf_packet: bills correct on all four key fields |
| re.post.pdf_packet.vendor_name.correct | 3 | post-fix (tuned on these 10 bills), pdf_packet: vendor_name correct |
| re.post.pdf_packet.invoice_number.correct | 3 | post-fix (tuned on these 10 bills), pdf_packet: invoice_number correct |
| re.post.pdf_packet.invoice_date.correct | 3 | post-fix (tuned on these 10 bills), pdf_packet: invoice_date correct |
| re.post.pdf_packet.amount.correct | 3 | post-fix (tuned on these 10 bills), pdf_packet: amount correct |
| re.post.pdf_packet.gstin.correct | 3 | post-fix (tuned on these 10 bills), pdf_packet: gstin correct |
| re.post.pdf_packet.po_or_wo_number.correct | 3 | post-fix (tuned on these 10 bills), pdf_packet: po_or_wo_number correct |
| re.post.phone_photo.fields_correct | 22 | post-fix (tuned on these 10 bills), phone_photo: field readings correct |
| re.post.phone_photo.key_bills_correct | 2 | post-fix (tuned on these 10 bills), phone_photo: bills correct on all four key fields |
| re.post.phone_photo.vendor_name.correct | 4 | post-fix (tuned on these 10 bills), phone_photo: vendor_name correct |
| re.post.phone_photo.invoice_number.correct | 4 | post-fix (tuned on these 10 bills), phone_photo: invoice_number correct |
| re.post.phone_photo.invoice_date.correct | 4 | post-fix (tuned on these 10 bills), phone_photo: invoice_date correct |
| re.post.phone_photo.amount.correct | 3 | post-fix (tuned on these 10 bills), phone_photo: amount correct |
| re.post.phone_photo.gstin.correct | 3 | post-fix (tuned on these 10 bills), phone_photo: gstin correct |
| re.post.phone_photo.po_or_wo_number.correct | 4 | post-fix (tuned on these 10 bills), phone_photo: po_or_wo_number correct |
| re.post.all.fields_correct | 58 | post-fix (tuned on these 10 bills), all: field readings correct |
| re.post.all.key_bills_correct | 8 | post-fix (tuned on these 10 bills), all: bills correct on all four key fields |
| re.post.all.vendor_name.correct | 10 | post-fix (tuned on these 10 bills), all: vendor_name correct |
| re.post.all.invoice_number.correct | 10 | post-fix (tuned on these 10 bills), all: invoice_number correct |
| re.post.all.invoice_date.correct | 10 | post-fix (tuned on these 10 bills), all: invoice_date correct |
| re.post.all.amount.correct | 9 | post-fix (tuned on these 10 bills), all: amount correct |
| re.post.all.gstin.correct | 9 | post-fix (tuned on these 10 bills), all: gstin correct |
| re.post.all.po_or_wo_number.correct | 10 | post-fix (tuned on these 10 bills), all: po_or_wo_number correct |
| re.post.cal.hi.n | 53 | post-fix: readings with confidence 0.90 or more |
| re.post.cal.hi.correct | 53 | post-fix: of those, correct |
| re.post.cal.mid.n | 4 | post-fix: readings with confidence 0.70 to 0.90 |
| re.post.cal.mid.correct | 3 | post-fix: of those, correct |
| re.post.cal.lo.n | 3 | post-fix: readings with confidence below 0.70 (or not read) |
| re.post.cal.lo.correct | 2 | post-fix: of those, correct |
| re.post.wrong_conf_070_plus | 1 | post-fix: wrong readings with confidence 0.70 or more |
| re.part1c.before.low | 24 | all 40 bills, before the post-fix reader: required fields (7 per bill) not found or below 0.70 confidence |
| re.part1c.before.reader_ok | 14 | all 40 bills, before the post-fix reader: bills the reader passes (status ok) |
| re.part1c.before.full_verdict | 27 | all 40 bills, before the post-fix reader: bills on which all six checks could run |
| re.part1c.before.some_verdict | 40 | all 40 bills, before the post-fix reader: bills on which at least one check could run |
| re.part1c.before.complete_read | 26 | all 40 bills, before the post-fix reader: bills with every required field read at 0.70 or more (the bills that got a verdict under the old all-or-nothing rule) |
| re.part1c.after.low | 13 | all 40 bills, after the post-fix reader: required fields (7 per bill) not found or below 0.70 confidence |
| re.part1c.after.reader_ok | 21 | all 40 bills, after the post-fix reader: bills the reader passes (status ok) |
| re.part1c.after.full_verdict | 29 | all 40 bills, after the post-fix reader: bills on which all six checks could run |
| re.part1c.after.some_verdict | 40 | all 40 bills, after the post-fix reader: bills on which at least one check could run |
| re.part1c.after.complete_read | 33 | all 40 bills, after the post-fix reader: bills with every required field read at 0.70 or more (the bills that got a verdict under the old all-or-nothing rule) |

<!-- END 15_reader_evaluation.py -->

<!-- BEGIN 16_intake_run.py -->

### Figures from `analysis/16_intake_run.py` (used in notes/intake-run.md. All 40 inbox bills through the reader results, the checks, the routing and parsed_bill)

Script: `analysis/16_intake_run.py`. Output: `analysis/out/figures_intake.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
python -I analysis/02_stage_times.py
python -I analysis/04_query_forensics.py
python -I analysis/16_intake_run.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| ir.files | 40 | bills run through reader results, checks, routing and parsed_bill |
| ir.parsed_bill_rows | 40 | rows written to parsed_bill in the working copy |
| ir.all.route.auto-clear | 1 | verdict auto-clear, all |
| ir.all.route.fix-before-sending | 4 | verdict fix-before-sending, all |
| ir.all.route.fix-internal | 0 | verdict fix-internal, all |
| ir.all.route.human-look | 35 | verdict human-look, all |
| ir.all.route.resend | 0 | verdict resend, all |
| ir.all.files | 40 | bills, all |
| ir.pdf_single.route.auto-clear | 1 | verdict auto-clear, pdf_single |
| ir.pdf_single.route.fix-before-sending | 3 | verdict fix-before-sending, pdf_single |
| ir.pdf_single.route.fix-internal | 0 | verdict fix-internal, pdf_single |
| ir.pdf_single.route.human-look | 17 | verdict human-look, pdf_single |
| ir.pdf_single.route.resend | 0 | verdict resend, pdf_single |
| ir.pdf_single.files | 21 | bills, pdf_single |
| ir.pdf_packet.route.auto-clear | 0 | verdict auto-clear, pdf_packet |
| ir.pdf_packet.route.fix-before-sending | 0 | verdict fix-before-sending, pdf_packet |
| ir.pdf_packet.route.fix-internal | 0 | verdict fix-internal, pdf_packet |
| ir.pdf_packet.route.human-look | 10 | verdict human-look, pdf_packet |
| ir.pdf_packet.route.resend | 0 | verdict resend, pdf_packet |
| ir.pdf_packet.files | 10 | bills, pdf_packet |
| ir.phone_photo.route.auto-clear | 0 | verdict auto-clear, phone_photo |
| ir.phone_photo.route.fix-before-sending | 1 | verdict fix-before-sending, phone_photo |
| ir.phone_photo.route.fix-internal | 0 | verdict fix-internal, phone_photo |
| ir.phone_photo.route.human-look | 8 | verdict human-look, phone_photo |
| ir.phone_photo.route.resend | 0 | verdict resend, phone_photo |
| ir.phone_photo.files | 9 | bills, phone_photo |
| ir.check.P1/H1.not_run | 5 | bills where check P1/H1 could not run (a field it needs was not read) |
| ir.check.P1/H1.pass | 30 | bills where check P1/H1 returns pass |
| ir.check.P1/H1.fail | 3 | bills where check P1/H1 returns fail |
| ir.check.P1/H1.warn | 2 | bills where check P1/H1 returns warn |
| ir.check.P1/H1.needs-document | 0 | bills where check P1/H1 returns needs-document |
| ir.check.P3.not_run | 0 | bills where check P3 could not run (a field it needs was not read) |
| ir.check.P3.pass | 37 | bills where check P3 returns pass |
| ir.check.P3.fail | 3 | bills where check P3 returns fail |
| ir.check.P3.warn | 0 | bills where check P3 returns warn |
| ir.check.P3.needs-document | 0 | bills where check P3 returns needs-document |
| ir.check.H3.not_run | 6 | bills where check H3 could not run (a field it needs was not read) |
| ir.check.H3.pass | 21 | bills where check H3 returns pass |
| ir.check.H3.fail | 10 | bills where check H3 returns fail |
| ir.check.H3.warn | 0 | bills where check H3 returns warn |
| ir.check.H3.needs-document | 3 | bills where check H3 returns needs-document |
| ir.check.H13.not_run | 6 | bills where check H13 could not run (a field it needs was not read) |
| ir.check.H13.pass | 26 | bills where check H13 returns pass |
| ir.check.H13.fail | 0 | bills where check H13 returns fail |
| ir.check.H13.warn | 8 | bills where check H13 returns warn |
| ir.check.H13.needs-document | 0 | bills where check H13 returns needs-document |
| ir.check.H11.not_run | 9 | bills where check H11 could not run (a field it needs was not read) |
| ir.check.H11.pass | 28 | bills where check H11 returns pass |
| ir.check.H11.fail | 0 | bills where check H11 returns fail |
| ir.check.H11.warn | 3 | bills where check H11 returns warn |
| ir.check.H11.needs-document | 0 | bills where check H11 returns needs-document |
| ir.check.H10.not_run | 8 | bills where check H10 could not run (a field it needs was not read) |
| ir.check.H10.pass | 20 | bills where check H10 returns pass |
| ir.check.H10.fail | 0 | bills where check H10 returns fail |
| ir.check.H10.warn | 12 | bills where check H10 returns warn |
| ir.check.H10.needs-document | 0 | bills where check H10 returns needs-document |
| ir.h3.expired | 1 | bills whose work order is expired (or not yet valid) on the bill date |
| ir.h3.exhausted | 10 | bills whose work order is over its approved value after the bill |
| ir.h3.both | 1 | bills with both |
| ir.h3.fail_any | 10 | bills where H3 fails |
| ir.h10.warn_two_readings_differ | 10 | bills where H10 warns because the two place-of-supply readings give different tax types |
| ir.reader_ok_but_flagged | 13 | bills the reader passes (status ok) that a check still fails or warns on |
| ir.own_row_linked | 33 | inbox bills linked to their own register row (needed to replay the duplicate check) |

<!-- END 16_intake_run.py -->

<!-- BEGIN 17_runway_90d.py -->

### Figures from `analysis/17_runway_90d.py` (used in app/ui (control tower headline and list of work orders likely to run dry), backtest/out/runway_90d.csv. Burn from the last 90 days of billing; the lifetime-average figure is kept for comparison)

Script: `analysis/17_runway_90d.py`. Output: `analysis/out/figures_runway.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/clean.py
python -I analysis/17_runway_90d.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| rw.window_days | 90 | days of billing before 30 April 2026 that the burn rate is taken from |
| rw.horizon_days | 45 | an order is likely to run dry when its balance covers this many days or fewer of its recent billing |
| rw.orders_billed_90d | 1111 | work orders with any billing in the last 90 days |
| rw.dry | 234 | work orders likely to run dry within 45 days, burn estimated from the last 90 days of billing |
| rw.dry.vendor_waiting | 49 | of those, orders whose vendor has a bill already waiting (an open bill in the register) |
| rw.dry.wo_waiting | 28 | of those, orders with a bill already waiting on that order itself |
| rw.dry.monthly_billing_inr | 27206798 | monthly billing, rupees, on those orders (last 90 days, per 30.4375 days) |
| rw.sens.window_60d.dry | 172 | sensitivity: work orders likely to run dry within 45 days if the burn is taken from the last 60 days of billing |
| rw.sens.window_90d.dry | 234 | sensitivity: work orders likely to run dry within 45 days if the burn is taken from the last 90 days of billing |
| rw.sens.window_120d.dry | 273 | sensitivity: work orders likely to run dry within 45 days if the burn is taken from the last 120 days of billing |
| rw.sens.window_180d.dry | 281 | sensitivity: work orders likely to run dry within 45 days if the burn is taken from the last 180 days of billing |
| rw.sens.horizon_30d.dry | 171 | sensitivity: work orders whose balance covers 30 days or fewer of the last 90 days of billing |
| rw.sens.horizon_45d.dry | 234 | sensitivity: work orders whose balance covers 45 days or fewer of the last 90 days of billing |
| rw.sens.horizon_60d.dry | 275 | sensitivity: work orders whose balance covers 60 days or fewer of the last 90 days of billing |
| rw.sens.window_lo_days | 60 | sensitivity: the shortest burn window tried, days |
| rw.sens.window_hi_days | 120 | sensitivity: the longer burn window shown beside the headline, days |
| rw.dry_lifetime | 132 | for comparison: the same view using each order's lifetime-average burn (the earlier headline) |

<!-- END 17_runway_90d.py -->

<!-- BEGIN 18_reader_comparison.py -->

### Figures from `analysis/18_reader_comparison.py` (used in notes/reader-comparison.md. Tesseract alone, the stored vision reading alone and the two together on the 10 hand-labelled bills (analysis/gold_labels.csv, read only by this script and by 15_reader_evaluation.py); the vision figures exist only once data/cache/vision holds the readings)

Script: `analysis/18_reader_comparison.py`. Output: `analysis/out/figures_comparison.csv`, one row per figure id below. Run from the project root. Exact commands to reproduce, in order:

```
python -I analysis/18_reader_comparison.py
```

Run from the project root with the project's virtual environment active (`.venv`). `python tasks.py analyse` (or `make analyse`) runs the whole chain and refreshes this register (`python tasks.py setup` first on a new machine).

| Figure id | Value | What it counts |
|---|---|---|
| rc.vision.successful_reads | 30.0 | stored vision responses over all models: bill files sent to Google's Gemini API that came back with a reading |
| rc.vision.distinct_files_read | 24.0 | of those, distinct bill files (the same file was read by two models) |
| rc.free_tier.requests_per_day_per_model | 20.0 | free-tier limit per model per day, as stated in Google's 429 message (not computed here) |
| rc.labelled_bills | 10.0 | hand-labelled bills |
| rc.vision_stored_of_labelled | 10.0 | of those, bills with a stored vision reading |
| rc.tess_first.fields_correct | 53.0 | Tesseract alone, first run: fields right (of 60) |
| rc.tess_first.key_bills | 5.0 | Tesseract alone, first run: bills right on the four key fields |
| rc.tess_live.fields_correct | 58.0 | Tesseract alone, stored reading now (tuned on these bills): fields right (of 60) |
| rc.tess_live.key_bills | 8.0 | Tesseract alone, stored reading now (tuned on these bills): bills right on the four key fields |
| rc.vision.fields_correct | 60.0 | vision alone: fields right (of 60) |
| rc.vision.key_bills | 10.0 | vision alone: bills right on the four key fields |
| rc.comb.trusted | 50.0 | combination: fields where the readers agree (trusted) |
| rc.comb.trusted_wrong | 0.0 | combination: trusted fields that are wrong |
| rc.comb.differ | 2.0 | combination: fields where the readers differ (go to a person) |
| rc.comb.vision_only | 8.0 | combination: fields only the vision reader read (go to a person) |
| rc.comb.tesseract_only | 0.0 | combination: fields only Tesseract read (no second opinion) |
| rc.comb.neither | 0.0 | combination: fields neither reader read |
| rc.comb.tess_wrong_readings | 2.0 | Tesseract readings that were wrong (a value, not the right one) |
| rc.comb.wrong_caught | 2.0 | of those, caught because the readers disagreed |
| rc.comb.wrong_already_low | 0.0 | of those, not caught by disagreement but already below 0.70 confidence |
| rc.comb.wrong_trusted | 0.0 | of those, trusted because the vision reader made the same error |
| rc.comb.key_bills_trusted_right | 3.0 | combination: bills with all four key fields agreed and right |
| rc.comb.key_bills_trusted_wrong | 0.0 | combination: bills with a key field agreed but wrong |
| rc.comb.key_bills_to_person | 7.0 | combination: bills with at least one key field that goes to a person |
| rc.vision.error_upper95_pct | 5.0 | rule of three: with no vision error in the scored fields, the 95% upper bound on its true field error rate, per cent |
| rc.comb.trusted_wrong_upper95_pct | 6.0 | rule of three: with no trusted-and-wrong field in the trusted fields, the 95% upper bound on the true rate of trusted-and-wrong fields, per cent |
| rc.vision.seconds_mean | 16.7 | vision: mean seconds per bill (one call, rate-limit pause excluded) |

<!-- END 18_reader_comparison.py -->
