# Interview: Head of IT

- **Role:** Head of IT, Property Management division
- **Location:** Head office, Gurugram
- **Date:** 6 March 2026
- **Interviewer:** Riklr FDE

---

*The interview took place in a meeting room on the IT floor. The IT head had just come off a call with the company's SAP support partner and still had the laptop open.*

**Head of IT:** Sorry, that call ran over. Our SAP partner. Every call is "we will revert by Monday." Which Monday, they do not say. *(closes laptop)* Okay. I am all yours for forty minutes. After that I have the mall network review.

**Interviewer:** Thanks. What is going on at the mall?

**Head of IT:** The bigger mall. Wi-Fi for the food court tenants keeps dropping, and the biometric at the service gate is on the same switch. When the network goes, the punches do not sync. Then the commercial executive calls me on the first of the month asking why attendance is missing. Everything comes back to IT on the first of the month. *(laughs)*

**Interviewer:** What is your view on vendor payments?

**Head of IT:** We need a proper vendor portal. Vendor logs in, uploads the bill, sees the status, sees payments, downloads TDS certificates. Property and head office approve inside the portal. It talks to SAP both ways. That is the end state.

**Interviewer:** Why a portal rather than something smaller?

**Head of IT:** Because I have seen the small things. Every year somebody does a small thing. A shared mailbox. An online form. Some Excel macro. Then there are ten small things and none of them talk to each other. A portal is one place. One login per vendor, one audit trail. Audit will be happy. I will be happy.

**Interviewer:** How long would that take?

**Head of IT:** If we buy a product, six to nine months with SAP integration. If we build, longer. We had a budget discussion last year. It did not go through.

**Interviewer:** What happened in that discussion?

**Head of IT:** I presented. Finance asked for the benefit in rupees. I said vendor satisfaction, faster payment, less calls. They said, how much faster? I did not have a number. I had complaints. The CFO said come back with data. That was the end of it. I am not blaming him. He was right. But nobody gave me the data either.

**Interviewer:** What did you try before?

**Head of IT:** Two years back we ran an OCR pilot at head office. Scan the bill, read the fields, push to a staging table. The extraction was decent on printed bills. Around ninety percent on the main fields. Handwritten challans, not so good.

**Interviewer:** Who sponsored it?

**Head of IT:** The previous finance head. He saw a demo at a conference and came back very excited. We bought a scanner for the AP bay, a good one, it is still there. We got a small vendor to set up the extraction. Three months to set up, six months live.

**Interviewer:** What happened to it?

**Head of IT:** It did not change anything. AP still waited for the physical packet. They still checked everything by hand. The scans sat in a folder. After six months we switched it off.

**Interviewer:** How did AP use it day to day?

**Head of IT:** Honestly, they used it as a scanner. The office boy scanned the packets after they arrived, the fields came into the staging table, and then the verifier opened the paper packet and did her checklist the same way as before. Some of them copied from the staging table instead of typing. Some did not trust it and typed anyway. I remember one verifier told me, sir, if the machine reads the wrong GSTIN, who will answer audit, me or the machine?

**Interviewer:** Why do you think it did not change anything?

**Head of IT:** It fixed the typing, and typing was not the slow part. I did not see that at the time.

**Interviewer:** Did anyone measure it?

**Head of IT:** We measured accuracy. We did not measure days. Our success metric was fields read correctly. We hit it. The project closed green. And nothing improved for the vendor. *(shakes head)* That one still bothers me a bit.

*His phone buzzed. He read the message and typed a reply.*

**Head of IT:** Sorry. The mall. They want to restart the switch during business hours. I said no. Okay.

**Interviewer:** What about SAP integration options?

**Head of IT:** We are on an older SAP version. We have RFC access for reading work orders, service entries and posting status. Writing invoices into SAP from outside needs a project with our SAP partner and audit sign-off. Reading is easy. Writing is slow to get approved.

**Interviewer:** How slow?

**Head of IT:** Last time we asked for a write interface was for the procurement team, for purchase requisitions. Let me think. It took, I think, five months for the approval. No, wait, longer. Five months only for the partner's estimate. Then audit took another two. So seven, eight months before anybody wrote code. And that was a simple one.

**Interviewer:** Vendors told us they prefer WhatsApp.

**Head of IT:** I know. Security team will not like it. Personal phones, no audit trail. If we do WhatsApp, it has to be the business API with our own number and the files stored on our side. Not people forwarding photos to each other.

**Interviewer:** But people already forward photos to each other.

**Head of IT:** Yes. That is exactly my worry. The commercial executives have groups with agency supervisors. AP has groups with the properties. Property heads have their own group. Bills, attendance photos, PAN cards, all on personal phones. If one phone is lost, that data is gone, or worse, it is with somebody else. So I am not against WhatsApp. I am against the way it is used today.

**Interviewer:** Would vendors use a portal if you built one?

**Head of IT:** If it is mandatory, they will. They use portals for other large clients. In the beginning they will complain. After three months it is normal. That is my experience with the employee self-service portal also. Everybody complained. Now nobody remembers the paper forms.

**Interviewer:** The property registers. Are they connected to anything?

**Head of IT:** No. Thirty eight Excel files on a shared drive. Each property built its own, so the columns are similar but not the same. We tried to standardise once.

**Interviewer:** What happened?

**Head of IT:** We sent a template with fixed columns and drop-downs. Locked cells. Around half the properties used it for a month. Then somebody needed a column for "courier docket number", somebody needed "remarks two", somebody unlocked it, and in six months we were back to thirty eight versions. Some properties still have the template file sitting next to their old file, unused. I can share both if you want.

**Interviewer:** Yes please. Who else depends on IT for this process?

**Head of IT:** Everybody, and nobody tells me in advance. Finance wants a dashboard tomorrow. AP wants nothing to change. Properties want the network to work. Procurement wants a workflow for amendments. Each one comes separately, each one is urgent. I have six people and two of them are on SAP support full time.

**Interviewer:** What would you want from us?

**Head of IT:** Honestly, show me where the time goes with data. Then I can argue for budget with something better than vendor complaints.

**Interviewer:** And if the data says a portal is not the first step?

**Head of IT:** *(pause)* Then show me what is. But keep it inside something we can control and audit. I do not want another pilot that closes green and changes nothing.
