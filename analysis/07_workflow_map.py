"""Map the vendor-bill workflow as it actually runs: swimlane source (Mermaid), hand-off table, double checks, information gaps.

Reads the figures files written by clean.py, 02_stage_times.py, 04_query_forensics.py, 06_msme_exposure.py and 05_claims_tested.py,
and analysis/out/query_rules.csv. Every number in the diagram and in notes/workflows.md is looked up by figure id, so it cannot drift.

Writes:
  notes/workflows/swimlane.mmd        Mermaid sequence diagram (lanes = actors, time runs downward)
  notes/workflows.md                  the readable note; it embeds notes/workflows/swimlane.svg
  analysis/out/figures_workflows.csv  figures computed here
The SVG is rendered from the .mmd by analysis/render_mermaid.py (needs the in-app browser; see that file).

Mermaid has no swimlane type. A flowchart with one subgraph per actor loses the subgraph direction as soon as an edge
crosses lanes, so the sequence diagram is used: one lifeline per actor, solid arrows for formal hand-offs, dashed arrows for
informal channels, and shaded blocks for the loops.

Run: python analysis/07_workflow_map.py
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis" / "out"
NOTES = ROOT / "notes"
(NOTES / "workflows").mkdir(exist_ok=True)

# ------------------------------------------------------------------ figures: lookup of everything already computed
F, SRC = {}, {}
for fname, script in [("figures.csv", "clean.py"), ("figures_stage_times.csv", "02_stage_times.py"),
                      ("figures_query_forensics.csv", "04_query_forensics.py"), ("figures_msme.csv", "06_msme_exposure.py"),
                      ("figures_claims_tested.csv", "05_claims_tested.py")]:
    for r in pd.read_csv(OUT / fname, keep_default_na=False).itertuples():
        F[r.id] = r.value
        SRC[r.id] = script
own: dict[str, tuple] = {}


def fig(k, v, d=""):
    own[k] = (v, d)
    F[k] = v
    SRC[k] = "07_workflow_map.py"


def n(i, fmt="{:g}"):
    return fmt.format(float(F[i]))


d1 = lambda i: n(i, "{:.1f}")
d0 = lambda i: n(i, "{:,.0f}")
pc = lambda i: n(i, "{:.1f}%")


def stage(k):
    """mean, median, p90 of a stage from the overall rows of stage_times.csv"""
    return (d1(f"overall.s{k:02d}.cal_mean"), d0(f"overall.s{k:02d}.cal_median"), d0(f"overall.s{k:02d}.cal_p90"))


qr = pd.read_csv(OUT / "query_rules.csv").set_index("rule_id").n

# ------------------------------------------------------------------ the double checks and their query counts
PAIRS = [("P1", "H1", "Vendor name and GSTIN match the vendor master", "R08", "GSTIN differs from vendor master"),
         ("P2", "H2", "Bill is addressed to the correct company entity", "R13", "Wrong company name on bill"),
         ("P4", "H4", "Rate matches the work order or purchase order", "R17", "Rate above work order rate"),
         ("P5", "H5", "Quantity, days or headcount match approved attendance or delivery (property); quantity matches the posted service entry (head office)", "R11", "Bill amount differs from service entry"),
         ("P6", "H6", "Attendance sheet is signed", "R23", "Attendance sheet unsigned"),
         ("P7", "H7", "PF and ESIC challans for the previous month are attached", "R22", "PF/ESIC challan missing"),
         ("P8", "H8", "Delivery challan carries the gate stamp", "R21", "Challan missing gate stamp"),
         ("P9", "H9", "Service report or job card is attached", "R20", "Service report missing")]
for p, h, _, rule, _ in PAIRS:
    fig(f"w.dup.{p}{h}.queries", int(qr[rule]), f"queries raised by head office on {p}/{h} items (rule {rule})")
fig("w.dup.queries_total", sum(int(qr[r]) for _, _, _, r, _ in PAIRS), "queries on items the property checklist already requires")
fig("w.dup.pairs", len(PAIRS), "checks that appear on both the property and the head-office checklist")
for k, rule in [("gl", "R03"), ("costcentre", "R02"), ("wbs", "R04"), ("wo_expired", "R26"), ("wo_balance", "R25"), ("wo_quantity", "R24"),
                ("wo_bal_other", "R10"), ("po_not_released", "R12"), ("rate_agreed_by_phone", "R17"), ("overtime", "R16")]:
    fig(f"w.q.{k}", int(qr[rule]), f"queries under rule {rule}")
fig("w.q.wo_all", int(qr["R25"] + qr["R24"] + qr["R10"] + qr["R12"] + qr["R26"]), "work-order balance, quantity, expiry and PO queries together")

# ------------------------------------------------------------------ the swimlane
lines: list[str] = []
num = {"n": 0}
keys: dict[str, int] = {}


def msg(a, arrow, b, text, key=None):
    num["n"] += 1
    if key:
        keys[key] = num["n"]
    lines.append(f"    {a}{arrow}{b}: {text}")


def note(where, text):
    lines.append(f"    Note over {where}: {text}")


FORMAL, INFORMAL = "->>", "-->>"
s1, s2, s3, s4, s5, s6, s7, s8 = (stage(k) for k in range(1, 9))
lines += ["sequenceDiagram", "    autonumber",
          "    participant V as Vendor", "    participant FD as Facility desk", "    participant CE as Commercial executive",
          "    participant PH as Property head", "    participant CR as Courier", "    participant AP as Central AP",
          "    participant PR as Procurement", "    participant TR as Treasury", "    participant IT as IT"]

lines.append("    rect rgb(240, 240, 240)")
note("V,CE", "Before submission: informal pre-checks")
msg("V", INFORMAL, "CE", "WhatsApp photo: is this OK before I print it? (reported)")
msg("V", INFORMAL, "CE", "Email scan first, then the print (reported)")
lines.append("    end")
msg("V", FORMAL, "FD", f"Paper bill, attendance, challans. Invoice to desk {s1[0]} d, median {s1[1]}", "submit")
msg("FD", FORMAL, "FD", "Stamp, tracker no., Excel register row")
msg("FD", FORMAL, "V", "Photocopy of the stamped page")
msg("FD", FORMAL, "CE", f"Bill to the executive. Desk to verified {s2[0]} d, median {s2[1]}", "to_ce")
note("CE,PH", "P1 GSTIN, P2 entity, P3 WO no., P4 rate, P5 headcount vs attendance, P6 attendance signed, P7 PF and ESIC, P8 gate stamp, P9 service report")
note("IT,CE", "P5 by hand: biometric + gate register photo + vendor claim")
msg("CE", FORMAL, "CE", "Service entry in SAP (P10). WO balance first tested here", "se")
msg("CE", FORMAL, "PH", f"Packet for signature. Verified to signed {s3[0]} d, max {d0('c.prop.sign_step_max')}", "to_ph")
note("PH", "P11 signs the packet")
msg("PH", FORMAL, "CR", f"Wait for the weekly pickup. Signed to HO {s4[0]} d (Wed {d0('c.courier.lag_signed_wednesday')}, Thu {d0('c.courier.lag_signed_thursday')})", "to_courier")
msg("CR", FORMAL, "AP", "Arrives on a Friday (every packet)", "arrive")
note("AP", f"Tray, then a verifier. Wait {s5[0]} d, median {s5[1]}, p90 {s5[2]}")
note("AP,PR", "H1 GSTIN, H2 entity, H3 WO valid + balance, H4 rate, H5 qty vs service entry, H6 attendance, H7 PF and ESIC, H8 gate stamp, H9 service report, H10 GST type, H11 HSN + rate, H12 GL + cost centre, H13 duplicate, H14 TDS")
msg("AP", FORMAL, "AP", f"Post in SAP. No query: {d1('c.ho.clean_pick_to_post_mean')} d", "post")
msg("AP", FORMAL, "TR", f"Next Tue or Fri run. Posted to paid {s8[0]} d, median {s8[1]}", "to_tr")
msg("TR", FORMAL, "V", "Payment", "pay")

lines.append("    rect rgb(253, 232, 232)")
note("AP,CE", f"QUERY LOOP: {pc('share.bills_with_query_pct')} of bills. Raised {d1('timing.days_desk_to_raised.mean')} d after the desk, {d1('timing.days_pick_to_raised.mean')} d after pick-up")
msg("AP", FORMAL, "CE", "Query by email", "q1")
msg("AP", INFORMAL, "CE", "WhatsApp photo: is this right? (not recorded)")
note("AP", "Own Excel of open queries. Fortnightly call with properties")
msg("CE", FORMAL, "V", "Ask for corrected bill, challan or credit note", "q2")
msg("V", FORMAL, "FD", "Corrected paper bill back to the desk", "q3")
msg("CE", FORMAL, "CE", "Redo the service entry", "q4")
msg("CE", FORMAL, "AP", f"Papers back. Query open {d1('query.mean_days_among_queried')} d, median {d0('timing.days_open.median')}, p90 {d0('timing.days_open.p90')}", "q5")
lines.append("    end")

lines.append("    rect rgb(255, 240, 220)")
note("CE,PR", f"WORK ORDER AMENDMENT LOOP: {d0('w.q.wo_all')} queries on balance, quantity, expiry or missing PO")
msg("CE", FORMAL, "PR", "Email: urgent WO amendment needed", "a1")
msg("AP", INFORMAL, "PR", "Query forwarded: please check")
msg("PR", FORMAL, "CE", "Asks for RWA letter or tenant approval", "a2")
msg("CE", FORMAL, "PR", "RWA letter", "a3")
msg("PR", FORMAL, "PR", "Budget note, approval note, amend in SAP. Not measured", "a4")
msg("PR", FORMAL, "CE", "Amended: redo service entry, packet back to AP", "a5")
note("PR", "Own sheet, sticky note of CFO-office cases")
lines.append("    end")

lines.append("    rect rgb(235, 245, 235)")
note("V,TR", "Informal channels carrying status and escalations")
msg("PH", INFORMAL, "AP", "WhatsApp complaint with tracker no.")
note("AP", "CFO EA list of unpaid vendors on WhatsApp each Monday")
msg("CE", INFORMAL, "AP", "Message to a friend: is my bill there?")
msg("V", INFORMAL, "AP", "Phone calls, three or four per bill (reported)")
msg("V", INFORMAL, "TR", "Phone calls to treasury (reported)")
msg("FD", INFORMAL, "AP", "Weekly Excel register, not updated by head office")
msg("CE", INFORMAL, "IT", "Phone call on the 1st: punches missing")
msg("PR", INFORMAL, "PH", "Monthly 60-day expiry list, no replies")
lines.append("    end")
note("IT", "Runs SAP, the gate biometric network and a shared drive of 38 registers")

MMD = "\n".join(lines) + "\n"
(NOTES / "workflows" / "swimlane.mmd").write_text(MMD, encoding="utf-8", newline="\n")
assert ";" not in MMD and "#" not in MMD, "mermaid separators in text"
fig("w.diagram.messages", num["n"], "numbered arrows in the swimlane")
K = keys

# ------------------------------------------------------------------ the note
md: list[str] = []
A = md.append
A("# How the workflow actually runs\n")
A("Built from the seven interviews, the checklists and the data. Where the documented journey (`context/org/company-profile.md`) and what people described differ, the note shows what people described. "
  "**Measured** numbers come from the register and the query log (`notes/numbers.md`, via the scripts named at the end); **reported** statements are quotes from the interviews and are not checked against data.\n")
A("## 1. Documented versus actual\n")
A("| Documented step | What actually happens | Measured |\n|---|---|---|")
A(f"| 1. Vendor prints the bill and hands it at the desk | Vendors often WhatsApp a photo or email a scan first to check it; one trip to each property, with waits at the desk | Invoice date to desk: mean {s1[0]} d, median {s1[1]}, p90 {s1[2]} |")
A("| 2. Desk stamps it, assigns a tracker number, logs it | Also gives the vendor a photocopy of the stamped first page so there is proof of receipt. The register is updated when the bill comes in and goes out, then never again | not separately timed |")
A(f"| 3. Executive checks it and creates the service entry | For manpower, three attendance sources are matched by hand. The work-order balance is first tested when the service entry fails. The executive keeps a personal Excel and a WhatsApp group with agency supervisors | Desk to verified: mean {s2[0]} d, median {s2[1]}, p90 {s2[2]} |")
A(f"| 4. Property head signs the packet | Signs on the summary and exceptions, from a folder with sticky notes for the most-called vendors | Verified to signed: mean {s3[0]} d, median {s3[1]}, max {d0('c.prop.sign_step_max')} |")
A(f"| 5. Packets go to head office by courier | One weekly pickup; every packet arrives on a Friday and the delay is set by the weekday of signing | Signed to received: mean {s4[0]} d; {d0('c.courier.lag_signed_wednesday')} d if signed Wednesday, {d0('c.courier.lag_signed_thursday')} d if Thursday |")
A(f"| 6. Central AP rechecks, then queries or posts | Not documented: the packet waits in a tray for a verifier. Then 14 checks. Queries go by email, and also by WhatsApp and phone | Wait for a verifier: mean {s5[0]} d, median {s5[1]}, p90 {s5[2]}. Pick-up to posting, no query: mean {d1('c.ho.clean_pick_to_post_mean')} d |")
A(f"| 7. Treasury pays in the next payment run | Runs are on Tuesdays and Fridays and the run list is closed ahead of each run (reported). Vendors also phone treasury directly | Posted to paid: mean {s8[0]} d, median {s8[1]}, p90 {s8[2]} |")
A(f"| Not documented: the query loop | {pc('share.bills_with_query_pct')} of bills go back; the query is open a mean of {d1('query.mean_days_among_queried')} d | See section 4 |")
A(f"| Not documented: the work-order amendment loop | {d0('w.q.wo_all')} queries on work-order balance, quantity, expiry or a missing PO | See section 5 |")
A("| Not documented: how vendors and properties learn status | WhatsApp, phone calls and one friendly verifier | reported only |\n")
A("## 2. The swimlane\n")
A("![Swimlane of the vendor-bill workflow](workflows/swimlane.svg)\n")
A("**How to read it.** One column per actor; time runs down the page. Solid arrows are formal hand-offs and carry the measured days for the stage they start. "
  "Dashed arrows are informal channels (WhatsApp, phone, personal Excel, email outside the register). Pink is the query loop, orange the work-order amendment loop, green the informal channels. "
  "Notes name the manual checks by checklist ID (P1 to P11 property, H1 to H14 head office). The department heads who sign attendance (P6) have no column; they sit inside the executive's step. "
  "Mermaid has no swimlane diagram, so this is a sequence diagram: lifelines for lanes, arrows for hand-offs. The source is `notes/workflows/swimlane.mmd`.\n")
A("<details><summary>Mermaid source</summary>\n\n```mermaid\n" + MMD + "```\n\n</details>\n")
A("## 3. Hand-offs and their measured days\n")
A("The arrow number matches the number on the diagram. Days are calendar days for the stage that starts at the hand-off, for the paid invoices in `stage_times.csv` (`02_stage_times.py`).\n")
A("| Arrow | From to | What moves, by which channel | Mean | Median | p90 | Notes |\n|---|---|---|---|---|---|---|")
A(f"| {K['submit']} | Vendor to desk | Paper bill with attendance and challans, by the vendor's own messenger | {s1[0]} | {s1[1]} | {s1[2]} | Invoice date to desk. Vendor-side time, before the company has the bill |")
A(f"| {K['to_ce']} | Desk to executive | Bill and tracker number, in person | {s2[0]} | {s2[1]} | {s2[2]} | Covers all checks P1 to P9 and the service entry (P10) |")
A(f"| {K['to_ph']} | Executive to property head | Packet in a folder on his desk | {s3[0]} | {s3[1]} | {s3[2]} | {pc('c.prop.sign_step_le2_pct')} signed within 2 days; {pc('c.prop.signed_on_weekend_pct')} of signature dates fall on a weekend, so read with care |")
A(f"| {K['to_courier']} | Property head to courier to AP | Weekly courier bag, no tracking | {s4[0]} | {s4[1]} | {s4[2]} | Fixed by weekday: minimum {d0('c.courier.lag_min')} d, maximum {d0('c.courier.lag_max')} d |")
A(f"| {K['arrive']} | Courier to central AP | Brown envelopes into trays | {s5[0]} | {s5[1]} | {s5[2]} | The wait for a verifier, the largest single wait |")
A(f"| {K['post']} | AP verification to posting | In SAP | {d1('c.ho.clean_pick_to_post_mean')} | {d0('c.ho.clean_pick_to_post_median')} | | Bills with no query. With a query the bill waits in section 4 |")
A(f"| {K['to_tr']} | AP to treasury | Posted invoice joins the run list | {s8[0]} | {s8[1]} | {s8[2]} | Payment runs Tuesday and Friday |")
A(f"| {K['q1']} to {K['q5']} | Query loop | Email, WhatsApp, courier | {d1('query.mean_days_among_queried')} | {d0('timing.days_open.median')} | {d0('timing.days_open.p90')} | Days the query is open, queried bills only |")
A(f"| {K['a1']} to {K['a5']} | Amendment loop | Email, paper approvals | | | | **Not measured**: the data has no amendment date |\n")
A("## 4. The query loop\n")
A(f"- **Share.** {d0('share.bills_with_query_pct') if False else pc('share.bills_with_query_pct')} of bills ({d0('share.bills_with_query')} of {d0('share.bills')}). No bill has more than one query in the log.")
A(f"- **When it is raised.** A mean {d1('timing.days_desk_to_raised.mean')} days after the desk logs the bill, {d1('timing.days_ho_received_to_raised.mean')} after head office receives it, and {d1('timing.days_pick_to_raised.mean')} after a verifier picks it up. The verifier finds the problem almost at once; the delay before is queue and courier time.")
A(f"- **How long it stays open.** Mean {d1('query.mean_days_among_queried')} days, median {d0('timing.days_open.median')}, p90 {d0('timing.days_open.p90')}. After the query is resolved the bill is posted a mean {d1('timing.days_resolved_to_posted.mean')} days later.")
A(f"- **Channels.** Official: email to the executive, vendor copied if it is a vendor issue, noted in the register. Actual: also verifier-to-executive WhatsApp (\"Unofficially, my verifiers are in WhatsApp groups with some of the commercial executives.\"), the AP lead's own sheet (\"And I keep my own Excel of open queries, separate from the register.\") and a fortnightly call (\"Every two weeks we have a call with the properties to go through open queries.\").")
A("- **Where it goes wrong.** An email can reach a stale address (the agency owner's went to an accountant who had left). The corrected papers return by a channel nobody recorded. The register cannot hold a second query on the same bill.\n")
A("## 5. The work-order amendment loop\n")
A(f"- **Trigger.** Usually the executive finds out when creating the service entry (\"I find out when the service entry fails.\") or AP raises a query. Procurement hears by email or a forwarded query (\"please check\"). {d0('w.q.wo_all')} queries fall here.")
A("- **What an amendment needs** (procurement): a budget approval from finance if the value rises, a letter from the RWA for residential or the tenant's approval for an office tower, a signed approval note, the amendment in SAP, and then the property redoes the service entry (\"If any one paper is missing, it stops.\").")
A(f"- **Measured.** The whole work-order query cycle closes in a median {d0('c.woq.median')} days (p90 {d0('c.woq.p90')}); {pc('c.woq.le14_pct')} close within 14 days. The amendment step itself cannot be timed.")
A("- **Reported, and they disagree.** The executive says five weeks end to end on one case; procurement says a week once all the paper is in. Both can be true if the paper takes four weeks. Neither is in the data.")
A(f"- **Warning that exists.** Procurement runs a report on the first of each month of orders ending in the next 60 days (\"Honestly, I do not know if anybody opens it. Nobody has ever replied.\"). {d0('c.wo.expiry_query_orders_on_a_60day_report')} of the {d0('ev.expiry_queries')} orders behind an expiry query would have appeared on it. It does not cover balance, which is what runs out first.\n")
A("## 6. Informal channels\n")
A("| Channel | Who uses it | For what | Evidence | What it replaces |\n|---|---|---|---|---|")
A("| WhatsApp group, executive and agency supervisors | Commercial executive | Attendance photos for the month's bill | \"I also have a WhatsApp group with all the agency supervisors for both sites. They send attendance photos there.\" | The official attendance record |")
A("| WhatsApp, vendors to executive | Vendors | Check a bill before printing | \"A lot of them send a photo on WhatsApp to ask if it is fine before printing.\" | A bill-intake check that does not exist |")
A("| WhatsApp, verifiers and executives | Central AP, properties | Small queries, status | \"Unofficially, my verifiers are in WhatsApp groups with some of the commercial executives.\" | The query register |")
A("| WhatsApp, property heads to AP lead | Property heads | Vendor complaints with the tracker number | \"I forward vendor complaints to the AP lead on WhatsApp directly, with the tracker number.\" | A status screen |")
A("| WhatsApp, CFO's office to AP lead | CFO's EA | Weekly list of unhappy vendors | \"Every Monday she forwards it to the AP lead on WhatsApp.\" | A report of the oldest unpaid bills |")
A("| Personal Excel, executive | Commercial executive | Pending bills, who she is waiting for | \"My own Excel. Every bill, the date it came, what is pending, who I am waiting for. Colour coded.\" | A shared tracker |")
A("| Personal Excel, AP lead | AP lead | Open queries | \"And I keep my own Excel of open queries, separate from the register.\" | The query log |")
A("| Personal Excel, procurement | Procurement executive | Pending amendments and what he awaits | \"SAP does not tell me who has not sent the RWA letter.\" | An amendment tracker |")
A("| Property Excel registers | 38 desks | The official bill log | \"Thirty eight Excel files on a shared drive.\" | A single register; a standard template was tried and abandoned |")
A("| Phone calls from vendors | Vendors to AP, treasury, properties | Status | \"Now vendors have found the treasury number also.\" | Status the vendor can see |")
A("| Email | Everyone | Official queries and amendment requests | Email can reach an old address | The record of record |")
A("| One friendly verifier | Executives | Whether a bill reached head office | \"That is my tracking system for head office. One person's kindness.\" | A shared status |\n")
A("**Risk the IT head names:** \"Bills, attendance photos, PAN cards, all on personal phones.\" None of it is kept under company control or logged.\n")
A("## 7. Checks done twice\n")
A(f"Eight checks appear on both checklists. In the year, head office raised **{d0('w.dup.queries_total')} queries** on exactly these items (a query is raised when the first check missed something or the second disagrees). "
  f"That is {d0('w.dup.queries_total')} of {d0('q.rows')} queries. The earlier figure of {d0('c.q.on_property_checklist_items')} in `notes/claims-tested.md` left out the {d0('w.dup.P5H5.queries')} bill-versus-service-entry queries.\n")
A("| Property check | Head-office check | What is checked | Queries raised by head office on this item |\n|---|---|---|---|")
for p, h, what, rule, label in PAIRS:
    A(f"| {p} | {h} | {what} | {d0(f'w.dup.{p}{h}.queries')} ({label}) |")
A("\n**Why it is done twice.** Head office does not trust the property check (\"I say, if I could trust you, I would not check.\", AP lead; after a diesel bill whose challan belonged to another property). "
  "The property head says the signature should settle it (\"If they do not trust our check, why do we do it? Either they check or we check.\"). Nobody has decided which of the two is the single check. "
  "The count above shows the second check does catch things; it does not show how many it re-did without finding anything, and no time is recorded for either side.\n")
A("Other overlaps are partial: P3 (work order number on the bill) and H3 (work order valid, open balance) are different checks, and so are P10 (service entry created) and H5 (quantity matches it).\n")
A("## 8. Checks that need information nobody has at that moment\n")
A("| Check | Information it needs | Where it exists | Who has it when the check happens | Evidence |\n|---|---|---|---|---|")
A(f"| P3, P10, H3: work order valid and open balance | Current balance (approved value less billed, including bills in flight) and validity | SAP; read access over RFC is approved | Nobody at the desk or executive's step. The executive finds out when the service entry fails; procurement's list shows expiry, not balance | \"Nobody has time to check SAP for forty work orders every week.\" Measured: {d0('c.wo.crossed_approved_value')} orders passed approved value; {d0('w.q.wo_all')} work-order queries; the extract's value rule reproduces {d0('ev.wo_balance_all.over_balance_on_day_one')} of {d0('ev.wo_balance_all.queries')} balance queries |")
A(f"| P5, H5: attendance and headcount | Biometric, paper gate register and the vendor claim, joined | Three separate places; the gate register cannot leave the gate | The executive, by hand, with a highlighter | In the one sample month, {d0('c.att.claim_gt_biometric_people')} of {d0('c.att.people')} people claim more days than biometric shows, {d0('c.att.claim_gt_gate_people')} more than the gate register; {d0('c.att.relievers')} relievers are not in biometric at all |")
A(f"| P4, H4: rate | The rate agreed by phone and not yet in the order | Nowhere recorded | Nobody: the order still holds the old rate | \"The vendor sends a new rate, the property agrees on the phone, and the vendor starts billing the new rate.\" Measured: {d0('w.q.rate_agreed_by_phone')} rate-above-order queries |")
A(f"| H12: GL code and cost centre | The expense type each order was meant for | Procurement's request form, filled by the property | Nobody holds a mapping from expense type to GL | Measured: {d0('w.q.gl')} GL queries, {d0('w.q.costcentre')} cost-centre queries, {d0('w.q.wbs')} closed-WBS queries |")
A(f"| H13: invoice not booked before | Every booking for the vendor, across all 38 properties and SAP | 38 separate registers plus SAP posted invoices | AP sees SAP; each property sees only its own register | Measured: {d0('dup_vendor_invoice.pairs')} vendor-and-invoice-number pairs on different bills; {d0('dup_query.rows')} duplicate queries, {d0('dup_query.not_on_any_pair')} of them with no twin in the register |")
A(f"| H10: GST type for the place of supply | The company's GST registration for each State, and the service type | Not in the pack | Nobody at the desk; the verifier decides from the vendor's State and the property | Measured: {d0('ev.igst.queries')} IGST queries, {d0('ev.igst.master_says_different_state')} on bills where the master says the supply is inter-State |")
A(f"| H1, P1: vendor details match the master | An up-to-date master (GSTIN, bank, MSME status) | Procurement, through a shared mailbox | The mailbox, which is \"not checked every day\" | Measured: {d0('msme.vendors_blank')} vendors have no MSME status |")
A("| H14: TDS section and rate | The section decided for each order, and the vendor's year-to-date payments | The AP lead's judgement, written on a note | The AP lead or the senior verifier, when asked | \"Just write the work order line on the note so audit does not ask.\" |")
A(f"| The 45-day payment rule (on neither checklist) | MSME status, the written payment term and the date of acceptance | Status partly; term and acceptance date not recorded | Nobody when treasury builds the run list | No payment-terms or acceptance-date field exists; {d0('msme.vendors_blank')} blank statuses |")
A("| Status after the packet leaves the property | Where the packet and the bill are | Head office's receipt and the verifier's tray | Nobody outside head office. The register is not updated | \"We do not get updates from head office into the register.\" |\n")
A("## 9. What is missing: decisions and information nobody owns\n")
A("| Gap | Why nobody owns it | Evidence | Measured |\n|---|---|---|---|")
A("| Watching work-order balance | Procurement watches expiry, the property finds out at the service entry, AP finds out at the query; none sees consumption against value | \"Nobody tells procurement.\"; the monthly list is never answered | " + f"{d0('c.wo.crossed_approved_value')} orders passed approved value; {d0('w.q.wo_all')} queries |")
A("| Telling procurement when scope changes | The property adds guards when the RWA asks; the order is the last to know | \"The order is the last one to know.\" | Not measured |")
A("| Who is the single checker | Property and head office both check; no decision on which | See section 7 | " + f"{d0('w.dup.queries_total')} queries on double-checked items |")
A("| An end-to-end bill status | The register stops at the property; head office has none; the vendor sees nothing | See section 8 | Vendors call about three times per bill (survey figure, not computed here) |")
A("| The query log as a whole | Email, WhatsApp and three personal Excel sheets, none complete; only one query per bill is kept | See section 4 | " + f"{d0('share.bills_with_query')} queries on {d0('share.bills_with_query')} bills; no bill with two |")
A("| The MSME clock | No field for the payment term or the acceptance date; the vendor master has gaps; the payment run has no MSME priority rule | `notes/research.md` sections 2 and 4 | " + f"{d0('msme.vendors_blank')} blank statuses; no field for terms |")
A("| The TDS section for each order | Decided ad hoc by the AP lead and her senior verifier | The note-on-the-bill exchange | Not measured |")
A("| One agreed register format | Thirty-eight versions; a locked template was tried and unlocked | IT head | " + f"{d0('property_code.distinct_raw')} different property-code spellings in the merged register for {d0('rows.properties')} properties |")
A("| Attendance as one joined view | Three sources held by three people | Section 8 | Sample month only |")
A("| The courier schedule | Nobody owns the frequency or the cut-off; cost and who prepares packets were the objections | \"Honestly, a few days here and there is not the issue.\" | " + f"{d1('overall.s04.cal_mean')} d mean, {d0('c.courier.lag_signed_thursday')} d if signed Thursday |")
A("| Escalation | The CFO becomes the route for every unhappy vendor, through his EA's notebook | \"Every escalation comes to me and I become the post office.\" | Two or three calls a week (reported) |")
A("| Whether the paper original must arrive before booking | The CFO asks the AP lead; the AP lead says nobody has asked her to change | `notes/research.md` section 6 | Not measured |")
A("| Keeping documents sent on WhatsApp | The IT head objects; operations depend on it; no policy or logging | Section 6 | Not measured |")
A("| Measuring days, not accuracy | The earlier OCR project closed green because it measured fields read | \"We measured accuracy. We did not measure days.\" | See `notes/stage-times` figures |\n")
A("## 10. Sources and how to reproduce\n")
A("Interviews: `pack/context/transcripts/01` to `07`. Checklists: `pack/context/documents/property-checklist.md` (P1 to P11), `head-office-checklist.md` (H1 to H14). Numbers: `analysis/02_stage_times.py`, `04_query_forensics.py`, `05_claims_tested.py`, `06_msme_exposure.py`, `clean.py` and `07_workflow_map.py`, registered in `notes/numbers.md`.\n")
A("```\n.venv\\Scripts\\python.exe -I analysis\\07_workflow_map.py     # writes the .mmd, this note and the figures\n.venv\\Scripts\\python.exe -I analysis\\render_mermaid.py          # renders notes/workflows/swimlane.svg\n```\n")
TEXT = "\n".join(md) + "\n"
TEXT = TEXT.replace(" See `notes/stage-times` figures", " See `analysis/out/stage_times.csv`")

# every quoted phrase must exist verbatim in the pack
pack = " ".join(p.read_text(encoding="utf-8") for p in (ROOT / "pack" / "context").rglob("*.md"))
norm = lambda s: re.sub(r"\s+", " ", s.replace("*", "")).strip().lower()
P = norm(pack)
bad = []
for lineno, line in enumerate(TEXT.splitlines(), 1):
    if line.startswith("<") or line.startswith("```"):
        continue
    for m in re.finditer(r'\\?"([^"\\]{14,})\\?"', line):
        q = m.group(1)
        if norm(q) not in P and norm(q).rstrip(".,") not in P:
            bad.append((lineno, q))
if bad:
    print("QUOTES NOT FOUND:"); [print(" ", b) for b in bad]
    raise SystemExit(1)
(NOTES / "workflows.md").write_text(TEXT, encoding="utf-8", newline="\n")
pd.DataFrame([dict(id=k, value=v, description=d) for k, (v, d) in own.items()]).to_csv(OUT / "figures_workflows.csv", index=False, lineterminator="\n")
print("wrote notes/workflows/swimlane.mmd and notes/workflows.md;", num["n"], "arrows;", len(own), "figures")
