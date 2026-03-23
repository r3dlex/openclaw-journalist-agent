# Meeting Minutes — 16 March 2026

**Topic:** Track 1 & Track 2 — Plan Definition & Alignment (6-Week Sprint)
**Duration:** 43 minutes
**Attendees:** Andre Burgstahler, Julien Seroi, Arthur Berganski, Reinhardt Fraunhoffer, Beate Kasper, Stefan Stelzer, Jaan Tasane

---

## Workstream Status Round-up

### WS 1.1 — Quality & Structural Fitness (Owner: Reinhardt Fraunhoffer)

- Reinhardt returned from two days out. His first PM alignment meeting on Track 1 priorities was scheduled for 10:30 the same day. He confirmed the methodology from the performance initiative run 15 months ago will be reused: benchmark identification per area, followed by a structured prioritization list. The document is not yet in place. He will provide an update during the week.
- **Critical escalation flagged:** the BIM topic has surfaced as the highest-priority performance issue. Two to three customers (Aramilio, Darno) are close to a formal escalation and may stop working with 4.0. Reinhardt will share details during the week.
- Andre added context on the prior week's technical sessions. Three hours of R&D-side technical discussion made clear that R&D does not yet know the performance drivers specific to the five target GCs. The conclusion: WS 1.1 must first produce that input before the technical workstream can prioritize its improvements. The BIM case was also cited as an example of how **not** to run these discussions — reactive, PM-in-the-loop on technical details, no clear non-functional target defined upfront. Moving forward, the pattern should be: define the non-functional target, then run technical discussions in the background without PM involvement.
- Jaan Tasane reinforced the information flow problem: performance reports from customers typically arrive as "it's slow" with no version, no module, no error message. Jaan's team cannot investigate without this data. This is partly a Support process issue.

### WS 2.1 — Next Generation Architecture (Owner: Stefan Stelzer)

- First workshops planned for the following week (virtual, given the short notice). Participants are listed in the Word document. The workshops will focus on SDRs (System Decision Records) and ADRs (Architectural Decision Records) to establish the principles for the next-generation architecture. This work runs in parallel with Track 1 without dependency.

### WS — Team Enablement (Owner: Beate Kasper)

- Kick-off held the previous Thursday. The workstream is starting with the capability assessment as the foundational step. Immediate action: Beate posted a draft craft group structure in the chat. All workstream members should review it and confirm whether the groupings are appropriate before defining assessment criteria per group.

### WS — Working Principles (Owner: Arthur Berganski)

- Arthur deprioritized the working principles workstream for this week in favor of the investment cases. He will pick it up from the following week.

### WS — Investment Cases (Owner: Arthur Berganski)

- Arthur sent a detailed email the previous Friday with Confluence links. Each workstream owner must:
  - Fill in the Confluence summary table (the first row is a marked example)
  - Create a detailed page per investment case using the provided template
  - Follow the same format used for last year's approved investment cases — this intentionally maximizes approval likelihood
  - When ready, book a 30-minute review session with Julien and Arthur before the group review
- **Timeline:** contributions can start immediately and be completed incrementally. The joint review session is on 13 April (20 minutes reserved). Final EMT material to be ready by 17 April.
- Arthur's explicit framing: this is not a wish list. Every investment case must demonstrate how it will be funded. Weak justification will not pass EMT.

---

## Critical Issue — ÖNORM / BOQ Capacity Gap

This topic dominated the second half of the meeting.

### Background

Two separate signals arrived last week:
1. Jens Kremer (PM) confirmed the ÖNORM concept has been aligned with customers
2. Jens Klein (PO, BOQ) raised a major capacity alarm: implementing ÖNORM for 26.2 requires an estimated **200 person-days** of BOQ effort. Available capacity is approximately **20 person-days**. The shortfall is **10x**.

Beate confirmed a similar picture looking at the Sales team planning page: roughly 130 person-days total availability in Sales, with significant maintenance overhead already consuming capacity. The total workload for ÖNORM across both teams does not appear to fit within either 26.2 or 26.3 combined.

### Historical Context (Reinhardt)

- Full ÖNORM implementation was estimated at 800–1,000 person-days last year
- What is now surfacing is a partial reallocation — Sales team pushing items they consider BOQ scope to the BOQ team — not new work
- Total effort has not increased. The problem is that BOQ is already overloaded and every other team is pushing scope toward them.

### Structural Observation (Reinhardt)

BOQ and Sales handle overlapping domain territory. Better cross-team collaboration between Janas (Sales), Silvio (BOQ), and the QTO team would help. The model working in Jeff's teams (shared work across team boundaries) is the reference.

### Julien's Position

Cross-team coordination may be part of the answer, but is not the root cause. The root cause is **capacity**. Two options on the table:
1. Accept a partial delivery (known quality risk)
2. Formally declare ÖNORM undeliverable in this release cycle and manage that communication

Julien's strong preference: face reality early rather than discover the miss in four months.

### Andre's Question

Is ÖNORM required for any of the five target GCs? If not, it competes directly with the non-negotiable goal and should be treated accordingly. He also noted that the cross-team collaboration problem is real but structural — it requires time and trust to build, not just a meeting. Introducing a PO for Sales is the correct enabling step.

### Positive Signal (Arthur)

The fact that Jens Klein raised this clearly and early is a direct result of having a PO in place. Before, this would have surfaced as vague concern rather than a quantified problem.

### Agreed Next Step

Beate to organize a sync with both Jens Kremer and Jens Klein, Reinhardt, and Andre to get a definitive answer on whether ÖNORM is deliverable across 26.2 and 26.3 combined. **This answer is needed before 26.2 release planning closes.**

---

## Support Request — Techsoft 3D (Andre)

Andre requested help identifying the key account manager and solutions architect on the RIB account at Techsoft 3D (the rendering server provider). The current practice of submitting tickets without leveraging the SLA relationship is insufficient for the BIM performance investigation.

Reinhardt confirmed the Techsoft 3D deal was negotiated by Stefan Gaba as an RIB-wide agreement covering multiple product lines for five to six years. Arthur suggested contacting Stefan Gaba directly via Teams message. Andre will send an email.

---

## Process

Arthur requested that all workstream owners add numeric IDs (e.g. 1.1, 2.1) to their Confluence pages to match the structure in the Word document. This is a low-effort change that significantly improves communication clarity.

---

## Action Items & Follow-ups

| Who | Action | Due |
|-----|--------|-----|
| Reinhardt Fraunhoffer | Share BIM escalation details and Track 1 priority list during the week, following his 10:30 PM alignment meeting | During the week |
| Reinhardt Fraunhoffer | Update Confluence with all relevant documents (Excel and other formats) | End of week |
| Beate Kasper | Organize sync with Jens Kremer, Jens Klein, Reinhardt, and Andre on ÖNORM feasibility across 26.2 and 26.3 | Before 26.2 release planning closes |
| Andre | Contact Stefan Gaba regarding the Techsoft 3D account relationship and SLA | ASAP |
| All workstream owners | Review Beate's craft group structure in the chat and confirm or propose changes | Promptly |
| All workstream owners | Begin populating Confluence investment case pages and book a review session with Julien and Arthur when ready | Incremental |
| Arthur Berganski | Start working principles workstream from the following week | Following week |
