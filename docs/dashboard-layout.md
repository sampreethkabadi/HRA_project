# Dashboard Layout

## Recommended information architecture

The website is organized as a research dashboard, not a generic reporting portal. Each tab is mapped to a specific question and contains enough context for a client or reviewer to understand the answer without opening the code.

## Sidebar

- event-app multiselect
- date-range selector
- methodology note

The sidebar filters apply to the behavioral research-question tabs. The performance tab also includes its own site/app selectors because performance entities are not identical to the event-app names.

## Main tabs

1. Overview
2. Event Frequency
3. UI Element Usage
4. RUI Opacity
5. EUI Spatial Search
6. CDE Downloads
7. Performance

## Tab details

### Overview

- KPI row: human events, sessions, tracked apps, cache-served rate
- Chart 1: monthly event volume by app
- Chart 2: overall event mix
- Table: section guide for the rest of the dashboard

### Event Frequency

- KPI row: total events, median events per session, most common event
- Chart 1: event type distribution
- Chart 2: histogram of session event intensity
- Chart 3: stacked event mix by app
- Chart 4: monthly event volume
- Table: event counts by app and event type

### UI Element Usage

- KPI row: distinct clicked paths, top clicked path, under-used count
- Chart 1: top 20 clicked paths
- Chart 2: lowest-use clicked paths
- Chart 3: top 20 hovered paths
- Chart 4: click density heatmap by app section
- Table: under-used paths with fewer than five clicks

### RUI Opacity

- KPI row: total opacity events, share of all RUI events, top affected structure
- Chart 1: opacity events by control type
- Chart 2: opacity events over time
- Chart 3: top anatomical structures / landmarks with opacity interactions
- Table: detailed opacity paths and counts

### EUI Spatial Search

- KPI row: spatial-search events, spatial-search sessions, largest funnel stage
- Chart 1: funnel by session
- Chart 2: most selected organs
- Chart 3: keyboard usage
- Table: detailed spatial-search interactions

### CDE Downloads

- KPI row: tracked download events, visualize page views, visualization-submit sessions
- Callout: explicit warning that download events are not instrumented
- Chart 1: CDE workflow funnel
- Chart 2: tracked CDE page views
- Table: page-view summary

### Performance

- Local controls: sites and apps-site pages
- KPI row: average cache-served rate, average time to first byte, average total time
- Chart 1: cache-served rate by site
- Chart 2: latency scatter by app page
- Chart 3: daily cache-served rate trend by site
- Tables: site summary and app-page summary

## Layout rationale

- Every tab starts with the question it answers.
- The charts are ordered from headline insight to deeper detail.
- Known instrumentation limits are surfaced in the UI, not hidden in documentation only.
- Performance remains a separate tab because it is request-level operational analysis, not user-behavior analysis.
