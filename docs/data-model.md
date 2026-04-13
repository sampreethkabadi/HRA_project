# Data Model

## Source parquet schema used directly

The raw parquet contains request-level fields such as:

- `date`
- `site`
- `traffic_type`
- `cs_uri_stem`
- `time_taken`
- `time_to_first_byte`
- `x_edge_result_type`
- `x_edge_response_result_type`
- `x_edge_detailed_result_type`
- `query` as a map of event-specific keys

## Derived table: `events_normalized`

This table is the basis for all five behavioral research questions.

Columns of interest:

- `event_date`
- `event_month`
- `event_timestamp`
- `session_id`
- `app_name`
- `event_name`
- `ui_path`
- `path_source`
- `event_value`
- `page_url`
- `page_title`
- `ui_section`
- `is_opacity_event`
- `is_spatial_search_event`
- `is_download_event`

## Derived table: `site_performance_daily`

This table supports the site-level performance section.

Columns of interest:

- `request_date`
- `site`
- `total_requests`
- `cache_served_requests`
- `miss_requests`
- `error_requests`
- `avg_ttfb`
- `avg_time_taken`
- `avg_bytes`

## Derived table: `app_page_performance_daily`

This table supports app-page performance inside `apps.humanatlas.io`.

Columns of interest:

- `request_date`
- `app_segment`
- `app_name`
- `total_requests`
- `cache_served_requests`
- `miss_requests`
- `error_requests`
- `avg_ttfb`
- `avg_time_taken`
- `avg_bytes`

## Event-specific extraction rules

### Unified path extraction

`ui_path` is built as:

```sql
COALESCE(map_extract_value(query, 'path'), map_extract_value(query, 'e.path'))
```

This is required because the tracking implementation changed over time.

### Session normalization

`sessionId` values such as `TODO`, empty string, `null`, and `undefined` are treated as missing.

### App mapping for performance

App-page performance labels are mapped from URL path segments as follows:

- `kg-explorer` → `KG Explorer`
- `asctb-reporter` → `ASCT+B Reporter`
- `cde` → `CDE`
- `eui` → `EUI`
- `rui` → `RUI`
- `dashboard` → `Dashboard`
- `ftu-explorer` → `FTU Explorer`

## Why these derived tables matter

The raw parquet is large and mixes several kinds of traffic. The derived DuckDB tables isolate:

- event telemetry needed for the five research questions
- cache/latency summaries needed for performance analysis

That separation keeps the dashboard fast and makes the analytical definitions inspectable and reproducible.
