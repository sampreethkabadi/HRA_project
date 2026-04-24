# Human Reference Atlas Dashboard
## Analysis & Recommendations Report

**Prepared for:** Client review  
**Prepared from dataset:** [`2026-01-13_hra-logs.parquet`](/Users/cinhtw/Downloads/2026-01-13_hra-logs.parquet)  
**Behavioral analysis window:** August 5, 2025 to January 12, 2026  
**Analytical application:** [dashboard.py](/Users/cinhtw/Documents/Playground/app/dashboard.py)

## Executive Summary

The HRA logs show meaningful usage across the ecosystem, but the platform is not used uniformly. Most measurable interaction value is concentrated in a handful of core workflows:

- RUI registration interactions
- EUI result exploration and spatial-search entry
- KG Explorer object browsing and download actions
- CDE visualization setup and output-page access
- Portal navigation to data, applications, training, and research surfaces

The strongest business conclusion is that the ecosystem is seeing real user engagement, but instrumentation quality and uneven performance limit how confidently some product decisions can be made. In particular:

- event volume is highly concentrated in a small number of sessions
- a large number of UI paths have extremely low click counts
- spatial search is discoverable but has steep funnel drop-off
- opacity in RUI is a niche but legitimate advanced feature
- direct CDE chart-download tracking is absent
- a substantial share of events are missing app or path context

## Data and Method

The dashboard and this report were built from the HRA combined log parquet and a local DuckDB database. The relevant definitions are:

- behavioral analysis uses `site = 'Events'`
- `Bot` and `AI-Assistant / Bot` rows are excluded
- event paths are normalized with `COALESCE(path, e.path)`
- request-level performance is derived from the full log file
- cache-served requests are defined as `Hit` or `RefreshHit`

Behavioral dataset summary:

- total human events: **111,405**
- total sessions: **6,663**
- tracked app buckets: **15**
- total error events: **25,811**

## Question 1
## What is the distribution of frequency of user events?

### Key findings

- `click` is the largest event type with **38,961 events** or about **35.0%** of all human events.
- `error` is the second-largest category with **25,811 events** or about **23.2%**.
- `hover` follows at **23,162 events** or about **20.8%**.
- `pageView` contributes **14,474 events** or about **13.0%**.

This means the platform is not simply being browsed. Users are interacting with it, but errors are far too common to ignore.

### Session concentration

Usage is very uneven across sessions:

- 25th percentile: **1** event
- median: **3** events
- 75th percentile: **9** events
- 90th percentile: **23** events
- 99th percentile: about **195** events
- largest observed session: **6,281** events

Interpretation:

- most sessions are lightweight
- a smaller set of users generate disproportionately large activity
- outlier sessions should be reviewed separately because they can distort averages

### App concentration

Largest event buckets:

- `Unspecified`: **28,087**
- `kg-explorer`: **21,946**
- `humanatlas.io`: **18,822**
- `ccf-eui`: **10,540**
- `ccf-rui`: **9,430**

The presence of `Unspecified` as the largest bucket is itself a data-quality finding, not just a usage finding.

### Recommendation

- Treat event-frequency analysis as valid at the platform level, but use caution for app-level comparisons until missing `app` attribution is reduced.
- Separate outlier sessions from normal sessions in future analysis so heavy internal/test sessions do not dominate client-facing usage narratives.

## Question 2
## Which UI elements were used frequently and not frequently?

### Most-used elements by app

**RUI**

- `rui.stage-content.3d`: **1,276 clicks**
- `rui.stage-content.register`: **514**
- `rui.review`: **191**

**EUI**

- `eui.right-panel.results.donor.card`: **372 clicks**
- `eui.right-panel.results.select`: **367**
- `eui.body-ui.scene`: **260**

**CDE**

- file upload: **163 clicks**
- visualize submit: **132**
- cell-type selector: **96**

**Portal**

- category expansion: **1,129 clicks**
- header navigation to data: **954**
- header navigation to applications: **574**

**KG Explorer**

- table link cell: **753 clicks**
- download menu: **364**
- main-page search: **296**

### Under-used elements

There are **2,486 clicked UI paths** with fewer than **5 clicks**.

Interpretation:

- some long-tail features are likely niche and acceptable
- others may be too hidden, too complex, or not aligned with user priorities
- this is a strong candidate list for simplification, de-prioritization, or redesign

### Features noticed but not converted

Several interfaces show large hover-to-click gaps:

- `eui.body-ui.scene`: **4,089 hovers** vs **260 clicks**
- `hra-pop-visualizer.bar-graph`: **2,407 hovers** vs **41 clicks**
- `eui.right-panel.statistics`: **590 hovers** vs **0 clicks**

Interpretation:

- users notice these areas
- many do not convert from attention to action
- this suggests a discoverability-to-usability problem, not necessarily a complete lack of interest

### Recommendation

- Prioritize redesign review for high-hover, low-click elements.
- Audit the under-used path list and classify each item as one of:
  - expected niche feature
  - hidden but valuable feature
  - low-value feature that can be reduced or removed

## Question 3
## How often was opacity changed in the RUI?

### Key findings

- total RUI events: **9,430**
- opacity-related events: **206**
- opacity share of all RUI events: about **2.2%**

Opacity is therefore a specialized behavior, not a mainstream one.

### Type of opacity usage

- anatomical structure toggles: **166**
- landmark toggles: **36**
- master opacity settings panel toggle: **4**

### Top targets

- `all-anatomical-structures`: **50**
- `bisection-line`: **35**
- `tongue`: **17**
- `submandibular-gland`: **8**
- `cortex-of-kidney`: **7**

### Interpretation

Users who need opacity use specific anatomy-focused controls more often than the general settings panel. That suggests:

- opacity is useful in targeted expert workflows
- the master control itself is not the main interaction entry point

### Recommendation

- Keep opacity support because it serves a real advanced-use audience.
- Do not treat opacity as a broad engagement feature.
- If product simplification is needed, preserve structure-level controls first and reconsider whether the master panel interaction can be made clearer or more compact.

## Question 4
## How often was spatial search used in the EUI?

### Key findings

- spatial-search interactions: **1,016**
- sessions with spatial-search usage: **69**

### Funnel findings

- open spatial search: **66 sessions**
- configure search: **50**
- continue: **27**
- review results: **24**
- apply or reset: **7**

This is a sharp drop-off:

- about **76%** of sessions that open the tool reach configuration
- about **41%** reach continue
- about **36%** reach results review
- only about **11%** reach apply/reset

### Organ selection

Top selected organs:

- `kidney-l`: **8**
- `heart`: **5**
- `large-intestine`: **3**
- `skin`: **3**

### Keyboard usage

- `s`: **44**
- `w`: **29**
- `e`: **26**
- `a`: **10**
- `q`: **4**
- `d`: **3**

Interpretation:

- a small but meaningful subset of users is engaging spatial search deeply
- many users start but do not complete the full workflow
- the interaction appears more compatible with advanced users than casual users

### Recommendation

- Treat spatial search as a high-value but low-throughput expert workflow.
- Improve the transition from configuration to continuation, since that is the biggest visible drop-off point.
- Add lightweight in-context guidance and confirmation states to help users understand what to do next.

## Question 5
## How often were the histograms and violin plots in the CDE downloaded?

### Key findings

Direct histogram and violin-download events are **not present** in the current logs.

What the logs do show:

- landing-page sessions: **143**
- create-page sessions: **71**
- submit-visualization sessions: **33**
- visualize-output sessions: **34**

Pageview evidence:

- `/cde/`: **259**
- `/cde/create`: **222**
- `/cde/visualize`: **165**

### Interpretation

Users are reaching the output stage and using CDE as a visualization workflow, but the actual download action is not instrumented. The dashboard can therefore support this conclusion:

- the feature pipeline is being used through generation and viewing
- actual download behavior is currently unmeasurable

### Recommendation

Add explicit event tracking for:

- histogram download
- violin plot download
- CSV/table download if applicable
- save/share/export interactions

Suggested event names:

- `cde-ui.visualize-page.histogram.download`
- `cde-ui.visualize-page.violin-plot.download`

## Performance Findings

### Site-level performance

- `CDN`: **79.03%** cache-served, strongest performance profile
- `API`: **34.41%** cache-served
- `KG`: **22.73%** cache-served with the slowest total time at about **2.29s**
- `Apps`: **17.09%** cache-served and **34.38%** error rate
- `Portal`: **0%** cache-served in the current view and **32.37%** error rate
- `Events`: **0%** cache-served by definition in the current logic

### App-page performance inside `apps.humanatlas.io`

- `KG Explorer`: **96.83%** cache-served, about **0.034s** total time
- `CDE`: **69.82%** cache-served, about **0.56s** total time
- `EUI`: **0%** cache-served
- `RUI`: **0%** cache-served
- `Dashboard`: **0%** cache-served
- `ASCT+B Reporter`: **0%** cache-served
- `FTU Explorer`: **0%** cache-served

### Interpretation

- static and CDN-driven assets are performing well
- KG Explorer page delivery is strong
- CDE is materially better than several other app-page routes
- dynamic app-page routes for EUI and RUI appear to have little or no effective caching in this dataset summary

### Recommendation

- Focus performance investigation on app-page routing and cache policy for `EUI`, `RUI`, `Dashboard`, and `ASCT+B Reporter`.
- Investigate whether some of these surfaces are intentionally uncached or whether they are missing cache opportunities.
- Review Portal and Apps error rates separately from behavior analysis, because they are high enough to affect user experience and interpretation.

## Instrumentation and Data-Quality Findings

These findings are strategically important because they affect confidence in every chart.

### Missing app attribution

- `Unspecified` app bucket: **28,087 events**

### Missing path attribution

- events with no usable UI path: **25,856**
- share of all human events: **23.21%**

### Path-source split

- `path`: **56,082**
- `e.path`: **29,489**
- missing path source: **25,834**

### Error concentration

Top error counts by app bucket:

- `Unspecified`: **13,049**
- `kg-explorer`: **7,525**
- `humanatlas.io`: **2,408**
- `ccf-eui`: **778**

Several very small app buckets are effectively all-error, which likely indicates incomplete or noisy instrumentation rather than normal product behavior.

### Recommendation

The highest-priority cross-cutting recommendation is instrumentation cleanup:

1. ensure all events include `app`
2. ensure all meaningful interactive events include `path` or `e.path`
3. eliminate placeholder session IDs like `TODO`
4. add explicit CDE download tracking
5. review high-error event producers for logging noise versus real failures

## Strategic Recommendations

### Priority 1: Fix instrumentation

This is the highest-leverage improvement because it improves confidence in every future analysis.

### Priority 2: Improve EUI spatial-search completion

Spatial search looks valuable but has strong drop-off between opening and completion.

### Priority 3: Improve conversion on hover-heavy surfaces

Users are clearly noticing some features without acting on them.

### Priority 4: Review low-use UI elements for simplification

The long tail of low-use elements is large enough to justify pruning or consolidating complexity.

### Priority 5: Preserve advanced RUI opacity capability without over-investing

Opacity matters for a specialized audience, but it is not a top-volume feature.

### Priority 6: Improve app-page caching and investigate high error rates

This is particularly important for `Apps`, `Portal`, `EUI`, and `RUI` delivery paths.

## Recommended Next Steps

### Short term

- ship instrumentation fixes
- add CDE download events
- review EUI spatial-search UX
- review high-error app buckets

### Medium term

- rerun the dashboard after instrumentation updates
- compare pre-fix and post-fix data
- separate internal/testing sessions from external usage where possible

### Long term

- build benchmark dashboards around funnel completion, error rate, and cache-served rate
- feed stable aggregate views into executive reporting if needed

## Bottom Line

The HRA ecosystem is seeing real usage and several workflows are clearly valuable, but the most actionable client insight is not just which features are used. It is that **instrumentation quality, spatial-search completion, and uneven caching are the biggest constraints on both user experience and analytical confidence**.
