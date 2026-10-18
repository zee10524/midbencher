# Research notes: rules and practice that change design decisions

Secondary research from public web sources, **16 October 2026** (every source below was accessed that day). **This is not legal or tax advice.** It records what the sources say, how sure I am, and what each finding changes in the design. Items I could not verify are marked **UNVERIFIED** and gathered in section 10.

**Evidence labels.** `[P]` primary text I read (statute or government document). `[S]` secondary commentary I opened and read. `[s]` secondary commentary seen only as a search-result summary, not opened. `[V]` vendor or marketing page: weigh as a claim, not a measurement. Numbers in square brackets such as [7] point to the source list in section 11.

## Summary: decisions this research drives

| # | Decision | Because | Confidence |
|---|---|---|---|
| 1 | Primary MSME clock starts at `desk_received_date`; show verified and invoice dates as floor and bracket; label results "at least" | Statutory clock starts at acceptance or deemed acceptance, i.e. delivery, earlier than any register date (s.2(b), s.15) `[P]` | High on the statute; which date counts as acceptance is for counsel |
| 2 | Store a payment term (days, or none) per work order; default warning at 45 days; flag "may be 15 days" where no written term | s.15: a written term may not exceed 45 days; with no written term the due date is 15 days after acceptance `[P]` | High on the statute; pack has no term field |
| 3 | Do not block booking on arrival of the paper original; keep the original filed and linked to the scan | No source found requires the paper original before booking; GST needs possession of the invoice and 72 months' retention, electronic records allowed `[S]` | Medium: the scan-only retention question is not settled by what I found |
| 4 | Validate tax type from the **supplier GSTIN state and the recipient GSTIN state on the bill**, not from the property's address; treat security bills as a special case | Place of supply for B2B services is the location of the registered recipient; reverse charge applies to security personnel from non-corporate suppliers `[S][s]` | Medium |
| 5 | Keep TDS section and tax rules as dated reference data; store the TDS section per work order and flag mismatches rather than decide | Contractor versus professional/technical is a judgement for AMCs; the Income-tax Act 2025 renumbers TDS from 1 April 2026 `[S]` | Medium |
| 6 | Check invoices against the work order and SAP on the day they reach the desk, route each exception to its owner, and measure first-time-right rate and touchless rate, not field accuracy | Exceptions, not extraction, drive AP cost; the earlier OCR pilot failed the same way `[S][V]` | Medium: sources are mostly vendors |
| 7 | If WhatsApp is used for intake: official Business API on a company-owned number, download each file within hours (not days), store it in company storage in India with its hash, and plan for DPDP consent and safeguards | Webhook media IDs expire after 7 days; Meta keeps media only briefly; DPDP core duties start about May 2027 `[P][S]` | High on Meta's docs; medium on legal characterisation |
| 8 | Do not send real vendor bills to a hosted AI model on a free tier; use a paid no-training tier with a data-processing agreement, or a model inside the client's own boundary | The DPDP duties in section 9.2 apply to personal data in bills (names, GSTINs, bank details), and a free tier may use inputs to improve the provider's products. I did send pack bills to a free tier during testing (`notes/assumptions.md`, assumption 7) | Medium: I did not read the provider's terms; this follows from the brief's instruction and section 9.2 |

## 1. What the pack says

- Payment policy: "MSME vendors registered as micro or small: payment within 45 days of accepting the goods or services, as required by law" (`context/documents/payment-policy.md`).
- Payment policy, vendor master: "Vendors must share their Udyam registration at onboarding".
- CFO: late payment to a micro or small vendor means "we cannot claim that expense in the year" (`transcripts/01-cfo.md`).

## 2. The MSME payment rule: what the Act says, and what "acceptance" means

Source: MSMED Act 2006 as enacted, PRS India copy `[P]` [1]. I did not check later amendments to the text (the micro, small and medium thresholds are set elsewhere and have been revised).

| Provision | What it says, in my words |
|---|---|
| s.2(n), "supplier" | A micro or small enterprise **that has filed a memorandum** with the authority in s.8 (today, Udyam registration). Only such a supplier is protected. |
| s.2(b) and Explanation, "appointed day" | The day after 15 days have passed from the day of acceptance or deemed acceptance. |
| s.2(b) Explanation (i), "day of acceptance" | Either the day of actual delivery of goods or rendering of services, or, if the buyer objects **in writing** within 15 days of delivery, the day the supplier removes the objection. |
| s.2(b) Explanation (ii), "day of deemed acceptance" | If the buyer makes no written objection within 15 days of delivery, the day of actual delivery or rendering. |
| s.15 | The buyer must pay on or before the date **agreed in writing**, or, if there is no agreement, **before the appointed day**. An agreed period can never exceed 45 days from acceptance or deemed acceptance. |
| s.16 | If the buyer does not pay as s.15 requires, compound interest with monthly rests runs from the appointed day (or the day after the agreed date) at three times the bank rate notified by the RBI, whatever the agreement says. |

**What "acceptance" means, in one paragraph.** It is not the date of the bill, the date the bill is received, or the date the buyer finishes its internal checks. It is the day the goods were delivered or the service rendered, unless the buyer objected in writing within 15 days, in which case it is the day the objection is removed. This reading comes straight from the statute text `[P]`. A summary of a 2025 Bombay High Court decision (*Mahindra Defence Systems v Ranjana Industries*) says a buyer that raises no objection within the period is taken to have accepted and cannot reject later `[s]` [26]; **UNVERIFIED**, read the judgment before relying on it.

**Uncertain:** whether the queries AP sends to vendors count as the "written objection regarding acceptance" in s.2(b); how the delivery day is fixed for a monthly service that runs all month.

## 3. The Income-tax Act link: section 43B(h)

I read the tax provision through commentary, not the statute text `[S]` [2][4][5].

- **Section 43B(h)**, inserted by the Finance Act 2023, effective from 1 April 2024 (assessment year 2024-25) [2]: a sum payable to a micro or small enterprise beyond the s.15 time limit is deductible only in the year it is **actually paid**, not the year the liability arose.
- **The usual relief does not apply to clause (h).** The proviso to s.43B that allows a deduction for payment made by the return due date carves out clause (h) [2][4].
- **Payment late but inside the financial year.** One commentary reads the deduction as still available for that year if the late payment is made before 31 March; an amount unpaid at 31 March after its limit has passed is deferred to the year of payment [4]. **UNVERIFIED** against the statute.
- **Who is covered.** Micro and small only; medium enterprises are outside it [2][3][4]. Commentary differs on traders: one says pure retail and wholesale traders are generally outside the protection [4], another says the Act applies to traders [2].
- **Registration.** A supplier that had not filed the memorandum on the transaction date is not a "supplier" under the Act, citing *Gujarat State Civil Supplies Corporation v Mahakali Foods*; a later registration does not help an earlier transaction [2]. **UNVERIFIED.**
- **Successor provision.** From 1 April 2026 the corresponding rule is reported to be s.37(2)(g) of the Income-tax Act 2025; tax years starting before that stay under the 1961 Act, so FY 2025-26 is under s.43B(h) [4][5]. The correspondence is also reported in a Rajya Sabha reply of 21 July 2026 [5]. I have not seen the enacted text of s.37(2)(g).

## 4. Where the MSME reading meets the pack

**4.1 The statutory clock starts earlier than any date in the register.** The register has none of delivery, acceptance or objection dates. The analysis uses three clocks that all start on or after delivery: `invoice_date`, `desk_received_date`, `property_verified_date`. On this reading each understates lateness, with `property_verified_date` the lowest. *To confirm:* which date counts as acceptance, and whether AP queries amount to the written objection in s.2(b).

**4.2 The policy's "45 days" holds only with a written term.** The Act caps an agreed period at 45 days but sets the default at the appointed day, 15 days after acceptance, where nothing is agreed in writing. Secondary sources agree [2][3][4]; one TaxGuru piece says 45 days applies without an agreement, which conflicts with the Act's text [6]. The pack's work-order table has no payment-terms field, so I cannot tell which applies. The stakes, from the data: of known Micro and Small invoices paid, **88.0% were paid more than 15 days after property verification, 97.5% after desk receipt and 99.7% after the invoice date** (`e.sens15.*`), against 6.0%, 10.4% and 20.2% over 45 days. *To confirm:* whether work orders and purchase orders carry a written payment term of 45 days or less.

**4.3 For the tax point, the year-end position matters more than late payment in the year.** If commentary [4] is right, what bears on FY 2025-26 is the amount to micro and small vendors still unpaid at 31 March 2026 after the limit. The analysis counts known Micro and Small invoices unpaid and past 45 days at that date: **13** from property verified, **25** from desk received, **39** from invoice date, and 16.5, 32.0 and 46.6 with blank-status vendors added at the central assumption (`e.ye.*`, `e.scen.*`). Those counts use 45 days. I have **not** computed the year-end position at a 15-day limit.

**4.4 The blank-status vendors are both a data gap and a legal one.** A vendor can only be covered if it was registered when the transaction occurred. The master has no registration date, so a blank can mean not registered, registered and unrecorded, or registered later. The 58.2% assumption in `notes/msme-exposure.md` is a base rate and cannot say which.

**4.5 Some vendors may be traders.** Diesel Supply and Cleaning Material vendors supply goods; whether any are traders outside the protection is a factual question per vendor. The analysis does not exclude any category.

**4.6 Interest is not in the analysis.** s.16 interest needs the acceptance date, the applicable limit and the RBI bank rate for each period. None is in the pack, so no interest figure is given.

## 5. Open questions and the data to ask for (MSME)

| Question | Needed to answer it |
|---|---|
| Which date starts the clock, and does an AP query count as a written objection? | Counsel's view; the written text of the objections or queries sent to vendors, with dates |
| Is there a written payment term, and is it 45 days or less? | Payment-terms clause in work orders and purchase orders; vendor agreements |
| Was each vendor registered when each bill was incurred? | Udyam registration number and date per vendor; the certificate emails to procurement with dates |
| Delivery or service date per bill | Delivery challans, attendance month-ends, service reports |
| Are any vendors traders? | Activity classification on each vendor's registration |
| Treatment of late payment inside the year | The tax adviser's written view for FY 2025-26 |

## 6. Is the original paper invoice needed before booking, or only for retention?

**Short answer.** I found **no source that says GST law requires the paper original in hand before an invoice is booked.** GST law requires that the recipient *possess* a valid tax invoice to claim input tax credit, and that records be *retained* for a set period, and it allows records to be kept electronically. Whether a **scan alone** is accepted as the retained record for an invoice that was issued on paper is **not settled by anything I found**.

**Certain (as far as secondary sources and one primary document go):**

| Point | What the sources say | Label |
|---|---|---|
| Retention period | Accounts and records kept for 72 months. One reading counts from the due date of the annual return for that year, another from the date of filing; the "due date" reading is the more common. Longer if an appeal, revision or investigation is pending (1 year after final disposal, or the normal period, whichever is later). CGST Act s.36 | `[S]` [8][9]. Start date **UNVERIFIED** |
| Electronic records are allowed | CGST Act s.35(1) allows records in electronic form "as per the manner prescribed"; the Rules require authentication by digital signature (Rule 56(15)), proper back-up (Rule 57(1)) and a log of any entry edited or deleted (Rule 56(8)) | `[S]` [8] |
| Invoices must be preserved | Rule 56(16): invoices, bills of supply, credit and debit notes and delivery challans are preserved for the s.36 period | `[S]` [8][9] |
| Input tax credit needs possession of the invoice | CGST Act s.16(2)(a): the recipient must hold a tax invoice, debit note or other prescribed document | `[s]` [10] |
| An e-invoice's authoritative form is electronic | CBIC Circular 160/16/2021-GST (20 September 2021), paragraph 2: no need to carry a **physical copy** of an e-invoice **during movement of goods**; the QR code with the IRN may be shown electronically instead | `[P]` [7]. **This concerns transit, not booking or retention**, so it does not answer the AP question; it shows only that for e-invoices the electronic document is the legal one |
| Electronic books under company law | Companies (Accounts) Rules 2014, Rule 3: books kept electronically must stay accessible in India, in a format that accurately represents the original; accounting software must keep an audit trail that cannot be disabled (from 1 April 2021); back-ups kept on servers physically in India | `[s]` [11] |
| Electronic records satisfy retention duties | IT Act 2000 s.7 treats a retention requirement as met by an electronic record if it stays accessible, is in a format that accurately represents the original, and keeps origin and timing details | `[s]` [12] |

**Not certain:**

- Whether tax officers and auditors accept a scan **in place of** the paper original for an invoice **issued on paper**. The law lets records be electronic; none of the pages I read says a scan of a paper invoice discharges the retention duty or that it does not. *To confirm with the tax adviser and internal audit.*
- Whether the client's own audit or policy requires the paper original on file regardless. The pack's policy says "Original bills and supporting documents are filed at head office", and the AP lead said working on a scan with the original arriving later is "technically" possible but "nobody has asked us to change" (`transcripts/02-central-ap-lead.md`). That is company practice, not something I found in the law.
- Whether any state law or contract adds a paper requirement. Not researched.

**What it changes in the design.**

- Booking does not have to wait for the courier. The product can book from the scan and the data, with the **original still travelling to head office, filed and linked to the booked invoice** (the CFO's control stays).
- For vendors that issue **e-invoices** (reported mandatory above ₹5 crore annual turnover, **UNVERIFIED** against the notification [23][24]), the intake step should read and **validate the IRN and QR code**, because a buyer's credit is reported to be at risk without a valid IRN [23][24]. A printed copy is then only a copy.
- The retained record should be stored as the electronic rules require: access log, edit log, backup, and storage in India (rows above).

## 7. Tax type, place of supply, and TDS

### 7.1 CGST and SGST versus IGST

**Certain `[S]`** [13][14]:
- Inter-State supply (IGST): supplier's location and place of supply are in different States or Union territories (IGST Act s.7). Intra-State (CGST plus SGST): both in the same State (s.8).
- For services between two parties in India (s.12), the **place of supply for a registered recipient is the location of that recipient**, meaning the place of business for which the registration was taken (or the fixed establishment that received the service).
- So the test is the **supplier's State against the State of the recipient's registration**, not the State where the building is.

**Not certain:**
- **Section 12(3)** makes the place of supply the location of the property for services *directly in relation to immovable property* [15]. Whether routine housekeeping, security or building maintenance fall under it is **UNVERIFIED**: the sources I found do not say. If they do, the tax type follows the property's State, not the registration on the bill.
- **Reverse charge on security.** Notification 29/2018-Central Tax (Rate), effective 1 January 2019, puts supply of **security personnel** by a supplier that is **not a body corporate** to a registered recipient under reverse charge, so the supplier's invoice would not carry the tax `[s]` [16]. A single Haryana advance ruling treated an LLP as a body corporate; that binds only the applicant. Later amendments **UNVERIFIED.**

**What it changes in the design.**
- The IGST rule must read the **recipient GSTIN printed on the bill** and the supplier GSTIN, and compare the two State codes (the first two digits). It needs the company's GST registrations by State as reference data; the pack does not list them.
- The pack's own query log shows why: 39 of the 55 "IGST on an intra-State supply" queries (`ev.igst.master_says_different_state`) are on bills where the vendor's State and the property's State differ. That check used property State as a stand-in for recipient registration, which this section says is not the test. *Ask for the company's GSTIN per State.*
- For security vendors, the rule needs **supplier type** (body corporate or not) before it calls a bill without GST wrong. The register shows 18% GST on every non-diesel bill, including security (`gst.rate_18pct_rows`, `gst.rate_zero_all_diesel`), so it cannot show whether reverse charge is applied. *Ask the client.*

### 7.2 TDS: 194C versus 194J, basics

**Certain at the level of basics `[S]`** [17]:
- **194C (contractors):** payments for work including labour supply, repairs and maintenance. Rates 1% for individual or HUF contractors, 2% for others. Thresholds reported as ₹30,000 for a single payment and ₹1,00,000 in the year.
- **194J (professional or technical services):** 10% for professional services (also royalty and directors' fees), 2% for technical services. Threshold raised from ₹30,000 to ₹50,000 from 1 April 2025. Sources disagree on whether the threshold is per category.
- **The grey zone is maintenance contracts.** One tribunal case treated computer AMC payments as professional or technical services rather than contracts for work [17]; the practical test offered is "expert advice or expertise" (194J) against "execution of work" (194C). The AP lead's lift AMC question in the pack is exactly this.
- **New Act from 1 April 2026.** Commentary says TDS moves to section 393 of the Income-tax Act 2025, effective 1 April 2026, with rates and thresholds "largely consistent", new payment codes, and a warning that old section numbers on returns can fail validation [18]. The mapping of 194C and 194J into the section 393 table is **UNVERIFIED**. I did not open the statute.

**What it changes in the design.**
- The product **must not decide** the TDS section for an AMC. It should store, per work order, the section the AP lead has decided (with the note she writes today) and **flag a bill whose deduction differs from it**.
- Rules, sections and rates are **reference data with effective dates**, because the same bill can fall under the 1961 Act numbering or section 393 depending on the date, and the MSME deduction rule changes name on the same date (section 3).
- Year-to-date payments per vendor are needed to apply the aggregate threshold; SAP can supply them.

## 8. Good AP practice: first-time-right, touchless processing, three-way match, why OCR-only projects stall

Most of what is publicly available is vendor writing. The benchmark figures below are definition-dependent and none comes from a primary study I could open, so treat them as ranges.

**Benchmarks, as relayed.**

| Measure | Figure | Source and label |
|---|---|---|
| Invoice exception rate, median | about 5% (95% of disbursements error-free the first time), attributed to APQC | Corpay blog `[V]` [19] |
| Touchless (straight-through) rate, average | 60%, attributed to The Hackett Group, 2025; teams at 30% or more touchless reported to show 3.5 times higher AP productivity | Corpay blog `[V]` [19] |
| Cost per invoice, median; cycle time, median | $6.00; 15 days from receipt to payment, attributed to APQC | Corpay blog `[V]` [19] |
| Best-in-class exception rate | under 9 to 10%, attributed to a PRGX/Ardent Partners report (2023) | Transcepta blog `[V]` [20] |
| Average exception rate | about 22.5%, attributed to Ardent Partners with no report cited | Transcepta FAQ `[V]` [20]. **UNVERIFIED** |

Two summaries of the same Corpay page disagreed on which firm the numbers came from; I rely on the page as fetched. Against these, this client's query rate is **13.1% of bills** (`share.bills_with_query_pct`), and the desk-to-paid mean is **31.3 days** (`policy.all.desk_received.mean`). The definitions differ (a query is not necessarily an "exception"; the benchmark clock starts at receipt), so this is a rough position, not a ranking.

**Three-way match.** The control compares the purchase order (what was ordered), the goods receipt (what was received) and the invoice (what is billed), and pays only when they agree within a tolerance [21]. Points repeated across sources `[V]`:
- Set tolerances as a percentage band plus an absolute floor and review them against real exception data.
- Route each mismatch by cause to an owner and say what closes it.
- **Most exceptions are created upstream** (procurement, receiving, master data), so fixing those shrinks the queue more than AP effort does.
- For services there is no goods receipt; the equivalent is confirmation by the person who ordered. In this client's process that is the **service entry or GRN**, which the property creates *after* the bill arrives.

**First-time-right and touchless.** Practitioners track "first time right rate", exception rate and validation coverage, and validate at intake rather than after the fact [22][23]. Recommended invoice content is a unique invoice number, date, supplier GSTIN, the purchase order reference and, on Indian invoices, HSN/SAC and place of supply [22]. One company's supplier guide (Cognizant) is the only checklist I found; it is one buyer's requirement, not a standard.

**Why OCR-only projects stall `[V]` [20][25][27][28].**
- Reading fields is not what costs time. Handling invoices that cannot post without a person is. The burden moves from keying to exception handling.
- Pilots often work on the standard path and fall back to email and spreadsheets for exceptions. Exceptions need structured routing with owners and a history.
- Approval rules, file naming and supplier master data are left unchanged underneath the tool.
- Accuracy ceilings of 95 to 99% are vendor claims; independent evidence is thin.
- This matches the IT head's account in the pack: the pilot hit its accuracy target, "AP still waited for the physical packet", and "nothing improved for the vendor".

**What it changes in the design.**
- The success measures are **first-time-right rate, share of bills with no query, and days to pay**, not fields read correctly.
- The check runs **on the day the bill reaches the desk**, against the work order and SAP, and tells the owner of the fix (vendor, property, procurement) the same day. From the query analysis, 237 of 1,441 queries could have been caught from the bill and the SAP extract (`layer.A.cum_queries`), 454 if the bill is read (`layer.AB.cum_queries`).
- The reader is an **intake step for a checking and routing process**, not the product. The exception queue, with owners and a history, is the product.
- Tolerances for amount and quantity are configurable per category and tuned on the client's own exception data.

## 9. WhatsApp Business API for document intake, and the data-protection limits

### 9.1 What Meta's documentation says `[P]` for the vendor's own platform

Read from Meta's developer pages [29][30]:
- Incoming media arrives as a media ID and URL in a webhook. The URL **expires after 5 minutes** and needs the access token. The ID in a webhook **expires after 7 days** (IDs from uploads last 30 days). The response carries a SHA-256 hash.
- Documents (PDF, Word, Excel and others) are accepted **up to 100 MB**.
- A "No Storage" setting keeps messages and media in Meta's data centres for at most one hour, with nothing at rest, and webhook retries limited to one hour. It **cannot be combined with** the data-localisation setting, and turning it off means re-registering the number [30].
- Business-initiated messages outside the 24-hour customer-service window need an approved template and **opt-in**; a customer messaging the business does not by itself give that opt-in `[s]` [31]. Template messages are charged per message from 2025 `[s]` [32]; third-party sites give 1 April or 1 July 2025 for the change, which Meta's page puts at 1 April, **UNVERIFIED** here.
- Several providers list **India as an at-rest storage region** chosen when a number is registered, with existing numbers needing re-registration; data may still be processed outside India `[s]` [33]. **Not verified on Meta's own page.**

### 9.2 Data-protection limits

- India's **Digital Personal Data Protection Rules 2025 were notified on 14 November 2025**, with an eighteen-month phased period for compliance `[P]` [34]. Commentary puts the core duties (notice, consent, security safeguards, breach notification) at about **May 2027**, with the exact day varying by source (12, 13 or 14 May), and consent-manager registration about a year after notification `[s]` [35]. A 72-hour breach notice and penalties up to ₹250 crore are reported in commentary only; **UNVERIFIED**.
- The material vendors would send is not only bills. Attendance sheets, PF and ESIC challans, gate-register photos and ID documents carry **employees' personal data**. The IT head's concern is that this already travels on personal phones with no audit trail (`transcripts/06-it-head.md`).
- Whether the company, the vendor, or the WhatsApp provider is the responsible party for each kind of data, and what notice and consent a first message must carry, I did **not** research. *Ask counsel.*

### 9.3 What it changes in the design

- Use the **official Business API with a number owned by the company**, as the IT head asked, through a named provider with a data-processing agreement. No forwarding through personal phones.
- **Download every file as it arrives**, not later. The 7-day life of a webhook ID is a hard limit, and the "No Storage" option removes the safety margin. Keep the SHA-256 and a received-at time with the file.
- Store files in **company-controlled storage in India**, with an access log, retention rule and deletion path. Do not rely on Meta as the record.
- Do not combine "No Storage" with an India at-rest region: the two are exclusive. Choose which constraint matters more; the pack does not say.
- Send **status updates** only inside the customer-service window or with an approved template and recorded opt-in. Plan the opt-in at vendor onboarding.
- Keep personal-data documents (attendance, challans) separate from the invoice record, with narrower access.
- Vendors asked for WhatsApp (58% of 212 survey responses prefer it) and the owner interviewed said "please, no portal". The design should not require a login.

## 10. What I could not verify

- The text of **section 43B(h)**, **CBDT Circular 1/2024** and **section 37(2)(g)** of the Income-tax Act 2025; all are read second-hand.
- Whether payment **before 31 March** after the limit preserves the deduction for that year (one commentary only).
- The **start of the 72-month** retention period (due date of annual return versus filing date).
- Whether a **scan alone** discharges the retention duty for an invoice issued on paper.
- **Section 12(3)** treatment of housekeeping, security and maintenance services.
- Current text of **Notification 29/2018** (reverse charge on security) and any amendment.
- The **mapping of 194C and 194J into section 393** and the exact 194C thresholds.
- The **₹5 crore e-invoice threshold** and IRN buyer-credit consequences against the official notifications.
- All **AP benchmark figures** (sources are vendor pages; the 22.5% has no cited report).
- **India at-rest storage** for WhatsApp on Meta's own page, and the exact date of the template-pricing change.
- The **72-hour DPDP breach notice**, the penalty ceiling and the exact 18-month date.
- **Responsibility for personal data** sent over WhatsApp under the DPDP Act.
- The Bombay High Court decision on deemed acceptance (summary only).

- **Google's Gemini free-tier terms.** I did not open them. That inputs may be used to improve the products is what I understood from the provider's published position, not something I read in the terms. The limit of 20 requests a day per model comes only from the provider's own error message.
- **The GSTIN check-digit rule.** I wrote it from memory and tested it on one published example GSTIN, which passes. I did not check it against the official specification.
- **Whether the pack is "real client data" in the legal sense.** The brief says to treat it that way and also says any resemblance to a real company is coincidental. I treated that as a question for the client, not one I can settle.

## 11. Sources

All accessed **16 October 2026**. "Read" means I opened the page or document and read it; "search result only" means I saw it only as a search-result summary.

| # | Source | URL | Accessed | Type, how read | Used for |
|---|---|---|---|---|---|
| 1 | MSMED Act 2006, as enacted (PRS India copy) | https://PRSINDIA.org/files/bills_acts/acts_parliament/2006/the-micro-small-and-medium-enterprises-development-act-2006.pdf | 16 Oct 2026 | Primary, read | s.2(b), 2(n), 15, 16 |
| 2 | 43B(h) Explained Briefly, ITAT Online | https://itatonline.org/digest/articles/43bh-explained-briefly/ | 16 Oct 2026 | Secondary, read | 43B(h) text, proviso, registration, effective date |
| 3 | The big buzz on small business payment delays, Vinod Kothari | https://vinodkothari.com/2024/02/the-big-buzz-on-small-business-payment-delays/ | 16 Oct 2026 | Secondary, search result only | Medium enterprises and traders |
| 4 | Section 43B(h): MSME Payment Rule and 45-Day Limit Explained, Busy | https://busy.in/tds/section-43bh-msme-payment-rule-and-45-day-limit-explained/ | 16 Oct 2026 | Secondary, read | Counting, 31 March, Income-tax Act 2025 |
| 5 | Finance Ministry clarifies Section 43B(h), TaxGuru | https://taxguru.in/income-tax/finance-ministry-clarifies-section-43bh-45-day-msme-payment-rule.html | 16 Oct 2026 | Secondary, read | Rajya Sabha reply 21 July 2026 |
| 6 | Section 43B(h) MSME payment, TaxGuru | https://www.taxguru.in/income-tax/section-43bh-msme-payment.html | 16 Oct 2026 | Secondary, search result only | The conflicting 45-day statement |
| 7 | CBIC Circular 160/16/2021-GST, 20 September 2021 (file named `circular_20no._20160_14_2021_gst.pdf`) | https://gstcouncil.gov.in/sites/default/files/2024-06/circular_20no._20160_14_2021_gst.pdf | 16 Oct 2026 | Primary, read | Physical copy of e-invoice in transit |
| 8 | Accounts and records under GST, sections 35 and 36, rules 56 to 58, TaxGuru | https://taxguru.in/goods-and-service-tax/accounts-records-maintained-gst-sec-35-36-rules-56-58-cgst-act.html | 16 Oct 2026 | Secondary, read | Retention, electronic records |
| 9 | Section 36 retention of accounts and records, GSTGyaan | https://www.gstgyaan.com/section-36-period-of-retention-of-accounts-records | 16 Oct 2026 | Secondary, search result only | Retention start date |
| 10 | Guide on section 16 CGST Act, GSTGyaan | https://gstgyaan.com/section-16-eligibility-conditions-time-limit-for-taking-input-tax-credit | 16 Oct 2026 | Secondary, search result only | Possession of the invoice |
| 11 | Rule 3, Companies (Accounts) Rules 2014 (ca2013.com) | https://ca2013.com/rule-3-companies-accounts-rules2014/ | 16 Oct 2026 | Secondary, search result only | Electronic books, audit trail, India back-ups |
| 12 | Section 7, Information Technology Act 2000 (LawX) | https://lawx.in/acts/section/17/216/2160 | 16 Oct 2026 | Secondary, search result only | Retention by electronic record |
| 13 | Place of supply provisions under GST, TaxGuru | https://taxguru.in/goods-and-service-tax/place-supply-provisions-gst.html | 16 Oct 2026 | Secondary, search result only | Sections 7, 8, 12 |
| 14 | Intra-State and inter-State supplies under GST law, Lakshmikumaran & Sridharan | https://lakshmisri.com/insights/articles/intra-state-supplies-inter-state-supplies-under-gst-law | 16 Oct 2026 | Secondary, search result only | Sections 7 and 8 |
| 15 | Section 12(3), place of supply for immovable property (CGGST) | https://cggst.com/wp-content/uploads/2023/06/Section-12-3.pdf | 16 Oct 2026 | Secondary, search result only | Section 12(3) |
| 16 | RCM on supply of security services, TaxGuru | https://taxguru.in/goods-and-service-tax/rcm-supply-security-services.html | 16 Oct 2026 | Secondary, search result only | Notification 29/2018 |
| 17 | Section 194C vs 194J, TaxBuddy; Section 194J, ClearTax; TDS on AMC under 194C, StudyCafe | https://www.taxbuddy.com/blog/section-194c-vs-194j-contractor-payments ; https://cleartax.in/s/section-194j ; https://studycafe.in/tds-u-s-194c-deductible-on-amc-for-repairs-maintenance-of-computers-70688.html | 16 Oct 2026 | Secondary, search result only | 194C and 194J basics, AMC case |
| 18 | Section 393 of the Income-tax Act 2025, India Briefing | https://www.india-briefing.com/news/section-393-income-tax-act-2025-tds-rules-rates-compliance-guide-44450.html | 16 Oct 2026 | Secondary, read | New TDS section, effective date |
| 19 | AP team productivity benchmarks, Corpay | https://www.corpay.com/resources/blog/ap-team-productivity-benchmarks | 16 Oct 2026 | Vendor, read | APQC and Hackett figures as relayed |
| 20 | 7 causes of invoice exceptions, Transcepta | https://www.transcepta.com/blog/7-causes-of-invoice-exceptions | 16 Oct 2026 | Vendor, read | Exception causes, Ardent figures as relayed |
| 21 | Three-way matching, Wisemonk; Tray; Kognitos | https://www.wisemonk.io/blogs/three-way-matching ; https://tray.ai/automate/three-way-match/ ; https://www.kognitos.com/blog/three-way-matching/ | 16 Oct 2026 | Vendor, search result only | Tolerances, exceptions, services |
| 22 | Supplier invoice submission guide, India, Cognizant; Tally PO invoice guide | https://www.cognizant.com/en_us/general/documents/supplier-invoice-submission-guide-india.pdf ; https://tallysolutions.com/accounting/po-invoice/ | 16 Oct 2026 | Corporate and vendor, search result only | Mandatory invoice fields |
| 23 | Validate e-invoice IRN in the AP workflow, AI Accountant; E-invoicing mandatory limit, The Munim | https://www.aiaccountant.com/blog/validate-einvoice-irn-ap-workflow ; https://themunim.com/govt-makes-gst-e-invoicing-mandatory-for-companies-with-rs-5-crore-sales | 16 Oct 2026 | Vendor, search result only | First-time-right, IRN, ₹5 crore threshold |
| 24 | E-invoice applicability limit 2025-26, Gimbooks | https://www.gimbooks.com/blog/e-invoice-applicability-limit-in-2025-latest-rules-threshold-who-must-comply/amp/ | 16 Oct 2026 | Vendor, search result only | E-invoice applicability |
| 25 | Beyond OCR: digital invoices eliminate exceptions, Transcepta | https://www.transcepta.com/blog/beyond-ocr-digital-invoices-eliminate-invoice-exceptions-for-accounts-payable-automation | 16 Oct 2026 | Vendor, search result only | Exceptions versus OCR |
| 26 | Mahindra Defence Systems v Ranjana Industries, summary (LawText) | https://lawtext.in/judgement.php?bid=44865 | 16 Oct 2026 | Secondary, search result only | Deemed acceptance, Bombay High Court 2025 |
| 27 | What causes errors and delays in AP invoice automation projects, Vroozi; Why AP automation fails, Docstar | https://www.vroozi.com/blog/what-causes-errors-and-delays-in-accounts-payable-invoice-automation-projects/ ; https://www.docstar.com/blog/why-ap-automation-fails/ | 16 Oct 2026 | Vendor, search result only | Why OCR-only projects stall |
| 28 | Invoice exceptions: where they come from, Transcepta | https://test.transcepta.com/blog/invoice-exceptions-where-they-come-from-and-how-to-prevent-them | 16 Oct 2026 | Vendor, search result only | Exception handling |
| 29 | WhatsApp Business Platform, media (Meta for Developers) | https://developers.facebook.com/documentation/business-messaging/whatsapp/business-phone-numbers/media | 16 Oct 2026 | Primary (platform owner), read | Media IDs, expiry, size, hash |
| 30 | WhatsApp Business Platform, No Storage (Meta for Developers) | https://developers.facebook.com/documentation/business-messaging/whatsapp/no-storage/ | 16 Oct 2026 | Primary (platform owner), read | Retention, webhook retries, localisation conflict |
| 31 | Get opt-in for WhatsApp (Meta for Developers) | https://developers.facebook.com/docs/whatsapp/overview/getting-opt-in | 16 Oct 2026 | Primary (platform owner), search result only | Opt-in |
| 32 | Pricing updates on the WhatsApp Business Platform (Meta for Developers) | https://developers.secure.facebook.com/docs/whatsapp/pricing/updates-to-pricing | 16 Oct 2026 | Primary (platform owner), search result only | Per-message template pricing |
| 33 | WhatsApp data localisation: Clickatell; 360dialog; Vonage | https://guides.clickatell.com/release-notes/q3-jul-sep-2024/channel-updates/whatsapp-data-localization ; https://docs.360dialog.com/docs/hub/local-storage ; https://api.support.vonage.com/hc/en-us/articles/12605491997212-WhatsApp-Local-Data-Storage | 16 Oct 2026 | Provider docs, search result only | India as an at-rest region |
| 34 | DPDP Rules 2025 notified (Press Information Bureau, 17 November 2025) | https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf | 16 Oct 2026 | Primary (government), read | Notification date, eighteen-month phasing |
| 35 | India's DPDP Act: phased rollout and key compliance milestones, AZB & Partners | https://www.azbpartners.com/bank/indias-digital-personal-data-protection-act-phased-rollout-and-key-compliance-milestones/ | 16 Oct 2026 | Secondary, search result only | Dates of the phases, obligations |

Also consulted, not relied on: [Taxmann FAQs on s.15 of the MSMED Act](https://taxmann.com/post/blog/faqs-liability-of-buyer-u-s-15-of-msmed-act-to-make-timely-payments-to-mse-suppliers) and [Taxmann on the interplay of s.43B with the MSME Act](https://taxmann.com/post/blog/analysis-interplay-of-section-43b-with-msme-act), both accessed 16 October 2026.