from __future__ import annotations

from pathlib import Path

import duckdb

from humanatlas_dashboard.config import Settings

REQUIRED_TABLES = (
    "events_normalized",
    "site_performance_daily",
    "app_page_performance_daily",
)


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _excluded_traffic_sql(settings: Settings) -> str:
    values = ", ".join(_sql_literal(value) for value in settings.excluded_traffic_types)
    return f"({values})"


def _performance_segments_case(settings: Settings) -> str:
    clauses = []
    for segment, label in settings.performance_app_segments.items():
        clauses.append(f"WHEN app_segment = {_sql_literal(segment)} THEN {_sql_literal(label)}")
    joined = "\n                ".join(clauses)
    return f"CASE\n                {joined}\n                ELSE NULL\n            END"


def build_database(settings: Settings) -> None:
    source_path = settings.paths.hra_logs_parquet
    duckdb_path = settings.paths.duckdb_path
    if not source_path.exists():
        raise FileNotFoundError(f"HRA parquet file not found: {source_path}")

    duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(duckdb_path))

    source_sql = _sql_literal(source_path.as_posix())
    excluded_sql = _excluded_traffic_sql(settings)
    performance_label_sql = _performance_segments_case(settings)

    con.execute(
        f"""
        CREATE OR REPLACE VIEW hra_logs_source AS
        SELECT *
        FROM read_parquet({source_sql});
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE events_normalized AS
        WITH base AS (
            SELECT
                date AS event_date,
                date_trunc('month', date) AS event_month,
                make_timestamp_ms(timestamp_ms) AS event_timestamp,
                year,
                month,
                day,
                site,
                traffic_type,
                x_host_header,
                distribution,
                referrer,
                c_country,
                cs_uri_stem,
                cs_uri_query,
                sc_status,
                time_to_first_byte,
                time_taken,
                CASE
                    WHEN map_extract_value(query, 'sessionId') IN ('TODO', '', 'null', 'undefined') THEN NULL
                    ELSE map_extract_value(query, 'sessionId')
                END AS session_id,
                COALESCE(NULLIF(map_extract_value(query, 'app'), ''), 'Unspecified') AS app_name,
                COALESCE(NULLIF(map_extract_value(query, 'event'), ''), 'Unspecified') AS event_name,
                COALESCE(map_extract_value(query, 'path'), map_extract_value(query, 'e.path')) AS ui_path,
                CASE
                    WHEN map_extract_value(query, 'path') IS NOT NULL THEN 'path'
                    WHEN map_extract_value(query, 'e.path') IS NOT NULL THEN 'e.path'
                    ELSE NULL
                END AS path_source,
                map_extract_value(query, 'e.value') AS event_value,
                map_extract_value(query, 'e.url') AS page_url,
                map_extract_value(query, 'e.title') AS page_title,
                map_extract_value(query, 'sv') AS schema_version
            FROM hra_logs_source
            WHERE site = 'Events'
              AND traffic_type NOT IN {excluded_sql}
        )
        SELECT
            *,
            regexp_extract(COALESCE(ui_path, ''), '^[^.]+\\.([^.]+)', 1) AS ui_section,
            lower(COALESCE(ui_path, '')) LIKE '%opacity%' AS is_opacity_event,
            lower(COALESCE(ui_path, '')) LIKE '%spatial-search%' AS is_spatial_search_event,
            lower(COALESCE(ui_path, '')) LIKE '%download%' AS is_download_event
        FROM base;
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE site_performance_daily AS
        SELECT
            date AS request_date,
            site,
            COUNT(*) AS total_requests,
            SUM(CASE WHEN x_edge_result_type IN ('Hit', 'RefreshHit') THEN 1 ELSE 0 END) AS cache_served_requests,
            SUM(CASE WHEN x_edge_result_type = 'Miss' THEN 1 ELSE 0 END) AS miss_requests,
            SUM(
                CASE
                    WHEN x_edge_result_type = 'Error'
                      OR x_edge_response_result_type = 'Error'
                      OR x_edge_detailed_result_type = 'ClientCommError'
                    THEN 1 ELSE 0
                END
            ) AS error_requests,
            AVG(time_to_first_byte) AS avg_ttfb,
            AVG(time_taken) AS avg_time_taken,
            AVG(sc_bytes) AS avg_bytes
        FROM hra_logs_source
        WHERE traffic_type NOT IN {excluded_sql}
        GROUP BY 1, 2;
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE app_page_performance_daily AS
        WITH app_requests AS (
            SELECT
                date AS request_date,
                regexp_extract(cs_uri_stem, '^/([^/]+)', 1) AS app_segment,
                x_edge_result_type,
                x_edge_response_result_type,
                x_edge_detailed_result_type,
                time_to_first_byte,
                time_taken,
                sc_bytes
            FROM hra_logs_source
            WHERE site = 'Apps'
              AND traffic_type NOT IN {excluded_sql}
        ),
        mapped AS (
            SELECT
                request_date,
                app_segment,
                {performance_label_sql} AS app_name,
                x_edge_result_type,
                x_edge_response_result_type,
                x_edge_detailed_result_type,
                time_to_first_byte,
                time_taken,
                sc_bytes
            FROM app_requests
        )
        SELECT
            request_date,
            app_segment,
            app_name,
            COUNT(*) AS total_requests,
            SUM(CASE WHEN x_edge_result_type IN ('Hit', 'RefreshHit') THEN 1 ELSE 0 END) AS cache_served_requests,
            SUM(CASE WHEN x_edge_result_type = 'Miss' THEN 1 ELSE 0 END) AS miss_requests,
            SUM(
                CASE
                    WHEN x_edge_result_type = 'Error'
                      OR x_edge_response_result_type = 'Error'
                      OR x_edge_detailed_result_type = 'ClientCommError'
                    THEN 1 ELSE 0
                END
            ) AS error_requests,
            AVG(time_to_first_byte) AS avg_ttfb,
            AVG(time_taken) AS avg_time_taken,
            AVG(sc_bytes) AS avg_bytes
        FROM mapped
        WHERE app_name IS NOT NULL
        GROUP BY 1, 2, 3;
        """
    )

    con.close()


def database_is_ready(settings: Settings) -> bool:
    duckdb_path = settings.paths.duckdb_path
    if not duckdb_path.exists():
        return False
    con = duckdb.connect(str(duckdb_path), read_only=True)
    try:
        existing = {
            row[0]
            for row in con.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'main'
                """
            ).fetchall()
        }
        return all(name in existing for name in REQUIRED_TABLES)
    finally:
        con.close()


def ensure_database(settings: Settings) -> None:
    if not database_is_ready(settings):
        build_database(settings)
