# Replication Guide

## 1. Prerequisites

- Python 3.11+
- access to the raw HRA parquet file
- local write access to the project workspace so DuckDB can be created

## 2. Configure the dataset path

Open [`config/humanatlas.yml`](/Users/cinhtw/Documents/Playground/config/humanatlas.yml) and verify:

- `datasets.hra_logs_parquet` points to the raw HRA parquet
- `database.duckdb_path` points to the desired local DuckDB output path

The current config is already set to:

- source parquet: `/Users/cinhtw/Downloads/2026-01-13_hra-logs.parquet`
- DuckDB target: `/Users/cinhtw/Documents/Playground/data/processed/hra_analytics.duckdb`

## 3. Create the Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 4. Build DuckDB

```bash
python3 scripts/build_duckdb.py --config config/humanatlas.yml
```

This step does the following:

1. reads the raw parquet
2. creates a DuckDB file
3. builds normalized event and performance tables
4. prints the discovered event apps, date range, performance sites, and apps-site segments

## 5. Launch the dashboard

```bash
streamlit run app/dashboard.py -- --config config/humanatlas.yml
```

## 5a. Regenerate the presentation deck

If you want the client presentation file as part of the reproducible handoff:

```bash
python3 scripts/generate_presentation.py
```

This writes:

- [hra_dashboard_client_presentation.pptx](/Users/cinhtw/Documents/Playground/deliverables/presentation/hra_dashboard_client_presentation.pptx)

## 6. Reproduce the same outputs later

To reproduce the same results:

1. keep the raw parquet unchanged
2. keep the same config file
3. rebuild DuckDB with the same code version
4. run the Streamlit app from the same repository revision

## 7. Core methodological decisions

These decisions are implemented in code and should remain unchanged unless the team intentionally changes the analysis definition:

### Event analysis

- only `site = 'Events'` rows are used
- `traffic_type` values `Bot` and `AI-Assistant / Bot` are excluded
- `ui_path` is derived from `COALESCE(path, e.path)`
- `sessionId = 'TODO'` is treated as missing session data

### Performance analysis

- request-level performance uses the full HRA request dataset, not only `Events`
- `Bot` and `AI-Assistant / Bot` traffic are excluded
- cache-served requests are `Hit` and `RefreshHit`
- app-page performance is derived from `site = 'Apps'` and mapped from the first URL path segment

### RQ5 caveat

- CDE histogram/violin downloads are not directly answerable from the current logs because download events are not instrumented
- the dashboard therefore shows the measurable CDE workflow and flags the missing tracking explicitly

## 8. Recommended handoff package

For a fully reproducible client handoff, provide:

1. this repository at a fixed commit
2. the final `config/humanatlas.yml`
3. the raw parquet snapshot or a secure reference to it
4. the generated DuckDB file if the client needs a ready-to-run copy
5. screenshots or exported PDFs if a static deliverable is also required
