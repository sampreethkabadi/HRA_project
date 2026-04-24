# Human Reference Atlas Dashboard
## Client Presentation Outline

### Slide 1
Title

- Human Reference Atlas Dashboard
- Analysis & Recommendations
- Based on HRA event and request logs

### Slide 2
Scope and dataset

- Source parquet: `2026-01-13_hra-logs.parquet`
- Human event window: August 5, 2025 to January 12, 2026
- 111,405 human events
- 6,663 sessions
- 15 app buckets

### Slide 3
Executive summary

- Real usage exists across RUI, EUI, KG Explorer, CDE, and Portal
- Event volume is concentrated in a minority of sessions
- Spatial search is discoverable but drops off sharply
- RUI opacity is real but niche
- CDE downloads are not instrumented
- Telemetry quality and performance are major opportunities

### Slide 4
RQ1: Event frequency

- Click is the largest event type
- Errors are unusually high
- Median session has only 3 events
- A small number of sessions dominate the distribution

### Slide 5
RQ2: UI element usage

- Strong engagement with RUI registration, EUI results, KG browsing, CDE setup
- 2,486 clicked UI paths have fewer than 5 clicks
- Hover-heavy, low-click surfaces suggest discoverability without conversion

### Slide 6
RQ3: RUI opacity

- 206 opacity events
- 2.2% of all RUI events
- Mostly structure-level toggles, not global settings
- Important for advanced workflows, not mainstream use

### Slide 7
RQ4: EUI spatial search

- 1,016 spatial-search events
- 69 sessions used it
- Funnel: 66 opened, 50 configured, 27 continued, 24 reviewed, 7 applied/reset
- Strong evidence of advanced use with steep drop-off

### Slide 8
RQ5: CDE downloads

- Users reach create and visualize stages
- No direct histogram or violin download events exist in the logs
- Current answer is a tracking-gap finding

### Slide 9
Performance

- CDN performs best
- KG Explorer pages are strongly cached
- CDE pages are decent
- EUI, RUI, Dashboard, and ASCT+B Reporter show little effective caching in this view

### Slide 10
Data-quality issues

- 28,087 events have no app attribution
- 25,856 events have no usable UI path
- Error volume is concentrated in Unspecified and KG Explorer buckets

### Slide 11
Recommendations

- Fix instrumentation first
- Improve EUI spatial-search completion
- Review hover-heavy, low-click interfaces
- Preserve RUI opacity as an expert feature
- Add explicit CDE download tracking
- Improve caching on dynamic app-page routes

### Slide 12
Next steps

- Instrumentation and error cleanup
- UX review of spatial search
- Add CDE export events
- Rerun the dashboard after fixes
- Use new results for a second-phase product prioritization
