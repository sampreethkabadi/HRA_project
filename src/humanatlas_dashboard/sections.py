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


def _render_insight_card(title: str, issue: str, impact: str, recommendation: str, priority: str) -> None:
    """Render an insight card with Issue | Impact | Recommendation structure"""
    priority_colors = {
        'CRITICAL': '#C00000',
        'HIGH': '#FFC000',
        'MEDIUM': '#0070C0',
        'LOW': '#00B050'
    }
    color = priority_colors.get(priority, '#000000')

    html = f"""
    <div style="border-left: 5px solid {color}; background-color: #F2F2F2; padding: 15px; margin-bottom: 15px; border-radius: 4px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h4 style="margin: 0; color: #333;">{title}</h4>
            <span style="background-color: {color}; color: white; padding: 4px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{priority}</span>
        </div>
        <div style="margin-bottom: 10px;">
            <strong style="color: #0070C0;">Issue:</strong> {issue}
        </div>
        <div style="margin-bottom: 10px;">
            <strong style="color: #0070C0;">Impact:</strong> {impact}
        </div>
        <div>
            <strong style="color: #0070C0;">Recommendation:</strong> {recommendation}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def _render_insights_panel(insights_list: list) -> None:
    """Render insights in a popover panel"""
    with st.popover("📊 View Actionable Insights", use_container_width=True):
        st.markdown("### Actionable Insights")

        # Count by priority
        critical = sum(1 for i in insights_list if i['priority'] == 'CRITICAL')
        high = sum(1 for i in insights_list if i['priority'] == 'HIGH')
        medium = sum(1 for i in insights_list if i['priority'] == 'MEDIUM')
        low = sum(1 for i in insights_list if i['priority'] == 'LOW')

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Critical", critical)
        col2.metric("High", high)
        col3.metric("Medium", medium)
        col4.metric("Low", low)

        st.divider()

        # Create tabs by priority
        priorities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        tabs = st.tabs([p for p in priorities if sum(1 for i in insights_list if i['priority'] == p) > 0])

        tab_index = 0
        for priority in priorities:
            priority_insights = [i for i in insights_list if i['priority'] == priority]
            if not priority_insights:
                continue

            with tabs[tab_index]:
                for insight in priority_insights:
                    _render_insight_card(
                        insight['title'],
                        insight['issue'],
                        insight['impact'],
                        insight['recommendation'],
                        insight['priority']
                    )
            tab_index += 1


def render_overview_tab(repository: DashboardRepository, filters: DashboardFilters) -> None:
    metrics = repository.overview_metrics(filters)
    trend = repository.overview_event_trend(filters)
    event_mix = repository.event_type_distribution(filters)
    _render_section_intro(
        "Overview",
        "This dashboard is driven by the Human Reference Atlas event logs only for behavioral questions, with bot and AI-bot traffic excluded. Paths are normalized from both `path` and `e.path` so older and newer instrumentation are counted together.",
    )

    overview_insights = [
        {'title': 'Error Rate Threatens User Experience', 'issue': '23% of all platform events are errors, indicating systemic stability issues affecting all apps.', 'impact': 'Users encountering errors abandon workflows, reduce session depth, and may churn. Error rate erodes trust in platform reliability.', 'recommendation': 'Implement centralized error monitoring dashboard. Conduct root cause analysis on top 10 error types. Set target to reduce error rate to <5% within 60 days.', 'priority': 'CRITICAL'},
        {'title': 'KG-Explorer Dominates but Risks Over-Dependency', 'issue': 'KG-Explorer accounts for 27% of all platform events (21.9K) and 34% of sessions. Creates over-concentration of traffic on single app.', 'impact': 'If KG-Explorer experiences downtime, 27% of platform activity is impacted. Business risk if only app is generating ROI.', 'recommendation': 'Develop contingency plans for KG-Explorer failures. Analyze what drives KG-Explorer success and replicate patterns in other apps.', 'priority': 'HIGH'},
        {'title': 'HumanAtlas.io Has High Sessions but Low Engagement Depth', 'issue': 'HumanAtlas.io generates 18.8K events across 2.5K sessions (highest session count) but lower events/session ratio than KG-Explorer.', 'impact': 'Users are visiting frequently but not engaging deeply, suggesting shallow interactions or incomplete workflows.', 'recommendation': 'Analyze user journeys in HumanAtlas.io. Identify drop-off points. Test UI/UX improvements to increase engagement per session.', 'priority': 'MEDIUM'},
        {'title': 'Secondary Apps Underutilized Relative to Investment', 'issue': '15 apps tracked but only 4 drive 80% of traffic. Remaining 11 apps likely receiving minimal user attention despite maintenance costs.', 'impact': 'Resources spent maintaining underutilized apps reduce ROI. Users may not discover features because apps are not discoverable.', 'recommendation': 'Conduct feature usage audit for bottom 5 apps. Either promote these apps, consolidate features, or sunset if no clear use case.', 'priority': 'MEDIUM'},
    ]
    _render_insights_panel(overview_insights)

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
    st.markdown("### Dashboard Guide")
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

    event_freq_insights = [
        {'title': 'Error Events (23% of Total) Indicate Broken Workflows', 'issue': 'Errors represent 25.8K events out of 111K total. Errors are not isolated incidents but regular occurrence affecting user experience.', 'impact': 'Every error represents a user attempting an action that failed. High error rate reduces productivity, frustrates users, and signals unfinished features.', 'recommendation': 'Segment errors by app and error type. Create error log analysis dashboard. Prioritize fixing top 3 error types. Track error rate weekly.', 'priority': 'CRITICAL'},
        {'title': '61% of Sessions Are Low-Intensity (1-5 Events)', 'issue': 'Majority of sessions have 5 or fewer events, suggesting quick lookups, search queries, or incomplete interactions.', 'impact': 'Low-intensity sessions may indicate users are not finding what they need or are abandoning workflows due to friction.', 'recommendation': 'Conduct user research on low-intensity sessions. Test onboarding flows, tooltips, and quick-start guides. Create breadcrumb trails for returning users.', 'priority': 'HIGH'},
        {'title': 'Power Users (5% of Sessions) Are Underutilized Asset', 'issue': 'Only 5% of sessions exceed 50 events. These power users represent deep engagement and understand platform value.', 'impact': 'Power users can provide feedback on features, use cases, and pain points. Their behavioral patterns indicate most effective workflows.', 'recommendation': 'Identify power user cohort. Conduct interviews on what drives their engagement. Create advanced features targeting power users.', 'priority': 'MEDIUM'},
        {'title': 'Hover Behavior Shows Feature Discovery Gap', 'issue': 'Hovers account for 21% of events but only 35% result in clicks. Many hover events do not convert to interaction.', 'impact': 'Features that users hover over but do not click suggest unclear purpose, unintuitive interaction, or low perceived value.', 'recommendation': 'Conduct A/B tests on hover-to-click conversion. Improve hover labels/tooltips. Track which hovered features convert highest.', 'priority': 'MEDIUM'},
    ]
    _render_insights_panel(event_freq_insights)

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

    ui_insights = [
        {'title': 'RUI 3D Viewer is Critical Path', 'issue': '3D stage viewer accounts for 1.2K clicks (90% of all RUI clicks), far exceeding other elements.', 'impact': 'RUI is effectively a 3D viewer app. Performance issues with 3D directly impact user satisfaction. No fallback engagement.', 'recommendation': 'Implement aggressive performance monitoring on 3D viewer. Profile load times. Optimize rendering. Set alerts for latency spikes.', 'priority': 'CRITICAL'},
        {'title': 'CDE Workflow Has Strong Upload Adoption', 'issue': 'File upload is most-clicked element (163 clicks), and submit button (132 clicks) shows good conversion.', 'impact': 'Strong adoption of file upload indicates users understand data preparation workflow. This entry point is working effectively.', 'recommendation': 'Maintain and optimize file upload experience. Monitor performance. Consider batch uploads. Track upload success rates.', 'priority': 'LOW'},
        {'title': 'EUI Results Browsing Dominates Over Scene Interaction', 'issue': 'Results display (739 clicks: 372 donor cards + 367 selections) outweighs scene visualization (260 clicks).', 'impact': 'Users value results browsing and filtering over 3D visualization. Scene view may be secondary or less intuitive.', 'recommendation': 'Enhance EUI results filtering and refinement options. Create comparison view for multiple organs. Test alternative result layouts.', 'priority': 'HIGH'},
        {'title': 'KG-Explorer Navigation Over Configuration', 'issue': 'Link cell (753 clicks) is most-used element, followed by downloads (364). Configuration has low clicks.', 'impact': 'Users want to explore knowledge graph through links, not build complex queries. UX should prioritize navigation.', 'recommendation': 'Simplify advanced search builders. Promote link-based navigation. Implement recommendation engine for related entities.', 'priority': 'MEDIUM'},
        {'title': 'Download Functionality Is Important Cross-App Feature', 'issue': 'Download elements appear in top 3 for multiple apps (KG-Explorer 364, RUI, CDE).', 'impact': 'Users want to export/download data for use in external workflows. Download reliability directly impacts productivity.', 'recommendation': 'Create download feature specification. Test reliability across formats. Implement download history. Provide format options.', 'priority': 'MEDIUM'},
    ]
    _render_insights_panel(ui_insights)

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

    rui_opacity_insights = [
        {'title': 'Opacity is Advanced Feature with Niche Adoption', 'issue': 'Only 2.18% of RUI events involve opacity. 23% of RUI sessions interact with opacity. Feature has dedicated but small user base.', 'impact': 'Opacity is not core RUI workflow. Feature usage suggests it serves power users or specific use cases (anatomy research, medical education).', 'recommendation': 'Maintain opacity feature but do not invest in major enhancements. Ensure it remains discoverable. Monitor adoption trends.', 'priority': 'LOW'},
        {'title': 'Anatomical Structure Visibility Drives Opacity Usage', 'issue': 'Anatomical structure toggles (166 interactions) account for 81% of opacity interactions vs. landmarks (36).', 'impact': 'Users care about controlling visibility of anatomical components for focusing on specific organs/systems.', 'recommendation': 'Prioritize anatomical structure organization. Create pre-built organ visibility profiles (e.g., "Show only cardiac system").', 'priority': 'MEDIUM'},
        {'title': 'Master Opacity Toggle Is Rarely Used', 'issue': 'Master toggle for all opacity controls has only 4 interactions. Users prefer granular per-structure control.', 'impact': 'Master toggle adds UI complexity without delivering user value. Users want fine-grained control.', 'recommendation': 'Consider removing or hiding master toggle. Focus UI on individual structure toggles. Simplify opacity control panel.', 'priority': 'LOW'},
    ]
    _render_insights_panel(rui_opacity_insights)

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

    eui_insights = [
        {'title': 'CRITICAL: 41% Drop-Off in Setup Phase', 'issue': '66 sessions initiate spatial search but only 50 proceed to configuration (24% drop). Setup process is major barrier.', 'impact': 'Users interested in spatial search abandon before completing initial setup. Features cannot deliver value if users cannot set them up.', 'recommendation': 'Conduct UX audit of configuration flow. Test with new users. Simplify inputs. Add tooltips. Create wizard mode for first-time users.', 'priority': 'CRITICAL'},
        {'title': 'Configuration to Continue: 54% Drop-Off', 'issue': '50 sessions reach configuration, but only 27 proceed to "Continue" (46% drop). Setup validation or complexity is preventing progression.', 'impact': 'Users struggle with data entry validation or do not understand what constitutes valid configuration.', 'recommendation': 'Review error messages. Simplify validation. Provide examples. Create quick start with pre-filled example. Add progress indicator.', 'priority': 'HIGH'},
        {'title': 'Results to Apply Conversion is Low (29%)', 'issue': '24 sessions reach results but only 7 apply them (29% conversion). High preview abandonment suggests results satisfy users without apply.', 'impact': 'Either spatial search results are sufficient OR apply button is unclear. Users may not understand what happens after apply.', 'recommendation': 'Test apply button clarity. Investigate what happens after apply. Create before/after visualization. Track usage by user type.', 'priority': 'MEDIUM'},
        {'title': 'Organ Selection Tracking Shows Data Quality Issue', 'issue': '"Search" category returns 85 selections but actual organ selections are very low (kidney-l=8, heart=5). Tracking gap detected.', 'impact': 'Cannot accurately measure which organs users select. Tracking issue makes feature analysis unreliable. May indicate bug.', 'recommendation': 'Audit tracking implementation. Verify organ path parsing. Add logging for "search" category. Fix data pipeline.', 'priority': 'HIGH'},
    ]
    _render_insights_panel(eui_insights)

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

    cde_insights = [
        {'title': 'URGENT: Zero Download Events Tracked', 'issue': 'Despite 34 sessions reaching visualization page, zero histogram or violin plot downloads are recorded.', 'impact': 'Cannot measure CDE feature success, ROI, or user satisfaction. Business cannot justify CDE investment if impact is unmeasurable.', 'recommendation': 'URGENT: Implement download event tracking in CDE application. Instrument histogram/violin plot downloads. Target: live within 2 weeks.', 'priority': 'CRITICAL'},
        {'title': 'Data Upload to Visualization Funnel Shows 76% Drop-Off', 'issue': '143 users land on CDE, but only 34 reach visualization (76% drop). Majority abandon before reaching value.', 'impact': 'Workflow friction is preventing CDE usage. Upload or data selection steps are barriers to adoption.', 'recommendation': 'Segment drop-off by step. User test the upload flow. Simplify required fields. Provide data templates. Consider drag-and-drop upload.', 'priority': 'CRITICAL'},
        {'title': 'Submit to Visualization Conversion Is Strong (103%)', 'issue': 'Slight increase in session count from submit (33) to visualize (34). Users who complete submission tend to reach visualization.', 'impact': 'Submit step is the correct barrier point. Users can recover if they abandon early.', 'recommendation': 'Investigate the 103% conversion. Maintain current submit flow. Focus optimization on earlier steps.', 'priority': 'LOW'},
    ]
    _render_insights_panel(cde_insights)

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
        "No direct histogram or violin-plot download events are present in the current tracking data. Download event instrumentation is critical for measuring CDE success."
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

    perf_insights = [
        {'title': 'KG-Explorer Paradox: High Cache Rate but Slowest Latency', 'issue': 'KG-Explorer has 96.83% cache hit rate but worst total time (2.065s) and TTFB (0.368s). Cache misses are extremely slow.', 'impact': 'Cache misses (3% of requests) experience 2+ second waits. Users on cache miss paths experience poor experience.', 'recommendation': 'Profile KG-Explorer origin requests. Implement origin caching layer. Increase cache TTL if safe. Consider request batching.', 'priority': 'HIGH'},
        {'title': 'Apps Site Cache Rate (40%) Is Below Industry Standard', 'issue': 'Apps site has 40.19% cache hit rate vs. CDN (83.97%) and Portal (48.82%). Apps content frequently fetched from origin.', 'impact': 'High miss rate means users frequently wait for origin response. Performance is inconsistent.', 'recommendation': 'Audit cache headers and versioning. Increase cache TTL for static content. Consider CDN distribution. Target: 60% cache rate in 30 days.', 'priority': 'HIGH'},
        {'title': 'CDE App Slowest Among Major Apps (0.375s)', 'issue': 'CDE has 64.56% cache rate but slowest app latency at 0.375s. 3D-heavy apps (RUI, EUI) are faster.', 'impact': 'CDE visualization slowness impacts data analysis workflow productivity.', 'recommendation': 'Profile origin requests and database queries. Identify bottleneck. Implement query caching. Consider async processing for large datasets.', 'priority': 'MEDIUM'},
        {'title': 'RUI and EUI Have Good Cache Plus Fast Response', 'issue': 'RUI/EUI have 70.84%+ cache rates and sub-150ms latencies. 3D app performance is optimized.', 'impact': 'Users get consistent fast performance on 3D workflows.', 'recommendation': 'Maintain current RUI/EUI infrastructure. Use as performance baseline. Document optimization techniques.', 'priority': 'LOW'},
    ]
    _render_insights_panel(perf_insights)

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
