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

## Generate the presentation deck

```bash
python3 scripts/generate_presentation.py
```

This writes the client deck to:

- [hra_dashboard_client_presentation.pptx](/Users/cinhtw/Documents/Playground/deliverables/presentation/hra_dashboard_client_presentation.pptx)

## Deliverables

- [Client analysis report](/Users/cinhtw/Documents/Playground/deliverables/report/hra_analysis_recommendations_report.md)
- [Presentation source](/Users/cinhtw/Documents/Playground/deliverables/presentation/hra_dashboard_client_presentation.md)
- [Presentation deck](/Users/cinhtw/Documents/Playground/deliverables/presentation/hra_dashboard_client_presentation.pptx)
- [Deliverables README](/Users/cinhtw/Documents/Playground/deliverables/README.md)

## Documentation

- [Architecture](/Users/cinhtw/Documents/Playground/docs/architecture.md)
- [Dashboard layout](/Users/cinhtw/Documents/Playground/docs/dashboard-layout.md)
- [Data model](/Users/cinhtw/Documents/Playground/docs/data-model.md)
- [Replication guide](/Users/cinhtw/Documents/Playground/docs/replication-guide.md)
- [GitHub publishing guide](/Users/cinhtw/Documents/Playground/docs/setup/github-publish.md)

## Verification

Run tests:

```bash
python3 -m pytest
```

## Power BI note

Power BI is still possible later, but it should sit downstream of this repository. The recommended pattern is:

1. Use this repo to define the canonical DuckDB tables and research logic.
2. Export aggregate tables if the client needs executive BI dashboards.
3. Keep the research-focused exploratory analysis in this versioned Streamlit project.
