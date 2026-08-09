"""
plotting.plot_glitches
======================
Glitch timeline and amplitude diagnostics.
"""

from __future__ import annotations

from collections import defaultdict

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from plotting.common import GLITCH_GREEN, MODEL_EDITED_RED, apply_layout, dataset_symbol, dataset_opacity


def _event_key(glep: float) -> float:
    return round(float(glep), 8)


def _component_description(index: int, glitch: dict, enabled: bool) -> str:
    terms = []
    if any(key in glitch for key in ["GLF0", "GLF1", "GLF2", "GLPH"]):
        terms.append("permanent")
    if "GLF0D" in glitch or "GLTD" in glitch:
        tau = glitch.get("GLTD")
        terms.append(f"exponential tau={float(tau):.3g} d" if tau is not None else "exponential")
    kind = " + ".join(terms) if terms else "no frequency terms"
    status = "included" if enabled else "ignored"
    return (
        f"G{index}: {kind}; {status}<br>"
        f"GLPH={float(glitch.get('GLPH', 0.0)):.3e}, "
        f"GLF0={float(glitch.get('GLF0', 0.0)):.3e}, "
        f"GLF1={float(glitch.get('GLF1', 0.0)):.3e}, "
        f"GLF2={float(glitch.get('GLF2', 0.0)):.3e}, "
        f"GLF0D={float(glitch.get('GLF0D', 0.0)):.3e}, "
        f"GLTD={float(glitch.get('GLTD', 0.0)):.3g} d"
    )


def plot_glitch_timeline(records: list[dict]) -> go.Figure:
    fig = go.Figure()
    if not records:
        fig.add_annotation(text="No datasets selected", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        return apply_layout(fig, "Glitch Analysis", height=350)

    for didx, record in enumerate(records):
        active = record.get("active_glitch_indices")
        grouped: dict[float, list[tuple[int, dict, bool]]] = defaultdict(list)
        for gidx, glitch in enumerate(record.get("params_edited", {}).get("glitches", []), start=1):
            glep = glitch.get("GLEP")
            if glep is None:
                continue
            enabled = active is None or gidx in active
            grouped[_event_key(float(glep))].append((gidx, glitch, enabled))

        xs, ys, labels, hover = [], [], [], []
        for glep in sorted(grouped):
            components = grouped[glep]
            indices = [idx for idx, _, _ in components]
            label = "/".join(f"G{idx}" for idx in indices)
            if len(label) > 14:
                label = f"G{indices[0]}–G{indices[-1]}"
            component_lines = [_component_description(idx, glitch, enabled) for idx, glitch, enabled in components]
            xs.append(glep)
            ys.append(record.get("pulsar_name") or record.get("name", f"Dataset {didx+1}"))
            labels.append(label)
            hover.append(
                f"Dataset: {record.get('name')}<br>"
                f"Pulsar: {record.get('pulsar_name') or 'Unidentified pulsar'}<br>"
                f"Event epoch: {glep:.8f} MJD<br>"
                f"Components at this epoch: {len(components)}<br><br>"
                + "<br><br>".join(component_lines)
            )

        if xs:
            fig.add_trace(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="markers+text",
                    marker=dict(
                        color=GLITCH_GREEN,
                        size=13,
                        symbol=dataset_symbol(didx),
                        line=dict(color="rgba(255,255,255,0.45)", width=0.9),
                    ),
                    text=labels,
                    textposition="top center",
                    textfont=dict(color=GLITCH_GREEN, size=10),
                    hovertext=hover,
                    hovertemplate="%{hovertext}<extra></extra>",
                    name=record.get("name", f"Dataset {didx+1}"),
                    opacity=dataset_opacity(didx),
                )
            )

    fig = apply_layout(fig, "Glitch Analysis", height=430)
    fig.update_xaxes(title_text="Glitch epoch GLEP [MJD]")
    fig.update_yaxes(title_text="Dataset / pulsar")
    return fig


def plot_glitch_amplitudes(record: dict | None) -> go.Figure:
    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=["|GLF0|", "|GLF1|", "Exponential recovery"],
        horizontal_spacing=0.10,
    )
    if record is None:
        return apply_layout(fig, "Glitch Amplitudes", height=360)

    glitches = record.get("params_edited", {}).get("glitches", [])
    labels = [f"G{i}" for i in range(1, len(glitches) + 1)]
    fig.add_trace(
        go.Bar(x=labels, y=[abs(float(g.get("GLF0", 0.0))) for g in glitches], name="|GLF0|", marker=dict(color=GLITCH_GREEN)),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(x=labels, y=[abs(float(g.get("GLF1", 0.0))) for g in glitches], name="|GLF1|", marker=dict(color="rgba(119,232,81,0.75)")),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Bar(x=labels, y=[abs(float(g.get("GLF0D", 0.0))) for g in glitches], name="|GLF0D|", marker=dict(color=MODEL_EDITED_RED)),
        row=1,
        col=3,
    )
    # Tau is shown as hover text because it has different units.
    fig.update_traces(
        hovertemplate="%{x}<br>value: %{y:.3e}<extra></extra>",
        row=1,
        col=1,
    )
    fig.update_traces(
        hovertemplate="%{x}<br>value: %{y:.3e}<extra></extra>",
        row=1,
        col=2,
    )
    fig.update_traces(
        hovertext=[f"GLTD={float(g.get('GLTD', 0.0)):.6g} d" for g in glitches],
        hovertemplate="%{x}<br>|GLF0D|: %{y:.3e} Hz<br>%{hovertext}<extra></extra>",
        row=1,
        col=3,
    )
    fig = apply_layout(fig, f"Glitch Amplitudes · {record.get('name', '')}", height=410)
    fig.update_yaxes(title_text="Hz", row=1, col=1)
    fig.update_yaxes(title_text="Hz/s", row=1, col=2)
    fig.update_yaxes(title_text="Hz", row=1, col=3)
    return fig
