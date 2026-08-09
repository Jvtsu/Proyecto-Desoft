"""
plotting.plot_residuals
=======================
Residual comparison plots.
"""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from plotting.common import RESIDUAL_PURPLE, MODEL_ORIGINAL_WHITE, apply_layout, dataset_symbol, dataset_opacity
from core.units import F1_DISPLAY_SCALE


def _record_key(record: dict) -> str:
    return str(record.get("id") or record.get("name") or id(record))


def _visible(trace_visibility: dict | None, record: dict, key: str, default: bool = True) -> bool:
    if trace_visibility is None:
        return default
    record_visibility = trace_visibility.get(_record_key(record), {})
    return bool(record_visibility.get(key, default))


def plot_residuals_comparison(records: list[dict], trace_visibility: dict | None = None) -> go.Figure:
    has_f1 = any("res_f1" in rec.get("cache", {}).get("residual_stats_edit", {}) for rec in records)
    rows = 2 if has_f1 else 1
    titles = ["F0 residuals"] + (["F1 residuals"] if has_f1 else [])
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, subplot_titles=titles, vertical_spacing=0.08)

    for idx, record in enumerate(records):
        data = record["data"]
        cache = record.get("cache", {})
        name = record.get("name", f"Dataset {idx+1}")
        res_orig = cache.get("residual_stats_orig", {})
        res_edit = cache.get("residual_stats_edit", {})
        symbol = dataset_symbol(idx)
        opacity = dataset_opacity(idx)

        if _visible(trace_visibility, record, "f0_original", True) and "res_f0" in res_orig:
            fig.add_trace(
                go.Scatter(
                    x=data["mjd"],
                    y=res_orig["res_f0"],
                    mode="markers",
                    marker=dict(color=MODEL_ORIGINAL_WHITE, size=6, symbol=f"{symbol}-open"),
                    name=f"{name}: F0 residual original",
                    legendgroup=name,
                    opacity=opacity,
                ),
                row=1,
                col=1,
            )
        if _visible(trace_visibility, record, "f0_edited", True) and "res_f0" in res_edit:
            fig.add_trace(
                go.Scatter(
                    x=data["mjd"],
                    y=res_edit["res_f0"],
                    mode="markers",
                    marker=dict(color=RESIDUAL_PURPLE, size=6, symbol=symbol),
                    name=f"{name}: F0 residual edited",
                    legendgroup=name,
                    opacity=opacity,
                ),
                row=1,
                col=1,
            )

        if has_f1 and _visible(trace_visibility, record, "f1_original", True) and "res_f1" in res_orig:
            fig.add_trace(
                go.Scatter(
                    x=data["mjd"],
                    y=res_orig["res_f1"] * F1_DISPLAY_SCALE,
                    mode="markers",
                    marker=dict(color=MODEL_ORIGINAL_WHITE, size=6, symbol=f"{symbol}-open"),
                    name=f"{name}: F1 residual original",
                    legendgroup=name,
                    opacity=opacity,
                ),
                row=2,
                col=1,
            )
        if has_f1 and _visible(trace_visibility, record, "f1_edited", True) and "res_f1" in res_edit:
            fig.add_trace(
                go.Scatter(
                    x=data["mjd"],
                    y=res_edit["res_f1"] * F1_DISPLAY_SCALE,
                    mode="markers",
                    marker=dict(color=RESIDUAL_PURPLE, size=6, symbol=symbol),
                    name=f"{name}: F1 residual edited",
                    legendgroup=name,
                    opacity=opacity,
                ),
                row=2,
                col=1,
            )

    for row in range(1, rows + 1):
        fig.add_hline(y=0, line=dict(color="rgba(255,255,255,0.35)", width=1), row=row, col=1)

    fig = apply_layout(fig, "Residuals", height=720 if has_f1 else 500)
    fig.update_xaxes(title_text="MJD [days]", row=rows, col=1)
    fig.update_yaxes(title_text="ΔF0 [Hz]", row=1, col=1)
    if has_f1:
        fig.update_yaxes(title_text="ΔF1 [10^-15 Hz/s]", row=2, col=1)
    return fig


def plot_residuals_comparison_legacy(data=None, res_orig=None, res_edit=None, **kwargs):
    record = {"name": "Dataset", "data": data or {}, "cache": {"residual_stats_orig": res_orig or {}, "residual_stats_edit": res_edit or {}}}
    return plot_residuals_comparison([record])
