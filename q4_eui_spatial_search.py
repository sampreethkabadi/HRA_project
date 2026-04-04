#!/usr/bin/env python3
"""
q4_eui_spatial_search.py
Q4 — EUI Spatial Search Usage

Produces (in charts/):
  q4_1_funnel.png         — Spatial Search session funnel
  q4_2_top_organs.png     — top organs selected in configuration
  q4_3_keyboard_stat.png  — keyboard navigation usage stat card
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# =============================================================================
# PATHS
# =============================================================================
EVENTS_PATH = "Data/processed/hra_events.parquet"
OUTPUT_DIR  = "charts"

EUI_COLOR  = "#2E7D32"
DROP_COLOR = "#C62828"
KEEP_COLOR = "#43A047"

# =============================================================================
# LOAD
# =============================================================================
def load_data():
    ev = pd.read_parquet(EVENTS_PATH)
    ev = ev[~ev["event_type"].isin(["test", "test2"])]
    eui = ev[ev["app"] == "ccf-eui"].copy()
    ss  = eui[eui["path"].str.contains("spatial-search", na=False, case=False)].copy()
    return eui, ss


def _clean_axes(ax):
    ax.spines[["top", "right"]].set_visible(False)


# =============================================================================
# CHART 1 — Spatial Search funnel (unique sessions per step)
# =============================================================================
def chart_funnel(eui, ss):
    steps = [
        ("Entry",          "spatial-search-button"),
        ("Configure organ","spatial-search-config.organ-sex-selection"),
        ("Continue",       "spatial-search-config.continue"),
        ("View results",   "spatial-search.results"),
        ("Apply",          "spatial-search.buttons.apply"),
    ]

    labels  = [s[0] for s in steps]
    counts  = [
        ss[ss["path"].str.contains(kw, na=False)]["session_id"].nunique()
        for _, kw in steps
    ]
    total_sessions = eui["session_id"].nunique()

    fig, ax = plt.subplots(figsize=(10, 6))

    bar_height = 0.55
    max_count  = counts[0]
    y_pos      = list(range(len(labels)))[::-1]   # top = first step

    for i, (y, count, label) in enumerate(zip(y_pos, counts, labels)):
        width  = count / max_count                 # normalised bar width
        color  = EUI_COLOR if i == 0 else (KEEP_COLOR if counts[i] >= counts[i-1] * 0.6 else DROP_COLOR)

        # Centred bar
        ax.barh(y, width, height=bar_height, left=(1 - width) / 2,
                color=color, alpha=0.85)

        # Session count inside bar
        ax.text(0.5, y, f"{count} sessions",
                ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")

        # % of entry step on the right
        pct_of_entry = count / counts[0] * 100
        ax.text(0.5 + width / 2 + 0.02, y, f"{pct_of_entry:.0f}% of entry",
                va="center", ha="left", fontsize=8.5, color="#444444")

        # Drop-off annotation between steps
        if i > 0:
            dropped    = counts[i - 1] - count
            drop_pct   = dropped / counts[i - 1] * 100
            y_mid      = (y + y_pos[i - 1]) / 2
            ax.text(0.5, y_mid, f"▼ {dropped} lost  ({drop_pct:.0f}%)",
                    ha="center", va="center", fontsize=8,
                    color=DROP_COLOR, style="italic")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.spines[["top", "right", "bottom", "left"]].set_visible(False)
    ax.set_title(
        f"EUI Spatial Search — Session Funnel\n"
        f"({total_sessions} total EUI sessions; funnel tracks unique sessions per step)",
        fontsize=11, fontweight="bold", pad=10,
    )

    # Legend
    legend_patches = [
        mpatches.Patch(color=EUI_COLOR,  label="Entry step"),
        mpatches.Patch(color=KEEP_COLOR, label="Majority retained (≥60%)"),
        mpatches.Patch(color=DROP_COLOR, label="Large drop-off (<60%)"),
    ]
    ax.legend(handles=legend_patches, loc="lower right",
              fontsize=8, framealpha=0.85)

    plt.tight_layout()
    return fig


# =============================================================================
# CHART 2 — Top organs selected in Spatial Search config
# =============================================================================
def chart_top_organs(ss):
    # Keep only specific organ selections (not the generic search box)
    organ_rows = ss[
        ss["path"].str.contains(r"organ\.[a-z]", na=False, regex=True) &
        ~ss["path"].str.contains("organ.search|organ-sex-selection$", na=False)
    ].copy()

    def extract_organ(path):
        parts = path.split(".")
        for i, p in enumerate(parts):
            if p == "organ" and i + 1 < len(parts):
                raw = parts[i + 1]
                # Clean up laterality suffix
                name = raw.replace("-", " ").title()
                name = name.replace(" L", " (L)").replace(" R", " (R)")
                return name
        return None

    organ_rows["organ"] = organ_rows["path"].apply(extract_organ)
    counts = organ_rows["organ"].value_counts().dropna()

    labels = counts.index[::-1]
    vals   = counts.values[::-1]
    colors = [EUI_COLOR if i >= len(vals) - 3 else "#81C784"
              for i in range(len(vals))]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(range(len(labels)), vals, color=colors, height=0.6)

    for i, v in enumerate(vals):
        ax.text(v + 0.08, i, str(v),
                va="center", ha="left", fontsize=9, color="#222222")

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Selection count", fontsize=9)
    ax.set_xlim(0, max(vals) * 1.2)
    ax.set_title(
        "Top Organs Selected in Spatial Search Configuration\n"
        f"({organ_rows['organ'].nunique()} unique organs selected across all sessions)",
        fontsize=11, fontweight="bold", pad=8,
    )
    _clean_axes(ax)
    plt.tight_layout()
    return fig


# =============================================================================
# CHART 3 — Keyboard navigation stat card
# =============================================================================
def chart_keyboard_stat(eui):
    total_sessions = eui["session_id"].nunique()
    kb_sessions    = (
        eui[eui["event_type"] == "keyboard"]["session_id"].nunique()
    )
    pct = kb_sessions / total_sessions * 100

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")
    fig.patch.set_facecolor("#F5F5F5")
    ax.set_facecolor("#F5F5F5")

    # Headline
    ax.text(0.5, 0.80, f"{pct:.1f}%",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=68, fontweight="bold", color=EUI_COLOR)
    ax.text(0.5, 0.59, "of EUI sessions used keyboard navigation",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=14, color="#444444")

    ax.axhline(y=0.47, xmin=0.1, xmax=0.9, color="#CCCCCC", linewidth=1)

    # Supporting stats
    stats = [
        (f"{kb_sessions}",       "sessions with keyboard events"),
        (f"{total_sessions}",    "total EUI sessions"),
        ("Power user signal",    "keyboard = advanced navigation"),
    ]
    for i, (val, label) in enumerate(stats):
        x = 0.18 + i * 0.32
        ax.text(x, 0.30, val,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=18, fontweight="bold", color="#E65100")
        ax.text(x, 0.12, label,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=8.5, color="#666666")

    ax.set_title("Q4 — EUI Keyboard Navigation Usage  (Power User Indicator)",
                 fontsize=12, fontweight="bold", pad=10)

    plt.tight_layout()
    return fig


# =============================================================================
# MAIN
# =============================================================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading data...")
    eui, ss = load_data()
    print(f"  EUI events: {len(eui):,} | Spatial search events: {len(ss):,}")

    specs = [
        ("q4_1_funnel.png",        lambda: chart_funnel(eui, ss)),
        ("q4_2_top_organs.png",    lambda: chart_top_organs(ss)),
        ("q4_3_keyboard_stat.png", lambda: chart_keyboard_stat(eui)),
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
