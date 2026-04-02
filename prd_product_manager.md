# HRA Web Analytics — Product Requirements Document
### Role: Senior Product Manager
### Audience: Internal IU/CNS Team
### Prepared for: Client Presentation (Course Project)

---

## Executive Summary

The Human Reference Atlas (HRA) is a suite of scientific web tools built by Indiana University's CNS Center. It includes the Registration User Interface (RUI), the Exploration User Interface (EUI), the Cell Distance Explorer (CDE), the HRA Portal, and the Knowledge Graph (KG). These tools serve researchers worldwide who work with human tissue data.

This PRD defines what we want to learn from the available web log data, what that means for the people who use these tools, and what the CNS team should do differently as a result. The analysis is grounded in two datasets: 16.3 million server log records from cns.iu.edu (2008–2026) and 12.8 million records from the HRA ecosystem (2023–2026), of which 114,884 are detailed user interaction events.

The five client questions are the starting point. This document expands them into a full picture of user behavior, surfaces critical tracking gaps, and proposes concrete improvements.

---

## Goals

- Understand how researchers actually use the RUI, EUI, and CDE — not how we assume they use them
- Identify features that are invisible to users (built but never clicked)
- Identify where users abandon workflows before completing them
- Define baseline success metrics that the team can track going forward
- Surface data collection gaps that are limiting future insight

## Non-Goals

- This is not a redesign specification — visual and interaction design decisions are owned by the design team
- This does not cover backend API performance or infrastructure optimization
- This does not cover the Knowledge Graph (KG) or Apps hub in depth — those are lower priority given available event data

---

## User Context

The primary users of the HRA tools are **biomedical researchers** — scientists who work with human tissue samples and need to register, explore, and analyze spatial data at the organ and cell level. They are technically literate but are not necessarily trained in software or UX. They use these tools as part of a research workflow, not casually.

Secondary users include **educators** and **students** who access the CNS Center website for publications and presentations.

A third and growing category is **AI crawlers** (classified as `AI-Assistant / Bot` in the data), which are indexing HRA content at an increasing rate. This is not a user in the traditional sense, but it signals that HRA content is being consumed programmatically and the team should monitor this trend.

---

## Success Metrics (Defined from Scratch)

These are the KPIs we recommend the CNS team adopt to measure HRA tool health going forward.

### Engagement Metrics

| Metric | Definition | Why It Matters |
|---|---|---|
| **Monthly Active Sessions** | Unique `sessionId` values per month across all apps | Top-line measure of tool usage |
| **Event Volume per Session** | Total events ÷ total sessions | Are users doing more per visit over time? |
| **Workflow Completion Rate** | % of sessions that reach the final step of a workflow (e.g., Register in RUI, Apply in EUI Spatial Search) | Reveals whether tools are usable end-to-end |
| **Feature Adoption Rate** | % of sessions that use a specific feature (e.g., opacity toggle, spatial search) | Tells us which features are actually discovered |
| **Error Rate** | Error events ÷ total events, per app and per version | Directly measures tool reliability |

### Content Metrics (CNS Website)

| Metric | Definition | Why It Matters |
|---|---|---|
| **Publication Download Volume** | Monthly PDF download count per paper | Measures academic reach and content relevance |
| **Human Traffic Share** | Likely Human ÷ total requests per month | Tracks bot infiltration over time |
| **Geographic Reach** | Unique countries visiting per quarter | Measures international adoption |

### Tracking Health Metric

| Metric | Definition | Why It Matters |
|---|---|---|
| **Instrumentation Coverage** | % of user-facing features that fire at least one tracked event | Measures how much of the product is observable |

---

## The 5 Questions: PM Analysis

---

### Q1 — Event Frequency Distribution: Where Does User Attention Go?

**What we're asking:** Of all the things users do inside the HRA tools — clicking, hovering, using the keyboard, navigating pages, changing model settings, hitting errors — what is the actual breakdown? And is usage growing?

**What the data can tell us:**
- The 114,884 event records break down into: `click`, `hover`, `pageView`, `keyboard`, `modelChange`, and `error`
- We can see this breakdown overall, per tool (RUI vs EUI vs CDE), and per month from 2023 to 2026
- The CNS website (no event tracking) gives a parallel view of page-request volume going back to 2008

**What this means for the product:**

*If errors are a large share of all events* (the analysis plan flags they may be ~25%), that is a reliability crisis — one in four user actions results in a failure. That is not acceptable in a research tool where scientists are trying to accomplish precise, time-sensitive tasks.

*If hover events far outnumber click events on a given element*, users are noticing it but not acting — a classic discoverability problem. The label, placement, or affordance is unclear.

*If event volume is growing month over month*, the tools are gaining traction and the investment in this infrastructure is paying off. If it is flat or declining, the team needs to investigate whether new tool versions broke something or whether researchers are switching to alternatives.

**What the CNS website adds:**
Even without click-level tracking, the 18-year traffic record (2008–2026) is a strategic asset. It shows whether overall interest in HRA research is growing, whether academic publications are driving traffic spikes, and how the bot/human ratio has shifted over time (important now that AI crawlers are active).

**Gaps:**
- There is no user segmentation — we cannot tell whether the same 10 researchers are responsible for most events, or whether usage is spread across hundreds of users. Session-level analysis (using `sessionId`) can partially address this.
- We cannot link events to outcomes (e.g., did the researcher who registered tissue go on to publish a paper using that data?).

**Recommendations for the team:**
1. Add a dashboard widget showing monthly event volume by app — make this the team's heartbeat metric
2. Immediately investigate the error event share — if it is above 10%, treat it as a P0 reliability issue
3. Add user segmentation to the tracking system: distinguish new vs. returning sessions (a hashed return-visit cookie would suffice)

---

### Q2 — Most and Least Used UI Elements: What Did We Build That Nobody Uses?

**What we're asking:** Which buttons, panels, and features do users actually click? Which ones were built but are effectively invisible?

**What the data can tell us:**
- Every `click` and `hover` event contains the exact UI element path (e.g., `rui.left-sidebar.opacity-settings.toggle`)
- We can rank every element in the RUI, EUI, and CDE by click count
- Elements with fewer than 5 total clicks across all sessions and time are candidates for "under-used"
- Comparing hover count to click count for the same element reveals discoverability problems

**What this means for the product:**

This is where the data becomes most actionable for a product team.

*Highly used elements* should be surfaced more prominently, documented thoroughly, and protected from removal in future versions.

*Under-used elements* fall into one of three categories:
1. **Niche but intentional** — used by a small subset of expert users (keep, but don't invest in expanding)
2. **Discoverable but unnecessary** — users find it but don't need it (consider removing to reduce cognitive load)
3. **Invisible** — users never find it even though it would help them (needs relabeling, repositioning, or onboarding)

The hover-vs-click comparison is the key to distinguishing categories 2 and 3. If users hover but don't click, the feature exists in their mental model but something is blocking action. If users never hover, they don't know it's there.

**What the CNS website adds:**
On the CNS website, "UI elements" translates to pages and PDFs. The top-20 most downloaded publications are a proxy for research impact — the team should know which papers drive the most interest and ensure they remain accessible and up to date.

**Gaps:**
- We only know which elements were clicked, not *why* users stopped there. Qualitative research (user interviews, usability testing) is needed to interpret the low-use elements correctly.
- The `hover` event may not be instrumented for all elements — confirming instrumentation completeness is important before drawing negative conclusions.

**Recommendations for the team:**
1. Share the ranked element list with the design team — prioritize the top 10 for polish and the bottom 10 for a usage investigation
2. For any element with >100 hovers but <10 clicks, schedule a usability review — this is a clear signal of a discoverability problem
3. For elements with 0 events, confirm they are actually instrumented before declaring them unused

---

### Q3 — RUI Opacity Feature: A Useful Tool That Most Users Miss

**What we're asking:** The RUI lets users toggle organ transparency to see inside the 3D body model. Did researchers use this?

**What the data tells us:**
- 206 opacity events out of 9,430 total RUI events = **2.2% of all RUI activity**
- The master opacity panel toggle (`opacity-settings.toggle`) was used only **4 times**
- Individual organ opacity toggles account for the majority — users who find the feature tend to use it on specific structures (tongue, bisection-line, etc.)
- The feature is real and functional — it is just not being discovered by most users

**What this means for the product:**

2.2% is low but not zero. The researchers who did use it appear to have engaged deeply with it (toggling 40+ individual structures). This is a **discoverability problem, not a value problem**.

The master toggle being used only 4 times suggests users are either:
- Not finding the opacity panel at all, or
- Finding it but not understanding that the top-level toggle controls all structures at once

**What the CNS website adds:**
1,422 downloads of the RUI paper (`2021-Bueckle-3D_VR_vs_2D_Desktop_RUI.pdf`) show strong academic interest in the RUI as a concept. The tool has an audience — they may just not be discovering all its features once inside it.

**Gaps:**
- We do not know what the user was trying to accomplish when they used or skipped opacity. Were they unaware it existed, or did they find it irrelevant to their task?
- We do not have data from before the current tracking period — we cannot say whether opacity usage has improved or declined since launch.

**Recommendations for the team:**
1. Add a tooltip or first-use callout to the opacity panel — something like "Adjust organ transparency to better position your tissue block"
2. Consider whether the opacity controls should be surfaced in the main viewport rather than buried in the left sidebar
3. Track whether the opacity tutorial (if one exists) correlates with higher opacity usage in the same session

---

### Q4 — EUI Spatial Search: A Power Feature With a Funnel Drop-Off Problem

**What we're asking:** Spatial Search is one of the EUI's flagship features. Did users actually use it, and how far through the workflow did they get?

**What the data tells us:**
- **3,071 spatial search events** recorded — this is the most-used advanced feature in the entire dataset
- **227 users** clicked the Spatial Search entry button
- **136 users** clicked "Continue" after configuring their organ selection → **40% drop-off at configuration step**
- Users who do complete the workflow engage deeply: they use keyboard navigation (q/w/e/a/s/d), explore all three result panels (anatomical structures, tissue blocks, cell types), and interact with the radius slider
- Brain is the most selected organ

**What this means for the product:**

Spatial Search is genuinely valued — 3,071 events across 227 initiated searches is strong signal. But losing **40% of users between the entry click and the "Continue" step** is a significant funnel problem. That configuration step (organ and sex selection) is where users are getting stuck or giving up.

The keyboard usage (q/w/e/a/s/d) is a strong indicator of **power users** — researchers who have invested time in learning the tool deeply. These users are valuable advocates. The team should consider whether there are features they could add specifically for this segment (keyboard shortcut reference, bookmarked searches, export of results).

**What the CNS website adds:**
Combined downloads of the two EUI papers (1,993 + 1,392 = 3,385) make these the most downloaded HRA tool papers on the CNS site. Academic interest in the EUI is high. There is an expectation from the research community that the tool will be capable and polished.

**Gaps:**
- We cannot see what users searched for, only that they searched (organ selection paths exist but need parsing)
- We do not know if the users who dropped off at "Continue" tried again later in the same session or a different session
- We cannot tell if the search results were useful — did users find tissue blocks that matched their query?

**Recommendations for the team:**
1. Redesign or simplify the organ/sex configuration step — reduce the number of required choices or add a "search for an organ" shortcut
2. Add a progress indicator ("Step 2 of 3") to set user expectations in the configuration flow
3. Track which organs are most searched and make those the default or most prominent options in the selector
4. Consider adding a "Save Search" or "Share Search" feature for power users

---

### Q5 — CDE Chart Downloads: A Blind Spot in the Data

**What we're asking:** After researchers generate histograms and violin plots in the CDE, how often do they download them?

**What the data tells us:**
- We can trace the CDE workflow to a point:
  - 259 users reached the landing page (`/cde/`)
  - 222 users navigated to the create page (`/cde/create`)
  - 132 users clicked Submit to generate a visualization
  - 165 users reached the output page (`/cde/visualize`) where charts appear
- **Download events for the charts do not exist in the tracking data** — this action was never instrumented

**What this means for the product:**

This is a tracking gap, not a user behavior finding. We know 132 users generated a visualization, but we have no idea how many downloaded the output. For a research tool, downloading charts is arguably the primary value delivery moment — the point where the user gets something they can put in a paper or share with a colleague. Not tracking this is a significant blind spot.

The funnel also reveals a notable anomaly: **165 users reached the visualize page but only 132 clicked Submit**. This means 33 users arrived at the output page without going through the normal creation flow — possibly direct links, bookmarks, or back-navigation. This warrants investigation.

**Gaps:**
- No download event tracking for histograms or violin plots
- No tracking of chart type selected (histogram vs. violin plot vs. other)
- No tracking of what data users uploaded (file type, size, content category)

**Recommendations for the team:**
1. **Immediately add download event tracking** for all chart types on the `/cde/visualize` page — this is the single highest-priority instrumentation gap
2. Recommended event names: `cde-ui.visualize-page.histogram.download` and `cde-ui.visualize-page.violin-plot.download`
3. Investigate the 33 users who reached the visualize page without submitting — understand whether this is a navigation bug or expected behavior
4. Add a "Share Results" event to understand whether users are sharing chart URLs with collaborators

---

## Additional Research Questions (Beyond the Original 5)

The following are answerable from the existing data and provide additional value for the client presentation.

---

### AQ1 — RUI Session Completion Rate: How Many Registrations Actually Happen?

**What we're asking:** Of all researchers who open the RUI, what percentage successfully complete a tissue registration?

**Why it matters:** The RUI's entire purpose is tissue registration. If completion rate is low, the tool has a fundamental usability problem — users are starting but not finishing the core task.

**What the data can tell us:** Using `sessionId`, trace sessions from first RUI event → `rui.stage-content.3d` (tissue block placed) → `rui.stage-content.register` (registration complete). The drop-off at each step reveals where users abandon.

**Recommendation:** If completion rate is below 70%, treat this as a critical UX problem. Conduct a usability study with 3–5 researchers to identify where they get stuck.

---

### AQ2 — Error Investigation: Is 25% of User Activity Failure?

**What we're asking:** Error events may represent ~25% of all tracked events. Which apps and versions are generating these errors, and is the situation improving or getting worse over time?

**Why it matters:** A 25% error rate in a scientific research tool is unacceptable. Researchers who hit errors repeatedly will stop trusting the tool and stop using it. This is a retention risk.

**What the data can tell us:** Filter to `event == 'error'`, group by `app` and `version` (from the `query` field). Plot error rate over time to see if recent versions have improved things.

**Recommendation:** If `ccf-eui` is the primary error source (as the analysis plan suggests), escalate this to the engineering team immediately as a reliability issue requiring a dedicated fix sprint.

---

### AQ3 — AI Bot Growth: Is HRA Being Indexed by AI Systems?

**What we're asking:** The `AI-Assistant / Bot` traffic type exists in both datasets. How much of HRA traffic comes from AI crawlers, and is this share growing?

**Why it matters:** AI systems indexing HRA content means HRA data may be showing up in AI-generated research summaries, chatbot answers, and automated literature reviews. This is a new form of impact that the team should be tracking and potentially designing for (e.g., structured metadata, robots.txt policies, API-first content access).

**What the data can tell us:** Filter to `traffic_type == 'AI-Assistant / Bot'`, plot share of total traffic by month from 2023 to 2026.

**Recommendation:** Present this trend to the CNS leadership team as a strategic consideration — if AI indexing is growing, the HRA may need a policy position on AI access to its content.

---

### AQ4 — Geographic Reach: Where in the World Is HRA Being Used?

**What we're asking:** Which countries generate the most HRA Portal traffic? Has the geographic distribution shifted since launch?

**Why it matters:** HRA is presented as a global resource for biomedical research. If 90% of usage comes from the US, that is a finding that should inform outreach, localization, and partnership strategy.

**What the data can tell us:** Use `c_country` filtered to Portal rows and human traffic. Plot a world heatmap and a top-20 country ranking. Compare 2023 vs. 2025 to show change over time.

**Recommendation:** If usage is heavily US-centric, recommend the team pursue partnerships with international biobanks or atlas initiatives (e.g., European initiatives) to broaden reach.

---

### AQ5 — Power Users vs. Casual Users: Session Depth Analysis

**What we're asking:** Using `sessionId`, how long are sessions and how many events do they contain? Are most users just browsing, or are there dedicated power users completing full workflows?

**Why it matters:** The answer changes the product strategy entirely. If most users are casual browsers, the priority is better onboarding and discoverability. If most users are power users doing long sessions, the priority is efficiency, keyboard shortcuts, and advanced features.

**What the data can tell us:** Group events by `sessionId`, count events per session and calculate session duration (max timestamp − min timestamp). Plot the distribution. Flag sessions with keyboard events as likely power users.

**Recommendation:** Segment the user base into at least two personas (casual / power user) and ensure the product roadmap serves both explicitly.

---

## Summary of Recommendations (Prioritized)

| Priority | Recommendation | Category |
|---|---|---|
| P0 | Investigate and fix error events — if ~25% of all events are errors, this is a reliability crisis | Reliability |
| P0 | Add download event tracking to CDE visualize page | Instrumentation |
| P1 | Redesign the EUI Spatial Search configuration step to reduce 40% drop-off | UX |
| P1 | Improve opacity feature discoverability in RUI (tooltip, repositioning) | UX |
| P1 | Define and begin tracking the 5 success metrics defined in this document | Metrics |
| P2 | Investigate under-used UI elements (< 5 clicks) and classify: niche, unnecessary, or invisible | UX |
| P2 | Investigate the 33 CDE users who reached `/visualize` without submitting | UX/Bug |
| P3 | Track AI crawler growth and develop a policy position on AI access to HRA content | Strategy |
| P3 | Conduct geographic analysis and present findings to CNS leadership | Strategy |
| P3 | Build power user persona using session depth data | Research |

---

## What We Cannot Answer (and What Would Fix It)

| Question | Current Gap | Fix Required |
|---|---|---|
| How many charts did users download from CDE? | Download events not instrumented | Add `cde-ui.visualize-page.*.download` tracking |
| Why did users abandon the EUI Spatial Search config step? | No qualitative data | Usability study with 3–5 researchers |
| Are the same researchers returning, or is it all new users? | No return-visit tracking | Add hashed return-visit identifier to event schema |
| What data did CDE users upload? | File metadata not tracked | Add file type + size to upload event |
| Did registered tissue samples lead to publications? | No downstream outcome tracking | Requires integration with publication databases |
