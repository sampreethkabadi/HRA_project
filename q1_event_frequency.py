#!/usr/bin/env python3
"""
q1_event_frequency.py
Q1 — Event Frequency Distribution

Produces:  charts/q1_event_frequency.png  (2×2 combined figure)

4 charts:
  [0,0] Horizontal bar  — event type share of total (% of 111K clean events)
  [0,1] Stacked bar     — event type mix per app (normalized to 100%)
  [1,0] Line chart      — monthly event volume, one line per app
  [1,1] Dual-axis area  — HRA events vs. CNS requests on the same timeline
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

# =============================================================================
# PATHS
# =============================================================================
EVENTS_PATH = "Data/processed/hra_events.parquet"
CNS_PATH    = "Data/processed/cns_clean.parquet"
OUTPUT_DIR  = "charts"

# =============================================================================
# PALETTES & ORDERING
# =============================================================================
EVENT_ORDER = ["click", "hover", "pageView", "keyboard", "modelChange", "error"]
EVENT_PALETTE = {
    "click":       "#2196F3",
    "hover":       "#FF9800",
    "pageView":    "#4CAF50",
    "keyboard":    "#9C27B0",
    "modelChange": "#009688",
    "error":       "#F44336",
}

# Apps shown in per-app charts, ordered by total event count (descending).
APP_ORDER = [
    "kg-explorer", "humanatlas.io", "ccf-eui", "ccf-rui",
    "cde-ui", "asct+b-reporter", "ftu-ui",
]
APP_LABELS = {
    "ccf-rui":         "RUI",
    "ccf-eui":         "EUI",
    "cde-ui":          "CDE",
    "kg-explorer":     "KG Explorer",
    "humanatlas.io":   "HRA Portal",
    "asct+b-reporter": "ASCT+B",
    "ftu-ui":          "FTU",
}
APP_PALETTE = {
    "ccf-rui":         "#1565C0",
    "ccf-eui":         "#2E7D32",
    "cde-ui":          "#E65100",
    "kg-explorer":     "#6A1B9A",
    "humanatlas.io":   "#00695C",
    "asct+b-reporter": "#B71C1C",
    "ftu-ui":          "#37474F",
}

# Shared axis style
def _clean_axes(ax):
    ax.spines[["top", "right"]].set_visible(False)


# =============================================================================
# CHART 1 — Event type breakdown (% of total)
# =============================================================================
def chart1_event_breakdown(ax, ev):
    counts = (
        ev["event_type"]
        .value_counts()
        .reindex(EVENT_ORDER)
        .dropna()
    )
    total = counts.sum()
    pct   = counts / total * 100

    # Draw bars bottom-to-top (reverse order so click is at top)
    order = pct.index[::-1]
    vals  = pct[order].values
    colors = [EVENT_PALETTE.get(e, "#999999") for e in order]

    bars = ax.barh(range(len(order)), vals, color=colors, height=0.55)

    for i, (bar, v) in enumerate(zip(bars, vals)):
        ax.text(v + 0.4, i, f"{v:.1f}%",
                va="center", ha="left", fontsize=9, color="#222222")

    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order, fontsize=9)
    ax.set_xlabel("Share of total events (%)", fontsize=9)
    ax.set_xlim(0, max(vals) * 1.22)
    ax.set_title(
        f"Event Type Distribution  ({total:,} events)",
        fontsize=11, fontweight="bold", pad=8,
    )

    _clean_axes(ax)


# =============================================================================
# CHART 2 — Event type mix per app (stacked, normalized to 100%)
# =============================================================================
def chart2_event_mix_per_app(ax, ev):
    sub = ev[ev["app"].isin(APP_ORDER)].copy()

    pivot = (
        sub.groupby(["app", "event_type"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=APP_ORDER, columns=EVENT_ORDER)
        .fillna(0)
    )

    # Normalize each row to 100 %
    row_totals = pivot.sum(axis=1).replace(0, 1)   # avoid /0
    pivot_pct  = pivot.div(row_totals, axis=0) * 100

    x_labels = [APP_LABELS.get(a, a) for a in pivot_pct.index]
    x        = np.arange(len(x_labels))
    bottom   = np.zeros(len(x_labels))

    for event in EVENT_ORDER:
        if event not in pivot_pct.columns:
            continue
        vals = pivot_pct[event].values
        ax.bar(x, vals, bottom=bottom,
               color=EVENT_PALETTE.get(event, "#999"),
               width=0.6, label=event)
        # Label segments at least 15% tall to avoid crowding
        for xi, (v, b) in enumerate(zip(vals, bottom)):
            if v >= 15:
                ax.text(xi, b + v / 2, f"{v:.0f}%",
                        ha="center", va="center",
                        fontsize=8, color="white", fontweight="bold")
        bottom += vals

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=8.5)
    ax.set_ylabel("% of app events", fontsize=9)
    ax.set_ylim(0, 108)
    ax.set_title("Event Type Mix per App (normalized)", fontsize=11, fontweight="bold", pad=8)
    ax.legend(fontsize=8, loc="upper right", ncol=2, framealpha=0.85,
              bbox_to_anchor=(1.0, 0.98))
    _clean_axes(ax)

    # Annotate apps with notably high error rates (inside the bar, not above)
    error_vals = pivot_pct["error"] if "error" in pivot_pct.columns else pd.Series(0, index=pivot_pct.index)
    error_bottoms = (pivot_pct[EVENT_ORDER[:EVENT_ORDER.index("error")]].sum(axis=1)
                     if "error" in EVENT_ORDER else pd.Series(0, index=pivot_pct.index))
    for xi, (app, err, bot) in enumerate(zip(pivot_pct.index, error_vals, error_bottoms)):
        if err > 30:
            ax.text(xi, bot + err / 2, f"{err:.0f}%\nerr",
                    ha="center", va="center", fontsize=7, color="white", fontweight="bold")


# =============================================================================
# CHART 3 — Monthly event volume per app (line chart)
# =============================================================================
def chart3_monthly_trend(ax, ev):
    sub     = ev[ev["app"].isin(APP_ORDER)].copy()
    monthly = (
        sub.groupby(["year_month", "app"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=APP_ORDER, fill_value=0)
    )
    monthly.index = monthly.index.astype(str)

    x = np.arange(len(monthly.index))

    for app in APP_ORDER:
        if app not in monthly.columns:
            continue
        vals = monthly[app].values
        if vals.sum() == 0:
            continue
        ax.plot(x, vals, marker="o", markersize=4, linewidth=2,
                label=APP_LABELS.get(app, app),
                color=APP_PALETTE.get(app, "#999"))

    ax.set_xticks(x)
    ax.set_xticklabels(monthly.index, rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("Events per month", fontsize=9)
    ax.set_title("Monthly Event Volume by App", fontsize=11, fontweight="bold", pad=8)
    ax.legend(fontsize=8, loc="upper left", ncol=2, framealpha=0.85,
              bbox_to_anchor=(0.0, 0.98))
    ax.yaxis.set_major_formatter(
        mtick.FuncFormatter(lambda v, _: f"{int(v):,}")
    )
    _clean_axes(ax)


# =============================================================================
# CHART 4 — HRA events vs. CNS requests (dual-axis area, overlapping window)
# =============================================================================
def chart4_hra_vs_cns(ax, ev):
    # HRA: monthly event counts (already human-only, test rows stripped)
    hra_monthly = ev.groupby("year_month").size().sort_index()
    hra_months  = set(hra_monthly.index)

    # CNS: load only the date column, re-derive year_month, then count
    cns_raw = pd.read_parquet(CNS_PATH, columns=["date"])
    cns_raw["year_month"] = (
        pd.to_datetime(cns_raw["date"], errors="coerce").dt.to_period("M")
    )
    cns_monthly = cns_raw.groupby("year_month").size().sort_index()
    del cns_raw

    # Align to the window where both datasets overlap
    common = sorted(hra_months & set(cns_monthly.index))
    hra_vals = [hra_monthly.get(m, 0) for m in common]
    cns_vals = [cns_monthly.get(m, 0) for m in common]
    labels   = [str(m) for m in common]
    x        = np.arange(len(common))

    ax2 = ax.twinx()

    # CNS — left axis (blue)
    ax.fill_between(x, cns_vals, alpha=0.20, color="#1565C0")
    ax.plot(x, cns_vals, color="#1565C0", linewidth=2,
            marker="o", markersize=4, label="CNS requests (left)")

    # HRA events — right axis (orange)
    ax2.fill_between(x, hra_vals, alpha=0.20, color="#E65100")
    ax2.plot(x, hra_vals, color="#E65100", linewidth=2,
             marker="s", markersize=4, label="HRA events (right)")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("CNS monthly requests", color="#1565C0", fontsize=9)
    ax2.set_ylabel("HRA monthly events", color="#E65100", fontsize=9)
    ax.tick_params(axis="y", colors="#1565C0")
    ax2.tick_params(axis="y", colors="#E65100")
    ax.set_title(
        "Monthly Volume: HRA Events vs. CNS Requests",
        fontsize=11, fontweight="bold", pad=8,
    )
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax2.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.spines[["top"]].set_visible(False)

    # Combined legend
    lines1, labs1 = ax.get_legend_handles_labels()
    lines2, labs2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labs1 + labs2,
              fontsize=8, loc="upper left", framealpha=0.85)


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("Loading HRA events...")
    ev = pd.read_parquet(EVENTS_PATH)
    # Strip test rows — they are not real user interactions
    ev = ev[~ev["event_type"].isin(["test", "test2"])].copy()
    print(f"  {len(ev):,} clean event rows")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    charts = [
        ("q1_1_event_type_breakdown.png",  "Event Type Distribution",          chart1_event_breakdown,   (8, 5),  ev),
        ("q1_2_event_mix_per_app.png",     "Event Type Mix per App",           chart2_event_mix_per_app, (10, 5), ev),
        ("q1_3_monthly_trend.png",         "Monthly Event Volume by App",      chart3_monthly_trend,     (10, 5), ev),
        ("q1_4_hra_vs_cns_volume.png",     "Monthly Volume: HRA vs. CNS",      chart4_hra_vs_cns,        (10, 5), ev),
    ]

    for filename, title, fn, figsize, *args in charts:
        print(f"Building {filename}...")
        fig, ax = plt.subplots(figsize=figsize)
        fn(ax, *args)
        out = os.path.join(OUTPUT_DIR, filename)
        plt.tight_layout()
        plt.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved: {out}")


if __name__ == "__main__":
    main()
