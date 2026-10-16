# Understanding the vendor-payments case

Built only from the documents in `pack/context/` and `pack/BRIEF.md`. No data file has been opened. Everything in double quotes is a verbatim quote from the file named beside it; anything not in double quotes is my reading, and I say so where it is inference. All paths are under `pack/context/`.

Short names for the files: `transcripts/01-cfo.md`, `02-central-ap-lead.md`, `03-property-commercial-executive.md`, `04-property-head.md`, `05-security-agency-owner.md`, `06-it-head.md`, `07-procurement-executive.md`.

---

## 1. The seven people

### 1.1 CFO (`transcripts/01-cfo.md`)

**Believes**
- The delay is at head office. "Honestly, head office." The basis is hearsay: "It is what I hear from the vendors, mostly."
- AI that reads bills is the fix: "Read the bill, fill the fields, flag the mistakes. My team should only look at exceptions."
- Bills are slow overall: "Forty five, fifty days. Sometimes more."
- Queries are mostly the vendor's fault: "Mostly. Sometimes the property team makes an error in the service entry. But the root is the vendor sending a bad bill."
- He has no stage-level view: "Not stage by stage."
- He distrusts the MSME master: "Whether it is updated, I would not bet on it."

**Wants**
- "Every bill read automatically when it lands at head office. No typing. And a dashboard for me that shows what is stuck and where."
- Success measured by "Days to pay, first. Then fewer calls from vendors. And no MSME disallowance next year."
- "I want a conversation about where the bill is." (not about who is at fault)

**Will not let us change**
- "Controls. Internal audit is strict. The property must certify the work. The original bill has to be with us for GST audit. I am not going to let anyone remove a check just to go faster."

### 1.2 Central AP lead (`transcripts/02-central-ap-lead.md`)

**Believes**
- AP is not the slow part: "The problem is never our speed. The problem is what comes to us."
- A big share of queries come from the company side: "But a big share is our own side. Work order, GL, service entry." She admits she has no count: "Not a clean one. I have not counted it properly."
- Typing is a small slice: "typing is maybe ten percent of our time. Chasing queries is much more. And waiting for packets."
- The double check is justified: "We check again because we have found too many mistakes."

**Wants**
- "Bills that come right the first time. And knowing on Monday what is coming on Friday, so I can plan who does what."

**Will not let us change**
- The line-by-line checking. After the diesel bill whose challan was for another property, "nobody in my team will skip a line." Her reason: "If I get audited, it is my team's name on the posting."
- Originals on file: "The originals are filed here for GST audit."
- She is open on timing only tentatively: "Could we work on a scan and receive the original later? Technically, yes, I think." and "But nobody has asked us to change."

### 1.3 Property commercial executive (`transcripts/03-property-commercial-executive.md`)

**Believes**
- She is the person in the middle: "Being the one in the middle."
- She learns of work-order problems too late: "I find out when the service entry fails."
- Head office repeats her checks: "Queries by email. Many are things I already checked."
- She has no official view of a bill after it leaves: "I do not, officially."

**Wants**
- "Give me one view where biometric, register and the vendor claim are matched, and only show me the people who do not match."
- "Second, tell me before a work order runs out, not after."

**Will not let us change** (not stated; inferred from what she does and says)
- She does the attendance match herself and the department head signs it. She says "the official one is paper at the facility desk." I infer she would not accept a tool that lets a bill skip her attendance match or the facility-desk log. Please treat this as my inference, not her words.

### 1.4 Property head (`transcripts/04-property-head.md`)

**Believes**
- The property is not the delay: "Fast. Once my team has it, it is out in a day or two. We are not the problem. I have seen bills sit at head office for weeks."
- Courier days are minor: "Honestly, a few days here and there is not the issue. The issue is what happens after."
- Head office duplicates the property's work: "Then head office checks everything again and asks us the same questions."

**Wants**
- "One check, done once, by whoever is best placed. And give the vendor a way to see where his bill is, so he stops calling me."

**Will not let us change**
- His signature: "My signature says the work was done and the bill is correct." He signs on the summary and exceptions: "I do not check every line."

### 1.5 Security agency owner, a micro vendor (`transcripts/05-security-agency-owner.md`)

**Believes**
- Payment is slow and he cannot see why: "Five weeks if everything is fine. Sometimes two months."
- His MSME status was never recorded: "I registered three years ago. I sent it to procurement by email. Nobody confirmed."
- Many queries are not his fault: "Many. Work order finished, so they cannot book."
- He is blind after submission: "Usually I call three, four times for each bill."

**Wants**
- Status in six words: "Received. Checked at property. With head office. Query, and what the query is. Paid, and the date."
- "Tell me about the query the same day. Not after three weeks."
- Channel: "WhatsApp. Everyone in my office has WhatsApp. Email also fine."

**Will not let us change** (no control; his red line is a channel)
- "So please, no portal." He also pays his guards "on the seventh" every month, so he cannot absorb a slower cycle.

### 1.6 Head of IT (`transcripts/06-it-head.md`)

**Believes**
- The end state is a portal: "We need a proper vendor portal."
- The earlier OCR pilot failed because it fixed the wrong step: "It fixed the typing, and typing was not the slow part."
- He lacked data to win budget: "I did not have a number. I had complaints."

**Wants**
- "Honestly, show me where the time goes with data."
- "I do not want another pilot that closes green and changes nothing."

**Will not let us change**
- Control and audit: "But keep it inside something we can control and audit."
- WhatsApp only in a controlled form: "If we do WhatsApp, it has to be the business API with our own number and the files stored on our side."
- Writing to SAP is a project, not a switch: "Writing invoices into SAP from outside needs a project with our SAP partner and audit sign-off."

### 1.7 Procurement executive (`transcripts/07-procurement-executive.md`)

**Believes**
- Work orders break because scope changes are not reported: "Nobody tells procurement."
- Amendments are slow because of paper, not procurement: "Once I have all the paper, an amendment is a week. Maybe less. The waiting is for paper."
- His monthly expiry report is ignored: "Honestly, I do not know if anybody opens it. Nobody has ever replied."
- GL errors are real but rarer than balance and validity: "Two, three a month, maybe." and "The bigger one is balance and validity."

**Wants**
- "Tell me before the order runs out, not after."
- "And give the property a simple way to see how much balance is left."

**Will not let us change**
- The approvals: "The approvals. I do not like the paper either." The reason: "But without the RWA letter, audit will catch us."

---

## 2. Claims ledger

"Test" says how to check the claim with the pack data later. Field names come from `context/documents/data-dictionary.md`. Nothing here has been run. "Stage" means the gaps between consecutive dates in `bill_register.csv`: `desk_received_date`, `property_verified_date`, `property_head_signed_date`, `ho_received_date`, `ho_picked_date`, `posted_date`, `paid_date`.

| ID | Claim (verbatim) | Who | Source file | How to test with the pack data |
|---|---|---|---|---|
| L1 | "Forty five, fifty days. Sometimes more." | CFO | transcripts/01-cfo.md | Days from `desk_received_date` (and from `invoice_date`) to `paid_date`: median, 90th percentile, share over 45 and over 60. Report both start points. |
| L2 | "Honestly, head office." | CFO | transcripts/01-cfo.md | Split total days into property stage (`desk_received_date` to `property_head_signed_date`), courier (`property_head_signed_date` to `ho_received_date`), HO wait (`ho_received_date` to `ho_picked_date`), HO work (`ho_picked_date` to `posted_date`) and treasury (`posted_date` to `paid_date`). Compare shares. |
| L3 | "I would say maybe one in five bills." | CFO | transcripts/01-cfo.md | Count distinct `bill_id` in `queries.csv` divided by bills in `bill_register.csv`. Check for `bill_id` values in queries that do not exist in the register. |
| L4 | "Mostly. Sometimes the property team makes an error in the service entry. But the root is the vendor sending a bad bill." | CFO | transcripts/01-cfo.md | Re-label each query from `query_text` (not `query_category`) as vendor error, property error, work-order/procurement or head-office. Compare shares. See L13 for the competing claim. |
| L5 | "if we pay a micro or small vendor late, we cannot claim that expense in the year." | CFO | transcripts/01-cfo.md | Join `bill_register.csv` to `vendors.csv`. Count bills for Micro and Small vendors paid after day 45, using more than one clock start (desk, property verified). Also count bills still unpaid at 30 April 2026 that are past day 45. This tests the size of the exposure, not the tax rule itself. |
| L6 | "Some vendors registered after they started with us and nobody updated the master." | CFO | transcripts/01-cfo.md | Share of `vendors.csv` with blank `msme_status`. Compare `vendor_master` in `sap_extract.sqlite` with `vendors.csv`. Look for small, long-standing vendors recorded as Not MSME. |
| L7 | "I think the team insists on the physical copy before they book." | CFO | transcripts/01-cfo.md | Courier gap (`property_head_signed_date` to `ho_received_date`) and the gap from `ho_received_date` to `posted_date`. If posting never happens before `ho_received_date`, that is consistent with the claim but does not prove it is a rule. |
| L8 | "If the packet is complete, we post it in two days." | AP lead | transcripts/02-central-ap-lead.md | `ho_picked_date` to `posted_date` for bills with no row in `queries.csv`. Compare with `ho_received_date` to `posted_date`. |
| L9 | "Honestly most bills take ten, fifteen minutes to verify." | AP lead | transcripts/02-central-ap-lead.md | Not testable: the data has dates, not effort. Only the elapsed days in L8 can be checked. |
| L10 | "The problem is never our speed. The problem is what comes to us." | AP lead | transcripts/02-central-ap-lead.md | Same stage split as L2, plus the time bills spend open in `queries.csv` (`raised_date` to `resolved_date`). If HO work time is short and query time is long, the claim holds. |
| L11 | "typing is maybe ten percent of our time. Chasing queries is much more. And waiting for packets." | AP lead | transcripts/02-central-ap-lead.md | Cannot measure typing. Proxy: the share of `ho_received_date` to `paid_date` that is query-open days, versus `ho_picked_date` to `posted_date` on clean bills. |
| L12 | "Mostly they land Friday, sometimes Monday if the courier is late." | AP lead | transcripts/02-central-ap-lead.md | Weekday distribution of `ho_received_date`. |
| L13 | "But a big share is our own side. Work order, GL, service entry." | AP lead | transcripts/02-central-ap-lead.md | Same re-labelling as L4. Cross-check with `work_orders.csv`: bills dated outside `valid_from` to `valid_to`, or where `billed_value_inr` exceeds `approved_value_inr`. |
| L14 | "People put a lot under Other." | AP lead | transcripts/02-central-ap-lead.md | Share of `query_category` equal to Other. Then classify those from `query_text` to see what is hidden. |
| L15 | "A missing challan, a week." | AP lead | transcripts/02-central-ap-lead.md | `resolved_date` minus `raised_date` for challan queries (found via `query_text`), median. |
| L16 | "That can be a month." (work-order amendment) | AP lead | transcripts/02-central-ap-lead.md | `resolved_date` minus `raised_date` for work-order queries. Compare with L33 and L34. |
| L17 | "In practice when the split is wrong, my verifier stops there." | AP lead | transcripts/02-central-ap-lead.md | Bills with two or more rows in `queries.csv`. Check whether later queries are raised only after the earlier one is resolved. Count how many could have been raised on day one. |
| L18 | "A vendor in Delhi charges IGST to a property in Delhi, or puts 12 percent where it should be 18." | AP lead | transcripts/02-central-ap-lead.md | `vendors.csv` `state` vs `properties.csv` `state`. `gst_inr` / `amount_inr` ratio per bill. Count bills where the tax type or rate does not fit. The register has no tax-type column, so same-state IGST is only visible in the bill-inbox and `parsed_bill` fields. |
| L19 | "Audit needs the original on file, not in my hand on the day I post." | AP lead | transcripts/02-central-ap-lead.md | Not testable with data. It is a legal question for the client's tax adviser. See section 4. |
| L20 | "Fast. Once my team has it, it is out in a day or two. We are not the problem." | Property head | transcripts/04-property-head.md | Property stage and `property_verified_date` to `property_head_signed_date`, per property. Look at the tail, not just the median. |
| L21 | "I have seen bills sit at head office for weeks." | Property head | transcripts/04-property-head.md | `ho_received_date` to `ho_picked_date` and to `posted_date`: share over 14 days. Split by clean vs queried bills. |
| L22 | "Honestly, a few days here and there is not the issue. The issue is what happens after." | Property head | transcripts/04-property-head.md | Courier gap and head-office stage lengths side by side. Also weekday of `property_head_signed_date` vs Thursday pickup (L26). |
| L23 | "Then head office checks everything again and asks us the same questions." | Property head | transcripts/04-property-head.md | Query texts that ask for something the property checklist already covers (P1 to P9 vs H1 to H9, which overlap). Share of queries on items the property had certified. |
| L24 | "The tracker number on the cover was written wrong, so head office had logged it under another vendor." | Property head | transcripts/04-property-head.md | Query texts mentioning not received, not found or wrong vendor. Bills with a very long `property_head_signed_date` to `ho_received_date` gap. Cannot be proven from the register alone. |
| L25 | "If the society added two guards in December, the value runs out before March." | Commercial executive | transcripts/03-property-commercial-executive.md | `work_orders.csv`: `billed_value_inr` against `approved_value_inr` and `valid_to`. Find orders exhausted before the end of the validity period, and the bills raised after exhaustion. |
| L26 | "Courier picks up on Thursday." | Commercial executive | transcripts/03-property-commercial-executive.md | Weekday of `property_head_signed_date` and of `ho_received_date`. A Thursday-sign / Friday-receive pattern would support it. |
| L27 | "He tries to do it once or twice a week." | Commercial executive | transcripts/03-property-commercial-executive.md | Gap `property_verified_date` to `property_head_signed_date`, and number of signing days per week per property. |
| L28 | "I find out when the service entry fails." | Commercial executive | transcripts/03-property-commercial-executive.md | Compute for each work order the date it hit full balance or validity. Check how many bills were raised after that date, and whether a warning N days earlier would have fired. Only a back-test; the data has no record of when the failure was noticed. |
| L29 | "Nobody has time to check SAP for forty work orders every week." | Commercial executive | transcripts/03-property-commercial-executive.md | Count of work orders per property in `work_orders.csv` (compare with procurement's "Forty orders per property"). |
| L30 | "The reliever is not in biometric. He signs the gate register." | Commercial executive | transcripts/03-property-commercial-executive.md | `attendance-sample/`: people in `gate_register_transcribed.csv` and `vendor_claim.csv` who are absent from `biometric_export.csv`. |
| L31 | "But the reliever's name is spelt differently in two places." | Commercial executive | transcripts/03-property-commercial-executive.md | Fuzzy-match names across the three attendance files. Count names that match only approximately. |
| L32 | "I am doing the attendance for four, five days every month with a highlighter." | Commercial executive | transcripts/03-property-commercial-executive.md | Person-days that disagree across biometric, register and claim in the February sample. Hours are not in the data; only the size of the mismatch set is. |
| L33 | "Once I have all the paper, an amendment is a week. Maybe less. The waiting is for paper." | Procurement executive | transcripts/07-procurement-executive.md | `queries.csv` work-order queries: time to resolve. `work_orders.csv` has no amendment date, so the amendment itself cannot be timed directly. |
| L34 | "The commercial executive thinks procurement sat on it for five weeks." | Procurement executive | transcripts/07-procurement-executive.md | Trace the December housekeeping bill with a club cost centre through `queries.csv` (several queries, one on work-order balance). Compare dates in his account (8 Jan, 20 Jan, 11 Feb, 13 Feb) with the data. |
| L35 | "I run a report on the first of every month. Orders ending in the next sixty days." | Procurement executive | transcripts/07-procurement-executive.md | For each bill that failed on expiry, check whether `valid_to` fell inside a 60-day window on the preceding 1st. That shows whether the report would have caught it. Whether anyone opened it is not in the data. |
| L36 | "Two, three a month, maybe." (GL errors) | Procurement executive | transcripts/07-procurement-executive.md | Count GL-related queries per month from `query_text`. Compare `gl_code` on `work_orders.csv` with the category of the bill. |
| L37 | "Eleven amendment requests in four days. No, twelve" (second week of February) | Procurement executive | transcripts/07-procurement-executive.md | Work-order queries raised in the second week of February 2026 in `queries.csv`. Look for a spike by `raised_date`. |
| L38 | "I said, sir, these orders were fine in December." | Procurement executive | transcripts/07-procurement-executive.md | Reconstruct `billed_value_inr` against `approved_value_inr` as of 31 December 2025 using the bill register. |
| L39 | "Most of them are for a year." | Procurement executive | transcripts/07-procurement-executive.md | Distribution of `valid_to` minus `valid_from` in `work_orders.csv`. |
| L40 | "MSME certificates, if somebody sends one later, it may sit." | Procurement executive | transcripts/07-procurement-executive.md | Same as L6. |
| L41 | "Five weeks if everything is fine. Sometimes two months." | Agency owner | transcripts/05-security-agency-owner.md | Days to pay for security-category vendors, split by clean vs queried bills. |
| L42 | "I registered three years ago. I sent it to procurement by email. Nobody confirmed." | Agency owner | transcripts/05-security-agency-owner.md | `msme_status` of security vendors with orders at about six properties in Haryana. Do not try to identify him; count how many look like his profile and have blank or Not MSME status. |
| L43 | "Last month they said IGST is wrong. Our office is in Faridabad, the property is in Gurugram, both Haryana." | Agency owner | transcripts/05-security-agency-owner.md | As L18: same-state vendor and property combined with IGST in `parsed_bill` (bill-inbox) or in query text. |
| L44 | "Many. Work order finished, so they cannot book." | Agency owner | transcripts/05-security-agency-owner.md | Same as L13, split by vendor. Count bills whose `invoice_date` is after the work order's `valid_to`. |
| L45 | "Sometimes they cut the days. I accept it because what can I do." | Agency owner | transcripts/05-security-agency-owner.md | `attendance-sample/vendor_claim.csv` days per person against the days supported by biometric plus register. Also negative-amount credit notes in `bill_register.csv`. |
| L46 | "Diwali time. October bill." / "Paid in December. Two months." | Agency owner | transcripts/05-security-agency-owner.md | Days to pay for October 2025 security bills, and any with an expired work order. |
| L47 | "Usually I call three, four times for each bill." | Agency owner | transcripts/05-security-agency-owner.md | No call log in the pack. Compare with the survey's "Vendors call the property or head office 3 times per bill on average to ask for status" (`documents/vendor-survey-summary.md`). Cannot be verified from the data. |
| L48 | "Around ninety percent on the main fields." (past OCR pilot) | IT head | transcripts/06-it-head.md | Not testable on the pack. We can measure our own reader on the 40 bills in `bill-inbox/` against the values we read by eye. |
| L49 | "It fixed the typing, and typing was not the slow part." | IT head | transcripts/06-it-head.md | Same stage split as L2 and L10. |
| L50 | "Thirty eight Excel files on a shared drive." | IT head | transcripts/06-it-head.md | Number of distinct `property_code` values in `bill_register.csv` (expect 38). Look for inconsistent dates or values that show the merge from 38 formats. |
| L51 | "We have RFC access for reading work orders, service entries and posting status." | IT head | transcripts/06-it-head.md | List the tables in `sap_extract.sqlite`. The spec names `vendor_master`, `work_orders`, `properties` and `posted_invoices`; no service-entry table is listed. |
| L52 | "If it is mandatory, they will." (use a portal) | IT head | transcripts/06-it-head.md | Not testable. Survey: portal preferred by 9%; "12% said they already use a portal for another large client and find it hard to use". |
| L53 | "Do not know where my bill is" | Vendor survey (71%) | documents/vendor-survey-summary.md | Share of bills where there is no visible status change a vendor could see between `desk_received_date` and `paid_date`. Not directly testable; the data shows dates, not what vendors were told. |
| L54 | "Queries come late" | Vendor survey (48%) | documents/vendor-survey-summary.md | `raised_date` minus `ho_received_date` (and minus `ho_picked_date`) per query. |
| L55 | "Same bill delivered to several places" | Vendor survey (33%) | documents/vendor-survey-summary.md | Duplicate `invoice_no` per `vendor_id` in `bill_register.csv` (check H13 covers this). The bill-inbox has a repeat-invoice packet to test against `posted_invoices`. |
| L56 | "Payment amount differs from bill without explanation" | Vendor survey (19%) | documents/vendor-survey-summary.md | The register has no paid-amount column. Only credit notes and attendance cuts (L45) are visible. |
| L57 | "MSME vendors registered as micro or small: payment within 45 days of accepting the goods or services, as required by law" | Payment policy | documents/payment-policy.md | See L5. The policy says "accepting"; the register has several candidate dates. Which date starts the clock is a question for the client's tax adviser. |

---

## 3. Where stakeholders contradict each other

Each point names the claims in the ledger.

1. **Where the time goes.** CFO: "Honestly, head office." Property head: "I have seen bills sit at head office for weeks." AP lead: "The problem is never our speed. The problem is what comes to us." IT head: "typing was not the slow part." Procurement: "The waiting is for paper." Four views, four places. Test: L2, L10, L21, L49.
2. **Whose mistakes cause the queries.** CFO: "the root is the vendor sending a bad bill." AP lead: "a big share is our own side." Agency owner: "Many. Work order finished, so they cannot book." Procurement: "Nobody asks why the scope changed without anyone telling us." The AP lead and the CFO both admit they do not have a count. Test: L3, L4, L13.
3. **Checking twice.** AP lead: "We check again because we have found too many mistakes." Property head: "Then head office checks everything again and asks us the same questions." The two checklists overlap on P1/H1, P2/H2, P4/H4, P5/H5, P6/H6, P7/H7, P8/H8, P9/H9. Test: L23.
4. **How long a work-order amendment takes.** Commercial executive: "The amendment came on the thirteenth of February" for a request mailed on 8 January. Procurement: "Once I have all the paper, an amendment is a week. Maybe less." Both accounts can be true if the paper took five weeks. They disagree on who owns the delay. Agency owner: "Procurement does not pick up." Test: L16, L33, L34.
5. **Who watches work-order balance.** Procurement runs a 60-day expiry report and says "Nobody has ever replied." Commercial executive: "I find out when the service entry fails." Procurement also says "I cannot see how fast a property is using up a work order". The expiry report does not cover balance, so the main failure mode (balance used up early) has no owner. Test: L28, L35.
6. **How fast the property is.** Property head: "Fast. Once my team has it, it is out in a day or two." Commercial executive: "Whatever is signed by Thursday morning goes. If the property head is travelling, it waits for next Thursday." Same property side, different pictures. Test: L20, L26, L27.
7. **Whether head office needs the physical bill before posting.** CFO: "I think the team insists on the physical copy before they book." AP lead: "We have always worked on the physical packet" but "Audit needs the original on file, not in my hand on the day I post." Policy: "Scans may be used for reference". Nobody has the legal answer, and the AP lead hedges ("Technically, yes, I think"). Test: L7, L19.
8. **What to build.** CFO: "Every bill read automatically when it lands at head office." AP lead: typing is "maybe ten percent of our time." IT head: the earlier OCR pilot "did not change anything". IT head wants a portal; the agency owner says "So please, no portal"; the survey has 58% preferring WhatsApp and 9% a portal. IT head also says WhatsApp "has to be the business API".
9. **MSME records.** Policy: "Vendors must share their Udyam registration at onboarding". CFO: "Procurement collects the certificate at onboarding." Agency owner: "Nobody confirmed." Procurement: "that mailbox is not checked every day". The CFO's own tax exposure estimate "was built on the master data". Test: L5, L6, L42.
10. **Frequency of GL errors.** AP lead lists "the GL is wrong" among the main causes. Procurement says "Two, three a month, maybe." Test: L36.
11. **What SAP can show us.** IT head: "We have RFC access for reading work orders, service entries and posting status." The extract spec lists four tables and none is a service-entry table. Test: L51.
12. **Time to sort a reliever dispute.** Commercial executive: "maybe half a day if it is clean" and "two, three days" if CCTV is needed. Agency owner: "That check takes one week." Test: L30, L31, L45.

---

## 4. Controls we must not weaken

Each one is stated by the person or document named. None of them should be removed, shortened or made optional by anything we build.

| # | Control | Who says so | Quote | Note for us |
|---|---|---|---|---|
| K1 | **Original bill kept at head office for GST audit** | CFO; AP lead; payment policy | CFO: "The original bill has to be with us for GST audit." AP lead: "The originals are filed here for GST audit." Policy: "Original bills and supporting documents are filed at head office" | The requirement is that the original is on file. Whether it must be in hand before posting is unresolved (section 3, point 7). Any design that works from a scan must still keep the original arriving and filed, and I would ask the client's tax adviser before we claim otherwise. |
| K2 | **Property certifies the work** | CFO; property head; property checklist; payment policy | CFO: "The property must certify the work." Property head: "My signature says the work was done and the bill is correct." Checklist P11: "Property head has signed the packet" | Packaged into the definition of a valid invoice: "It passes the property and head office checklists". We can make the signing faster or visible. We cannot sign for him or skip him. |
| K3 | **RWA letter for work-order amendments** | Procurement | "For residential, a letter from the RWA approving the extra scope." and "But without the RWA letter, audit will catch us." | Also: "If the value goes up, a budget approval from finance" and, for office towers, "the tenant's approval if it is recoverable". We can ask for the letter earlier and track it; we cannot waive it. |

Further constraints stated in the documents that I would treat as fixed:

- **Head-office tax checks (H10 to H14)**: GST type, HSN/SAC and rate, GL and cost centre, duplicate invoice number, TDS section and rate (`documents/head-office-checklist.md`). These are not on the property checklist. The AP lead's stated reason for AP's own checking is "If I get audited, it is my team's name on the posting."
- **A human answers for each posting.** A verifier told IT: "if the machine reads the wrong GSTIN, who will answer audit, me or the machine?" (`transcripts/06-it-head.md`). A reader we build should propose, and a person should confirm.
- **SAP writes are out of scope.** "Writing invoices into SAP needs a separate project with the SAP partner and audit sign-off" (`documents/sap-extract-spec.md`). IT head puts the lead time at "seven, eight months before anybody wrote code." The prototype writes to `parsed_bill` only. Reading is approved ("Reading these tables over RFC is approved and available").
- **Payment timing rules.** MSME: "within 45 days of accepting the goods or services"; others: "within 60 days of a valid invoice"; "Payment runs happen every Tuesday and Friday" (`documents/payment-policy.md`).
- **Audit trail on messaging.** IT head would accept WhatsApp only through the business API with "the files stored on our side", not forwarded photos.
- **Vendors' pay cycle.** The agency owner pays guards "on the seventh. Every month." Anything that adds days for vendors lands on them first.
