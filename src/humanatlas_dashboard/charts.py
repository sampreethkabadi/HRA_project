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


def _style(fig, x_label: str = "", y_label: str = ""):
    layout_update = {
        "paper_bgcolor": PALETTE["surface"],
        "plot_bgcolor": "#FFFFFF",
        "font": {"family": "IBM Plex Sans, Avenir Next, Segoe UI Variable, sans-serif", "color": PALETTE["text"]},
        "margin": {"l": 24, "r": 24, "t": 40, "b": 24},
        "legend_title_text": "",
    }
    if x_label:
        layout_update["xaxis_title"] = x_label
    if y_label:
        layout_update["yaxis_title"] = y_label
    fig.update_layout(**layout_update)
    return fig


def line_chart(frame: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = "", x_label: str = "", y_label: str = ""):
    fig = px.line(frame, x=x, y=y, color=color, title=title, markers=True, color_discrete_sequence=COLOR_SEQUENCE)
    return _style(fig, x_label=x_label, y_label=y_label)


def bar_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    title: str = "",
    orientation: str = "v",
    barmode: str = "group",
    x_label: str = "",
    y_label: str = "",
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
    return _style(fig, x_label=x_label, y_label=y_label)


def histogram(frame: pd.DataFrame, x: str, color: str | None = None, title: str = "", x_label: str = "", y_label: str = ""):
    fig = px.histogram(frame, x=x, color=color, title=title, nbins=24, color_discrete_sequence=COLOR_SEQUENCE)
    return _style(fig, x_label=x_label, y_label=y_label)


def scatter_chart(frame: pd.DataFrame, x: str, y: str, color: str | None = None, size: str | None = None, title: str = "", x_label: str = "", y_label: str = ""):
    fig = px.scatter(frame, x=x, y=y, color=color, size=size, title=title, color_discrete_sequence=COLOR_SEQUENCE)
    return _style(fig, x_label=x_label, y_label=y_label)


def funnel_chart(frame: pd.DataFrame, y: str, x: str, color: str | None = None, title: str = ""):
    fig = px.funnel(frame, y=y, x=x, color=color, title=title, color_discrete_sequence=COLOR_SEQUENCE)
    return _style(fig)


def heatmap_chart(frame: pd.DataFrame, x: str, y: str, z: str, title: str = "", x_label: str = "", y_label: str = ""):
    fig = px.density_heatmap(frame, x=x, y=y, z=z, histfunc="sum", title=title, color_continuous_scale="Teal")
    return _style(fig, x_label=x_label, y_label=y_label)


def donut_chart(frame: pd.DataFrame, names: str, values: str, title: str = ""):
    fig = px.pie(frame, names=names, values=values, title=title, hole=0.45, color_discrete_sequence=COLOR_SEQUENCE)
    return _style(fig)
