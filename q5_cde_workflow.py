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
    total_events   = len(cde)
    visualize_sess = cde[
        cde["path"].str.contains("/cde/visualize|/visualize", na=False)
    ]["session_id"].nunique()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis("off")
    fig.patch.set_facecolor("#FFF8E1")
    ax.set_facecolor("#FFF8E1")

    # Warning banner
    banner = mpatches.FancyBboxPatch(
        (0.04, 0.60), 0.92, 0.32,
        boxstyle="round,pad=0.02",
        linewidth=2, edgecolor=WARN_COLOR,
        facecolor="#FFEBEE", transform=ax.transAxes, zorder=2,
    )
    ax.add_patch(banner)

    ax.text(0.5, 0.80, "Download events are not tracked in the current CDE implementation",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=13, fontweight="bold", color=WARN_COLOR)
    ax.text(0.5, 0.67,
            "The original question — histogram & violin-plot download counts — cannot be answered from existing log data.",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=10, color="#444444")

    # Divider
    ax.plot([0.05, 0.95], [0.56, 0.56], color="#CCCCCC", linewidth=1,
            transform=ax.transAxes)

    # Supporting context stats
    stats = [
        (f"{total_events:,}",    "total CDE events logged"),
        (f"{visualize_sess}",    "sessions reached visualize page"),
        ("0",                    "download events found"),
    ]
    for i, (val, label) in enumerate(stats):
        x     = 0.18 + i * 0.32
        color = WARN_COLOR if val == "0" else CDE_COLOR
        ax.text(x, 0.38, val,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=26, fontweight="bold", color=color)
        ax.text(x, 0.22, label,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=9, color="#666666")

    ax.set_title("Q5 — CDE Download Tracking Gap",
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
