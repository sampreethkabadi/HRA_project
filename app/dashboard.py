from __future__ import annotations

import argparse
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humanatlas_dashboard.config import load_settings
from humanatlas_dashboard.data_access import DashboardRepository, DashboardFilters
from humanatlas_dashboard.sections import (
    inject_theme,
    render_cde_downloads_tab,
    render_eui_spatial_search_tab,
    render_event_frequency_tab,
    render_overview_tab,
    render_performance_tab,
    render_rui_opacity_tab,
    render_ui_element_usage_tab,
)


def _parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config", default="config/humanatlas.yml")
    args, _ = parser.parse_known_args(sys.argv[1:])
    return args


@st.cache_resource(show_spinner=False)
def get_repository(config_path: str) -> DashboardRepository:
    settings = load_settings(config_path)
    return DashboardRepository(settings)


def main() -> None:
    args = _parse_cli_args()
    repository = get_repository(args.config)

    st.set_page_config(
        page_title="Human Atlas Research Dashboard",
        page_icon="HA",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_theme()

    st.title("Human Atlas Research Dashboard")
    st.caption(
        "Research-focused telemetry dashboard built on DuckDB and parquet for Human Atlas interactions."
    )

    filter_options = repository.get_filter_options()
    with st.sidebar:
        st.markdown("### Global Filters")
        selected_apps = st.multiselect(
            "Event apps",
            options=filter_options.apps,
            default=filter_options.apps,
        )
        date_range = st.date_input(
            "Date range",
            value=(filter_options.min_date, filter_options.max_date),
            min_value=filter_options.min_date,
            max_value=filter_options.max_date,
        )
        st.markdown(
            """
            <div class="note-card">
              <strong>Methodology</strong><br/>
              Event tabs use normalized `Events` rows with `Bot` and `AI-Assistant / Bot` traffic excluded. Performance is derived from request-level cache fields in the same parquet.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if isinstance(date_range, tuple):
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range
    filters = DashboardFilters(apps=selected_apps, start_date=start_date, end_date=end_date)

    tabs = st.tabs(
        [
            "Overview",
            "Event Frequency",
            "UI Element Usage",
            "RUI Opacity",
            "EUI Spatial Search",
            "CDE Downloads",
            "Performance",
        ]
    )

    with tabs[0]:
        render_overview_tab(repository, filters)
    with tabs[1]:
        render_event_frequency_tab(repository, filters)
    with tabs[2]:
        render_ui_element_usage_tab(repository, filters)
    with tabs[3]:
        render_rui_opacity_tab(repository, filters)
    with tabs[4]:
        render_eui_spatial_search_tab(repository, filters)
    with tabs[5]:
        render_cde_downloads_tab(repository, filters)
    with tabs[6]:
        render_performance_tab(repository, filters)


if __name__ == "__main__":
    main()
