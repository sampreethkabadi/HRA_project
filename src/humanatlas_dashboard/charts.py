from __future__ import annotations

import pandas as pd
import plotly.express as px


PALETTE = {
    "primary": "#0F766E",
    "secondary": "#F97316",
    "accent": "#164E63",
    "rose": "#BE123C",
    "surface": "#F5F3EF",
    "text": "#1F2937",
}

COLOR_SEQUENCE = [
    PALETTE["primary"],
    PALETTE["secondary"],
    PALETTE["accent"],
    "#7C3AED",
    "#65A30D",
    PALETTE["rose"],
]


def _style(fig):
    fig.update_layout(
        paper_bgcolor=PALETTE["surface"],
        plot_bgcolor="#FFFFFF",
        font={"family": "IBM Plex Sans, Avenir Next, Segoe UI Variable, sans-serif", "color": PALETTE["text"]},
        margin={"l": 24, "r": 24, "t": 40, "b": 24},
        legend_title_text="",
    )
    return fig


def line_chart(frame: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = ""):
    fig = px.line(frame, x=x, y=y, color=color, title=title, markers=True, color_discrete_sequence=COLOR_SEQUENCE)
    return _style(fig)


def bar_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    title: str = "",
    orientation: str = "v",
    barmode: str = "group",
):
    fig = px.bar(
        frame,
        x=x,
        y=y,
        color=color,
        title=title,
        orientation=orientation,
        barmode=barmode,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    return _style(fig)


def histogram(frame: pd.DataFrame, x: str, color: str | None = None, title: str = ""):
    fig = px.histogram(frame, x=x, color=color, title=title, nbins=24, color_discrete_sequence=COLOR_SEQUENCE)
    return _style(fig)


def scatter_chart(frame: pd.DataFrame, x: str, y: str, color: str | None = None, size: str | None = None, title: str = ""):
    fig = px.scatter(frame, x=x, y=y, color=color, size=size, title=title, color_discrete_sequence=COLOR_SEQUENCE)
    return _style(fig)


def funnel_chart(frame: pd.DataFrame, y: str, x: str, color: str | None = None, title: str = ""):
    fig = px.funnel(frame, y=y, x=x, color=color, title=title, color_discrete_sequence=COLOR_SEQUENCE)
    return _style(fig)


def heatmap_chart(frame: pd.DataFrame, x: str, y: str, z: str, title: str = ""):
    fig = px.density_heatmap(frame, x=x, y=y, z=z, histfunc="sum", title=title, color_continuous_scale="Teal")
    return _style(fig)
