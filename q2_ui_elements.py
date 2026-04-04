#!/usr/bin/env python3
"""
q2_ui_elements.py
Q2 — Most and Least Used UI Elements

Produces (in charts/):
  q2_1_rui_top_clicks.png      — top 20 clicked paths in RUI
  q2_2_eui_top_clicks.png      — top 20 clicked paths in EUI
  q2_3_cde_top_clicks.png      — top 20 clicked paths in CDE
  q2_4_under_used_table.png    — table: paths with < 5 clicks, by app
  q2_5_hover_vs_click.png      — scatter: hover count vs click count per path
"""

import os
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

# =============================================================================
# PATHS & CONSTANTS
# =============================================================================
EVENTS_PATH       = "Data/processed/hra_events.parquet"
OUTPUT_DIR        = "charts"
UNDER_USED_THRESH = 5      # paths with fewer clicks than this are "under-used"
TOP_N             = 20     # number of elements shown in bar charts
MAX_LABEL_LEN     = 42     # max character width for path labels before truncation

MAIN_APPS = ["ccf-rui", "ccf-eui", "cde-ui"]

APP_LABELS = {"ccf-rui": "RUI", "ccf-eui": "EUI", "cde-ui": "CDE"}
APP_COLORS = {"ccf-rui": "#1565C0", "ccf-eui": "#2E7D32", "cde-ui": "#E65100"}


def truncate(label, maxlen=MAX_LABEL_LEN):
    """Strip the leading app prefix and truncate if still too long."""
    # Remove first dot-segment (the app name) since it's redundant in a per-app chart
    parts = str(label).split(".", 1)
    short = parts[1] if len(parts) > 1 else parts[0]
    return short if len(short) <= maxlen else short[:maxlen - 1] + "…"


def _clean_axes(ax):
    ax.spines[["top", "right"]].set_visible(False)


# =============================================================================
# LOAD
# =============================================================================
def load_data():
    ev = pd.read_parquet(EVENTS_PATH)
    ev = ev[~ev["event_type"].isin(["test", "test2"])].copy()
    clicks = ev[ev["event_type"] == "click"].copy()
    hovers = ev[ev["event_type"] == "hover"].copy()
    return clicks, hovers


# =============================================================================
# CHARTS 1–3 — Top-N clicked paths per app
# =============================================================================
def chart_top_clicks(app, clicks, n=TOP_N):
    sub    = clicks[(clicks["app"] == app) & clicks["path"].notna()]
    counts = sub["path"].value_counts().head(n)

    labels = [truncate(p) for p in counts.index[::-1]]
    vals   = counts.values[::-1]
    color  = APP_COLORS.get(app, "#555555")

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(labels)), vals, color=color, height=0.65)

    for i, v in enumerate(vals):
        ax.text(v + max(vals) * 0.01, i, str(v),
                va="center", ha="left", fontsize=8.5, color="#222222")

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlabel("Click count", fontsize=9)
    ax.set_xlim(0, max(vals) * 1.14)
    ax.set_title(
        f"Top {n} Clicked UI Elements — {APP_LABELS.get(app, app)}"
        f"  ({len(sub):,} total clicks)",
        fontsize=11, fontweight="bold", pad=8,
    )
    _clean_axes(ax)
    plt.tight_layout()
    return fig


# =============================================================================
# CHART 4 — Under-used elements table (< UNDER_USED_THRESH clicks)
# =============================================================================
def chart_under_used_table(clicks):
    # Count clicks per (app, path), keep only under-used paths
    counts = (
        clicks[clicks["app"].isin(MAIN_APPS) & clicks["path"].notna()]
        .groupby(["app", "path"])
        .size()
        .reset_index(name="clicks")
    )
    under = (
        counts[counts["clicks"] < UNDER_USED_THRESH]
        .sort_values(["app", "clicks"], ascending=[True, False])
    )

    # Build display table: truncate path, add app label
    rows = []
    for _, row in under.iterrows():
        rows.append({
            "App":    APP_LABELS.get(row["app"], row["app"]),
            "Path":   truncate(row["path"], maxlen=55),
            "Clicks": int(row["clicks"]),
        })
    df_table = pd.DataFrame(rows)

    # Summarise counts per app for the subtitle
    summary = under.groupby("app").size().rename(APP_LABELS).to_dict()
    subtitle = "  |  ".join(f"{k}: {v}" for k, v in summary.items())

    # --- Render as a matplotlib table ---
    # Show at most 40 rows to keep the figure readable; sort by app then clicks desc
    display = df_table.head(40)

    fig_h = max(4, len(display) * 0.28 + 1.2)
    fig, ax = plt.subplots(figsize=(11, fig_h))
    ax.axis("off")

    col_widths = [0.08, 0.72, 0.08]   # proportions for App / Path / Clicks
    tbl = ax.table(
        cellText=display.values,
        colLabels=display.columns,
        cellLoc="left",
        loc="center",
        colWidths=col_widths,
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    tbl.scale(1, 1.35)

    # Style header row
    for col in range(len(display.columns)):
        cell = tbl[0, col]
        cell.set_facecolor("#37474F")
        cell.set_text_props(color="white", fontweight="bold")

    # Alternate row shading + color-code by app
    app_row_colors = {"RUI": "#E3F2FD", "EUI": "#E8F5E9", "CDE": "#FFF3E0"}
    for row_idx in range(1, len(display) + 1):
        app_val = display.iloc[row_idx - 1]["App"]
        base_color = app_row_colors.get(app_val, "#FAFAFA")
        for col in range(len(display.columns)):
            tbl[row_idx, col].set_facecolor(base_color)

    ax.set_title(
        f"Under-used UI Elements  (< {UNDER_USED_THRESH} clicks)\n{subtitle}",
        fontsize=11, fontweight="bold", pad=10, loc="left",
    )

    if len(df_table) > 40:
        ax.text(0.5, -0.02,
                f"Showing 40 of {len(df_table)} total under-used paths.",
                transform=ax.transAxes, ha="center", fontsize=8, color="#666666")

    plt.tight_layout()
    return fig


# =============================================================================
# CHART 5 — Hover count vs. click count scatter (discoverability)
# =============================================================================
def chart_hover_vs_click(clicks, hovers):
    fig, ax = plt.subplots(figsize=(9, 7))

    # Build per-path click/hover counts for each app
    app_data = {}
    for app in MAIN_APPS:
        c = (clicks[(clicks["app"] == app) & clicks["path"].notna()]
             ["path"].value_counts().rename("clicks"))
        h = (hovers[(hovers["app"] == app) & hovers["path"].notna()]
             ["path"].value_counts().rename("hovers"))
        merged = pd.concat([c, h], axis=1).fillna(0)
        if not merged.empty:
            app_data[app] = merged

    # Set axis limits: cap at the 2nd-highest value on each axis so only the
    # single extreme outlier (4K-hover EUI path) gets clipped, not the bulk.
    all_clicks = pd.concat([d["clicks"] for d in app_data.values()])
    all_hovers = pd.concat([d["hovers"] for d in app_data.values()])
    sorted_clicks = all_clicks.sort_values(ascending=False)
    sorted_hovers = all_hovers.sort_values(ascending=False)
    x_max = sorted_clicks.iloc[1] * 1.15 if len(sorted_clicks) > 1 else sorted_clicks.iloc[0]
    y_max = sorted_hovers.iloc[1] * 1.15 if len(sorted_hovers) > 1 else sorted_hovers.iloc[0]
    clipped = int(((all_clicks > x_max) | (all_hovers > y_max)).sum())

    for app, merged in app_data.items():
        color = APP_COLORS.get(app, "#999")
        label = APP_LABELS.get(app, app)
        ax.scatter(
            merged["clicks"], merged["hovers"],
            color=color, alpha=0.65, s=40, label=label, zorder=3,
        )

        # Annotate top "high hover, low click" outliers within the visible range
        visible = merged[(merged["clicks"] <= x_max) & (merged["hovers"] <= y_max)]
        outliers = visible[
            (visible["hovers"] > visible["hovers"].quantile(0.90)) &
            (visible["clicks"] < visible["clicks"].quantile(0.25))
        ].head(3)
        for path, row in outliers.iterrows():
            short = truncate(path, maxlen=30)
            ax.annotate(
                short,
                xy=(row["clicks"], row["hovers"]),
                xytext=(row["clicks"] + x_max * 0.04, row["hovers"]),
                fontsize=7, color=color,
                arrowprops=dict(arrowstyle="-", color=color, lw=0.7),
            )

    ax.set_xlim(0, x_max * 1.05)
    ax.set_ylim(0, y_max * 1.05)

    # Diagonal reference line within the visible window
    diag = min(x_max, y_max)
    ax.plot([0, diag], [0, diag], color="#BBBBBB", linewidth=1,
            linestyle="--", label="hover = click", zorder=1)

    if clipped:
        ax.text(0.99, 0.01,
                f"{clipped} outlier(s) clipped for readability",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=7.5, color="#888888")

    ax.set_xlabel("Click count per path", fontsize=9)
    ax.set_ylabel("Hover count per path", fontsize=9)
    ax.set_title(
        "Hover vs. Click Count per UI Element\n"
        "Elements above the dashed line have high hover but low click — discoverability risk",
        fontsize=11, fontweight="bold", pad=8,
    )
    ax.legend(fontsize=8.5, framealpha=0.85)
    _clean_axes(ax)
    plt.tight_layout()
    return fig


# =============================================================================
# MAIN
# =============================================================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading data...")
    clicks, hovers = load_data()
    print(f"  {len(clicks):,} click events | {len(hovers):,} hover events")

    specs = [
        ("q2_1_rui_top_clicks.png",   lambda: chart_top_clicks("ccf-rui", clicks)),
        ("q2_2_eui_top_clicks.png",   lambda: chart_top_clicks("ccf-eui", clicks)),
        ("q2_3_cde_top_clicks.png",   lambda: chart_top_clicks("cde-ui",  clicks)),
        ("q2_4_under_used_table.png", lambda: chart_under_used_table(clicks)),
        ("q2_5_hover_vs_click.png",   lambda: chart_hover_vs_click(clicks, hovers)),
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
