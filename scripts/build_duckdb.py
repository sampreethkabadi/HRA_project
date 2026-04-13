from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humanatlas_dashboard.config import load_settings
from humanatlas_dashboard.duckdb_builder import build_database
from humanatlas_dashboard.data_access import DashboardRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or refresh the DuckDB database for the HRA dashboard.")
    parser.add_argument("--config", default="config/humanatlas.yml")
    args = parser.parse_args()

    settings = load_settings(args.config)
    build_database(settings)

    repository = DashboardRepository(settings)
    filter_options = repository.get_filter_options()
    performance_options = repository.get_performance_filter_options()

    print(f"DuckDB ready at {settings.paths.duckdb_path}")
    print(f"Source parquet: {settings.paths.hra_logs_parquet}")
    print(f"Event apps: {', '.join(filter_options.apps)}")
    print(f"Event date range: {filter_options.min_date} to {filter_options.max_date}")
    print(f"Performance sites: {', '.join(performance_options.sites)}")
    print(f"Apps site segments: {', '.join(performance_options.apps)}")


if __name__ == "__main__":
    main()
