from __future__ import annotations

import pandas as pd
import streamlit as st

from humanatlas_dashboard.charts import bar_chart, donut_chart, funnel_chart, heatmap_chart, histogram, line_chart, scatter_chart
from humanatlas_dashboard.data_access import DashboardFilters, DashboardRepository


def inject_theme() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(15, 118, 110, 0.18), transparent 28%),
                    radial-gradient(circle at top right, rgba(249, 115, 22, 0.14), transparent 24%),
                    #f5f3ef;
            }
            [data-testid="stMetric"] {
                background: rgba(255, 255, 255, 0.88);
                border: 1px solid rgba(15, 118, 110, 0.12);
                padding: 0.9rem 1rem;
                border-radius: 18px;
            }
            .note-card {
                background: rgba(255,255,255,0.86);
                border-left: 4px solid #0F766E;
                padding: 0.9rem 1rem;
                border-radius: 12px;
                margin-top: 1rem;
            }
            .section-intro {
                background: rgba(255,255,255,0.82);
                padding: 0.85rem 1rem;
                border-radius: 14px;
                border: 1px solid rgba(22, 78, 99, 0.12);
                margin-bottom: 1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_section_intro(question: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="section-intro">
            <strong>{question}</strong><br/>
            {description}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _extract_ui_path_segment(path: str) -> str:
    if not path or pd.isna(path):
        return path
    parts = path.split('.')
    if len(parts) > 1:
        return '.'.join(parts[1:])
    return path


def render_overview_tab(repository: DashboardRepository, filters: DashboardFilters) -> None:
    metrics = repository.overview_metrics(filters)
    trend = repository.overview_event_trend(filters)
    event_mix = repository.event_type_distribution(filters)
    _render_section_intro(
        "Overview",
        "This dashboard is driven by the Human Reference Atlas event logs only for behavioral questions, with bot and AI-bot traffic excluded. Paths are normalized from both `path` and `e.path` so older and newer instrumentation are counted together.",
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Human Events", f"{int(metrics['total_events']):,}")
    c2.metric("Sessions", f"{int(metrics['total_sessions']):,}")
    c3.metric("Tracked Apps", f"{int(metrics['active_apps']):,}")
    c4.metric("Cache-Served Requests", f"{metrics['cache_hit_rate']:.1f}%")

    trend = trend[~trend["app_name"].isin(["Unspecified", "asct+b-reporter"])]
    event_mix = event_mix[~event_mix["event_name"].isin(["Unspecified", "test2", "test"])]

    left, right = st.columns((1.65, 1.0))
    with left:
        if not trend.empty:
            trend_apps = sorted(trend["app_name"].unique().tolist())
            trend_tabs = st.tabs(trend_apps)
            for app, tab in zip(trend_apps, trend_tabs):
                with tab:
                    app_trend = trend[trend["app_name"] == app]
                    st.plotly_chart(
                        line_chart(app_trend, "event_month", "event_count", title=f"{app} Monthly Events",
                                  x_label="Date", y_label="Event Count"),
                        use_container_width=True,
                    )
    with right:
        fig = bar_chart(event_mix, "event_name", "event_count", title="Overall Event Mix",
                       x_label="Event Name", y_label="Event Count")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    guide = pd.DataFrame(
        [
            ["Event Frequency", "Counts and monthly distribution of clicks, hovers, pageviews, errors, and model changes."],
            ["UI Element Usage", "Top and under-used UI paths, plus click density by app section."],
            ["RUI Opacity", "All RUI interactions whose path contains `opacity`."],
            ["EUI Spatial Search", "Spatial-search workflow, funnel drop-off, organ selection, and keyboard behavior."],
            ["CDE Downloads", "Instrumented CDE flow with an explicit tracking-gap callout for plot downloads."],
            ["Performance", "Cache-served rate, misses, errors, and latency by HRA site and app page."],
        ],
        columns=["Section", "What it answers"],
    )
    st.dataframe(guide, use_container_width=True, hide_index=True)


def render_event_frequency_tab(repository: DashboardRepository, filters: DashboardFilters) -> None:
    event_mix = repository.event_type_distribution(filters)
    by_app = repository.event_type_by_app(filters)
    session_distribution = repository.session_event_distribution(filters)
    monthly = repository.overview_event_trend(filters)
    _render_section_intro(
        "RQ1. What is the distribution of frequency of user events?",
        "This section shows the mix of event types, how the mix changes by app, and whether activity is broadly distributed or concentrated into a smaller number of sessions.",
    )

    event_mix = event_mix[~event_mix["event_name"].isin(["Unspecified", "test2", "test"])]
    busiest_event = str(event_mix.iloc[0]["event_name"]) if not event_mix.empty else "N/A"
    total_events = int(event_mix["event_count"].sum()) if not event_mix.empty else 0
    median_per_session = float(session_distribution["event_count"].median()) if not session_distribution.empty else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Events", f"{total_events:,}")
    c2.metric("Median Events per Session", f"{median_per_session:.1f}")
    c3.metric("Most Common Event", busiest_event)

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            bar_chart(event_mix, "event_name", "event_count", title="Event Type Distribution",
                     x_label="Event Name", y_label="Event Count"),
            use_container_width=True,
        )
    with right:
        sd = session_distribution.copy()
        bins = [0, 5, 20, 50, float("inf")]
        labels = ["1–5 events", "6–20 events", "21–50 events", "51+ events"]
        sd["intensity_bucket"] = pd.cut(sd["event_count"], bins=bins, labels=labels)
        bucket_counts = sd.groupby("intensity_bucket", observed=True)["session_id"].count().reset_index()
        bucket_counts.columns = ["intensity_bucket", "session_count"]
        st.plotly_chart(
            bar_chart(bucket_counts, "intensity_bucket", "session_count", title="Session Event Intensity",
                     x_label="Event Intensity Range", y_label="Number of Sessions"),
            use_container_width=True,
        )

    by_app_clean = by_app[~by_app["event_name"].isin(["Unspecified", "test2", "test"])]
    st.plotly_chart(
        bar_chart(
            by_app_clean,
            "app_name",
            "event_count",
            "event_name",
            "Event Mix by App",
            barmode="stack",
            x_label="App Name",
            y_label="Event Count",
        ),
        use_container_width=True,
    )
    monthly = monthly[~monthly["app_name"].isin(["Unspecified", "asct+b-reporter"])]
    monthly_fig = line_chart(monthly, "event_month", "event_count", "app_name", "Monthly Event Volume",
                            x_label="Event Date", y_label="Event Count")
    monthly_fig.update_xaxes(nticks=4, tickformat="%b %Y")
    st.plotly_chart(monthly_fig, use_container_width=True)
    st.dataframe(by_app, use_container_width=True, hide_index=True)


def render_ui_element_usage_tab(repository: DashboardRepository, filters: DashboardFilters) -> None:
    clicks = repository.ui_click_usage(filters)
    hovers = repository.ui_hover_usage(filters)
    heatmap = repository.ui_section_heatmap(filters)
    _render_section_intro(
        "RQ2. Which UI elements were used frequently and not frequently?",
        "Usage is driven primarily by click paths, with hover behavior included to show features people notice but do not always activate.",
    )

    click_totals = clicks.groupby("ui_path", as_index=False)["click_count"].sum().sort_values("click_count", ascending=False)
    underused = click_totals.loc[click_totals["click_count"] < 5].sort_values("click_count", ascending=True)
    top_element = str(click_totals.iloc[0]["ui_path"]) if not click_totals.empty else "N/A"
    c1, c2, c3 = st.columns(3)
    c1.metric("Clicked Paths", f"{click_totals['ui_path'].nunique():,}" if not click_totals.empty else "0")
    c2.metric("Top Clicked Element", top_element)
    c3.metric("Under-used Elements (<5 clicks)", f"{len(underused):,}")

    st.markdown("### Overall Top 10 Clicked UI Paths (All Apps)")
    st.plotly_chart(
        bar_chart(click_totals.head(10), "ui_path", "click_count", title="Top 10 Clicked UI Paths",
                 x_label="UI Element", y_label="Click Count"),
        use_container_width=True,
    )

    st.markdown("### Usage by App")
    _CORE_APPS = ["ccf-rui", "ccf-eui", "cde-ui", "kg-explorer"]
    app_tabs = st.tabs(_CORE_APPS)

    for app, tab in zip(_CORE_APPS, app_tabs):
        with tab:
            app_clicks = clicks[clicks["app_name"] == app]
            app_hovers = hovers[hovers["app_name"] == app]

            if not app_clicks.empty:
                click_totals_app = app_clicks.groupby("ui_path", as_index=False)["click_count"].sum().sort_values("click_count", ascending=False)
                click_totals_app["ui_element"] = click_totals_app["ui_path"].apply(_extract_ui_path_segment)

                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(
                        bar_chart(click_totals_app.head(10), "ui_element", "click_count",
                                 title=f"{app.upper()} - Top 10 Clicked Elements",
                                 x_label="UI Element", y_label="Click Count"),
                        use_container_width=True,
                    )

                underused_app = click_totals_app.loc[click_totals_app["click_count"] < 5].sort_values("click_count", ascending=True)
                with col2:
                    if not underused_app.empty:
                        st.plotly_chart(
                            bar_chart(underused_app.head(10), "ui_element", "click_count",
                                     title=f"{app.upper()} - Lowest-Use Elements",
                                     x_label="UI Element", y_label="Click Count"),
                            use_container_width=True,
                        )
                    else:
                        st.info("No under-used elements (all elements have 5+ clicks)")

            if not app_hovers.empty:
                hover_totals_app = app_hovers.groupby("ui_path", as_index=False)["hover_count"].sum().sort_values("hover_count", ascending=False)
                hover_totals_app["ui_element"] = hover_totals_app["ui_path"].apply(_extract_ui_path_segment)
                st.plotly_chart(
                    bar_chart(hover_totals_app.head(10), "ui_element", "hover_count",
                             title=f"{app.upper()} - Top 10 Hovered Elements",
                             x_label="UI Element", y_label="Hover Count"),
                    use_container_width=True,
                )

    st.markdown("### Click Density by App Section")
    _CORE_APPS_LIST = ["ccf-rui", "ccf-eui", "cde-ui", "kg-explorer"]
    if not heatmap.empty:
        all_heatmap_apps = sorted(heatmap["app_name"].unique().tolist())
        other_apps = [a for a in all_heatmap_apps if a not in _CORE_APPS_LIST]
        selected_heatmap_apps = st.multiselect(
            "Filter apps",
            options=_CORE_APPS_LIST + other_apps,
            default=_CORE_APPS_LIST,
            key="ui_heatmap_apps",
        )
        heatmap_filtered = heatmap[heatmap["app_name"].isin(selected_heatmap_apps)]
        st.plotly_chart(
            heatmap_chart(heatmap_filtered, "ui_section", "app_name", "click_count",
                         "Click Density by App Section", x_label="UI Section", y_label="App"),
            use_container_width=True,
        )


def render_rui_opacity_tab(repository: DashboardRepository, filters: DashboardFilters) -> None:
    opacity = repository.rui_opacity_details(filters)
    total_rui_events, opacity_events = repository.rui_event_totals(filters)
    _render_section_intro(
        "RQ3. How often was opacity changed in the RUI?",
        "The logic counts any human RUI event whose normalized path contains `opacity`. This captures the master opacity toggle plus anatomical-structure and landmark opacity controls.",
    )

    share = (opacity_events / total_rui_events * 100) if total_rui_events else 0
    top_target = (
        opacity.dropna(subset=["target_name"]).groupby("target_name")["opacity_count"].sum().sort_values(ascending=False).index[0]
        if not opacity.dropna(subset=["target_name"]).empty
        else "N/A"
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Opacity Events", f"{opacity_events:,}")
    c2.metric("Share of RUI Events", f"{share:.1f}%")
    c3.metric("Top Affected Target", str(top_target))

    by_group = opacity.groupby("opacity_group", as_index=False)["opacity_count"].sum().sort_values("opacity_count", ascending=False)
    by_target = opacity.dropna(subset=["target_name"]).groupby("target_name", as_index=False)["opacity_count"].sum().sort_values("opacity_count", ascending=False)
    by_day = opacity.groupby("event_date", as_index=False)["opacity_count"].sum()
    by_month = opacity.copy()
    by_month["event_month"] = pd.to_datetime(by_month["event_date"]).dt.to_period("M").dt.to_timestamp()
    by_month = by_month.groupby("event_month", as_index=False)["opacity_count"].sum()

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            bar_chart(by_group.head(5), "opacity_group", "opacity_count", title="Top 5 Opacity Control Types",
                     x_label="Control Type", y_label="Count"),
            use_container_width=True,
        )
    with right:
        st.plotly_chart(
            line_chart(by_month, "event_month", "opacity_count", title="Opacity Interactions Over Time (Monthly)",
                      x_label="Month", y_label="Count"),
            use_container_width=True,
        )

    if not by_target.empty:
        st.plotly_chart(
            bar_chart(by_target.head(5), "target_name", "opacity_count", title="Top 5 Anatomical Structures / Landmarks",
                     x_label="Structure/Landmark", y_label="Count"),
            use_container_width=True,
        )
    st.dataframe(opacity, use_container_width=True, hide_index=True)


def render_eui_spatial_search_tab(repository: DashboardRepository, filters: DashboardFilters) -> None:
    details = repository.eui_spatial_details(filters)
    funnel = repository.eui_spatial_funnel(filters)
    organs = repository.eui_spatial_organs(filters)
    keyboard = repository.eui_spatial_keyboard_usage(filters)
    _render_section_intro(
        "RQ4. How often was spatial search used in the EUI?",
        "Spatial-search usage is identified from normalized EUI paths containing `spatial-search`, then grouped into workflow stages to show both total interaction volume and where users drop off.",
    )

    total_events = int(len(details.index))
    total_sessions = int(details["session_id"].dropna().nunique()) if not details.empty else 0
    peak_stage = str(funnel.sort_values("session_count", ascending=False).iloc[0]["funnel_stage"]) if not funnel.empty else "N/A"
    c1, c2, c3 = st.columns(3)
    c1.metric("Spatial-Search Events", f"{total_events:,}")
    c2.metric("Sessions with Spatial Search", f"{total_sessions:,}")
    c3.metric("Largest Funnel Stage", peak_stage)

    left, right = st.columns(2)
    with left:
        if not funnel.empty:
            st.plotly_chart(
                funnel_chart(funnel, "funnel_stage", "session_count", title="Spatial Search Funnel by Session"),
                use_container_width=True,
            )
    with right:
        if not organs.empty:
            st.plotly_chart(
                bar_chart(organs.head(10), "organ_name", "selection_count", title="Most Selected Organs",
                         x_label="Organ", y_label="Selection Count"),
                use_container_width=True,
            )

    if not keyboard.empty:
        st.plotly_chart(
            bar_chart(keyboard, "key_name", "key_count", title="Spatial Search Keyboard Usage",
                     x_label="Key", y_label="Count"),
            use_container_width=True,
        )

    st.dataframe(details, use_container_width=True, hide_index=True)


def render_cde_downloads_tab(repository: DashboardRepository, filters: DashboardFilters) -> None:
    funnel = repository.cde_funnel(filters)
    pageviews = repository.cde_pageview_summary(filters)
    candidates = repository.cde_download_candidates(filters)
    _render_section_intro(
        "RQ5. How often were the histograms and violin plots in the CDE downloaded?",
        "The current event logs support the CDE workflow up to visualization generation, but they do not show actual histogram or violin-plot download events. This section makes that instrumentation gap explicit.",
    )

    total_candidates = int(candidates["event_count"].sum()) if not candidates.empty else 0
    visualize_views = int(
        pageviews.loc[pageviews["page_url"].fillna("").str.contains("/cde/visualize", case=False), "pageview_count"].sum()
    ) if not pageviews.empty else 0
    submit_clicks = 0
    if not funnel.empty:
        submit_row = funnel.loc[funnel["funnel_stage"] == "3. Submit visualization", "session_count"]
        submit_clicks = int(submit_row.iloc[0]) if not submit_row.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Tracked Download Events", f"{total_candidates:,}")
    c2.metric("Visualize Page Views", f"{visualize_views:,}")
    c3.metric("Submit Visualization Sessions", f"{submit_clicks:,}")

    st.warning(
        "No direct histogram or violin-plot download events are present in the current tracking data. The dashboard therefore answers this question as an instrumentation gap, not as a positive count of downloads."
    )

    pageviews_clean = pageviews[~pageviews["page_url"].str.contains("localhost", na=False)]

    left, right = st.columns(2)
    with left:
        if not funnel.empty:
            st.plotly_chart(
                funnel_chart(funnel, "funnel_stage", "session_count", title="CDE Workflow Funnel"),
                use_container_width=True,
            )
    with right:
        if not pageviews_clean.empty:
            st.plotly_chart(
                bar_chart(pageviews_clean.head(10), "page_url", "pageview_count", title="Tracked CDE Page Views",
                         x_label="Page URL", y_label="Pageviews"),
                use_container_width=True,
            )

    st.dataframe(pageviews_clean, use_container_width=True, hide_index=True)


def render_performance_tab(repository: DashboardRepository, filters: DashboardFilters) -> None:
    options = repository.get_performance_filter_options()
    _render_section_intro(
        "Performance and cache behavior",
        "Performance is computed from the full HRA request logs with bot and AI-bot traffic removed. Cache-served requests are defined as CloudFront `Hit` or `RefreshHit` responses; misses, errors, and latency are shown alongside them.",
    )

    with st.container():
        left_filter, right_filter = st.columns(2)
        selected_sites = left_filter.multiselect("Sites", options.sites, default=options.sites, key="perf_sites")
        selected_apps = right_filter.multiselect("Apps Site Pages", options.apps, default=options.apps, key="perf_apps")

    site_summary = repository.performance_site_summary(filters.start_date, filters.end_date, selected_sites)
    site_trend = repository.performance_site_trend(filters.start_date, filters.end_date, selected_sites)
    app_summary = repository.performance_app_summary(filters.start_date, filters.end_date, selected_apps)

    avg_cache = float(site_summary["cache_served_pct"].mean()) if not site_summary.empty else 0
    avg_ttfb = float(site_summary["avg_ttfb"].mean()) if not site_summary.empty else 0
    avg_time = float(site_summary["avg_time_taken"].mean()) if not site_summary.empty else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Cache-Served Rate", f"{avg_cache:.1f}%")
    c2.metric("Avg Time to First Byte", f"{avg_ttfb:.3f}s")
    c3.metric("Avg Total Time", f"{avg_time:.3f}s")

    st.markdown("#### Cache-Served Rate by Site")
    st.markdown("Percentage of requests served from cache (CloudFront Hit/RefreshHit) vs. fetched from origin.")
    if not site_summary.empty:
        st.plotly_chart(
            bar_chart(site_summary, "site", "cache_served_pct", title="Cache-Served Rate by Site",
                     x_label="Site", y_label="Cache-Served Rate (%)"),
            use_container_width=True,
        )

    st.markdown("#### Daily Cache-Served Rate Trend")
    st.markdown("How cache-served rate changed over time for each site.")
    if not site_trend.empty:
        st.plotly_chart(
            line_chart(site_trend, "request_date", "cache_served_pct", "site", "Daily Cache-Served Rate",
                      x_label="Date", y_label="Cache-Served Rate (%)"),
            use_container_width=True,
        )

    st.markdown("#### Apps Site Performance Map")
    st.markdown("Scatter plot showing response time vs. total time for each app. Bubble size indicates total requests.")
    if not app_summary.empty:
        st.plotly_chart(
            scatter_chart(
                app_summary,
                "avg_ttfb",
                "avg_time_taken",
                "app_name",
                "total_requests",
                "Apps Site Performance Map",
                x_label="Response Time (s)",
                y_label="Total Time (s)",
            ),
            use_container_width=True,
        )

    st.dataframe(site_summary, use_container_width=True, hide_index=True)
    st.dataframe(app_summary, use_container_width=True, hide_index=True)
