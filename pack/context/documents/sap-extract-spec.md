# SAP extract

`data/sap_extract.sqlite` stands in for the company's SAP. IT shared a read-only extract of the tables below. The real system is not available.

## Tables you can read

| Table | What it holds |
|---|---|
| vendor_master | Vendor code, name, category, state, GSTIN and MSME status |
| work_orders | Work orders and purchase orders with validity, GL, cost centre, approved value and value billed so far |
| properties | Property code, name, type and location |
| posted_invoices | Invoices already posted in SAP, with invoice number and date |

## Table you can write

`parsed_bill` is empty. It is where a bill read from the inbox would be recorded before posting.

| Column | Meaning |
|---|---|
| source_file | File name in `context/documents/bill-inbox/` |
| parsed_at | When the bill was read |
| vendor_gstin, vendor_name | As printed on the bill |
| invoice_no, invoice_date | As printed on the bill |
| property_code | Property the bill is for |
| wo_id | Work order or purchase order number on the bill |
| taxable_inr, cgst_inr, sgst_inr, igst_inr, total_inr | Amounts as printed |
| confidence | How sure the reader is about the fields, 0 to 1 |
| check_status | Outcome of any checks, for example `ok` or `query` |
| check_notes | Why a check failed |

## What the real SAP connection allows

- Reading these tables over RFC is approved and available
- Writing invoices into SAP needs a separate project with the SAP partner and audit sign-off
