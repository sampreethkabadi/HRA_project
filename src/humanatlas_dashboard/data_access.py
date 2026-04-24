from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import duckdb
import pandas as pd

from humanatlas_dashboard.config import Settings
from humanatlas_dashboard.duckdb_builder import ensure_database


@dataclass(frozen=True)
class DashboardFilters:
    apps: list[str]
    start_date: date
    end_date: date


@dataclass(frozen=True)
class FilterOptions:
    apps: list[str]
    min_date: date
    max_date: date


@dataclass(frozen=True)
class PerformanceFilterOptions:
    sites: list[str]
    apps: list[str]


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


class DashboardRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        ensure_database(settings)
        self.connection = duckdb.connect(str(settings.paths.duckdb_path), read_only=True)

    def get_filter_options(self) -> FilterOptions:
        apps = self.connection.execute(
            """
            SELECT DISTINCT app_name
            FROM events_normalized
            WHERE app_name IS NOT NULL
            ORDER BY app_name
            """
        ).fetchdf()["app_name"].tolist()

        bounds = self.connection.execute(
            """
            SELECT MIN(event_date) AS min_date, MAX(event_date) AS max_date
            FROM events_normalized
            """
        ).fetchone()

        return FilterOptions(apps=apps, min_date=bounds[0], max_date=bounds[1])

    def get_performance_filter_options(self) -> PerformanceFilterOptions:
        sites = self.connection.execute(
            "SELECT DISTINCT site FROM site_performance_daily ORDER BY site"
        ).fetchdf()["site"].tolist()
        apps = self.connection.execute(
            "SELECT DISTINCT app_name FROM app_page_performance_daily ORDER BY app_name"
        ).fetchdf()["app_name"].tolist()
        return PerformanceFilterOptions(sites=sites, apps=apps)

    def _event_where(self, filters: DashboardFilters, extra: list[str] | None = None) -> str:
        clauses = [
            f"event_date BETWEEN {_sql_literal(str(filters.start_date))} AND {_sql_literal(str(filters.end_date))}"
        ]
        if filters.apps:
            app_list = ", ".join(_sql_literal(app) for app in filters.apps)
            clauses.append(f"app_name IN ({app_list})")
        if extra:
            clauses.extend(extra)
        return " AND ".join(clauses)

    def _date_where(self, start_date: date, end_date: date, date_column: str) -> str:
        return f"{date_column} BETWEEN {_sql_literal(str(start_date))} AND {_sql_literal(str(end_date))}"

    def overview_metrics(self, filters: DashboardFilters) -> dict[str, float]:
        where_sql = self._event_where(filters)
        perf_where = self._date_where(filters.start_date, filters.end_date, "request_date")
        query = f"""
        WITH event_stats AS (
            SELECT
                COUNT(*) AS total_events,
                COUNT(DISTINCT session_id) AS total_sessions,
                COUNT(DISTINCT app_name) AS active_apps,
                COUNT(*) FILTER (WHERE event_name = 'error') AS error_events
            FROM events_normalized
            WHERE {where_sql}
        ),
        perf_stats AS (
            SELECT
                SUM(cache_served_requests) AS cached_requests,
                SUM(total_requests) AS total_requests
            FROM site_performance_daily
            WHERE {perf_where}
        )
        SELECT * FROM event_stats CROSS JOIN perf_stats
        """
        row = self.connection.execute(query).fetchone()
        cached_requests = row[4] or 0
        total_requests = row[5] or 0
        cache_rate = (cached_requests / total_requests * 100) if total_requests else 0
        return {
            "total_events": row[0] or 0,
            "total_sessions": row[1] or 0,
            "active_apps": row[2] or 0,
            "error_events": row[3] or 0,
            "cache_hit_rate": round(cache_rate, 2),
        }

    def overview_event_trend(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(filters)
        return self.connection.execute(
            f"""
            SELECT
                event_month,
                app_name,
                COUNT(*) AS event_count
            FROM events_normalized
            WHERE {where_sql}
            GROUP BY 1, 2
            ORDER BY 1, 2
            """
        ).fetchdf()

    def event_type_distribution(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(filters)
        return self.connection.execute(
            f"""
            SELECT
                event_name,
                COUNT(*) AS event_count
            FROM events_normalized
            WHERE {where_sql}
            GROUP BY 1
            ORDER BY event_count DESC
            """
        ).fetchdf()

    def event_type_by_app(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(filters)
        return self.connection.execute(
            f"""
            SELECT
                app_name,
                event_name,
                COUNT(*) AS event_count
            FROM events_normalized
            WHERE {where_sql}
            GROUP BY 1, 2
            ORDER BY app_name, event_count DESC
            """
        ).fetchdf()

    def session_event_distribution(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(filters, ["session_id IS NOT NULL"])
        return self.connection.execute(
            f"""
            SELECT
                session_id,
                app_name,
                COUNT(*) AS event_count
            FROM events_normalized
            WHERE {where_sql}
            GROUP BY 1, 2
            ORDER BY event_count DESC
            """
        ).fetchdf()

    def ui_click_usage(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(
            filters,
            ["event_name = 'click'", "ui_path IS NOT NULL", "ui_path <> ''"],
        )
        return self.connection.execute(
            f"""
            SELECT
                app_name,
                ui_path,
                ui_section,
                COUNT(*) AS click_count
            FROM events_normalized
            WHERE {where_sql}
            GROUP BY 1, 2, 3
            ORDER BY click_count DESC
            """
        ).fetchdf()

    def ui_hover_usage(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(
            filters,
            ["event_name = 'hover'", "ui_path IS NOT NULL", "ui_path <> ''"],
        )
        return self.connection.execute(
            f"""
            SELECT
                app_name,
                ui_path,
                ui_section,
                COUNT(*) AS hover_count
            FROM events_normalized
            WHERE {where_sql}
            GROUP BY 1, 2, 3
            ORDER BY hover_count DESC
            """
        ).fetchdf()

    def ui_section_heatmap(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(
            filters,
            ["event_name = 'click'", "ui_section IS NOT NULL", "ui_section <> ''"],
        )
        return self.connection.execute(
            f"""
            SELECT
                app_name,
                ui_section,
                COUNT(*) AS click_count
            FROM events_normalized
            WHERE {where_sql}
            GROUP BY 1, 2
            ORDER BY click_count DESC
            """
        ).fetchdf()

    def rui_opacity_details(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(filters, ["app_name = 'ccf-rui'", "is_opacity_event"])
        return self.connection.execute(
            f"""
            SELECT
                event_date,
                ui_path,
                CASE
                    WHEN ui_path = 'rui.left-sidebar.opacity-settings.toggle' THEN 'Opacity settings panel'
                    WHEN ui_path LIKE 'rui.left-sidebar.AS-visibility.%' THEN 'Anatomical structure toggle'
                    WHEN ui_path LIKE 'rui.left-sidebar.landmarks-visibility.%' THEN 'Landmark toggle'
                    ELSE 'Other opacity control'
                END AS opacity_group,
                CASE
                    WHEN ui_path LIKE 'rui.left-sidebar.AS-visibility.%' THEN regexp_extract(ui_path, '^rui\\.left-sidebar\\.AS-visibility\\.([^.]+)\\.opacity-toggle$', 1)
                    WHEN ui_path LIKE 'rui.left-sidebar.landmarks-visibility.%' THEN regexp_extract(ui_path, '^rui\\.left-sidebar\\.landmarks-visibility\\.([^.]+)\\.opacity-toggle$', 1)
                    ELSE NULL
                END AS target_name,
                COUNT(*) AS opacity_count
            FROM events_normalized
            WHERE {where_sql}
            GROUP BY 1, 2, 3, 4
            ORDER BY event_date, opacity_count DESC
            """
        ).fetchdf()

    def rui_event_totals(self, filters: DashboardFilters) -> tuple[int, int]:
        overall_where = self._event_where(filters, ["app_name = 'ccf-rui'"])
        opacity_where = self._event_where(filters, ["app_name = 'ccf-rui'", "is_opacity_event"])
        overall = self.connection.execute(
            f"SELECT COUNT(*) FROM events_normalized WHERE {overall_where}"
        ).fetchone()[0]
        opacity = self.connection.execute(
            f"SELECT COUNT(*) FROM events_normalized WHERE {opacity_where}"
        ).fetchone()[0]
        return int(overall or 0), int(opacity or 0)

    def eui_spatial_details(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(filters, ["app_name = 'ccf-eui'", "is_spatial_search_event"])
        return self.connection.execute(
            f"""
            SELECT
                event_date,
                session_id,
                ui_path,
                event_name,
                CASE
                    WHEN ui_path = 'eui.body-ui.spatial-search-button' THEN '1. Open spatial search'
                    WHEN ui_path = 'eui.body-ui.spatial-search-config.continue' THEN '3. Continue'
                    WHEN ui_path LIKE 'eui.body-ui.spatial-search-config.%' THEN '2. Configure search'
                    WHEN ui_path LIKE 'eui.body-ui.spatial-search.results.%'
                      OR ui_path = 'eui.body-ui.spatial-search.scene' THEN '4. Review results'
                    WHEN ui_path LIKE 'eui.body-ui.spatial-search.buttons.%' THEN '5. Apply or reset'
                    ELSE 'Other spatial-search interaction'
                END AS funnel_stage
            FROM events_normalized
            WHERE {where_sql}
            """
        ).fetchdf()

    def eui_spatial_funnel(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(filters, ["app_name = 'ccf-eui'", "is_spatial_search_event", "session_id IS NOT NULL"])
        return self.connection.execute(
            f"""
            WITH staged AS (
                SELECT
                    session_id,
                    CASE
                        WHEN ui_path = 'eui.body-ui.spatial-search-button' THEN '1. Open spatial search'
                        WHEN ui_path = 'eui.body-ui.spatial-search-config.continue' THEN '3. Continue'
                        WHEN ui_path LIKE 'eui.body-ui.spatial-search-config.%' THEN '2. Configure search'
                        WHEN ui_path LIKE 'eui.body-ui.spatial-search.results.%'
                          OR ui_path = 'eui.body-ui.spatial-search.scene' THEN '4. Review results'
                        WHEN ui_path LIKE 'eui.body-ui.spatial-search.buttons.%' THEN '5. Apply or reset'
                        ELSE NULL
                    END AS funnel_stage
                FROM events_normalized
                WHERE {where_sql}
            )
            SELECT
                funnel_stage,
                COUNT(DISTINCT session_id) AS session_count
            FROM staged
            WHERE funnel_stage IS NOT NULL
            GROUP BY 1
            ORDER BY funnel_stage
            """
        ).fetchdf()

    def eui_spatial_organs(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(
            filters,
            [
                "app_name = 'ccf-eui'",
                "ui_path LIKE 'eui.body-ui.spatial-search-config.organ-sex-selection.organ.%'",
                "ui_path NOT LIKE '%search'",
            ],
        )
        return self.connection.execute(
            f"""
            SELECT
                regexp_extract(ui_path, '^eui\\.body-ui\\.spatial-search-config\\.organ-sex-selection\\.organ\\.([^.]+)$', 1) AS organ_name,
                COUNT(*) AS selection_count
            FROM events_normalized
            WHERE {where_sql}
            GROUP BY 1
            HAVING organ_name IS NOT NULL AND organ_name <> ''
            ORDER BY selection_count DESC
            """
        ).fetchdf()

    def eui_spatial_keyboard_usage(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(
            filters,
            [
                "app_name = 'ccf-eui'",
                "(ui_path LIKE 'eui.body-ui.spatial-search.keyboard.%' OR ui_path LIKE 'eui.body-ui.spatial-search.keyboard-ui.%')",
            ],
        )
        return self.connection.execute(
            f"""
            SELECT
                regexp_extract(ui_path, '([qweasd])$', 1) AS key_name,
                COUNT(*) AS key_count
            FROM events_normalized
            WHERE {where_sql}
            GROUP BY 1
            HAVING key_name IS NOT NULL AND key_name <> ''
            ORDER BY key_count DESC
            """
        ).fetchdf()

    def cde_funnel(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(filters, ["app_name = 'cde-ui'", "session_id IS NOT NULL"])
        return self.connection.execute(
            f"""
            WITH staged AS (
                SELECT
                    session_id,
                    CASE
                        WHEN event_name = 'pageView'
                          AND regexp_matches(lower(COALESCE(page_url, '')), '/cde/?$') THEN '1. Landing page'
                        WHEN event_name = 'pageView' AND lower(COALESCE(page_url, '')) LIKE '%/cde/create%' THEN '2. Create page'
                        WHEN ui_path = 'cde-ui.create-visualization-page.visualize-data.submit' THEN '3. Submit visualization'
                        WHEN event_name = 'pageView' AND lower(COALESCE(page_url, '')) LIKE '%/cde/visualize%' THEN '4. Visualize output'
                        ELSE NULL
                    END AS funnel_stage
                FROM events_normalized
                WHERE {where_sql}
            )
            SELECT
                funnel_stage,
                COUNT(DISTINCT session_id) AS session_count
            FROM staged
            WHERE funnel_stage IS NOT NULL
            GROUP BY 1
            ORDER BY funnel_stage
            """
        ).fetchdf()

    def cde_pageview_summary(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(filters, ["app_name = 'cde-ui'", "event_name = 'pageView'"])
        return self.connection.execute(
            f"""
            SELECT
                page_url,
                COUNT(*) AS pageview_count
            FROM events_normalized
            WHERE {where_sql}
            GROUP BY 1
            HAVING page_url IS NOT NULL
            ORDER BY pageview_count DESC
            """
        ).fetchdf()

    def cde_download_candidates(self, filters: DashboardFilters) -> pd.DataFrame:
        where_sql = self._event_where(filters, ["app_name = 'cde-ui'"])
        return self.connection.execute(
            f"""
            SELECT
                ui_path,
                event_name,
                COUNT(*) AS event_count
            FROM events_normalized
            WHERE {where_sql}
              AND (
                lower(COALESCE(ui_path, '')) LIKE '%download%'
                OR lower(COALESCE(ui_path, '')) LIKE '%violin%'
                OR lower(COALESCE(ui_path, '')) LIKE '%histogram%'
              )
            GROUP BY 1, 2
            ORDER BY event_count DESC
            """
        ).fetchdf()

    def performance_site_summary(self, start_date: date, end_date: date, sites: list[str] | None = None) -> pd.DataFrame:
        clauses = [self._date_where(start_date, end_date, "request_date")]
        if sites:
            site_list = ", ".join(_sql_literal(site) for site in sites)
            clauses.append(f"site IN ({site_list})")
        where_sql = " AND ".join(clauses)
        return self.connection.execute(
            f"""
            SELECT
                site,
                SUM(total_requests) AS total_requests,
                SUM(cache_served_requests) AS cache_served_requests,
                ROUND(100.0 * SUM(cache_served_requests) / NULLIF(SUM(total_requests), 0), 2) AS cache_served_pct,
                ROUND(SUM(miss_requests) * 100.0 / NULLIF(SUM(total_requests), 0), 2) AS miss_pct,
                ROUND(SUM(error_requests) * 100.0 / NULLIF(SUM(total_requests), 0), 2) AS error_pct,
                AVG(avg_ttfb) AS avg_ttfb,
                AVG(avg_time_taken) AS avg_time_taken
            FROM site_performance_daily
            WHERE {where_sql}
            GROUP BY 1
            ORDER BY total_requests DESC
            """
        ).fetchdf()

    def performance_site_trend(self, start_date: date, end_date: date, sites: list[str] | None = None) -> pd.DataFrame:
        clauses = [self._date_where(start_date, end_date, "request_date")]
        if sites:
            site_list = ", ".join(_sql_literal(site) for site in sites)
            clauses.append(f"site IN ({site_list})")
        where_sql = " AND ".join(clauses)
        return self.connection.execute(
            f"""
            SELECT
                request_date,
                site,
                ROUND(100.0 * SUM(cache_served_requests) / NULLIF(SUM(total_requests), 0), 2) AS cache_served_pct,
                AVG(avg_ttfb) AS avg_ttfb,
                AVG(avg_time_taken) AS avg_time_taken
            FROM site_performance_daily
            WHERE {where_sql}
            GROUP BY 1, 2
            ORDER BY 1, 2
            """
        ).fetchdf()

    def performance_app_summary(self, start_date: date, end_date: date, apps: list[str] | None = None) -> pd.DataFrame:
        clauses = [self._date_where(start_date, end_date, "request_date")]
        if apps:
            app_list = ", ".join(_sql_literal(app) for app in apps)
            clauses.append(f"app_name IN ({app_list})")
        where_sql = " AND ".join(clauses)
        return self.connection.execute(
            f"""
            SELECT
                app_name,
                SUM(total_requests) AS total_requests,
                SUM(cache_served_requests) AS cache_served_requests,
                ROUND(100.0 * SUM(cache_served_requests) / NULLIF(SUM(total_requests), 0), 2) AS cache_served_pct,
                ROUND(SUM(miss_requests) * 100.0 / NULLIF(SUM(total_requests), 0), 2) AS miss_pct,
                ROUND(SUM(error_requests) * 100.0 / NULLIF(SUM(total_requests), 0), 2) AS error_pct,
                AVG(avg_ttfb) AS avg_ttfb,
                AVG(avg_time_taken) AS avg_time_taken
            FROM app_page_performance_daily
            WHERE {where_sql}
            GROUP BY 1
            ORDER BY total_requests DESC
            """
        ).fetchdf()
