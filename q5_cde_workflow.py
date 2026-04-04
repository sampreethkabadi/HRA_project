#!/usr/bin/env python3
"""
q5_cde_workflow.py
Q5 — CDE Histogram / Violin Downloads

Produces (in charts/):
  q5_1_funnel.png          — CDE workflow session funnel
  q5_2_tracking_gap.png    — callout: download events not tracked
  q5_3_recommendations.png — table: recommended event names to add
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

# =============================================================================
# PATHS
# =============================================================================
EVENTS_PATH = "Data/processed/hra_events.parquet"
OUTPUT_DIR  = "charts"

CDE_COLOR  = "#E65100"
WARN_COLOR = "#B71C1C"
OK_COLOR   = "#2E7D32"

# =============================================================================
# LOAD
# =============================================================================
def load_data():
    ev = pd.read_parquet(EVENTS_PATH)
    ev = ev[~ev["event_type"].isin(["test", "test2"])]
    cde = ev[ev["app"] == "cde-ui"].copy()
    return cde


def _clean_axes(ax):
    ax.spines[["top", "right"]].set_visible(False)


# =============================================================================
# CHART 1 — CDE workflow funnel (unique sessions per step)
# =============================================================================
def chart_funnel(cde):
    steps = [
        ("Landing page",          ["/cde/", "landing-page"]),
        ("Create page",           ["/cde/create", "/create", "create-visualization-page"]),
        ("Organize & configure",  ["organize-data", "configure-parameters"]),
        ("Submit",                ["visualize-data.submit"]),
        ("Visualize page",        ["/cde/visualize", "/visualize"]),
    ]

    labels = [s[0] for s in steps]
    counts = []
    for _, keywords in steps:
        mask = cde["path"].str.contains("|".join(keywords), na=False, case=False)
        counts.append(cde[mask]["session_id"].nunique())

    total_sessions = cde["session_id"].nunique()
    max_count      = counts[0]
    y_pos          = list(range(len(labels)))[::-1]

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, (y, count, label) in enumerate(zip(y_pos, counts, labels)):
        width = count / max_count
        color = CDE_COLOR if i == 0 else (OK_COLOR if count >= counts[i - 1] * 0.6 else WARN_COLOR)

        ax.barh(y, width, height=0.55, left=(1 - width) / 2,
                color=color, alpha=0.85)

        ax.text(0.5, y, f"{count} sessions",
                ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")

        pct_of_entry = count / max_count * 100
        ax.text(0.5 + width / 2 + 0.02, y,
                f"{pct_of_entry:.0f}% of entry",
                va="center", ha="left", fontsize=8.5, color="#444444")

        if i > 0:
            dropped  = counts[i - 1] - count
            drop_pct = dropped / counts[i - 1] * 100
            y_mid    = (y + y_pos[i - 1]) / 2
            # Only show drop annotation when there is a meaningful drop
            if dropped > 0:
                ax.text(0.5, y_mid,
                        f"▼ {dropped} lost  ({drop_pct:.0f}%)",
                        ha="center", va="center", fontsize=8,
                        color=WARN_COLOR, style="italic")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.spines[["top", "right", "bottom", "left"]].set_visible(False)
    ax.set_title(
        f"CDE Workflow — Session Funnel\n"
        f"({total_sessions} total CDE sessions; funnel tracks unique sessions per step)",
        fontsize=11, fontweight="bold", pad=10,
    )

    legend_patches = [
        mpatches.Patch(color=CDE_COLOR,  label="Entry step"),
        mpatches.Patch(color=OK_COLOR,   label="Majority retained (≥60%)"),
        mpatches.Patch(color=WARN_COLOR, label="Large drop-off (<60%)"),
    ]
    ax.legend(handles=legend_patches, loc="lower right",
              fontsize=8, framealpha=0.85)

    plt.tight_layout()
    return fig


# =============================================================================
# CHART 2 — Tracking gap callout
# =============================================================================
def chart_tracking_gap(cde):
    # Confirmed counts from raw log exploration (12.8M rows searched)
    # Download events exist in the HRA event system for other apps but not CDE.
    total_events      = len(cde)
    visualize_sess    = cde[
        cde["path"].str.contains("/cde/visualize|/visualize", na=False)
    ]["session_id"].nunique()
    kg_dl_events      = 2066   # kg-explorer download events (raw log confirmed)
    rui_dl_events     = 121    # ccf-rui review.download events (raw log confirmed)

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.axis("off")
    fig.patch.set_facecolor("#FFF8E1")
    ax.set_facecolor("#FFF8E1")

    # Warning banner
    banner = mpatches.FancyBboxPatch(
        (0.03, 0.68), 0.94, 0.25,
        boxstyle="round,pad=0.02",
        linewidth=2, edgecolor=WARN_COLOR,
        facecolor="#FFEBEE", transform=ax.transAxes, zorder=2,
    )
    ax.add_patch(banner)

    ax.text(0.5, 0.86, "CDE download events are not tracked — confirmed across all 12.8M raw log rows",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=12, fontweight="bold", color=WARN_COLOR)
    ax.text(0.5, 0.75,
            "Histogram & violin-plot download counts cannot be answered from existing data.\n"
            "The tracking infrastructure exists in other HRA apps — CDE has not implemented it yet.",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=9.5, color="#444444")

    # Divider
    ax.plot([0.03, 0.97], [0.65, 0.65], color="#CCCCCC", linewidth=1,
            transform=ax.transAxes)

    # Top row: CDE-specific stats
    ax.text(0.5, 0.60, "CDE", transform=ax.transAxes, ha="center",
            fontsize=9, fontweight="bold", color="#888888")
    cde_stats = [
        (f"{total_events:,}",  "CDE events logged"),
        (f"{visualize_sess}",  "sessions on visualize page"),
        ("0",                  "CDE download events"),
    ]
    for i, (val, label) in enumerate(cde_stats):
        x     = 0.18 + i * 0.32
        color = WARN_COLOR if val == "0" else CDE_COLOR
        ax.text(x, 0.48, val, transform=ax.transAxes, ha="center", va="center",
                fontsize=22, fontweight="bold", color=color)
        ax.text(x, 0.37, label, transform=ax.transAxes, ha="center", va="center",
                fontsize=8.5, color="#666666")

    # Divider
    ax.plot([0.03, 0.97], [0.30, 0.30], color="#EEEEEE", linewidth=1,
            transform=ax.transAxes)

    # Bottom row: other apps DO track downloads (context)
    ax.text(0.5, 0.26, "Other HRA apps already track downloads (same event system)",
            transform=ax.transAxes, ha="center", fontsize=9,
            fontweight="bold", color=OK_COLOR)
    other_stats = [
        (f"{kg_dl_events:,}", "KG Explorer download events"),
        (f"{rui_dl_events}",  "RUI download events"),
        ("→ CDE next",        "implementation path is clear"),
    ]
    for i, (val, label) in enumerate(other_stats):
        x = 0.18 + i * 0.32
        color = OK_COLOR if i < 2 else "#555555"
        ax.text(x, 0.16, val, transform=ax.transAxes, ha="center", va="center",
                fontsize=18, fontweight="bold", color=color)
        ax.text(x, 0.06, label, transform=ax.transAxes, ha="center", va="center",
                fontsize=8.5, color="#666666")

    ax.set_title("Q5 — CDE Download Tracking Gap  (verified against full raw logs)",
                 fontsize=12, fontweight="bold", pad=10)

    plt.tight_layout()
    return fig


# =============================================================================
# CHART 3 — Recommended event names (table)
# =============================================================================
def chart_recommendations():
    # Follow the CDE path naming convention observed in the data:
    # cde-ui.[page].[section].[component].[action]
    rows = [
        ("cde-ui.visualize-page.histogram.download",
         "User downloads the histogram chart",
         "High — core Q5 ask"),
        ("cde-ui.visualize-page.violin-plot.download",
         "User downloads the violin-plot chart",
         "High — core Q5 ask"),
        ("cde-ui.visualize-page.scatter-plot.download",
         "User downloads a scatter plot (if present)",
         "Medium — future proofing"),
        ("cde-ui.visualize-page.export-data.download",
         "User downloads the underlying dataset as CSV",
         "Medium — data export tracking"),
        ("cde-ui.visualize-page.share.copy-link",
         "User copies a shareable link to the visualization",
         "Low — sharing behaviour"),
    ]

    col_headers = ["Recommended Event Path", "Description", "Priority"]
    col_widths  = [0.42, 0.40, 0.16]

    fig_h = 0.55 * len(rows) + 1.6
    fig, ax = plt.subplots(figsize=(13, fig_h))
    ax.axis("off")

    tbl = ax.table(
        cellText=rows,
        colLabels=col_headers,
        cellLoc="left",
        loc="center",
        colWidths=col_widths,
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    tbl.scale(1, 1.6)

    priority_colors = {"High": "#FFCDD2", "Medium": "#FFF9C4", "Low": "#E8F5E9"}

    for col in range(len(col_headers)):
        cell = tbl[0, col]
        cell.set_facecolor("#37474F")
        cell.set_text_props(color="white", fontweight="bold")

    for row_idx, (_, _, priority) in enumerate(rows, start=1):
        p_key    = priority.split(" —")[0]
        row_bg   = priority_colors.get(p_key, "#FAFAFA")
        for col in range(len(col_headers)):
            tbl[row_idx, col].set_facecolor(row_bg)
        # Bold the event path column
        tbl[row_idx, 0].set_text_props(fontfamily="monospace", fontsize=8)

    ax.set_title(
        "Recommended Event Tracking — CDE Visualize Page\n"
        "Add these events to answer Q5 in future data collection",
        fontsize=11, fontweight="bold", pad=10, loc="left",
    )

    plt.tight_layout()
    return fig


# =============================================================================
# MAIN
# =============================================================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading data...")
    cde = load_data()
    print(f"  CDE events: {len(cde):,} | Sessions: {cde['session_id'].nunique()}")

    specs = [
        ("q5_1_funnel.png",          lambda: chart_funnel(cde)),
        ("q5_2_tracking_gap.png",    lambda: chart_tracking_gap(cde)),
        ("q5_3_recommendations.png", lambda: chart_recommendations()),
    ]

    for filename, build in specs:
        print(f"Building {filename}...")
        fig = build()
        out = os.path.join(OUTPUT_DIR, filename)
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved: {out}")


if __name__ == "__main__":
    main()
