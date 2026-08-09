"""
plotting.plot_data
==================
Raw observational data overview.
"""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from plotting.common import OBSERVATIONAL_CYAN, apply_layout, dataset_symbol, dataset_opacity
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


def plot_data_overview(records: list[dict], trace_visibility: dict | None = None) -> go.Figure:
    has_f1 = any("f1" in record["data"] for record in records)
    rows = 2 if has_f1 else 1
    titles = ["F0 observations"] + (["F1 observations"] if has_f1 else [])
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, subplot_titles=titles, vertical_spacing=0.08)

    for idx, record in enumerate(records):
        data = record["data"]
        name = record.get("name", f"Dataset {idx+1}")
        opacity = dataset_opacity(idx)
        symbol = dataset_symbol(idx)
        err_f0 = _err(data, "err_f0", "f0_err")
        if _visible(trace_visibility, record, "f0_data", True):
            fig.add_trace(
                go.Scatter(
                    x=data["mjd"],
                    y=data["f0"],
                    mode="markers",
                    marker=dict(color=OBSERVATIONAL_CYAN, size=5, symbol=symbol, line=dict(width=0.6, color="rgba(255,255,255,0.35)")),
                    error_y=dict(array=err_f0, visible=err_f0 is not None, thickness=1, width=3, color=OBSERVATIONAL_CYAN),
                    name=f"{name}: F0",
                    opacity=opacity,
                ),
                row=1,
                col=1,
            )
        if has_f1 and _visible(trace_visibility, record, "f1_data", True) and "f1" in data:
            err_f1 = _err(data, "err_f1", "f1_err")
            fig.add_trace(
                go.Scatter(
                    x=data["mjd"],
                    y=data["f1"] * F1_DISPLAY_SCALE,
                    mode="markers",
                    marker=dict(color=OBSERVATIONAL_CYAN, size=5, symbol=symbol, line=dict(width=0.6, color="rgba(255,255,255,0.35)")),
                    error_y=dict(array=err_f1 * F1_DISPLAY_SCALE if err_f1 is not None else None, visible=err_f1 is not None, thickness=1, width=3, color=OBSERVATIONAL_CYAN),
                    name=f"{name}: F1",
                    showlegend=False,
                    opacity=opacity,
                ),
                row=2,
                col=1,
            )

    fig = apply_layout(fig, "Dataset Inspector", height=670 if has_f1 else 460)
    fig.update_xaxes(title_text="MJD [days]", row=rows, col=1)
    fig.update_yaxes(title_text="F0 [Hz]", row=1, col=1)
    if has_f1:
        fig.update_yaxes(title_text="F1 [10^-15 Hz/s]", row=2, col=1)
    return fig
