"""
plotting.common
===============
Shared Plotly styling and helpers.
"""

from __future__ import annotations

import plotly.graph_objects as go

# Observatory palette
OBSERVATIONAL_CYAN = "#64B5F6"
MODEL_ORIGINAL_WHITE = "#FFFFFF"
MODEL_EDITED_RED = "#F7350C"
GLITCH_GREEN = "#77E851"
RESIDUAL_PURPLE = "#6273E3"
PHASE_CYAN = OBSERVATIONAL_CYAN
DERIV1_BLUE = "#0022FF"
DERIV2_ORANGE = "#FF7B00"
GRID_COLOR = "rgba(157, 178, 191, 0.12)"
AXIS_COLOR = "rgba(255,255,255,0.18)"
PLOT_BG = "#0E1522"
PAPER_BG = "rgba(0,0,0,0)"
TEXT_COLOR = "#E8EEF8"
MUTED_TEXT = "#9DB2C7"
CARD_BG = "rgba(18, 28, 45, 0.95)"
CARD_BORDER = "rgba(103, 126, 157, 0.35)"

DATASET_SYMBOLS = ["circle", "diamond"]
DATASET_LINE_STYLES = ["solid", "dot"]
ORIGINAL_DASH = "solid"
EDITED_DASH = "dash"

LAYOUT_BASE = dict(
    paper_bgcolor=PAPER_BG,
    plot_bgcolor=PLOT_BG,
    font=dict(color=TEXT_COLOR, size=12),
    margin=dict(l=62, r=28, t=70, b=60),
    legend=dict(
        orientation="v",
        bgcolor="rgba(8, 14, 24, 0.75)",
        bordercolor=CARD_BORDER,
        borderwidth=1,
        x=1.02,
        y=1,
        xanchor="left",
        yanchor="top",
        font=dict(size=12),
    ),
    hovermode="x unified",
)


def apply_layout(fig: go.Figure, title: str, height: int = 600) -> go.Figure:
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=title, x=0.02, font=dict(size=19, color=TEXT_COLOR)),
        height=height,
    )
    fig.update_xaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=AXIS_COLOR,
        showline=True,
        linecolor=AXIS_COLOR,
        ticks="outside",
        tickcolor=AXIS_COLOR,
        title_font=dict(size=13, color=TEXT_COLOR),
    )
    fig.update_yaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=AXIS_COLOR,
        showline=True,
        linecolor=AXIS_COLOR,
        ticks="outside",
        tickcolor=AXIS_COLOR,
        title_font=dict(size=13, color=TEXT_COLOR),
    )
    return fig


def dataset_symbol(index: int) -> str:
    return DATASET_SYMBOLS[index % len(DATASET_SYMBOLS)]


def dataset_line_style(index: int) -> str:
    return DATASET_LINE_STYLES[index % len(DATASET_LINE_STYLES)]


def dataset_opacity(index: int) -> float:
    return 1.0 if index == 0 else 0.82


def add_glitch_lines(fig: go.Figure, record: dict, row: int | None = None, col: int | None = None) -> None:
    active = record.get("active_glitch_indices")
    for idx, glitch in enumerate(record.get("params_edited", {}).get("glitches", []), start=1):
        if active is not None and idx not in active:
            continue
        glep = glitch.get("GLEP")
        if glep is None:
            continue
        kwargs = dict(
            x=float(glep),
            line=dict(color="rgba(119, 232, 81, 0.55)", dash="dot", width=1),
            annotation_text=f"G{idx}",
            annotation_position="top",
            annotation_font=dict(color=GLITCH_GREEN, size=9),
        )
        if row is not None and col is not None:
            kwargs.update(row=row, col=col)
        fig.add_vline(**kwargs)
