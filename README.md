# Human Atlas Research Dashboard

This repository contains a reproducible analytics dashboard for the Human Reference Atlas (HRA), built from the raw HRA CloudFront/event parquet and organized around the client's five research questions plus a performance section.

It includes:

- a Streamlit website
- a DuckDB build pipeline
- documentation for reproducibility
- a client-ready analysis report
- a client presentation deck in `.pptx` format

## Repository status

This repo is ready to run locally. It is also organized for GitHub publication, but this local folder does not currently have a Git remote configured yet.

## What is in scope

The dashboard answers:

1. What is the distribution of frequency of user events?
2. Which UI elements were used frequently and not frequently?
3. How often was opacity changed in the RUI?
4. How often was spatial search used in the EUI?
5. How often were the histograms and violin plots in the CDE downloaded?
6. How does performance vary across HRA sites and app pages?

## Key finding to know before presenting this

The current HRA logs do not contain direct histogram-download or violin-plot download events for CDE. The dashboard and report therefore treat question 5 as a tracking-gap finding, not as a positive count of download activity.

## Project structure

```text
app/                       Streamlit entrypoint
config/                    Dataset and DuckDB config
data/                      Generated DuckDB database and exports
deliverables/              Client report, presentation, and handoff materials
docs/                      Architecture, data model, replication, and publishing docs
scripts/                   Database build and presentation generation scripts
src/humanatlas_dashboard/  Query layer, DuckDB builder, charts, and tab sections
tests/                     Automated verification
```

## Install

### Runtime only

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Runtime plus presentation generation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,deliverables]"
```

## Configure the dataset

The main config file is [humanatlas.yml](/Users/cinhtw/Documents/Playground/config/humanatlas.yml).

Current defaults:

- source parquet: `/Users/cinhtw/Downloads/2026-01-13_hra-logs.parquet`
- DuckDB output: `/Users/cinhtw/Documents/Playground/data/processed/hra_analytics.duckdb`

If the parquet moves, update `datasets.hra_logs_parquet` in the config file.

## Build DuckDB

```bash
python3 scripts/build_duckdb.py --config config/humanatlas.yml
```

This creates:

- `events_normalized`
- `site_performance_daily`
- `app_page_performance_daily`

inside the DuckDB file.

## Run the dashboard website

```bash
streamlit run app/dashboard.py -- --config config/humanatlas.yml
```

Then open the local Streamlit URL, usually `http://localhost:8501`.

## Dashboard Navigation Guide

The dashboard opens with 7 tabs organized around research questions. All tabs share the same global filters in the left sidebar.

### Global Filters (Sidebar)

Use these filters to control data across all tabs:

1. **Event apps**: Select which applications to analyze (default: ccf-eui, ccf-rui, cde-ui, kg-explorer). All other apps are available but disabled by default.

2. **Date range**: Choose the analysis period. Defaults to the full date range available in the dataset (August 2025 to January 2026).

3. **Methodology note**: Explains that all event data excludes bot and AI-assistant traffic, and performance data comes from CloudFront request logs.

### Tab Descriptions

#### Tab 1: Overview

Entry point to the dashboard with high-level platform health metrics.

Shows:
- Key metrics: total human events, total sessions, number of tracked apps, cache-served request percentage
- Monthly event volume by app: separate line charts for each application showing trends over time
- Overall event mix: bar chart of all event types (clicks, hovers, pageviews, errors, model changes)
- Dashboard guide table: quick reference for what each tab answers

Actionable insights focus on traffic concentration, error rates, and engagement depth across apps.

#### Tab 2: Event Frequency

Detailed analysis of event distribution patterns across the platform.

Shows:
- Key metrics: total events, median events per session, most common event type
- Event type distribution: bar chart showing count of each event type
- Session event intensity: how many sessions fall into event count ranges (1-5 events, 6-20 events, 21-50 events, 51+ events)
- Event mix by app: stacked bar chart showing which event types occur in each app
- Monthly event volume: line chart tracking total events by app over time
- Full data table: raw event counts by app

Insights highlight error prevalence, session engagement patterns, and feature discoverability issues.

#### Tab 3: UI Element Usage

Analysis of which UI elements drive interaction within each application.

Shows:
- Key metrics: total unique clicked paths, top clicked element, count of under-used elements
- Overall top 10 clicked UI paths: bar chart across all selected apps combined
- Usage by app: separate tabs for each core app (CDE, RUI, EUI, KG-Explorer) showing top 10 clicked elements, lowest-use clicked elements, and top 10 hovered elements for each
- Click density by app section: heatmap showing click concentration by UI section and app
- Full data table: detailed click and hover counts

Insights identify critical user workflows, feature adoption patterns, and UI elements needing attention.

#### Tab 4: RUI Opacity

Specialized analysis of opacity control interactions in the Registration User Interface.

Shows:
- Key metrics: total opacity events, percentage of RUI events that are opacity-related, top affected anatomical structure
- Top 5 opacity control types: which opacity controls are used most (master toggle vs structure-specific)
- Opacity interactions over time: monthly trend line showing usage patterns
- Top 5 anatomical structures/landmarks: which anatomy targets receive opacity changes most often
- Full data table: detailed opacity interaction logs

Insights reveal whether opacity control is a core workflow or advanced feature, and which anatomical structures matter most to users.

#### Tab 5: EUI Spatial Search

Analysis of spatial search workflow usage in the Exploration User Interface.

Shows:
- Key metrics: total spatial search events, sessions using spatial search, largest funnel stage
- Spatial search funnel: funnel chart showing progression through workflow stages (setup, configuration, continue, results, apply)
- Most selected organs: bar chart of organs users select most often in spatial search
- Spatial search keyboard usage: bar chart of which keyboard shortcuts are used during spatial search
- Full data table: detailed spatial search interaction logs

Insights identify workflow friction points, user preferences for organ selection, and power user patterns.

#### Tab 6: CDE Downloads

Analysis of the Cell Distance Explorer data download workflow with explicit tracking gap callout.

Shows:
- Key metrics: tracked download events, visualize page views, submit visualization sessions
- Warning: highlights that direct histogram and violin plot downloads are not tracked in the current logs
- CDE workflow funnel: funnel chart showing progression from landing to visualization to download
- Tracked CDE page views: bar chart of page URLs accessed during CDE workflow
- Full data table: detailed page view and download attempt logs

Insights focus on workflow dropout rates and data instrumentation gaps.

#### Tab 7: Performance

Infrastructure and application performance analysis including cache efficiency and latency.

Shows:
- Key metrics: average cache-served rate, average time to first byte, average total response time
- Filter controls: select which sites and app pages to analyze
- Cache-served rate by site: bar chart comparing cache efficiency across infrastructure layers (CDN, Portal, API, KG, Apps, Events)
- Daily cache-served rate trend: line chart showing how cache performance changes over time for each site
- Apps site performance map: scatter plot with response time vs total time for each app, bubble size indicates request volume
- Full data tables: site and app performance metrics

Insights identify infrastructure bottlenecks, apps experiencing slow origin fetches, and opportunities for cache optimization.

### Actionable Insights

Each tab includes an "View Actionable Insights" button that opens a collapsible panel with insight cards organized by priority level:
- CRITICAL (red): Issues requiring immediate action
- HIGH (orange): Important issues to address soon
- MEDIUM (blue): Improvements to consider
- LOW (green): Nice-to-have optimizations

Each insight includes the issue description, business impact, and specific recommendation.

### Data Notes

All dashboard data excludes bot and AI-assistant traffic to focus on genuine human user behavior. Performance metrics come from CloudFront request logs and reflect both cache hits and origin fetches. Monthly aggregations use calendar month boundaries.

## Generate the presentation deck

```bash
python3 scripts/generate_presentation.py
```

## Verification

Run tests:

```bash
python3 -m pytest
```
