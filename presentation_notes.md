# Visualization Presentation Notes
**HRA Web Analytics Dashboard — Team Crimson**

Brief talking points for each chart. Organized by client question.

---

## Q1 — Event Frequency Distribution

> *"How often are different types of user interactions happening, and how is usage trending over time?"*

---

### q1_1 — Event Type Distribution (Horizontal Bar)

**What it shows:** The share of each interaction type across all 111,382 clean events.

**Key talking points:**
- **Clicks dominate at 35%** — users are actively engaging with UI elements, not just browsing.
- **Hover at 20.8%** — a significant portion of interactions are exploratory, suggesting users scan before committing to a click.
- **23.2% error rate** is the most important number here. Nearly 1 in 4 events is an error event. This is worth flagging directly to the client — is this a known issue, or new information?

---

### q1_2 — Event Type Mix per App (Stacked Bar)

**What it shows:** For each app, what proportion of its events are clicks, hovers, page views, etc. Each bar adds to 100%.

**Key talking points:**
- Comparing bars side by side reveals that **apps have very different interaction profiles** — not all tools are used the same way.
- Apps with a high error segment (especially CDE and ASCT+B) may have UI reliability issues worth investigating.
- **KG Explorer and HRA Portal** are predominantly click-driven, suggesting more directed, goal-oriented usage.

---

### q1_3 — Monthly Event Volume by App (Line Chart)

**What it shows:** How event volume for each app has changed month over month from Aug 2025 to Jan 2026.

**Key talking points:**
- **KG Explorer spiked sharply in Oct–Nov 2025** then dropped — this likely corresponds to a specific event, publication, or outreach push. Worth asking the client what happened in that window.
- **EUI, RUI, and CDE are lower volume but stable** — consistent core user base.
- The data covers 6 months (Aug 2025–Jan 2026); longer historical data would reveal seasonal trends.

---

### q1_4 — Monthly Volume: HRA Events vs. CNS Requests (Dual-Axis Area)

**What it shows:** Two different scales of activity plotted together — CNS website requests (left axis, blue) and HRA interaction events (right axis, orange) — over the same months.

**Key talking points:**
- **CNS sees 150,000–200,000 human requests per month**, making it a high-traffic informational site.
- **HRA interaction events are much lower volume** because they track deliberate user actions inside tools, not page loads — the two datasets measure different things.
- Both datasets show activity in the same window, providing a cross-platform picture of the HRA ecosystem's reach.

---

## Q2 — Most and Least Used UI Elements

> *"Which UI elements do users interact with most, and which are being ignored?"*

---

### q2_1 — Top 20 Clicked Elements — RUI (Horizontal Bar)

**What it shows:** The 20 most-clicked UI paths in the RUI tool, by total click count.

**Key talking points:**
- **`stage-content.3d` leads with 1,276 clicks** — the 3D viewer is by far the most-used element; users are actively exploring the spatial model.
- **`stage-content.register` (514 clicks)** is the second-highest — the core registration action is being used heavily, which is the tool's primary purpose.
- Metadata fields (donor organ, author name, sex) cluster in the middle — users do fill in registration details, but the 3D interaction is the dominant behaviour.

---

### q2_2 — Top 20 Clicked Elements — EUI (Horizontal Bar)

**What it shows:** The 20 most-clicked UI paths in the EUI tool.

**Key talking points:**
- **`right-panel.results.donor.card` and `right-panel.results.select`** are nearly tied at the top (~370 each) — users are browsing and selecting donor results as their primary workflow.
- **`body-ui.scene` (260 clicks)** shows strong engagement with the 3D body model.
- **`body-ui-controls.organ-select.organ-search` (249)** — users are actively filtering by organ, suggesting the organ-specific search is a key entry point.

---

### q2_3 — Top 20 Clicked Elements — CDE (Horizontal Bar)

**What it shows:** The 20 most-clicked UI paths in the CDE tool.

**Key talking points:**
- The top elements all belong to the **create-visualization-page workflow** — file upload, submit, axis selectors — showing users follow a clear, linear process.
- **`file-upload.upload` (163)** and **`visualize-data.submit` (132)** are the two gateway actions; everything else is configuration in between.
- Navigation elements (header links) also appear frequently, suggesting some users explore the platform after arriving at CDE rather than immediately starting a visualization.

---

### q2_4 — Under-used Elements Table

**What it shows:** UI paths that received fewer than 5 total clicks, grouped by app.

**Key talking points:**
- **EUI has 449 under-used paths** — by far the most. Many of these are specific organ-toggle and filter controls that users are not discovering.
- **RUI has 104 under-used paths**, mostly edge-case structure adjustments.
- **CDE has only 27** — its simpler, linear UI has less surface area for users to miss.
- This table is most useful as a starting point for a UX audit: which of these are intentionally niche features, and which should be more prominent?

---

### q2_5 — Hover vs. Click Scatter (Discoverability)

**What it shows:** Each dot is a unique UI element. Position on the x-axis = how many times it was clicked; y-axis = how many times it was hovered. Elements in the upper-left quadrant (many hovers, few clicks) signal discoverability problems.

**Key talking points:**
- The dashed diagonal line is the reference — elements on the line are hovered and clicked equally.
- **`eui.right-panel.statistics`** sits far above the line: ~590 hovers but 0 clicks. Users are hovering over it but never clicking — the element looks interactive but either doesn't respond to clicks, or users don't know they can click it.
- **`eui.left-panel.filter-text`** shows similar behaviour with ~287 hovers and 0 clicks.
- These are concrete, actionable discoverability findings to bring to the design team.
- Note: 1 extreme outlier (~4,100 hovers) is clipped from the chart for readability.

---

## Q3 — RUI Opacity Feature Usage

> *"Are users engaging with the opacity toggle feature in the RUI?"*

---

### q3_1 — Stat Card

**What it shows:** Headline numbers for opacity feature usage.

**Key talking points:**
- **206 opacity toggle events** out of 9,430 total RUI events = **2.2% of all RUI activity**.
- Users toggled opacity on **47 unique anatomical structures**, showing the feature is being used across a wide range of structures — not just one or two.
- Low adoption overall, but the breadth of structure coverage suggests the feature is genuinely useful to the users who find it.

---

### q3_2 — Top Anatomical Structures (Horizontal Bar)

**What it shows:** Which specific structures users most commonly toggled opacity on.

**Key talking points:**
- **Tongue leads with 17 toggles**, followed by Submandibular Gland and Cortex of Kidney — these align with common tissue registration use cases.
- Most structures below the top 3 have very low counts (3 or fewer) — the feature is used occasionally for a wide variety of structures, not concentrated on just a few.
- A good follow-up question for the client: does this structure distribution match what the team expected from the tool's target user base?

---

### q3_3 — Toggle Type Breakdown (Donut)

**What it shows:** What proportion of opacity interactions are per-structure toggles vs. broader controls.

**Key talking points:**
- **56% are per-structure toggles (116 events)** — users are making fine-grained adjustments to individual anatomical structures.
- **24% use the all-structures toggle (50 events)** — showing and hiding everything at once is also a common operation.
- **17.5% are landmark toggles (36 events)** — the bisection line and other landmarks are being managed separately.
- **The master settings toggle accounts for only 1.9% (4 events)** — almost no one opens the master opacity settings panel. This is a discoverability signal.

---

## Q4 — EUI Spatial Search Usage

> *"Are users engaging with the Spatial Search feature, and where do they drop off?"*

---

### q4_1 — Spatial Search Session Funnel

**What it shows:** How many unique user sessions made it through each step of the Spatial Search workflow.

**Key talking points:**
- **66 sessions opened Spatial Search** out of 515 total EUI sessions — about 1 in 8 users try it.
- The sharpest single drop is **Configure → Continue: 50 down to 27 sessions (46% lost)**. Nearly half of users who configure an organ never click Continue. This is the most actionable finding — something about the configuration step is causing abandonment.
- **Only 5 sessions ultimately applied** Spatial Search results to their filters, a 92% drop from entry. The feature is being explored but rarely completing its intended workflow.
- A client question worth raising: was the organ configuration step recently redesigned? If it's new, the drop-off may reflect unfamiliarity rather than a UX problem.

---

### q4_2 — Top Organs Selected (Horizontal Bar)

**What it shows:** Which organs users most commonly select when configuring a Spatial Search.

**Key talking points:**
- **Kidney (L) is the most selected organ (8 times)**, followed by Heart (5) and Large Intestine (4).
- The organ distribution is heavily skewed toward kidney — this likely reflects the HRA's strong kidney dataset coverage and an active kidney research user base.
- 19 unique organs were selected in total, showing breadth of use even within the small set of sessions that configure a search.

---

### q4_3 — Keyboard Navigation Stat Card

**What it shows:** What percentage of EUI sessions used keyboard navigation (a power-user behaviour).

**Key talking points:**
- **Only 0.6% of sessions (3 out of 515)** used keyboard shortcuts.
- This is either a sign that very few power users are in the dataset, or — more likely — that the keyboard navigation feature is not discoverable. Users who would benefit from it simply don't know it exists.
- A simple fix could be a keyboard shortcut hint or tooltip on first use.

---

## Q5 — CDE Histogram / Violin Downloads

> *"How often are users downloading histogram and violin-plot visualizations from the CDE?"*

---

### q5_1 — CDE Workflow Session Funnel

**What it shows:** How many unique sessions progressed through the CDE's core workflow, from landing to generating a visualization.

**Key talking points:**
- **175 sessions landed on the CDE**; only **33 sessions reached Submit** (19% of entry).
- The biggest drop is **Landing → Create page: 100 sessions lost (57%)**. More than half of users who land on the CDE never start creating a visualization. This could point to unclear onboarding, or users arriving via a link and bouncing once they see the tool requires a data upload.
- **35 sessions reached the Visualize page** — slightly more than the 33 who submitted, likely because some users navigated directly to a saved visualization URL.

---

### q5_2 — Download Tracking Gap (Callout)

**What it shows:** A clear statement of a data gap: the original question cannot be answered from existing logs.

**Key talking points:**
- Despite **4,294 CDE events logged** and **35 sessions reaching the Visualize page**, there are **0 download events** in the data.
- Download interactions on the histogram and violin-plot charts are simply not being tracked.
- This is an important finding to surface honestly — the client may not realize this gap exists.
- It is also an opportunity: adding tracking now means the question can be answered in the next data collection cycle.

---

### q5_3 — Recommended Event Names (Table)

**What it shows:** A concrete list of event tracking additions, following the CDE's own path naming convention.

**Key talking points:**
- **Two high-priority events** directly answer Q5: `cde-ui.visualize-page.histogram.download` and `cde-ui.visualize-page.violin-plot.download`.
- The event names follow the exact same dot-notation pattern already used in the CDE (e.g., `cde-ui.create-visualization-page.visualize-data.submit`), so integration should be straightforward.
- Medium-priority additions (scatter plot download, data export) would further enrich the dataset at low implementation cost.
- A good client question: is download tracking intentionally absent, or was it overlooked? If it was for a grant report or publication, the urgency changes.

---

## Quick Reference — All Charts

| File | Question | Chart Type | Key Finding |
|---|---|---|---|
| q1_1 | Q1 | Horizontal bar | 23.2% error rate — flag for client |
| q1_2 | Q1 | Stacked bar | App-level interaction profiles vary significantly |
| q1_3 | Q1 | Line chart | KG Explorer spike Oct–Nov 2025 |
| q1_4 | Q1 | Dual-axis area | CNS 150–200K requests/month vs HRA 5–50K events |
| q2_1 | Q2 | Horizontal bar | RUI: 3D viewer dominates (1,276 clicks) |
| q2_2 | Q2 | Horizontal bar | EUI: results browsing is the core workflow |
| q2_3 | Q2 | Horizontal bar | CDE: linear upload→submit workflow |
| q2_4 | Q2 | Table | EUI has 449 under-used paths |
| q2_5 | Q2 | Scatter | `right-panel.statistics`: 590 hovers, 0 clicks |
| q3_1 | Q3 | Stat card | 206 opacity events = 2.2% of RUI activity |
| q3_2 | Q3 | Horizontal bar | Tongue most toggled (17); 47 unique structures |
| q3_3 | Q3 | Donut | 56% per-structure; master settings almost unused |
| q4_1 | Q4 | Funnel | 66 → 5 sessions; Configure→Continue loses 46% |
| q4_2 | Q4 | Horizontal bar | Kidney (L) most selected organ |
| q4_3 | Q4 | Stat card | 0.6% of EUI sessions use keyboard navigation |
| q5_1 | Q5 | Funnel | 175 → 33 sessions; 57% drop at landing |
| q5_2 | Q5 | Callout | 0 download events tracked in CDE |
| q5_3 | Q5 | Table | 2 high-priority events to add for Q5 |
