from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb

from humanatlas_dashboard.config import load_settings
from humanatlas_dashboard.data_access import DashboardFilters, DashboardRepository
from humanatlas_dashboard.duckdb_builder import build_database


def test_duckdb_build_and_repository_queries(tmp_path: Path) -> None:
    parquet_path = tmp_path / "hra_logs.parquet"
    duckdb_path = tmp_path / "hra_analytics.duckdb"
    config_path = tmp_path / "config.yml"

    con = duckdb.connect()
    con.execute(
        f"""
        COPY (
            SELECT * FROM (
                VALUES
                    (
                        'anon-1', DATE '2026-01-01', '10:00:00', 100::BIGINT, 'GET', '/tr', 200,
                        1704103200000::BIGINT, 2026, 1, 1, 'Likely Human', 'Events', 'cdn.humanatlas.io', 'cdn',
                        'direct', 'US', 'sessionId=s1',
                        MAP(['sessionId','app','event','path'], ['s1','ccf-rui','click','rui.left-sidebar.opacity-settings.toggle']),
                        'Miss', 'Miss', 'Miss', 0.10, 0.20, 500::BIGINT
                    ),
                    (
                        'anon-2', DATE '2026-01-01', '10:05:00', 120::BIGINT, 'GET', '/tr', 200,
                        1704103500000::BIGINT, 2026, 1, 1, 'Likely Human', 'Events', 'cdn.humanatlas.io', 'cdn',
                        'direct', 'US', 'sessionId=s2',
                        MAP(['sessionId','app','event','e.url'], ['s2','cde-ui','pageView','https://apps.humanatlas.io/cde/create']),
                        'Miss', 'Miss', 'Miss', 0.15, 0.30, 600::BIGINT
                    ),
                    (
                        'anon-3', DATE '2026-01-01', '10:10:00', 150::BIGINT, 'GET', '/tr', 200,
                        1704103800000::BIGINT, 2026, 1, 1, 'Likely Human', 'Events', 'cdn.humanatlas.io', 'cdn',
                        'direct', 'US', 'sessionId=s2',
                        MAP(['sessionId','app','event','path'], ['s2','cde-ui','click','cde-ui.create-visualization-page.visualize-data.submit']),
                        'Miss', 'Miss', 'Miss', 0.16, 0.32, 650::BIGINT
                    ),
                    (
                        'anon-8', DATE '2026-01-01', '10:12:00', 150::BIGINT, 'GET', '/tr', 200,
                        1704103920000::BIGINT, 2026, 1, 1, 'Likely Human', 'Events', 'cdn.humanatlas.io', 'cdn',
                        'direct', 'US', 'sessionId=s2',
                        MAP(['sessionId','app','event','path','e.url'], ['s2','cde-ui','pageView','cde-ui.visualize-page.chart','https://apps.humanatlas.io/cde/visualize']),
                        'Miss', 'Miss', 'Miss', 0.16, 0.32, 650::BIGINT
                    ),
                    (
                        'anon-4', DATE '2026-01-01', '10:15:00', 200::BIGINT, 'GET', '/eui', 200,
                        1704104100000::BIGINT, 2026, 1, 1, 'Likely Human', 'Apps', 'apps.humanatlas.io', 'apps',
                        'direct', 'US', '',
                        MAP(['dummy'], ['value']),
                        'Hit', 'Hit', 'Hit', 0.05, 0.07, 900::BIGINT
                    ),
                    (
                        'anon-5', DATE '2026-01-01', '10:16:00', 210::BIGINT, 'GET', '/cde', 200,
                        1704104160000::BIGINT, 2026, 1, 1, 'Likely Human', 'Apps', 'apps.humanatlas.io', 'apps',
                        'direct', 'US', '',
                        MAP(['dummy'], ['value']),
                        'Miss', 'Miss', 'Miss', 0.09, 0.13, 1200::BIGINT
                    ),
                    (
                        'anon-6', DATE '2026-01-01', '10:20:00', 180::BIGINT, 'GET', '/', 200,
                        1704104400000::BIGINT, 2026, 1, 1, 'Likely Human', 'Portal', 'humanatlas.io', 'humanatlas.io',
                        'direct', 'US', '',
                        MAP(['dummy'], ['value']),
                        'RefreshHit', 'RefreshHit', 'RefreshHit', 0.08, 0.11, 1500::BIGINT
                    ),
                    (
                        'anon-7', DATE '2026-01-01', '10:25:00', 180::BIGINT, 'GET', '/bot', 200,
                        1704104700000::BIGINT, 2026, 1, 1, 'Bot', 'Events', 'cdn.humanatlas.io', 'cdn',
                        'direct', 'US', 'sessionId=bot-session',
                        MAP(['sessionId','app','event','path'], ['bot-session','ccf-rui','click','rui.left-sidebar.opacity-settings.toggle']),
                        'Miss', 'Miss', 'Miss', 0.20, 0.25, 700::BIGINT
                    )
            ) AS t(
                anon_id, date, time, sc_bytes, cs_method, cs_uri_stem, sc_status, timestamp_ms,
                year, month, day, traffic_type, site, x_host_header, distribution, referrer, c_country, cs_uri_query, query,
                x_edge_result_type, x_edge_response_result_type, x_edge_detailed_result_type,
                time_to_first_byte, time_taken, cs_bytes
            )
        ) TO '{parquet_path.as_posix()}' (FORMAT PARQUET)
        """
    )
    con.close()

    config_path.write_text(
        f"""
database:
  duckdb_path: {duckdb_path}

datasets:
  hra_logs_parquet: {parquet_path}

filters:
  excluded_traffic_types:
    - Bot
    - AI-Assistant / Bot

performance:
  app_segments:
    cde: CDE
    eui: EUI
        """.strip(),
        encoding="utf-8",
    )

    settings = load_settings(config_path)
    build_database(settings)
    repository = DashboardRepository(settings)
    filters = DashboardFilters(apps=["ccf-rui", "cde-ui"], start_date=date(2026, 1, 1), end_date=date(2026, 1, 1))

    metrics = repository.overview_metrics(filters)
    opacity_total = repository.rui_event_totals(filters)[1]
    cde_funnel = repository.cde_funnel(filters)
    performance = repository.performance_app_summary(date(2026, 1, 1), date(2026, 1, 1), ["CDE", "EUI"])

    assert metrics["total_events"] == 4
    assert metrics["total_sessions"] == 2
    assert metrics["active_apps"] == 2
    assert round(metrics["cache_hit_rate"], 2) == 28.57
    assert opacity_total == 1
    assert set(cde_funnel["funnel_stage"]) == {"2. Create page", "3. Submit visualization", "4. Visualize output"}
    assert set(performance["app_name"]) == {"CDE", "EUI"}
