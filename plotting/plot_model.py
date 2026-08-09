"""
plotting.plot_model
===================
Spin evolution plots: observational data with original and edited timing models.
"""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from plotting.common import (
    OBSERVATIONAL_CYAN,
    MODEL_ORIGINAL_WHITE,
    MODEL_EDITED_RED,
    apply_layout,
    add_glitch_lines,
    dataset_symbol,
    dataset_line_style,
    dataset_opacity,
)
from core.units import F1_DISPLAY_SCALE


def _err(data: dict, *names: str):
    for name in names:
        if name in data:
            return data[name]
    return None


def _record_key(record: dict) -> str:
    return str(record.get("id") or record.get("name") or id(record))


def _visible(trace_visibility: dict | None, record: dict, key: str, default: bool = True) -> bool:
    if trace_visibility is None:
        return default
    record_visibility = trace_visibility.get(_record_key(record), {})
    return bool(record_visibility.get(key, default))


def plot_timing_models(
    records: list[dict],
    show_original: bool = True,
    show_edited: bool = True,
    use_glitches: bool = True,
    trace_visibility: dict | None = None,
) -> go.Figure:
    has_f1 = any("f1" in record["data"] for record in records)
    rows = 2 if has_f1 else 1
    titles = ["F0(t) · Spin frequency"] + (["F1(t) · First frequency derivative"] if has_f1 else [])
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, subplot_titles=titles, vertical_spacing=0.08)

    for idx, record in enumerate(records):
        data = record["data"]
        cache = record.get("cache", {})
        model_mjd = cache.get("model_mjd", data["mjd"])
        name = record.get("name", f"Dataset {idx+1}")
        symbol = dataset_symbol(idx)
        style = dataset_line_style(idx)
        opacity = dataset_opacity(idx)

        if _visible(trace_visibility, record, "f0_data", True):
            fig.add_trace(
                go.Scatter(
                    x=data["mjd"],
                    y=data["f0"],
                    mode="markers",
                    marker=dict(color=OBSERVATIONAL_CYAN, size=5, symbol=symbol, line=dict(width=0.6, color="rgba(255,255,255,0.35)")),
                    error_y=dict(array=_err(data, "err_f0", "f0_err"), visible=_err(data, "err_f0", "f0_err") is not None, thickness=1, width=3, color=OBSERVATIONAL_CYAN),
                    name=f"{name}: F0 observed data",
                    legendgroup=name,
                    opacity=opacity,
                ),
                row=1,
                col=1,
            )
        if show_original and _visible(trace_visibility, record, "f0_original", True) and "f0_model_orig" in cache:
            fig.add_trace(
                go.Scatter(
                    x=model_mjd,
                    y=cache["f0_model_orig"],
                    mode="lines",
                    line=dict(color=MODEL_ORIGINAL_WHITE, width=2.2, dash="solid" if idx == 0 else style),
                    name=f"{name}: F0 original model",
                    legendgroup=name,
                    opacity=opacity,
                ),
                row=1,
                col=1,
            )
        if show_edited and _visible(trace_visibility, record, "f0_edited", True) and "f0_model_edit" in cache:
            fig.add_trace(
                go.Scatter(
                    x=model_mjd,
                    y=cache["f0_model_edit"],
                    mode="lines",
                    line=dict(color=MODEL_EDITED_RED, width=2.2, dash="dash" if idx == 0 else "dashdot"),
                    name=f"{name}: F0 edited model",
                    legendgroup=name,
                    opacity=opacity,
                ),
                row=1,
                col=1,
            )

        if has_f1 and _visible(trace_visibility, record, "f1_data", True) and "f1" in data:
            fig.add_trace(
                go.Scatter(
                    x=data["mjd"],
                    y=data["f1"] * F1_DISPLAY_SCALE,
                    mode="markers",
                    marker=dict(color=OBSERVATIONAL_CYAN, size=5, symbol=symbol, line=dict(width=0.6, color="rgba(255,255,255,0.35)")),
                    error_y=dict(array=_err(data, "err_f1", "f1_err") * F1_DISPLAY_SCALE if _err(data, "err_f1", "f1_err") is not None else None, visible=_err(data, "err_f1", "f1_err") is not None, thickness=1, width=3, color=OBSERVATIONAL_CYAN),
                    name=f"{name}: F1 observed data",
                    legendgroup=name,
                    showlegend=True,
                    opacity=opacity,
                ),
                row=2,
                col=1,
            )
        if has_f1 and show_original and _visible(trace_visibility, record, "f1_original", True) and "f1_model_orig" in cache:
            fig.add_trace(
                go.Scatter(
                    x=model_mjd,
                    y=cache["f1_model_orig"] * F1_DISPLAY_SCALE,
                    mode="lines",
                    line=dict(color=MODEL_ORIGINAL_WHITE, width=2.1, dash="solid" if idx == 0 else style),
                    name=f"{name}: F1 original model",
                    legendgroup=name,
                    showlegend=True,
                    opacity=opacity,
                ),
                row=2,
                col=1,
            )
        if has_f1 and show_edited and _visible(trace_visibility, record, "f1_edited", True) and "f1_model_edit" in cache:
            fig.add_trace(
                go.Scatter(
                    x=model_mjd,
                    y=cache["f1_model_edit"] * F1_DISPLAY_SCALE,
                    mode="lines",
                    line=dict(color=MODEL_EDITED_RED, width=2.1, dash="dash" if idx == 0 else "dashdot"),
                    name=f"{name}: F1 edited model",
                    legendgroup=name,
                    showlegend=True,
                    opacity=opacity,
                ),
                row=2,
                col=1,
            )

        if use_glitches and _visible(trace_visibility, record, "glitches", True):
            add_glitch_lines(fig, record, row=1, col=1)
            if has_f1:
                add_glitch_lines(fig, record, row=2, col=1)

    fig = apply_layout(fig, "Spin Evolution", height=740 if has_f1 else 500)
    fig.update_xaxes(title_text="MJD [days]", row=rows, col=1)
    fig.update_yaxes(title_text="F0 [Hz]", row=1, col=1)
    if has_f1:
        fig.update_yaxes(title_text="F1 [10^-15 Hz/s]", row=2, col=1)
    return fig
