# vendor-payments: brief

## The client

A North Indian real estate developer based in NCR manages 38 residential societies, office towers and retail malls through its property management division. About 900 vendors supply these properties with security guards and housekeeping staff. Others provide maintenance contracts, diesel and consumables. Together they raise about 11,000 bills a year which the division books in SAP.

## The ask

The CFO wants vendor bills paid faster. Vendors complain about the wait and the central accounts team says it is overloaded. Late payment to small vendors now also carries a tax cost under the MSME payment rule.

The CFO's starting idea is to use AI to read bills at head office and cut data entry. You are free to agree or disagree.

Your job:

1. Find out where the time actually goes between a vendor raising a bill and getting paid
2. Decide which one or two problems are worth solving first
3. Build a working prototype that fixes them
4. Show how much faster or cleaner the process gets, with numbers

## What is in this folder

| Path | Contents |
|---|---|
| `context/org/` | Company profile, teams and systems |
| `context/transcripts/` | Seven stakeholder interviews from a discovery week |
| `context/documents/` | Checklists, payment policy, vendor survey, data dictionary, SAP extract spec |
| `context/documents/bill-inbox/` | 40 bills as they reach the properties: full packets, PDFs, scans and phone photos |
| `data/` | Bill register, vendors, work orders, queries, one month of attendance records |
| `data/sap_extract.sqlite` | A stand-in for SAP, with a table to record bills you read |

## Things to know

- The interviews reflect what people believe. They may not match the data.
- The data is an export from the client's systems. Treat it as you would treat real client data.
- The prototype does not need to connect to SAP. `data/sap_extract.sqlite` stands in for it. Explain what a real connection would need.
- Any resemblance to a real company, person or vendor is coincidental.

Read the 1-pager at the root of this repo for what to submit and how you are assessed.
