## attendance-sample\biometric_export.csv
rows=352 cols=4

| column | non-null | null | blank | unique | min | max | sample |
|---|---|---|---|---|---|---|---|
| date | 352 | 0 | 0 | 28 | 2026-02-01 | 2026-02-28 | 2026-02-01 / 2026-02-02 / 2026-02-03 |
| guard_id | 352 | 0 | 0 | 14 | G101 | G114 | G101 / G102 / G104 |
| punch_in | 352 | 0 | 0 | 20 | 07:50 | 19:59 | 07:57 / 19:58 / 19:51 |
| punch_out | 352 | 0 | 0 | 21 |  | 20:09 |  / 08:09 / 08:04 |

## attendance-sample\gate_register_transcribed.csv
rows=384 cols=6

| column | non-null | null | blank | unique | min | max | sample |
|---|---|---|---|---|---|---|---|
| date | 384 | 0 | 0 | 28 | 2026-02-01 | 2026-02-28 | 2026-02-01 / 2026-02-02 / 2026-02-03 |
| person_id | 384 | 0 | 0 | 17 | G101 | R-903 | G101 / G102 / R-902 |
| shift | 384 | 0 | 0 | 2 | Day | Night | Day / Night |
| time_in | 384 | 0 | 0 | 22 | 07:50 | 20:00 | 07:57 / 19:58 / 08:00 |
| time_out | 384 | 0 | 0 | 20 | 08:00 | 20:09 | 20:02 / 08:09 / 20:00 |
| remarks | 384 | 0 | 0 | 12 |  | Reliever for G113 |  / Reliever for G103 / Reliever for G110 |

## attendance-sample\vendor_claim.csv
rows=17 cols=2

| column | non-null | null | blank | unique | min | max | sample |
|---|---|---|---|---|---|---|---|
| person_id | 17 | 0 | 0 | 17 | G101 | R-903 | G101 / G102 / G103 |
| days_claimed | 17 | 0 | 0 | 8 | 10 | 8 | 23 / 28 / 27 |

## bill_register.csv
rows=11220 cols=19

| column | non-null | null | blank | unique | min | max | sample |
|---|---|---|---|---|---|---|---|
| bill_id | 11220 | 0 | 0 | 11000 | TRK250001 | TRK261000 | TRK251334 / TRK251981 / TRK260987 |
| vendor_id | 11220 | 0 | 0 | 899 | V10001 | V10900 | V10374 / V10276 / V10695 |
| property_code | 11220 | 0 | 0 | 150 |  DEL-R03 | snp-r21 | NOI-R12 / NOI-C32 / PKL-C34 |
| category | 11220 | 0 | 0 | 11 | Cleaning Material | Water Testing | Water Testing / Security Manpower / Diesel Supply |
| doc_type | 11220 | 0 | 0 | 2 | credit_note | invoice | invoice / credit_note |
| invoice_no | 11220 | 0 | 0 | 10932 | 001/25-26/009 | 900/25-26/839 | 374/25-26/222 / 276/25-26/722 / 695/25-26/659 |
| invoice_date | 11220 | 0 | 0 | 365 | 2025-04-01 | 2026-03-31 | 2025-05-30 / 2025-07-04 / 2025-06-10 |
| desk_received_date | 11220 | 0 | 0 | 382 | 2025-04-02 | 2026-04-22 | 2025-06-04 / 2025-07-20 / 2025-06-13 |
| property_verified_date | 11220 | 0 | 0 | 386 | 2025-04-04 | 2026-04-26 | 2025-06-07 / 2025-07-27 / 2025-06-15 |
| property_head_signed_date | 11220 | 0 | 0 | 385 | 2025-04-05 | 2026-04-29 | 2025-06-09 / 2025-07-28 / 2025-06-15 |
| ho_received_date | 11220 | 0 | 0 | 56 |  | 2026-04-24 | 2025-06-13 / 2025-08-01 / 2025-06-20 |
| ho_picked_date | 11220 | 0 | 0 | 384 |  | 2026-04-30 | 2025-06-20 / 2025-08-09 / 2025-07-01 |
| ho_verifier | 11220 | 0 | 0 | 6 |  | AP-5 | AP-1 / AP-4 / AP-2 |
| posted_date | 11220 | 0 | 0 | 383 |  | 2026-04-30 | 2025-06-20 / 2025-10-07 / 2025-07-01 |
| paid_date | 11220 | 0 | 0 | 176 |  | 2026-04-28 | 2025-06-24 / 2025-10-10 / 2025-07-04 |
| amount_inr | 11220 | 0 | 0 | 9514 | -101828 | 99970 | 3380 / 612810 / 268910 |
| gst_inr | 11220 | 0 | 0 | 8548 | -10134 | 9994 | 608 / 110306 / 0 |
| wo_id | 11220 | 0 | 0 | 2092 | 4100001 | 4102092 | 4100871 / 4100128 / 4100017 |
| status | 11220 | 0 | 0 | 5 | In Transit | With AP | Paid / Query / Posted |

## properties.csv
rows=38 cols=6

| column | non-null | null | blank | unique | min | max | sample |
|---|---|---|---|---|---|---|---|
| property_code | 38 | 0 | 0 | 38 | DEL-R03 | SNP-R21 | FBD-R01 / NOI-R02 / DEL-R03 |
| property_name | 38 | 0 | 0 | 38 | Office Tower, Sector 17,  | Retail Mall, Sector 44, N | Residential Society, Sector 70, Faridabad / Residential Soci |
| property_type | 38 | 0 | 0 | 3 | Office Tower | Retail Mall | Residential Society / Office Tower / Retail Mall |
| city | 38 | 0 | 0 | 7 | Faridabad | Sonipat | Faridabad / Noida / New Delhi |
| state | 38 | 0 | 0 | 3 | Delhi | Uttar Pradesh | Haryana / Uttar Pradesh / Delhi |
| units_or_sqft | 38 | 0 | 0 | 38 | 1037337 | 914 | 1728 / 1249 / 310 |

## queries.csv
rows=1441 cols=7

| column | non-null | null | blank | unique | min | max | sample |
|---|---|---|---|---|---|---|---|
| query_id | 1441 | 0 | 0 | 1441 | Q00001 | Q01441 | Q00001 / Q00002 / Q00003 |
| bill_id | 1441 | 0 | 0 | 1441 | TRK250012 | TRK260998 | TRK250012 / TRK250016 / TRK250023 |
| raised_date | 1441 | 0 | 0 | 363 | 2025-04-15 | 2026-04-30 | 2025-10-10 / 2026-04-09 / 2026-01-11 |
| resolved_date | 1441 | 0 | 0 | 357 |  | 2026-04-30 | 2025-10-16 / 2026-04-28 / 2026-01-18 |
| raised_by | 1441 | 0 | 0 | 5 | AP-1 | AP-5 | AP-1 / AP-4 / AP-5 |
| query_category | 1441 | 0 | 0 | 8 | Duplicate bill | WO balance or validity | Service entry or GRN not posted / Supporting documents / GL  |
| query_text | 1441 | 0 | 0 | 515 | Attendance sheet not sign | Wrong company name on bil | Service entry still parked. Please post so we can book. / De |

## vendors.csv
rows=900 cols=6

| column | non-null | null | blank | unique | min | max | sample |
|---|---|---|---|---|---|---|---|
| vendor_id | 900 | 0 | 0 | 900 | V10001 | V10900 | V10001 / V10002 / V10003 |
| vendor_name | 900 | 0 | 0 | 900 | Abhay Abhay Enterprises | Yamuna Vardhan Security S | Yamuna Elevator Care Pvt Ltd / Dhruv Hygiene Solutions Pvt L |
| category | 900 | 0 | 0 | 11 | Cleaning Material | Water Testing | Lift AMC / Cleaning Material / Diesel Supply |
| state | 900 | 0 | 0 | 5 | Delhi | Uttar Pradesh | Delhi / Uttar Pradesh / Haryana |
| gstin | 900 | 0 | 0 | 900 | 03AJVFJ5959X1ZP | 09ZZEPV5121J1Z7 | 07SBDPT4452Q1ZF / 07BTTFV3567V1Z1 / 07FOSFO5228F1ZN |
| msme_status | 900 | 0 | 0 | 5 |  | Small | Micro / Not MSME / Small |

## work_orders.csv
rows=2092 cols=10

| column | non-null | null | blank | unique | min | max | sample |
|---|---|---|---|---|---|---|---|
| wo_id | 2092 | 0 | 0 | 2092 | 4100001 | 4102092 | 4100001 / 4100002 / 4100003 |
| vendor_id | 2092 | 0 | 0 | 899 | V10001 | V10900 | V10021 / V10882 / V10139 |
| property_code | 2092 | 0 | 0 | 38 | DEL-R03 | SNP-R21 | NOI-C32 / SNP-C30 / NOI-C33 |
| category | 2092 | 0 | 0 | 11 | Cleaning Material | Water Testing | Cleaning Material / Security Manpower / Water Testing |
| valid_from | 2092 | 0 | 0 | 201 | 2024-09-13 | 2025-04-01 | 2024-10-08 / 2025-02-04 / 2024-10-28 |
| valid_to | 2092 | 0 | 0 | 302 | 2025-02-03 | 2026-09-27 | 2026-05-13 / 2026-05-30 / 2026-03-14 |
| gl_code | 2092 | 0 | 0 | 2063 | 610035 | 699997 | 680722 / 624111 / 699709 |
| cost_centre | 2092 | 0 | 0 | 38 | CC-DEL-R03 | CC-SNP-R21 | CC-NOI-C32 / CC-SNP-C30 / CC-NOI-C33 |
| approved_value_inr | 2092 | 0 | 0 | 2092 | 10003822 | 998216 | 78459 / 8735266 / 30499 |
| billed_value_inr | 2092 | 0 | 0 | 2039 | 0 | 999300 | 64240 / 8646810 / 32850 |

# sap_extract.sqlite
```sql
CREATE TABLE parsed_bill (
    source_file      TEXT NOT NULL,
    parsed_at        TEXT NOT NULL,
    vendor_gstin     TEXT,
    vendor_name      TEXT,
    invoice_no       TEXT,
    invoice_date     TEXT,
    property_code    TEXT,
    wo_id            TEXT,
    taxable_inr      REAL,
    cgst_inr         REAL,
    sgst_inr         REAL,
    igst_inr         REAL,
    total_inr        REAL,
    confidence       REAL,
    check_status     TEXT,
    check_notes      TEXT
)
```
## sqlite:parsed_bill
rows=0 cols=16

| column | non-null | null | blank | unique | min | max | sample |
|---|---|---|---|---|---|---|---|
| source_file | 0 | 0 | 0 | 0 | nan | nan |  |
| parsed_at | 0 | 0 | 0 | 0 | nan | nan |  |
| vendor_gstin | 0 | 0 | 0 | 0 | nan | nan |  |
| vendor_name | 0 | 0 | 0 | 0 | nan | nan |  |
| invoice_no | 0 | 0 | 0 | 0 | nan | nan |  |
| invoice_date | 0 | 0 | 0 | 0 | nan | nan |  |
| property_code | 0 | 0 | 0 | 0 | nan | nan |  |
| wo_id | 0 | 0 | 0 | 0 | nan | nan |  |
| taxable_inr | 0 | 0 | 0 | 0 | nan | nan |  |
| cgst_inr | 0 | 0 | 0 | 0 | nan | nan |  |
| sgst_inr | 0 | 0 | 0 | 0 | nan | nan |  |
| igst_inr | 0 | 0 | 0 | 0 | nan | nan |  |
| total_inr | 0 | 0 | 0 | 0 | nan | nan |  |
| confidence | 0 | 0 | 0 | 0 | nan | nan |  |
| check_status | 0 | 0 | 0 | 0 | nan | nan |  |
| check_notes | 0 | 0 | 0 | 0 | nan | nan |  |

```sql
CREATE TABLE posted_invoices (bill_id, vendor_id, invoice_no, invoice_date, posted_date, amount_inr, gst_inr, wo_id)
```
## sqlite:posted_invoices
rows=11075 cols=8

| column | non-null | null | blank | unique | min | max | sample |
|---|---|---|---|---|---|---|---|
| bill_id | 11075 | 0 | 0 | 10856 | TRK250001 | TRK261000 | TRK251334 / TRK251981 / TRK260987 |
| vendor_id | 11075 | 0 | 0 | 899 | V10001 | V10900 | V10374 / V10276 / V10695 |
| invoice_no | 11075 | 0 | 0 | 10796 | 001/25-26/009 | 900/25-26/839 | 374/25-26/222 / 276/25-26/722 / 695/25-26/659 |
| invoice_date | 11075 | 0 | 0 | 365 | 2025-04-01 | 2026-03-31 | 2025-05-30 / 2025-07-04 / 2025-06-10 |
| posted_date | 11075 | 0 | 0 | 382 | 2025-04-14 | 2026-04-30 | 2025-06-20 / 2025-10-07 / 2025-07-01 |
| amount_inr | 11075 | 0 | 0 | 9402 | -101828 | 99970 | 3380 / 612810 / 268910 |
| gst_inr | 11075 | 0 | 0 | 8450 | -10134 | 9994 | 608 / 110306 / 0 |
| wo_id | 11075 | 0 | 0 | 2087 | 4100001 | 4102092 | 4100871 / 4100128 / 4100017 |

```sql
CREATE TABLE properties (property_code, property_name, property_type, city, state, units_or_sqft)
```
## sqlite:properties
rows=38 cols=6

| column | non-null | null | blank | unique | min | max | sample |
|---|---|---|---|---|---|---|---|
| property_code | 38 | 0 | 0 | 38 | DEL-R03 | SNP-R21 | FBD-R01 / NOI-R02 / DEL-R03 |
| property_name | 38 | 0 | 0 | 38 | Office Tower, Sector 17,  | Retail Mall, Sector 44, N | Residential Society, Sector 70, Faridabad / Residential Soci |
| property_type | 38 | 0 | 0 | 3 | Office Tower | Retail Mall | Residential Society / Office Tower / Retail Mall |
| city | 38 | 0 | 0 | 7 | Faridabad | Sonipat | Faridabad / Noida / New Delhi |
| state | 38 | 0 | 0 | 3 | Delhi | Uttar Pradesh | Haryana / Uttar Pradesh / Delhi |
| units_or_sqft | 38 | 0 | 0 | 38 | 1037337 | 914 | 1728 / 1249 / 310 |

```sql
CREATE TABLE vendor_master (vendor_id, vendor_name, category, state, gstin, msme_status)
```
## sqlite:vendor_master
rows=900 cols=6

| column | non-null | null | blank | unique | min | max | sample |
|---|---|---|---|---|---|---|---|
| vendor_id | 900 | 0 | 0 | 900 | V10001 | V10900 | V10001 / V10002 / V10003 |
| vendor_name | 900 | 0 | 0 | 900 | Abhay Abhay Enterprises | Yamuna Vardhan Security S | Yamuna Elevator Care Pvt Ltd / Dhruv Hygiene Solutions Pvt L |
| category | 900 | 0 | 0 | 11 | Cleaning Material | Water Testing | Lift AMC / Cleaning Material / Diesel Supply |
| state | 900 | 0 | 0 | 5 | Delhi | Uttar Pradesh | Delhi / Uttar Pradesh / Haryana |
| gstin | 900 | 0 | 0 | 900 | 03AJVFJ5959X1ZP | 09ZZEPV5121J1Z7 | 07SBDPT4452Q1ZF / 07BTTFV3567V1Z1 / 07FOSFO5228F1ZN |
| msme_status | 900 | 0 | 0 | 5 |  | Small | Micro / Not MSME / Small |

```sql
CREATE TABLE work_orders (wo_id, vendor_id, property_code, category, valid_from, valid_to, gl_code, cost_centre, approved_value_inr, billed_value_inr)
```
## sqlite:work_orders
rows=2092 cols=10

| column | non-null | null | blank | unique | min | max | sample |
|---|---|---|---|---|---|---|---|
| wo_id | 2092 | 0 | 0 | 2092 | 4100001 | 4102092 | 4100001 / 4100002 / 4100003 |
| vendor_id | 2092 | 0 | 0 | 899 | V10001 | V10900 | V10021 / V10882 / V10139 |
| property_code | 2092 | 0 | 0 | 38 | DEL-R03 | SNP-R21 | NOI-C32 / SNP-C30 / NOI-C33 |
| category | 2092 | 0 | 0 | 11 | Cleaning Material | Water Testing | Cleaning Material / Security Manpower / Water Testing |
| valid_from | 2092 | 0 | 0 | 201 | 2024-09-13 | 2025-04-01 | 2024-10-08 / 2025-02-04 / 2024-10-28 |
| valid_to | 2092 | 0 | 0 | 302 | 2025-02-03 | 2026-09-27 | 2026-05-13 / 2026-05-30 / 2026-03-14 |
| gl_code | 2092 | 0 | 0 | 2063 | 610035 | 699997 | 680722 / 624111 / 699709 |
| cost_centre | 2092 | 0 | 0 | 38 | CC-DEL-R03 | CC-SNP-R21 | CC-NOI-C32 / CC-SNP-C30 / CC-NOI-C33 |
| approved_value_inr | 2092 | 0 | 0 | 2092 | 10003822 | 998216 | 78459 / 8735266 / 30499 |
| billed_value_inr | 2092 | 0 | 0 | 2039 | 0 | 999300 | 64240 / 8646810 / 32850 |
