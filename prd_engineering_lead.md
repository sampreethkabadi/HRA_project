# HRA Web Analytics — Engineering Specification
### Role: Senior Engineering Lead
### Deliverable: Static Analysis Dashboard (Course Project)
### Audience: Internal IU/CNS Team

---

## Overview

This document specifies the end-to-end technical implementation for answering five client questions (plus additional research questions) from two Apache Parquet log datasets. The deliverable is a **static dashboard** — a reproducible set of charts, tables, and findings produced by a Python analysis pipeline and presented as a structured report or notebook export.

The analysis must be correct, reproducible, and clearly documented for handoff to the CNS team. Every number that appears in the final output should be traceable back to a specific filter condition and transformation step defined in this document.

---

## Data Sources

| File | Rows | Columns | Key Use |
|---|---|---|---|
| `Data/2026-033-23_cns-logs.parquet` | 16,333,922 | 40 | Website traffic, PDF downloads, long-term trends |
| `Data/2026-01-13_hra-logs.parquet` | 12,779,123 | 40 | HRA tool events, user interactions, funnel analysis |

Both files share the same 40-column schema. Column names have minor casing differences between files — normalize on load.

---

## Architecture: Static Analysis Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                     Data Layer                          │
│  cns-logs.parquet          hra-logs.parquet             │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                 Preprocessing Module                    │
│  - Bot filter                                           │
│  - Query column parser                                  │
│  - Unified path extractor (path OR e.path)              │
│  - Date normalization                                    │
└────────────────┬────────────────────────────────────────┘
                 │
     ┌───────────┴──────────┐
     │                      │
┌────▼──────┐        ┌──────▼──────────────────────────┐
│ CNS       │        │ HRA Events Analysis              │
│ Analysis  │        │  Q1 · Q2 · Q3 · Q4 · Q5 · AQ1–5 │
└────┬──────┘        └──────┬──────────────────────────┘
     │                      │
┌────▼──────────────────────▼────────────────────────────┐
│                   Output Layer                         │
│  Charts (matplotlib/seaborn/plotly)                    │
│  Summary tables (pandas → HTML or CSV)                 │
│  Jupyter Notebook export / static HTML report          │
└────────────────────────────────────────────────────────┘
```

---

## Preprocessing: Do This Once, Reuse Everywhere

Before any question-specific logic runs, apply these transformations consistently. Putting them in shared utility functions prevents subtle discrepancies between analyses.

### 1. Load and Normalize

```python
import pandas as pd

cns = pd.read_parquet("Data/2026-033-23_cns-logs.parquet")
hra = pd.read_parquet("Data/2026-01-13_hra-logs.parquet")

# Normalize column names to lowercase
cns.columns = cns.columns.str.lower()
hra.columns = hra.columns.str.lower()
```

### 2. Bot Filter

Apply to both datasets before any analysis. Never mix bot and human rows in user behavior metrics.

```python
HUMAN = "Likely Human"

def filter_human(df):
    return df[df["traffic_type"] == HUMAN].copy()

cns_human = filter_human(cns)
hra_human = filter_human(hra)
```

### 3. Events Subset

All Q1–Q5 and additional question analysis uses only the Events site rows.

```python
events = hra_human[hra_human["site"] == "Events"].copy()
# Expected: ~114,884 rows after human filter
```

### 4. Query Column Parser

The `query` column contains a list of `(key, value)` tuples. Extract named fields from it efficiently.

```python
def extract_field(query_list, key):
    """Return the first value for a given key in the query list, or None."""
    if not isinstance(query_list, list):
        return None
    for k, v in query_list:
        if k == key:
            return v
    return None

events["event_type"] = events["query"].apply(lambda q: extract_field(q, "event"))
events["app"]        = events["query"].apply(lambda q: extract_field(q, "app"))
events["session_id"] = events["query"].apply(lambda q: extract_field(q, "sessionid"))
events["version"]    = events["query"].apply(lambda q: extract_field(q, "sv"))
```

### 5. Unified Path Extractor (Critical)

Older events use `e.path`. Newer events (version `sv=0`) use `path`. Both must be checked.
**Failing to do this causes severe undercounting. This is the most common error in this analysis.**

```python
def extract_path(query_list):
    """Check 'path' first, then fall back to 'e.path'."""
    if not isinstance(query_list, list):
        return None
    path_val = None
    epath_val = None
    for k, v in query_list:
        if k == "path":
            path_val = v
        elif k == "e.path":
            epath_val = v
    return path_val if path_val is not None else epath_val

events["path"] = events["query"].apply(extract_path)
```

### 6. Date Parsing

```python
events["date_parsed"] = pd.to_datetime(events["date"], errors="coerce")
events["year_month"]  = events["date_parsed"].dt.to_period("M")

cns_human["date_parsed"] = pd.to_datetime(cns_human["date"], errors="coerce")
cns_human["year_month"]  = cns_human["date_parsed"].dt.to_period("M")
```

---

## Q1 — Event Frequency Distribution

**Objective:** Count and visualize the distribution of event types overall, per app, and per month.

### HRA Events Analysis

```python
# --- Overall event type distribution ---
event_counts = events["event_type"].value_counts()
event_pct    = event_counts / len(events) * 100

# --- Per-app breakdown ---
app_event_crosstab = (
    events.groupby(["app", "event_type"])
    .size()
    .unstack(fill_value=0)
)

# --- Monthly event volume ---
monthly_events = (
    events.groupby("year_month")
    .size()
    .reset_index(name="event_count")
)

monthly_by_app = (
    events.groupby(["year_month", "app"])
    .size()
    .unstack(fill_value=0)
)
```

**Output Specs:**

| Chart | Type | X-axis | Y-axis | Notes |
|---|---|---|---|---|
| Overall event type distribution | Horizontal bar | Event type | Count + % label | Sort descending |
| Per-app event mix | Grouped or stacked bar | App | Count per event type | One bar group per app |
| Monthly event volume | Line chart | Month (2023–2026) | Event count | One line per app |

**Validation check:** `event_counts.sum()` must equal `len(events)`. If not, some rows have null event_type — investigate before presenting.

### CNS Website Analysis (Parallel)

```python
# Monthly request volume (human traffic only)
cns_monthly = (
    cns_human.groupby("year_month")
    .size()
    .reset_index(name="request_count")
)

# Human vs. bot share per year
traffic_by_year = (
    cns.groupby(["year", "traffic_type"])
    .size()
    .unstack(fill_value=0)
)
traffic_by_year_pct = traffic_by_year.div(traffic_by_year.sum(axis=1), axis=0) * 100
```

**Output Specs:**

| Chart | Type | Notes |
|---|---|---|
| Monthly CNS requests 2008–2026 | Line chart | Human traffic only |
| Human vs. bot share per year | Stacked bar (%) | Show AI-bot as separate category |

**Known edge case:** The `year` column may be string type in one file and int in the other — cast to int before grouping.

---

## Q2 — Most and Least Used UI Elements

**Objective:** Rank every UI element by click count within each app. Flag under-used elements. Compare hover vs. click.

### Click Ranking

```python
clicks  = events[events["event_type"] == "click"].copy()
hovers  = events[events["event_type"] == "hover"].copy()

# Extract app prefix from path for grouping
clicks["app_from_path"] = clicks["path"].str.split(".").str[0]

# Per-app click ranking
for app_name in ["rui", "eui", "cde-ui", "humanatlas"]:
    app_clicks = clicks[clicks["path"].str.startswith(app_name, na=False)]
    ranked = app_clicks["path"].value_counts().reset_index()
    ranked.columns = ["ui_element", "click_count"]
    # Save per-app: ranked_rui, ranked_eui, etc.
```

### Under-Used Elements

```python
UNDER_USED_THRESHOLD = 5

underused = (
    clicks["path"]
    .value_counts()
    .reset_index()
    .rename(columns={"path": "ui_element", "count": "click_count"})
    .query("click_count < @UNDER_USED_THRESHOLD")
    .sort_values("click_count")
)
```

### Hover vs. Click Comparison

```python
click_counts = clicks["path"].value_counts().rename("clicks")
hover_counts = hovers["path"].value_counts().rename("hovers")

hover_vs_click = pd.concat([click_counts, hover_counts], axis=1).fillna(0)
hover_vs_click["hover_to_click_ratio"] = hover_vs_click["hovers"] / hover_vs_click["clicks"].replace(0, float("nan"))

# High ratio = users notice but don't click = discoverability problem
discoverability_issues = hover_vs_click[hover_vs_click["hover_to_click_ratio"] > 3].sort_values("hover_to_click_ratio", ascending=False)
```

**Output Specs:**

| Chart | Type | Notes |
|---|---|---|
| Top 20 clicked elements per app | Horizontal bar (4 charts) | One chart per app: RUI, EUI, CDE, Portal |
| Under-used elements table | Table | Columns: element path, click count, app |
| Hover-to-click ratio heatmap | Heatmap or table | Flag ratio > 3 as discoverability issue |

**Known edge case:** Some `path` values may be null (events where path was not captured). These should be counted separately as "untracked events" and excluded from element ranking — do not silently drop them.

---

## Q3 — RUI Opacity Feature Usage

**Objective:** Count all opacity-related events in the RUI and identify which anatomical structures were toggled most.

```python
rui_events = events[events["app"] == "ccf-rui"].copy()
# Validation: should be ~9,430 rows

opacity_events = rui_events[rui_events["path"].str.contains("opacity", case=False, na=False)]
total_rui      = len(rui_events)
total_opacity  = len(opacity_events)
opacity_pct    = total_opacity / total_rui * 100
# Expected: ~206 events, ~2.2%

# Break down by path
opacity_breakdown = opacity_events["path"].value_counts().reset_index()
opacity_breakdown.columns = ["ui_element", "count"]

# Extract anatomical structure name from path
# Pattern: rui.left-sidebar.AS-visibility.<structure_name>.opacity-toggle
opacity_breakdown["structure"] = opacity_breakdown["ui_element"].str.extract(
    r"AS-visibility\.(.+?)\.opacity"
)
```

**Output Specs:**

| Output | Type | Notes |
|---|---|---|
| Opacity usage summary | Single stat card | "206 events = 2.2% of all RUI activity" |
| Top anatomical structures toggled | Horizontal bar | Top 15, sorted descending |
| Master toggle vs. per-structure breakdown | Pie or donut | Two segments: master toggle (4), individual (202) |

**Validation check:** `opacity_events["path"].isna().sum()` should be 0 — every opacity event should have a valid path. If not, investigate.

---

## Q4 — EUI Spatial Search Funnel

**Objective:** Count users at each step of the Spatial Search workflow to produce a drop-off funnel.

### Step Definitions

```python
eui_events = events[events["app"] == "ccf-eui"].copy()
spatial    = eui_events[eui_events["path"].str.contains("spatial-search", case=False, na=False)]

FUNNEL_STEPS = {
    "1_entry":       "eui.body-ui.spatial-search-button",
    "2_configure":   "eui.body-ui.spatial-search-config",   # prefix match
    "3_continue":    "eui.body-ui.spatial-search-config.continue",
    "4_results":     "eui.body-ui.spatial-search.results",  # prefix match
    "5_apply":       "eui.body-ui.spatial-search.buttons.apply",
}

# Count sessions (not raw events) at each step — a user who clicks twice still counts once per step
def sessions_at_step(df, path_pattern, exact=True):
    if exact:
        mask = df["path"] == path_pattern
    else:
        mask = df["path"].str.startswith(path_pattern, na=False)
    return df.loc[mask, "session_id"].nunique()

funnel = {
    "Entry (clicked Spatial Search)":   sessions_at_step(spatial, FUNNEL_STEPS["1_entry"]),
    "Configured organ selection":        sessions_at_step(spatial, FUNNEL_STEPS["2_configure"], exact=False),
    "Clicked Continue":                  sessions_at_step(spatial, FUNNEL_STEPS["3_continue"]),
    "Viewed results":                    sessions_at_step(spatial, FUNNEL_STEPS["4_results"],   exact=False),
    "Applied results":                   sessions_at_step(spatial, FUNNEL_STEPS["5_apply"]),
}
```

**Important:** Count unique `session_id` values at each step, not raw event counts. A funnel measures users, not clicks. Using raw event counts will make each step appear artificially large and mask the real drop-off.

### Organ Selection Analysis

```python
# Extract organ from path: eui.body-ui.spatial-search-config.organ-sex-selection.organ.<organ_name>
organ_pattern = r"organ-sex-selection\.organ\.([^.]+)"
spatial["organ_selected"] = spatial["path"].str.extract(organ_pattern)

organ_counts = spatial["organ_selected"].dropna().value_counts().head(15)
```

### Keyboard Usage (Power Users)

```python
keyboard_events = eui_events[eui_events["event_type"] == "keyboard"]
keyboard_sessions = keyboard_events["session_id"].nunique()
total_sessions    = eui_events["session_id"].nunique()
power_user_pct    = keyboard_sessions / total_sessions * 100
```

**Output Specs:**

| Chart | Type | Notes |
|---|---|---|
| Spatial Search funnel | Funnel chart or horizontal waterfall | Show absolute count AND % retained at each step |
| Top organs selected | Horizontal bar | Top 15 |
| Power user indicator | Single stat | "X% of EUI sessions used keyboard navigation" |

**Known edge case:** Some sessions may appear at a later step (e.g., results) without appearing at an earlier step (entry). This can happen due to direct URL access or tracking gaps. Document the count of such sessions rather than silently dropping them.

---

## Q5 — CDE Workflow Funnel and Tracking Gap

**Objective:** Trace the CDE workflow using both pageView events and click events. Document the download tracking gap.

```python
cde_events = events[events["app"] == "cde-ui"].copy()

# PageView funnel — use e.url field
def extract_url(query_list):
    return extract_field(query_list, "e.url")

cde_events["page_url"] = cde_events["query"].apply(extract_url)

page_funnel = {
    "Landing (/cde/)":                cde_events[cde_events["page_url"].str.contains("/cde/$",          na=False, regex=True)]["session_id"].nunique(),
    "Create page (/cde/create)":      cde_events[cde_events["page_url"].str.contains("/cde/create",     na=False)]["session_id"].nunique(),
    "Visualize page (/cde/visualize)":cde_events[cde_events["page_url"].str.contains("/cde/visualize",  na=False)]["session_id"].nunique(),
}

# Click funnel
click_funnel = {
    "Submit (generate viz)": cde_events[cde_events["path"] == "cde-ui.create-visualization-page.visualize-data.submit"]["session_id"].nunique(),
}

# Check for download events (expected: none)
download_events = cde_events[cde_events["path"].str.contains("download", case=False, na=False)]
download_count  = len(download_events)
# This should return 0 — document as a tracking gap
```

**Output Specs:**

| Output | Type | Notes |
|---|---|---|
| CDE workflow funnel | Funnel chart | Combine page + click steps into one flow |
| Tracking gap callout | Text box / annotation | Clearly state: download events not instrumented |
| Recommended event names | Table | Include in final report for dev team |

**Anomaly to document:** If `sessions at /cde/visualize` > `sessions who clicked Submit`, flag this in the output with an explanation (direct URL access, back-navigation, or tracking order issue).

---

## Additional Research Questions — Engineering Specs

---

### AQ1 — RUI Session Completion Rate

```python
rui = events[events["app"] == "ccf-rui"].copy()

sessions_any_event  = rui["session_id"].nunique()
sessions_placed_3d  = rui[rui["path"] == "rui.stage-content.3d"]["session_id"].nunique()
sessions_registered = rui[rui["path"] == "rui.stage-content.register"]["session_id"].nunique()

completion_rate = sessions_registered / sessions_any_event * 100
```

**Output:** Funnel (opened RUI → placed tissue block → registered). Report completion rate as a percentage.

---

### AQ2 — Error Rate by App and Version

```python
error_events = events[events["event_type"] == "error"].copy()

# By app
error_by_app = error_events.groupby("app").size() / events.groupby("app").size() * 100

# By version
error_events["version"] = error_events["query"].apply(lambda q: extract_field(q, "sv"))
error_by_version = (
    error_events.groupby(["app", "version"])
    .size()
    .div(events.groupby(["app", "version"]).size())
    .mul(100)
    .reset_index(name="error_rate_pct")
)

# Over time
error_monthly = (
    events.assign(is_error=events["event_type"] == "error")
    .groupby("year_month")["is_error"]
    .mean()
    .mul(100)
)
```

**Output:** Error rate % per app, per version, and over time. Flag any app with error rate > 10%.

---

### AQ3 — AI Bot Traffic Growth

```python
ai_bot_label = "AI-Assistant / Bot"

# Use full hra dataset (not filtered to human) for this question
hra_traffic = hra.copy()
hra_traffic["date_parsed"] = pd.to_datetime(hra_traffic["date"], errors="coerce")
hra_traffic["year_month"]  = hra_traffic["date_parsed"].dt.to_period("M")

monthly_share = (
    hra_traffic.groupby(["year_month", "traffic_type"])
    .size()
    .unstack(fill_value=0)
)
monthly_share_pct = monthly_share.div(monthly_share.sum(axis=1), axis=0) * 100
ai_trend = monthly_share_pct[ai_bot_label]
```

**Output:** Line chart showing AI bot share of total HRA traffic by month from 2023 to 2026.

---

### AQ4 — Geographic Reach

```python
geo = hra_human[hra_human["site"] == "Portal"].copy()
country_counts = geo["c_country"].value_counts().head(20)

# Year-over-year comparison
geo_yearly = (
    geo.groupby(["year", "c_country"])
    .size()
    .unstack(fill_value=0)
)
```

**Output:** World choropleth heatmap (top 20 country bar chart as fallback if choropleth is out of scope). Year-over-year top-10 comparison table.

**Library note:** `plotly.express.choropleth` handles this cleanly with ISO country codes. If keeping the stack simple, a seaborn bar chart of top 20 countries is sufficient.

---

### AQ5 — Session Depth (Power User vs. Casual)

```python
session_stats = (
    events.groupby("session_id")
    .agg(
        event_count   = ("event_type", "count"),
        duration_sec  = ("timestamp", lambda x: x.max() - x.min()),
        has_keyboard  = ("event_type", lambda x: (x == "keyboard").any()),
        app           = ("app", "first"),
    )
    .reset_index()
)

# Define segments
session_stats["user_type"] = "Casual"
session_stats.loc[session_stats["has_keyboard"] | (session_stats["event_count"] > 50), "user_type"] = "Power User"
```

**Output:** Distribution histogram of events per session (log scale). Pie chart of casual vs. power user sessions. Median session duration per app.

---

## Output Specification Summary

All outputs should be generated in a single reproducible Jupyter notebook. Each Q has its own section. Charts should be exported as `.png` files for embedding in the final report.

| Q | Primary Chart | Secondary Output |
|---|---|---|
| Q1 | Event type distribution bar + monthly line | App × event type table |
| Q2 | Top 20 clicked elements per app (4 charts) | Under-used elements table, hover/click ratio table |
| Q3 | Opacity breakdown bar | Summary stat (206 events, 2.2%) |
| Q4 | Spatial search funnel + organ bar | Power user keyboard stat |
| Q5 | CDE workflow funnel | Tracking gap documentation table |
| AQ1 | RUI completion funnel | Completion rate % |
| AQ2 | Error rate over time line | Per-app and per-version error rate table |
| AQ3 | AI bot share over time line | Growth rate from 2023 to 2026 |
| AQ4 | Country bar chart (top 20) or choropleth | Year-over-year comparison |
| AQ5 | Session depth histogram | Casual vs. power user breakdown |

---

## Validation Checklist

Before presenting any number to the client, verify:

- [ ] Row counts match expected values (events: ~114,884; RUI events: ~9,430; opacity events: ~206)
- [ ] Bot rows are excluded from all user behavior metrics
- [ ] Path extraction uses unified `path` OR `e.path` lookup — never just one
- [ ] Funnels count unique `session_id` values, not raw event rows
- [ ] Null `path` values are accounted for and documented, not silently dropped
- [ ] Date parsing produced no unexpected nulls (check `.isna().sum()` on `date_parsed`)
- [ ] CDE download event count is explicitly reported as 0 (not just absent from output)
- [ ] All chart axes are labeled with units; all percentages sum to 100% where applicable

---

## Known Technical Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `query` column contains malformed tuples | Medium | Add try/except in `extract_field`; log malformed rows |
| `path` and `e.path` both present in same row | Low | Prefer `path` over `e.path` when both exist — document this choice |
| `sessionId` key casing inconsistent across apps | Medium | Normalize key to lowercase before extraction |
| Memory pressure loading 16M + 12M row files | Medium | Use `pd.read_parquet(columns=[...])` to load only needed columns per analysis; do not join both files in memory simultaneously |
| Timezone inconsistencies in timestamps | Low | Treat all timestamps as UTC; document assumption |
