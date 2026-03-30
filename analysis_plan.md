# HRA Project — Analysis Plan

---

## What Are We Even Looking At?

Before diving into the plan, let's break down what this data actually is and why it exists.

### The Big Picture

Indiana University's CNS Center built a set of web tools called the **Human Reference Atlas (HRA)**. Think of the HRA as Google Maps — but instead of mapping cities, it maps the human body all the way down to individual cell types. Researchers use it to register tissue samples, explore organs in 3D, and analyze cell neighborhoods.

These tools live on the internet at **humanatlas.io**. Every time someone visits a webpage or clicks a button on the internet, that action leaves a digital footprint. Amazon CloudFront is the service that sits between users and the website — it's like the front desk of a hotel that logs every guest who comes in and what they asked for.

CNS configured CloudFront to capture two kinds of logs:
1. **Standard server logs** — every file requested (images, pages, PDFs)
2. **Custom event logs** — specific user actions like "clicked this button" or "searched for this organ"

We have both kinds.

---

## The Two Datasets

### Dataset 1: CNS Website Logs (`2026-033-23_cns-logs.parquet`)

**What it is:** A record of every request made to **cns.iu.edu** — the CNS Center's main academic website — from 2008 to March 2026. Think of it as a guest book for the website: every visit, every file download, every page load got an entry.

**Size:** ~16.3 million rows

**What each row means:** One HTTP request. If you open a webpage that loads 20 images, that's 21 rows (1 for the page + 20 for the images).

**Key things it tells us:**
- Which pages and files people downloaded (PDFs, presentations, etc.)
- Where visitors came from geographically
- Whether the visitor was a real human or a bot
- What website sent them here (referrer)
- When traffic peaked over 18 years

**What it does NOT tell us:** Anything about button clicks inside the HRA tools (RUI, EUI, CDE). This is just the CNS homepage, not the HRA app.

**Key columns to know:**

| Column | Plain English |
|---|---|
| `anon_id` | A scrambled ID for each unique visitor — like a loyalty card number, but anonymous |
| `date`, `time` | When the request happened |
| `cs_uri_stem` | The URL path they asked for, e.g. `/publications.html` or `/docs/publications/paper.pdf` |
| `traffic_type` | Was this a real person (`Likely Human`), a crawler (`Bot`), or an AI assistant? |
| `c_country` | What country the visitor was in |
| `sc_bytes` | How many bytes were sent back — big number = large file download |
| `referrer` | What website sent them here (e.g. `google.com`, `humanatlas.io`) |

---

### Dataset 2: HRA Portal Logs (`2026-01-13_hra-logs.parquet`)

**What it is:** A record of every request and user interaction across the entire HRA ecosystem — the portal, the tools, the APIs — from June 2023 to January 2026.

**Size:** ~12.8 million rows

**This dataset is split into different "sites":**

| Site | What it is | Rows |
|---|---|---|
| `KG` | Knowledge Graph — linked data browser for HRA digital objects | 3.4M |
| `Portal` | The main HRA homepage at humanatlas.io | 3.4M |
| `CDN` | Content Delivery Network — static files (JavaScript, CSS, images) | 3.3M |
| `API` | Backend API calls from apps | 1.7M |
| `Apps` | The HRA Applications hub at apps.humanatlas.io | 0.8M |
| **`Events`** | **Custom user interaction events — the gold mine for this project** | **114,884** |

The `Events` site is the most important for answering the client's questions. It's a tiny fraction of total traffic but contains all the detailed user behavior data.

**How the Events system works:**

Every time a user does something meaningful in an HRA app (clicks a button, hovers over an organ, changes a setting), the app fires a small tracking request to the `/tr` endpoint. That request encodes what happened as URL query parameters. For example:

```
/tr?sessionId=abc123&app=ccf-rui&event=click&path=rui.stage-content.register
```

This translates to: *"User in session abc123, using the RUI app, clicked the Register button."*

**Key columns for the Events data:**

| Column | Plain English |
|---|---|
| `query` | A list of key-value pairs encoding the event. This is where all the action is. |
| `sessionId` (inside query) | Groups all actions from one user session together |
| `app` (inside query) | Which HRA tool fired the event (ccf-rui, ccf-eui, cde-ui, etc.) |
| `event` (inside query) | What type of thing happened: `click`, `hover`, `pageView`, `keyboard`, `modelChange`, `error` |
| `path` or `e.path` (inside query) | Dot-notation name of the exact UI element. E.g. `rui.left-sidebar.opacity-settings.toggle` |
| `e.value` (inside query) | What value was set (for modelChange events) |
| `e.url`, `e.title` (inside query) | Page context (for pageView events) |

> **Important technical note:** Older events store the UI path under the key `e.path`. Newer events (version `sv=0`) store it under `path`. Both keys must be checked when extracting the UI element name. Missing this causes severe undercounting.

---

## The 5 Client Questions — Analysis Plan

---

### Question 1: What is the distribution of frequency of user events?

**Plain English:** How often does each type of user action happen? Are users mostly clicking, or hovering, or hitting errors? And how is activity spread — do a few users do everything, or is usage spread across many people?

---

#### Plan for HRA Logs (primary answer)

**Data source:** `Events` site rows only (`site == 'Events'`)

**Steps:**
1. Extract the `event` key from the `query` column for every row
2. Count occurrences of each event type (`click`, `hover`, `pageView`, `keyboard`, `modelChange`, `error`)
3. Visualize as a bar chart or pie chart showing the percentage breakdown
4. Break this down further by `app` — does the RUI have a different event mix than the EUI?
5. Plot event volume over time (by month) to show whether usage is growing

**Expected output:**
- Bar chart: event type distribution (overall and per app)
- Line chart: total events per month from 2023 to 2026
- Table: event counts by app × event type

**Filter to apply:** Exclude `traffic_type == 'Bot'` and `traffic_type == 'AI-Assistant / Bot'` rows

---

#### Plan for CNS Logs (complementary answer)

The CNS logs don't have UI events — every row is just a file/page request. So "event frequency" here means request frequency.

**Data source:** Full file, filtered to `traffic_type == 'Likely Human'`

**Steps:**
1. Count total requests per day/month/year
2. Count unique visitors per month using `anon_id`
3. Plot request volume over time (2008–2026)
4. Show the share of human vs. bot traffic over time

**Expected output:**
- Line chart: monthly request volume (human traffic) 2008–2026
- Stacked bar: human vs. bot vs. AI-bot share per year

---

### Question 2: Which UI elements were used frequently and not frequently?

**Plain English:** Which buttons and features do users actually click? Are there things that were built but nobody ever touches?

---

#### Plan for HRA Logs (primary answer)

**Data source:** `Events` site, `event == 'click'` rows

**Steps:**
1. Extract `path` key (checking both `path` and `e.path` in the query list) for every click event
2. Count clicks per path
3. Split path by the first segment to group by app (`rui.*`, `eui.*`, `cde-ui.*`, etc.)
4. Within each app, rank elements from most to least clicked
5. Flag elements with fewer than 5 total clicks as "under-used"
6. Repeat for `hover` events to see what users notice but don't always click

**Expected output:**
- Horizontal bar charts: top 20 most clicked elements per app (RUI, EUI, CDE, Portal)
- Table: "under-used" elements (< 5 clicks across all sessions)
- Heatmap: app × UI section → click density

---

#### Plan for CNS Logs (complementary answer)

Here "UI elements" = pages and resources on the CNS website.

**Data source:** Full file, `traffic_type == 'Likely Human'`

**Steps:**
1. Count requests per `cs_uri_stem`
2. Group by content type: HTML pages, PDF publications, PDF presentations, images
3. Rank by popularity within each group
4. Identify pages with very low traffic (under-visited content)

**Expected output:**
- Bar chart: top 20 most-visited pages on cns.iu.edu
- Bar chart: top 20 most-downloaded publications and presentations
- List of pages with near-zero traffic

---

### Question 3: How often was opacity changed in the RUI?

**Plain English:** The RUI (Registration User Interface) lets users toggle the transparency of organs and anatomical structures so they can see inside the 3D body model. Did users actually use this feature?

---

#### Plan for HRA Logs (primary answer)

**Data source:** `Events` site, `app == 'ccf-rui'` rows

**Steps:**
1. Extract the `path` key from every RUI event (using unified `path` OR `e.path` lookup)
2. Filter to paths containing `opacity`
3. Count total opacity events and break down by:
   - `opacity-settings.toggle` — the master opacity panel toggle
   - `AS-visibility.*.opacity-toggle` — per-structure toggles (each one names an anatomical structure)
   - `landmarks-visibility.*.opacity-toggle` — landmark toggles
4. Calculate opacity events as a percentage of all RUI events (9,430 total)
5. List which anatomical structures had their opacity changed most frequently

**Expected output:**
- Single number: total opacity events (206), as % of all RUI events (2.2%)
- Bar chart: top anatomical structures whose opacity was toggled
- Interpretation: is this feature well-used, underused, or niche?

---

#### Plan for CNS Logs (not directly applicable)

The CNS logs don't contain RUI interaction data. However, we can look at downloads of the RUI paper as a proxy for interest in the RUI:

- Count downloads of `/docs/publications/2021-Bueckle-3D_VR_vs_2D_Desktop_RUI.pdf` (1,422 downloads)
- Compare to downloads of other HRA tool papers

---

### Question 4: How often was spatial search used in the EUI?

**Plain English:** The EUI (Exploration User Interface) has a feature called Spatial Search — users can drop a 3D sphere into a body organ and find all registered tissue samples that overlap with it. Did people actually use this? How far did they get through the workflow?

---

#### Plan for HRA Logs (primary answer)

**Data source:** `Events` site, `app == 'ccf-eui'` rows

**Steps:**
1. Extract `path` from all EUI events
2. Filter to paths containing `spatial-search`
3. Map out the spatial search workflow as a funnel:
   - Step 1: Click `eui.body-ui.spatial-search-button` (entry point — 227 clicks)
   - Step 2: Configure organ — `eui.body-ui.spatial-search-config.organ-sex-selection.organ.*`
   - Step 3: Click `eui.body-ui.spatial-search-config.continue` (136 clicks)
   - Step 4: Interact with results — `eui.body-ui.spatial-search.results.*`
   - Step 5: Apply or reset — `eui.body-ui.spatial-search.buttons.apply` / `.reset-all`
4. Count users who completed each step to build a drop-off funnel
5. Identify which organs were most selected in the config step
6. Note keyboard usage (q/w/e/a/s/d keys) as an indicator of power users

**Expected output:**
- Funnel chart: entry → configure → continue → results → apply (drop-off at each step)
- Bar chart: which organs were most selected for spatial search
- Total: 3,071 spatial search events across 227+ initiated searches

---

#### Plan for CNS Logs (complementary)

Count downloads of the EUI paper as interest proxy:
- `/docs/publications/2021-Borner_Tissue-Registration-and-EUIs.pdf` (1,993 downloads)
- `/docs/publications/2022-Borner_Tissue-Registration-and-EUIs.pdf` (1,392 downloads)

---

### Question 5: How often were histograms and violin plots in the CDE downloaded?

**Plain English:** The CDE (Cell Distance Explorer) generates charts — histograms and violin plots — showing how different cell types are distributed in space. After generating these charts, users can download them. How often did that happen?

---

#### Plan for HRA Logs (primary answer — with caveat)

**Data source:** `Events` site, `app == 'cde-ui'` rows

**Steps:**
1. Map the CDE workflow using pageView events and click events:
   - Landing: `/cde/` (259 pageViews)
   - Create page: `/cde/create` (222 pageViews)
   - Visualize page: `/cde/visualize` (165 pageViews) ← output with charts
   - Submit button: `cde-ui.create-visualization-page.visualize-data.submit` (132 clicks)
2. Check for any download-related click paths in CDE events
3. **Finding:** No download events for histograms or violin plots are present in the tracking data

**Caveat:** Download tracking for CDE output plots was **not instrumented**. We can say 132 users generated a visualization and 165 reached the output page, but we cannot say how many downloaded the charts. This is a gap to flag to the development team.

**Expected output:**
- Funnel: landing → create page → submit → visualize page (showing drop-off)
- Clear statement: histogram/violin download events are not currently tracked
- Recommendation: add `cde-ui.visualize-page.histogram.download` and `cde-ui.visualize-page.violin-plot.download` event tracking

---

#### Plan for CNS Logs (not applicable)

No CDE data exists in the CNS logs.

---

## Overall Workflow Summary

```
For both datasets:
  1. Load the parquet file with pandas
  2. Filter out bots: traffic_type == 'Likely Human'

For CNS logs:
  3. Analyze cs_uri_stem for page/download frequency
  4. Group by date columns for time-series analysis
  5. Use c_country for geographic breakdown

For HRA logs — general traffic:
  3. Group by site to understand which part of the platform gets what traffic
  4. Use x_host_header or distribution for sub-site breakdowns

For HRA logs — Events only (site == 'Events'):
  3. Extract event fields from query column:
       event_type = first value where key == 'event'
       app        = first value where key == 'app'
       path       = first value where key == 'path' OR key == 'e.path'
  4. Filter by app and path to answer each specific question
  5. Group by sessionId to do session-level funnel analysis
```

---

## What We Can and Cannot Answer

| Question | HRA Logs | CNS Logs |
|---|---|---|
| Q1: Event frequency distribution | ✅ Full answer | ✅ Page-request proxy |
| Q2: Frequently/rarely used UI elements | ✅ Full answer | ✅ Page-level only |
| Q3: Opacity changes in RUI | ✅ Full answer (206 events) | ❌ Not available |
| Q4: Spatial search in EUI | ✅ Full answer (3,071 events) | ❌ Not available |
| Q5: CDE histogram/violin downloads | ⚠️ Tracking gap — not instrumented | ❌ Not available |

---

## Proposed Additional Research Questions

These go beyond the client's original list but are answerable from the data:

1. **RUI session completion rate** — Of all sessions that opened the RUI, what % completed a registration? (`rui.stage-content.register` vs. first RUI event per session)
2. **Error investigation** — Error events are 25% of all events. Which apps and versions generate the most errors? Are errors improving over time?
3. **AI bot growth** — The `AI-Assistant / Bot` traffic type is growing. What % of HRA portal traffic now comes from AI crawlers vs. 2023?
4. **Geographic reach** — Which countries use the HRA Portal most? Has the geographic distribution shifted since launch?
5. **Power users vs. casual users** — Using `sessionId`, how long do sessions last? Do most users just browse or do they complete full workflows?
6. **Feature discoverability** — Comparing hover counts to click counts for the same element reveals whether users notice but don't use a feature.
