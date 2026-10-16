# Data dictionary

All files are in `data/`. Dates are `YYYY-MM-DD`. Amounts are in INR. The extract covers bills dated 1 April 2025 to 31 March 2026, with status as of 30 April 2026.

## bill_register.csv

One row per bill, merged from the 38 property registers and SAP posting data.

| Column | Meaning |
|---|---|
| bill_id | Tracker number assigned at the facility desk |
| vendor_id | Vendor code, joins to `vendors.csv` |
| property_code | Property code, joins to `properties.csv` |
| category | Spend category |
| doc_type | `invoice` or `credit_note` |
| invoice_no | Vendor's invoice number |
| invoice_date | Date on the vendor's bill |
| desk_received_date | Date the facility desk logged the bill |
| property_verified_date | Date the commercial executive finished checks and created the service entry or GRN |
| property_head_signed_date | Date the property head signed the packet |
| ho_received_date | Date the packet reached head office |
| ho_picked_date | Date a central AP verifier started work on the bill |
| ho_verifier | Verifier code |
| posted_date | Date the invoice was posted in SAP |
| paid_date | Date of payment |
| amount_inr | Bill amount before GST. Credit notes are negative. |
| gst_inr | GST charged on the bill |
| wo_id | Work order or purchase order number, joins to `work_orders.csv` |
| status | Status on 30 April 2026 |

## queries.csv

One row per query raised by central AP.

| Column | Meaning |
|---|---|
| query_id | Query reference |
| bill_id | Bill the query is about |
| raised_date | Date the query was raised |
| resolved_date | Date the query was closed. Blank if open. |
| raised_by | Verifier code |
| query_category | Category picked by the verifier |
| query_text | Text of the query email |

## vendors.csv

| Column | Meaning |
|---|---|
| vendor_id | Vendor code |
| vendor_name | Registered name |
| category | Main spend category |
| state | State of registration |
| gstin | GSTIN from the vendor master |
| msme_status | Micro, Small, Medium, Not MSME, or blank if unknown |

## work_orders.csv

| Column | Meaning |
|---|---|
| wo_id | Work order or purchase order number |
| vendor_id | Vendor code |
| property_code | Property code |
| category | Spend category |
| valid_from, valid_to | Validity period |
| gl_code | GL account |
| cost_centre | Cost centre |
| approved_value_inr | Approved value |
| billed_value_inr | Value billed against it so far |

## properties.csv

| Column | Meaning |
|---|---|
| property_code | Property code |
| property_name | Type and location |
| property_type | Residential Society, Office Tower or Retail Mall |
| city, state | Location |
| units_or_sqft | Residential units, or leasable area in square feet |

## attendance-sample/

One month of security attendance at one property, February 2026.

| File | Meaning |
|---|---|
| biometric_export.csv | Gate biometric punches per guard per day |
| gate_register_transcribed.csv | The paper gate register, typed up. Includes relievers. |
| vendor_claim.csv | Days per person claimed on the agency's bill |

## sap_extract.sqlite

A read-only SAP extract plus one table to write to. See `sap-extract-spec.md`.

## bill-inbox/

Not data, but listed here for completeness. 40 bills in `context/documents/bill-inbox/`, with an index of file and format.
