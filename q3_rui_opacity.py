#!/usr/bin/env python3
"""
q3_rui_opacity.py
Q3 — RUI Opacity Feature Usage

Produces (in charts/):
  q3_1_stat_card.png       — key headline numbers
  q3_2_top_structures.png  — top anatomical structures by opacity toggles
  q3_3_donut.png           — master vs. per-structure toggle breakdown
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

RUI_COLOR   = "#1565C0"
ACCENT      = "#E65100"

# =============================================================================
# LOAD & CATEGORISE
# =============================================================================
def load_opacity():
    ev = pd.read_parquet(EVENTS_PATH)
    ev = ev[~ev["event_type"].isin(["test", "test2"])]

    rui     = ev[ev["app"] == "ccf-rui"]
    opacity = rui[rui["path"].str.contains("opacity", na=False, case=False)].copy()

    def categorise(path):
        if "opacity-settings.toggle" in path:
            return "Master settings toggle"
        if "all-anatomical-structures" in path:
            return "All-structures toggle"
        if "landmarks-visibility" in path:
            return "Landmark toggles"
        if "AS-visibility" in path:
            return "Per-structure toggles"
        return "Other"

    opacity["category"] = opacity["path"].apply(categorise)

    def extract_structure(path):
        parts = path.split(".")
        if "AS-visibility" in parts:
            idx = parts.index("AS-visibility")
            if idx + 1 < len(parts):
                raw = parts[idx + 1]
                if raw == "all-anatomical-structures":
                    return None          # exclude from per-structure bar chart
                return raw.replace("-", " ").title()
        return None

    opacity["structure"] = opacity["path"].apply(extract_structure)

    return rui, opacity


def _clean_axes(ax):
    ax.spines[["top", "right"]].set_visible(False)


# =============================================================================
# CHART 1 — Stat card
# =============================================================================
def chart_stat_card(rui, opacity):
    total_rui   = len(rui)
    total_opacity = len(opacity)
    pct         = total_opacity / total_rui * 100
    n_structures = opacity["structure"].notna().sum()   # per-structure events
    n_unique_str = opacity["structure"].dropna().nunique()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")

    # Background card
    fig.patch.set_facecolor("#F5F5F5")
    ax.set_facecolor("#F5F5F5")

    # Main headline
    ax.text(0.5, 0.82, f"{total_opacity}",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=64, fontweight="bold", color=RUI_COLOR)
    ax.text(0.5, 0.62, "opacity toggle events",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=16, color="#444444")

    # Divider
    ax.axhline(y=0.50, xmin=0.1, xmax=0.9, color="#CCCCCC", linewidth=1)

    # Supporting stats
    stats = [
        (f"{pct:.1f}%",       "of all RUI activity"),
        (f"{n_unique_str}",   "anatomical structures toggled"),
        (f"{total_rui:,}",    "total RUI events"),
    ]
    for i, (val, label) in enumerate(stats):
        x = 0.18 + i * 0.32
        ax.text(x, 0.32, val,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=22, fontweight="bold", color=ACCENT)
        ax.text(x, 0.14, label,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=9, color="#666666")

    ax.set_title("Q3 — RUI Opacity Feature Usage",
                 fontsize=13, fontweight="bold", pad=10)

    plt.tight_layout()
    return fig


# =============================================================================
# CHART 2 — Top anatomical structures (horizontal bar)
# =============================================================================
def chart_top_structures(opacity, top_n=15):
    # Per-structure events only (excludes all-anatomical-structures master toggle)
    per_struct = opacity[opacity["structure"].notna()]
    counts = per_struct["structure"].value_counts().head(top_n)

    labels = counts.index[::-1]
    vals   = counts.values[::-1]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(labels)), vals, color=RUI_COLOR, height=0.65)

    for i, v in enumerate(vals):
        ax.text(v + 0.1, i, str(v),
                va="center", ha="left", fontsize=9, color="#222222")

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Opacity toggle clicks", fontsize=9)
    ax.set_xlim(0, max(vals) * 1.18)
    ax.set_title(
        f"Top {top_n} Anatomical Structures — Opacity Toggles\n"
        f"({per_struct['structure'].nunique()} unique structures toggled total)",
        fontsize=11, fontweight="bold", pad=8,
    )
    _clean_axes(ax)
    plt.tight_layout()
    return fig


# =============================================================================
# CHART 3 — Donut: toggle category breakdown
# =============================================================================
def chart_donut(opacity):
    cat_counts = opacity["category"].value_counts()

    # Fixed display order
    order = [
        "Per-structure toggles",
        "All-structures toggle",
        "Landmark toggles",
        "Master settings toggle",
    ]
    labels = [c for c in order if c in cat_counts.index]
    sizes  = [cat_counts[c] for c in labels]
    total  = sum(sizes)

    colors = ["#1565C0", "#42A5F5", "#78909C", "#E65100"][:len(labels)]

    fig, ax = plt.subplots(figsize=(8, 6))

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct=lambda p: f"{p:.1f}%\n({int(round(p * total / 100))})",
        colors=colors,
        startangle=90,
        pctdistance=0.72,
        wedgeprops=dict(width=0.52, edgecolor="white", linewidth=2),
    )

    for at in autotexts:
        at.set_fontsize(9)
        at.set_fontweight("bold")
        at.set_color("white")

    # Centre annotation
    ax.text(0, 0, f"{total}\nevents", ha="center", va="center",
            fontsize=14, fontweight="bold", color="#333333")

    # Legend
    legend_patches = [
        mpatches.Patch(color=c, label=f"{l}  ({v})")
        for c, l, v in zip(colors, labels, sizes)
    ]
    ax.legend(handles=legend_patches, loc="lower center",
              bbox_to_anchor=(0.5, -0.12), ncol=2,
              fontsize=9, framealpha=0.85)

    ax.set_title(
        "Opacity Toggle Type Breakdown",
        fontsize=11, fontweight="bold", pad=8,
    )
    plt.tight_layout()
    return fig


# =============================================================================
# MAIN
# =============================================================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading data...")
    rui, opacity = load_opacity()
    print(f"  RUI events: {len(rui):,} | Opacity events: {len(opacity):,}")

    specs = [
        ("q3_1_stat_card.png",      lambda: chart_stat_card(rui, opacity)),
        ("q3_2_top_structures.png", lambda: chart_top_structures(opacity)),
        ("q3_3_donut.png",          lambda: chart_donut(opacity)),
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
