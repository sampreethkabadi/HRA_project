# HRA Project — Data Exploration Report

## Datasets

| File | Rows | Columns | Date Range | Scope |
|---|---|---|---|---|
| `Data/2026-033-23_cns-logs.parquet` | 16,333,922 | 40 | 2008-04-13 → 2026-03-23 | cns.iu.edu (CNS Center website) |
| `Data/2026-01-13_hra-logs.parquet` | 12,779,123 | 40 | 2023-06-05 → 2026-01-12 | humanatlas.io and related HRA domains |

Both files share the same 40-column schema (minor column name casing differences).

---

## Column Reference (shared schema)

| Column | Type | Description |
|---|---|---|
| `anon_id` | string | Anonymized user identifier |
| `date` | string | Date of request (YYYY-MM-DD) |
| `time` | string | Time of request (HH:MM:SS) |
| `timestamp` | int | Unix timestamp (seconds) |
| `timestamp_ms` | int | Unix timestamp (milliseconds) |
| `year`, `month`, `day` | string/int | Extracted date components |
| `cs_uri_stem` | string | URL path requested |
| `cs_uri_query` | string | Raw query string |
| `query` | list | Parsed query params as list of (key, value) tuples |
| `cs_method` | string | HTTP method (GET / POST) |
| `sc_status` | int | HTTP response code (200, 404, etc.) |
| `cs_user_agent` | string | Browser or client identifier |
| `traffic_type` | string | `Likely Human` / `Bot` / `AI-Assistant / Bot` |
| `c_country` | string | ISO country code of the visitor |
| `referrer` | string | Cleaned referring domain |
| `cs_referer` | string | Full original Referer header |
| `sc_bytes` | int/float | Response size in bytes |
| `cs_bytes` | int/float | Request size in bytes |
| `time_taken` | float | Total request time (seconds) |
| `time_to_first_byte` | float | Time to first byte (seconds) |
| `x_edge_location` | string | CloudFront edge location code |
| `airport` | string | Airport code for edge location |
| `x_host_header` | string | Host header sent by client |
| `x_edge_result_type` | string | CloudFront cache result (Hit/Miss/Error) |
| `x_edge_response_result_type` | string | Edge response type |
| `x_edge_detailed_result_type` | string | Detailed edge result |
| `x_edge_request_id` | string | Unique CloudFront request identifier |
| `sc_content_type` | string | MIME type of response |
| `sc_content_len` | float | Content-Length of response |
| `sc_range_start` / `sc_range_end` | float | Byte-range request bounds |
| `cs_protocol` | string | Protocol (HTTP/HTTPS) |
| `cs_protocol_version` | string | HTTP version (e.g. HTTP/2.0) |
| `ssl_protocol` | string | TLS/SSL version used |
| `ssl_cipher` | string | Cipher suite |
| `cs_cookie` | string | Cookie header |
| `distribution` | string | CloudFront distribution name |
| `site` | string | Logical site label |

---

## Column Explanations with Examples

### Identity & Time

| Column | What it means | Example |
|---|---|---|
| `anon_id` | A scrambled ID to track a user without storing their real identity | `"a3f9c2..."` |
| `date` | The date of the request | `"2025-01-05"` |
| `time` | The time of the request | `"14:32:07"` |
| `timestamp` | Same moment, expressed as seconds since Jan 1, 1970 (standard machine format) | `1736087527` |
| `timestamp_ms` | Same but in milliseconds — more precise | `1736087527413` |
| `year`, `month`, `day` | The date broken into separate pieces for easier filtering | `2025`, `1`, `5` |

### What Was Requested

| Column | What it means | Example |
|---|---|---|
| `cs_uri_stem` | The page or file path the user asked for | `"/docs/publications/paper.pdf"` |
| `cs_uri_query` | Extra parameters tacked onto the URL | `"?page=2&lang=en"` |
| `query` | Same query string, but parsed into key-value pairs | `[("page","2"), ("lang","en")]` |
| `cs_method` | Whether the browser was fetching data (GET) or submitting something (POST) | `"GET"` |
| `sc_status` | The server's response code — 200 means success, 404 means not found | `200` |
| `cs_protocol` | HTTP or HTTPS (secure vs. not) | `"HTTPS"` |
| `cs_protocol_version` | The version of the HTTP protocol used | `"HTTP/2.0"` |

### Who Visited

| Column | What it means | Example |
|---|---|---|
| `cs_user_agent` | Identifies the browser or bot that made the request | `"Mozilla/5.0 (Chrome/131)"` |
| `traffic_type` | A label classifying the visitor as human, bot, or AI crawler | `"Likely Human"` |
| `c_country` | Where the visitor is from, as a 2-letter country code | `"US"`, `"DE"`, `"IN"` |
| `referrer` | The cleaned domain they came from (what site linked them here) | `"google.com"` |
| `cs_referer` | The full, raw Referer header as the browser sent it | `"https://www.google.com/search?q=..."` |
| `cs_cookie` | Any cookie data sent with the request | `"session=abc123"` |

### Size & Speed

| Column | What it means | Example |
|---|---|---|
| `sc_bytes` | How many bytes the server sent back (response size) | `52400` (≈ 51 KB) |
| `cs_bytes` | How many bytes the user's browser sent (request size, usually small) | `512` |
| `time_taken` | Total time from request to response completing | `0.34` (seconds) |
| `time_to_first_byte` | How long until the server started sending data back | `0.12` (seconds) |
| `sc_content_type` | The type of file/data returned | `"application/pdf"`, `"text/html"` |
| `sc_content_len` | The declared size of the response content | `52400` |
| `sc_range_start` / `sc_range_end` | If only part of a file was requested (e.g. resuming a download), the byte range | `0` / `10240` |

### CloudFront / Server Infrastructure

These columns come from AWS CloudFront, the content delivery network (CDN) that serves the website from servers around the world.

| Column | What it means | Example |
|---|---|---|
| `x_edge_location` | Code for the CloudFront server that handled the request | `"ORD52-C1"` |
| `airport` | Human-readable airport code for that edge location | `"ORD"` (Chicago O'Hare) |
| `x_host_header` | The domain the browser thought it was talking to | `"humanatlas.io"` |
| `x_edge_result_type` | Whether the file was served from cache or fetched fresh | `"Hit"`, `"Miss"`, `"Error"` |
| `x_edge_response_result_type` | Similar — the edge's response classification | `"Hit"` |
| `x_edge_detailed_result_type` | More specific version of the above | `"OriginShieldHit"` |
| `x_edge_request_id` | A unique ID for this specific request (useful for debugging) | `"abc123XYZ..."` |
| `ssl_protocol` | The encryption standard used for HTTPS | `"TLSv1.3"` |
| `ssl_cipher` | The specific encryption algorithm negotiated | `"ECDHE-RSA-AES128-GCM-SHA256"` |
| `distribution` | Which CloudFront distribution served the file | `"hra"`, `"cns"` |
| `site` | A human-readable label for the website | `"HRA"`, `"CNS"` |

### Example Row (putting it all together)

> On Jan 5, 2025 at 2:32 PM, a visitor from Germany (`c_country = "DE"`) came from Google (`referrer = "google.com"`) and downloaded a PDF (`cs_uri_stem = "/docs/publications/paper.pdf"`, `sc_content_type = "application/pdf"`). They were classified as a human (`traffic_type = "Likely Human"`), the file was 51 KB (`sc_bytes = 52400`), and the server responded in 0.34 seconds (`time_taken = 0.34`). The request was served from the Chicago CloudFront node (`airport = "ORD"`) with a cache hit (`x_edge_result_type = "Hit"`).

---

## File 1: `2026-033-23_cns-logs.parquet` — CNS Website Logs

### Traffic Composition

| Traffic Type | Rows | % |
|---|---|---|
| Likely Human | 12,635,272 | 77.4% |
| Bot | 3,376,322 | 20.7% |
| AI-Assistant / Bot | 322,328 | 2.0% |
| **Total** | **16,333,922** | |

- Single site/distribution: all rows tagged `site=CNS`, `distribution=cns`
- Covers `cns.iu.edu` — the CNS Center's main academic website
- Does **not** contain HRA UI event tracking data

### What Can Be Analyzed

- Long-term traffic trends (2008–2026) for the CNS website
- HRA-related publication and presentation download counts (PDFs served from `/docs/publications/` and `/docs/presentations/`)
- Geographic distribution of visitors via `c_country`
- Bot vs. human traffic trends over time
- Referral sources (Google, Bing, humanatlas.io, etc.)

### Top HRA-Related Publication Downloads

| Publication | Downloads |
|---|---|
| `2021-Borner_Tissue-Registration-and-EUIs.pdf` | 1,993 |
| `2021-Borner-ASCT+B_of_the_HRA.pdf` | 1,675 |
| `2021-Bueckle-3D_VR_vs_2D_Desktop_RUI.pdf` | 1,422 |
| `2022-Borner_Tissue-Registration-and-EUIs.pdf` | 1,392 |
| `2023-Bueckle_HRA-Organ-Gallery.pdf` | 926 |

---

## File 2: `2026-01-13_hra-logs.parquet` — HRA Portal Logs

### Traffic Composition

| Traffic Type | Rows | % |
|---|---|---|
| Likely Human | 9,866,210 | 77.2% |
| Bot | 2,562,640 | 20.1% |
| AI-Assistant / Bot | 350,273 | 2.7% |
| **Total** | **12,779,123** | |

### Sites and Distributions

| `site` label | Rows | `distribution` / `x_host_header` | Description |
|---|---|---|---|
| KG | 3,443,647 | `lod.humanatlas.io` | Knowledge Graph / Linked Open Data |
| Portal | 3,362,959 | `humanatlas.io` | Main HRA Portal |
| CDN | 3,324,994 | `cdn.humanatlas.io` | Static assets (JS, CSS, images) |
| API | 1,705,448 | `lod.humanatlas.io` | HRA API endpoints |
| Apps | 827,191 | `apps.humanatlas.io` | HRA Applications hub |
| **Events** | **114,884** | — | **UI event tracking (key for analysis)** |

### The Events Tracking System

All user interaction events are captured via GET requests to `/tr` (production) and `/tr-dev` (staging). Each request encodes a structured event as query parameters:

| Parameter | Meaning |
|---|---|
| `sessionId` | Unique session identifier |
| `app` | Which HRA application fired the event |
| `version` | App version |
| `event` | Event type (click, hover, pageView, keyboard, modelChange, error) |
| `e.path` | Dot-notation path of the UI element that triggered the event |
| `e.trigger` | Interaction type (click, hover, etc.) |
| `e.value` | Current value (for modelChange events) |
| `e.url`, `e.title`, `e.path` | Page context (for pageView events) |

### Event Type Distribution (Events site only, 114,884 rows)

| Event Type | Count |
|---|---|
| click | 38,961 |
| error | 29,222 |
| hover | 23,162 |
| pageView | 14,474 |
| keyboard | 5,807 |
| modelChange | 3,167 |

### Applications Tracked

| App | Event Count |
|---|---|
| kg-explorer | 22,243 |
| humanatlas.io | 19,880 |
| ccf-eui | 11,068 |
| ccf-rui | 9,430 |
| apps.humanatlas.io | 5,034 |
| cns-website | 4,561 |
| cde-ui | 4,297 |
| asct+b-reporter | 3,494 |
| ftu-ui | 2,664 |
| ccf-organ-info | 1,890 |
| docs.humanatlas.io | 1,343 |
| dashboard-ui | 550 |

---

## Client Questions — Answers from HRA Logs

> **Note on event path keys:** Events fired by newer app versions store the UI path under the key `path`; older events use `e.path`. Both must be checked together to get accurate counts. All numbers below use the unified lookup.

### Q1: Distribution of frequency of user events? ✅ Answerable

The Events table has **114,884 rows** of structured interactions across all HRA UIs.

| Event Type | Count | % |
|---|---|---|
| click | 38,961 | 33.9% |
| error | 29,222 | 25.4% |
| hover | 23,162 | 20.2% |
| pageView | 14,474 | 12.6% |
| keyboard | 5,807 | 5.1% |
| modelChange | 3,167 | 2.8% |

Notable: error events are the second most common type (25%), suggesting UX or stability issues worth investigating.

### Q2: Which UI elements were used frequently and not frequently? ✅ Answerable

Tracked via the `path` / `e.path` field on click events (38,961 total). Top 20 most-clicked elements across all apps:

| UI Path | Clicks |
|---|---|
| `rui.stage-content.3d` | 1,455 |
| `humanatlas.navigation-category-expansion` | 1,223 |
| `humanatlas.header.navigation.data` | 1,076 |
| `kg-explorer.main-page.digital-objects.table.link-cell` | 798 |
| `eui.right-panel.results.select` | 775 |
| `humanatlas.header.navigation.applications` | 642 |
| `humanatlas.table.link-cell` | 629 |
| `eui.right-panel.results.donor.card` | 564 |
| `rui.stage-content.register` | 548 |
| `humanatlas.navigation-category-expansion.navigation-item-internal` | 530 |
| `header.navigation.research` | 428 |
| `eui.body-ui-controls.organ-select.organ-search` | 427 |
| `kg-explorer.main-page.digital-objects.table.menu-cell.download` | 383 |
| `humanatlas.header.navigation.menu-toggle` | 369 |
| `kg-explorer.metadata-page...3d-model-viewer` | 366 |
| `eui.body-ui.scene` | 364 |
| `eui.left-panel.open-filters` | 336 |
| `humanatlas.landing-page.carousel.controls.next-slide` | 331 |
| `asctb-reporter.visualization` | 329 |
| `kg-explorer.main-page.digital-objects.search` | 317 |

Under-used elements can be identified by paths with single-digit counts across the full event log.

### Q3: How often was opacity changed in the RUI? ✅ Answerable

**206 opacity toggle events recorded** across 50+ distinct anatomical structures:

| UI Path | Count |
|---|---|
| `rui.left-sidebar.AS-visibility.all-anatomical-structures.opacity-toggle` | 50 |
| `rui.left-sidebar.landmarks-visibility.bisection-line.opacity-toggle` | 35 |
| `rui.left-sidebar.AS-visibility.tongue.opacity-toggle` | 17 |
| `rui.left-sidebar.opacity-settings.toggle` | 4 |
| *(40+ individual structure opacity toggles)* | 1–8 each |

Out of **9,430 total RUI events**, only 206 (~2.2%) involve opacity — still relatively low, but spread across many anatomical structures. The bisection-line and all-structures toggles are the most used. The master opacity panel toggle itself (`opacity-settings.toggle`) was used only 4 times, suggesting most users toggle individual structures rather than the global control.

### Q4: How often was spatial search used in the EUI? ✅ Answerable

**3,071 spatial search events recorded** — clearly an actively-used feature.

| UI Path | Count |
|---|---|
| `eui.body-ui.spatial-search.scene` | 509 |
| `eui.body-ui.spatial-search.results.anatomical-structures` | 352 |
| `eui.body-ui.spatial-search.results.tissue-blocks` | 335 |
| `eui.body-ui.spatial-search-button` | 227 (entry point click) |
| `eui.body-ui.spatial-search.keyboard.d` | 212 |
| `eui.body-ui.spatial-search-config.organ-sex-selection.organ.search` | 168 |
| `eui.body-ui.spatial-search.results.cell-types` | 166 |
| `eui.body-ui.spatial-search-config.continue` | 136 |

Users engage deeply: they use keyboard navigation (q/w/e/a/s/d), adjust the radius slider, hover over results, and explore all three result panels (anatomical structures, tissue blocks, cell types). Brain is the most selected organ for spatial search.

### Q5: How often were CDE histograms and violin plots downloaded? ⚠️ Partially Answerable

**No specific histogram or violin plot download events are tracked in the CDE.** The CDE has 4,297 total events:

| CDE Path | Clicks |
|---|---|
| `cde-ui.create-visualization-page.upload-data.file-upload.upload` | 163 |
| `cde-ui.create-visualization-page.visualize-data.submit` | 132 |
| `cde-ui.create-visualization-page.organize-data.cell-type-selector` | 96 |
| `cde-ui.landing-page.create-and-explore.visual-cards.create-a-visualization` | 94 |

165 users reached the `/cde/visualize` output page (where histograms/violin plots appear), and 132 actually submitted a visualization. However, no `download` actions on the output plots were instrumented. This is a **tracking gap** — download events for CDE plots were either never added or are not being fired.

---

## Recommended Analysis Plan

1. **Filter to `traffic_type == 'Likely Human'`** for all analyses to exclude bots.
2. **Use unified path lookup** (`path` OR `e.path` key) when extracting UI element paths from the `query` column.
3. **Error events** (25% of all events, dominated by `ccf-eui`) deserve a dedicated investigation — what errors are users hitting and in which app versions?
4. **RUI session funnels**: trace `sessionId` through open → place tissue block (`rui.stage-content.3d`) → register (`rui.stage-content.register`) to measure completion rates.
5. **CDE tracking gap**: recommend the team add download tracking for histogram and violin plot exports in a future CDE release.
6. **Proposed additional research questions:**
   - Which organs are most selected in EUI spatial search? (parse `organ-sex-selection.organ.*` paths)
   - What is the RUI registration completion rate per session?
   - How do error rates differ across app versions (`version` field)?
   - Which countries generate the most HRA Portal traffic (`c_country` on Portal rows)?
   - What share of humanatlas.io traffic comes from AI assistants, and is it growing year-over-year?
