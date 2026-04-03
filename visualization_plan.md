# HRA Project — Visualization Plan

> **Purpose:** Ranked list of all proposed visualizations, mapped to client questions or flagged as additional. Use this to guide the client meeting and confirm priorities before implementation.

---

## Mapping to the 5 Client Questions

| Your Idea | Client Question | Notes |
|---|---|---|
| #9 — CDE histogram/violin downloads | **Q5** | Direct match |
| #6 — HRA vs CNS distribution | **Q1** (partial) | Volume split; supplements event type breakdown |
| #1, #2, #3, #4, #5, #7, #8 | **Additional / Misc** | Outside the 5 questions — ranked by impact below |

---

## The 5 Client Questions — Visualization Specs

---

### Q1 — Event Frequency Distribution

**Visualizations:**
1. **Horizontal bar chart** — event type breakdown (click, hover, pageView, keyboard, modelChange, error) as % of total 114K events
2. **Stacked bar chart** — event type mix per app (RUI, EUI, CDE) — one bar per app, segments = event types
3. **Line chart** — monthly event volume from mid-2023 to Jan 2026, one line per app
4. **Stacked area chart** — HRA vs. CNS monthly request volume on the same timeline (supplements #6 from your list)

**Data source:** HRA logs (`site == 'Events'`) + CNS logs (page requests)
**Filter:** Human traffic only

**Client question to ask:** "Is the ~25% error event rate a known issue, or is this new information?"

---

### Q2 — Most and Least Used UI Elements

**Visualizations:**
5. **Horizontal bar chart × 3** — top 20 clicked elements for RUI, EUI, and CDE separately (three charts)
6. **Table** — under-used elements (< 5 total clicks), grouped by app, with click count
7. **Scatter plot** — hover count vs. click count per element; elements far above the diagonal (high hover, low click) are discoverability problems

**Data source:** HRA logs (`site == 'Events'`, `event == 'click'` and `event == 'hover'`)
**Filter:** Human traffic only

**Client question to ask:** "Are there UI elements you know are under-used that you'd like us to investigate specifically?"

---

### Q3 — RUI Opacity Feature Usage

**Visualizations:**
8. **Single stat card** — "206 opacity events = 2.2% of all RUI activity"
9. **Horizontal bar chart** — top anatomical structures whose opacity was toggled (top 15)
10. **Donut chart** — master opacity toggle (4 events) vs. per-structure toggles (202 events)

**Data source:** HRA logs (`app == 'ccf-rui'`, paths containing `opacity`)
**Filter:** Human traffic only

**Client question to ask:** "Was the opacity feature recently added or redesigned? That would explain the low adoption."

---

### Q4 — EUI Spatial Search Usage

**Visualizations:**
11. **Funnel chart** — Spatial Search workflow: Entry → Configure organ → Continue → View results → Apply (with % retained at each step and absolute session counts)
12. **Horizontal bar chart** — top organs selected in Spatial Search configuration
13. **Single stat** — "X% of EUI sessions used keyboard navigation" (power user indicator)

**Data source:** HRA logs (`app == 'ccf-eui'`, paths containing `spatial-search`)
**Filter:** Human traffic only; funnel counts unique sessions, not raw clicks

**Client question to ask:** "The configuration step (organ selection) loses ~40% of users — is this step newly added, or has it always been part of the workflow?"

---

### Q5 — CDE Histogram/Violin Downloads

**Visualizations:**
14. **Funnel chart** — CDE workflow: Landing → Create page → Submit → Visualize page (session counts at each step)
15. **Callout / annotation** — "Download events for charts are not currently tracked — this question cannot be answered from existing data"
16. **Table** — recommended event names to add: `cde-ui.visualize-page.histogram.download`, `cde-ui.visualize-page.violin-plot.download`

**Data source:** HRA logs (`app == 'cde-ui'`)
**Filter:** Human traffic only

**Client question to ask:** "Was download tracking intentionally left out of the CDE, or is this an oversight? Do you need this for a grant report or publication?"

---

## Additional / Miscellaneous Visualizations (Ranked by Impact)

---

### MISC-1 — Geographic Reach ⭐⭐⭐⭐⭐
*(Your idea #1 and #8 combined)*

**Why high impact:** Visually impressive for a client presentation. Shows global reach of a US-funded research tool. Directly answers "who is using this?"

**Visualizations:**
- **World choropleth map** — shaded by number of human visits per country (HRA Portal rows)
- **Top 20 countries bar chart** — absolute visit count, colored by region
- **Top downloaded file per country** — table showing the single most-requested meaningful file per country, across both datasets (file names extracted from `cs_uri_stem`)
- **Content type per country** — stacked bar chart, top 15 countries × meaningful content type breakdown (PDF, 3D model, dataset, HTML page)

#### File-Level Granularity Strategy (HRA Logs)

The HRA logs mix scientifically meaningful files with CDN noise (JS/CSS/fonts/images). We apply three filters in combination to isolate meaningful files:

**Layer 1 — Filter by `sc_content_type`** (keep these):
| Content Type | What it is |
|---|---|
| `application/pdf` | Publications, presentations |
| `model/gltf+json` | 3D organ/tissue models (GLTF format) |
| `application/octet-stream` | Binary 3D models (GLB format) |
| `application/json` | HRA datasets and API responses |
| `text/html` | Portal and app pages |

Drop: `text/javascript`, `text/css`, `image/*`, `font/*`, `application/wasm`

**Layer 2 — Filter by file extension from `cs_uri_stem`** (keep these):
`.pdf`, `.glb`, `.gltf`, `.json`, `.csv`, `.html`

Drop: `.js`, `.css`, `.png`, `.jpg`, `.svg`, `.woff`, `.woff2`, `.map`

**Layer 3 — Filter by path prefix** (keep these):
`/docs/`, `/v1/`, `/api/`, `/ccf-api/`, `/assets/`

Drop paths starting with: `/static/`, `/_next/`, `/chunks/`, `/fonts/`

> Applying all three layers together gives a clean, noise-free file list. In practice, Layer 1 alone removes ~80% of CDN noise. The CNS logs are already clean — every meaningful row is a page or document request with no CDN assets mixed in, so file names can be extracted directly from `cs_uri_stem` without additional filtering.

**Three sub-visuals for country vs. file analysis:**
1. **Top downloaded file per country** — for each of the top 20 countries, the single most-requested file name (useful for spotting which publication or 3D model drives interest in each region)
2. **Content type per country** — stacked bar: PDF vs. 3D model vs. dataset vs. HTML page, top 15 countries
3. **Top 3D model downloads by country** — specifically for `.glb`/`.gltf` files (organ models) — which countries are downloading 3D tissue data most? This is unique to the HRA dataset and would be a strong visual for the client presentation.

**Data source:** CNS logs (all meaningful rows) + HRA logs filtered to meaningful files as above, `c_country` column
**Filter:** Human traffic only

**Client question to ask:** "Is there a specific country or region you're trying to grow adoption in? And are there any countries where usage surprised you?"

---

### MISC-2 — Cache Hit/Miss Distribution ⭐⭐⭐⭐
*(Your idea #5)*

**Why high impact:** Directly actionable for the infrastructure team. Shows which content is being served efficiently vs. always fetching from origin.

**Visualizations:**
- **Stacked bar chart** — `x_edge_result_type` (Hit / Miss / Error) distribution by content type (`sc_content_type`) — e.g., are PDFs always a Miss while HTML is always a Hit?
- **Pie chart** — overall cache hit rate (Hit vs. Miss vs. Error) as a single summary

> **Scope:** Meaningful for HRA Portal, CDN, and Apps rows. Not meaningful for Events rows (tiny tracking requests, always a Miss by design). CNS logs also included.

**Data source:** HRA logs (`site` in Portal, CDN, Apps) + CNS logs
**Filter:** Human traffic only; exclude `site == 'Events'` and `site == 'API'`

**Client question to ask:** "Does the team control CloudFront cache policies, or is that managed by IU central IT? This determines whether these findings are actionable by your team."

---

### MISC-3 — Response Time by App / Content ⭐⭐⭐
*(Your ideas #2 and #3 combined)*

**Why medium-high impact:** Performance directly affects user experience. Slow-loading tools lose users before they even start.

**Visualizations:**
- **Box plot** — `time_taken` distribution per HRA app (inferred from `cs_uri_stem` path prefix: `/ccf-rui/`, `/ccf-eui/`, `/cde/`)
- **Bar chart** — median response time per content type (`sc_content_type`): HTML, PDF, JavaScript, WebAssembly, etc.

> **Assumption:** App identity is inferred from the URL path prefix (e.g., `/ccf-eui/` → EUI, `/ccf-rui/` → RUI, `/cde/` → CDE). This is an accepted approximation. Flag it with the client in case they have a cleaner mapping.
> **Scope:** CNS logs and HRA Portal/Apps/CDN rows. Events rows excluded (those are tiny `/tr` requests, not meaningful for performance).

**Data source:** CNS logs + HRA logs (`site` in Portal, CDN, Apps)
**Filter:** Human traffic only; remove outliers (time_taken > 99th percentile) before plotting

**Client question to ask:** "Are there known performance issues with any specific tool? The box plots may confirm or contradict what the team has observed anecdotally."

---

### MISC-4 — File Size vs. Load Time ⭐⭐⭐
*(Your idea #4)*

**Why medium impact:** Shows whether large files are the bottleneck or whether small files are also slow (which would point to a different problem).

**Visualizations:**
- **Scatter plot** — `sc_content_len` (file size) vs. `time_taken` (load time), colored by `sc_content_type`; one dot per request (sampled if needed for performance)
- **Trend line** — linear regression overlay to show whether size and time are correlated

> **Scope:** CNS logs are best for this — they have a wide range of file sizes (small HTML pages to large PDFs). HRA CDN rows also work.

**Data source:** CNS logs (primary), HRA CDN rows
**Filter:** Human traffic only; filter out rows where `sc_content_len` is null or 0

**Client question to ask:** "Are there specific large files (3D models, datasets) where slow load times have been reported by users?"

---

### MISC-5 — Airport (Edge Location) vs. Response Time ⭐⭐
*(Your idea #7)*

**Why lower impact:** Infrastructure-level detail that is more relevant to a DevOps team than a product or UX discussion. Still interesting to show geographic CDN performance differences.

**Visualizations:**
- **Box plot** — `time_taken` per `airport` code, for the top 10 busiest edge locations
- **Map overlay (optional)** — airport locations plotted on a world map, sized by request volume, colored by median response time

> **Scope:** Meaningful only for Portal and CDN rows where actual content is being served. CNS logs also included.

**Data source:** CNS logs + HRA logs (`site` in Portal, CDN)
**Filter:** Human traffic only; top 10 airports by request volume

**Client question to ask:** "Has the team received complaints about slow load times from users in specific regions? That would tell us which airports to investigate first."

---

## Summary: Impact Ranking

| Rank | Visualization | Maps To | Why |
|---|---|---|---|
| 1 | Event frequency distribution + monthly trends | Q1 | Core client question; shows growth |
| 2 | Most/least used UI elements + hover vs. click | Q2 | Directly actionable for design team |
| 3 | EUI Spatial Search funnel | Q4 | 40% drop-off is a clear finding |
| 4 | Geographic reach map + country downloads | MISC-1 | High visual impact; global story |
| 5 | RUI opacity usage breakdown | Q3 | Specific finding; discoverability story |
| 6 | CDE workflow funnel + tracking gap callout | Q5 | Tracking gap is important to surface |
| 7 | Cache hit/miss by content type | MISC-2 | Actionable for infrastructure team |
| 8 | Response time by app and content type | MISC-3 | Performance baseline |
| 9 | File size vs. load time scatter | MISC-4 | Supporting detail for performance |
| 10 | Airport vs. response time | MISC-5 | Niche; lower audience relevance |

---

## Open Questions for Client Meeting

| # | Question | Relevant To |
|---|---|---|
| 1 | Is the ~25% error event rate a known issue? | Q1 |
| 2 | Are there specific UI elements you want investigated? | Q2 |
| 3 | Was the opacity feature recently added or changed? | Q3 |
| 4 | Is the EUI organ selection step newly added? | Q4 |
| 5 | Was CDE download tracking intentionally omitted? | Q5 |
| 6 | Which countries/regions are growth targets? | MISC-1 |
| 7 | Does the team control CloudFront cache policies? | MISC-2 |
| 8 | Are there known slow-loading tools or regions? | MISC-3/5 |
