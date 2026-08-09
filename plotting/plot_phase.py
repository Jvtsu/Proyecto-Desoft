"""
plotting.plot_phase
===================
Phase evolution and derivative consistency plots.
"""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from plotting.common import (
    PHASE_CYAN,
    DERIV1_BLUE,
    DERIV2_ORANGE,
    apply_layout,
    dataset_line_style,
    dataset_opacity,
)
from core.units import F1_DISPLAY_SCALE


def _record_key(record: dict) -> str:
    return str(record.get("id") or record.get("name") or id(record))


def _visible(trace_visibility: dict | None, record: dict, key: str, default: bool = True) -> bool:
    if trace_visibility is None:
        return default
    record_visibility = trace_visibility.get(_record_key(record), {})
    return bool(record_visibility.get(key, default))


def plot_phase_evolution(
    records: list[dict],
    show_original: bool = True,
    show_edited: bool = True,
    trace_visibility: dict | None = None,
) -> go.Figure:
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        subplot_titles=["Phase", "First phase derivative", "Second phase derivative"],
        vertical_spacing=0.08,
    )

    for idx, record in enumerate(records):
        data = record["data"]
        cache = record.get("cache", {})
        model_mjd = cache.get("model_mjd", data["mjd"])
        name = record.get("name", f"Dataset {idx+1}")
        style = dataset_line_style(idx)
        opacity = dataset_opacity(idx)

        if show_original and _visible(trace_visibility, record, "phase_original", True) and "phi_orig" in cache:
            fig.add_trace(
                go.Scatter(
                    x=model_mjd,
                    y=cache["phi_orig"],
                    mode="lines",
                    line=dict(color=PHASE_CYAN, width=1.9, dash="solid" if idx == 0 else style),
                    name=f"{name}: phase original",
                    legendgroup=name,
                    opacity=opacity,
                ),
                row=1,
                col=1,
            )
        if show_original and _visible(trace_visibility, record, "derivative1_original", True) and "phi_dot_orig" in cache:
            fig.add_trace(
                go.Scatter(
                    x=model_mjd,
                    y=cache["phi_dot_orig"],
                    mode="lines",
                    line=dict(color=DERIV1_BLUE, width=1.7, dash="solid" if idx == 0 else style),
                    name=f"{name}: derivative 1 original",
                    legendgroup=name,
                    opacity=opacity,
                ),
                row=2,
                col=1,
            )
        if show_original and _visible(trace_visibility, record, "derivative2_original", True) and "phi_ddot_orig" in cache:
            fig.add_trace(
                go.Scatter(
                    x=model_mjd,
                    y=cache["phi_ddot_orig"] * F1_DISPLAY_SCALE,
                    mode="lines",
                    line=dict(color=DERIV2_ORANGE, width=1.7, dash="solid" if idx == 0 else style),
                    name=f"{name}: derivative 2 original",
                    legendgroup=name,
                    opacity=opacity,
                ),
                row=3,
                col=1,
            )

        if show_edited and _visible(trace_visibility, record, "phase_edited", True) and "phi_edit" in cache:
            fig.add_trace(
                go.Scatter(
                    x=model_mjd,
                    y=cache["phi_edit"],
                    mode="lines",
                    line=dict(color=PHASE_CYAN, width=2.2, dash="dash" if idx == 0 else "dashdot"),
                    name=f"{name}: phase edited",
                    legendgroup=name,
                    opacity=opacity,
                ),
                row=1,
                col=1,
            )
        if show_edited and _visible(trace_visibility, record, "derivative1_edited", True) and "phi_dot_edit" in cache:
            fig.add_trace(
                go.Scatter(
                    x=model_mjd,
                    y=cache["phi_dot_edit"],
                    mode="lines",
                    line=dict(color=DERIV1_BLUE, width=2.0, dash="dash" if idx == 0 else "dashdot"),
                    name=f"{name}: derivative 1 edited",
                    legendgroup=name,
                    opacity=opacity,
                ),
                row=2,
                col=1,
            )
        if show_edited and _visible(trace_visibility, record, "derivative2_edited", True) and "phi_ddot_edit" in cache:
            fig.add_trace(
                go.Scatter(
                    x=model_mjd,
                    y=cache["phi_ddot_edit"] * F1_DISPLAY_SCALE,
                    mode="lines",
                    line=dict(color=DERIV2_ORANGE, width=2.0, dash="dash" if idx == 0 else "dashdot"),
                    name=f"{name}: derivative 2 edited",
                    legendgroup=name,
                    opacity=opacity,
                ),
                row=3,
                col=1,
            )

    fig = apply_layout(fig, "Phase Evolution", height=820)
    fig.update_xaxes(title_text="MJD [days]", row=3, col=1)
    fig.update_yaxes(title_text="Phase [cycles]", row=1, col=1)
    fig.update_yaxes(title_text="dPhase/dt [Hz]", row=2, col=1)
    fig.update_yaxes(title_text="d²Phase/dt² [10^-15 Hz/s]", row=3, col=1)
    return fig


def plot_phase_consistency(records: list[dict], trace_visibility: dict | None = None) -> go.Figure:
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=["dPhase/dt − F0", "d²Phase/dt² − F1"],
        vertical_spacing=0.10,
    )
    for idx, record in enumerate(records):
        data = record["data"]
        cache = record.get("cache", {})
        model_mjd = cache.get("model_mjd", data["mjd"])
        name = record.get("name", f"Dataset {idx+1}")
        opacity = dataset_opacity(idx)
        if _visible(trace_visibility, record, "consistency_d1", True) and "phi_dot_edit" in cache and "f0_model_edit" in cache:
            fig.add_trace(
                go.Scatter(
                    x=model_mjd,
                    y=cache["phi_dot_edit"] - cache["f0_model_edit"],
                    mode="lines",
                    line=dict(color=DERIV1_BLUE, width=1.6, dash="solid" if idx == 0 else "dot"),
                    name=f"{name}: dPhase/dt - F0",
                    opacity=opacity,
                ),
                row=1,
                col=1,
            )
        if _visible(trace_visibility, record, "consistency_d2", True) and "phi_ddot_edit" in cache and "f1_model_edit" in cache:
            fig.add_trace(
                go.Scatter(
                    x=model_mjd,
                    y=(cache["phi_ddot_edit"] - cache["f1_model_edit"]) * F1_DISPLAY_SCALE,
                    mode="lines",
                    line=dict(color=DERIV2_ORANGE, width=1.6, dash="solid" if idx == 0 else "dot"),
                    name=f"{name}: d²Phase/dt² - F1",
                    opacity=opacity,
                ),
                row=2,
                col=1,
            )
    fig = apply_layout(fig, "Phase Derivative Consistency", height=580)
    fig.update_xaxes(title_text="MJD [days]", row=2, col=1)
    fig.update_yaxes(title_text="Hz", row=1, col=1)
    fig.update_yaxes(title_text="10^-15 Hz/s", row=2, col=1)
    return fig
