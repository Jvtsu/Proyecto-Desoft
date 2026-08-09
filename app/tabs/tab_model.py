from __future__ import annotations

import streamlit as st

import app.state as state
from app.callbacks import compute_visible_datasets
from app.plot_visibility import render_grouped_trace_controls
from plotting.plot_model import plot_timing_models


def render_model_tab() -> None:
    records = compute_visible_datasets()
    if not records:
        st.info("No visible datasets selected.")
        return

    st.subheader("Spin Evolution")
    st.caption(
        "This view separates observational measurements from the timing model. "
        "Cyan markers are measured values from the .dat file, white solid curves are the original .par model, "
        "red dashed curves are the edited model, and green markers indicate glitch epochs."
    )

    has_f1 = any("f1" in record["data"] for record in records)

    visibility_groups = [
        {
            "title": "F0(t) · Spin frequency",
            "description": "Controls for the upper panel. F0 is the pulsar spin frequency in Hz.",
            "options": [
                ("f0_data", "F0 observed data · cyan markers from .dat", True),
                ("f0_original", "F0 original model · white solid line from .par", True),
                ("f0_edited", "F0 edited model · red dashed line", True),
            ],
        },
    ]

    if has_f1:
        visibility_groups.append(
            {
                "title": "F1(t) · First frequency derivative",
                "description": "Controls for the lower panel. F1 describes the spin-down rate in 10^-15 Hz/s.",
                "options": [
                    ("f1_data", "F1 observed data · cyan markers from .dat", True),
                    ("f1_original", "F1 original model · white solid line from .par", True),
                    ("f1_edited", "F1 edited model · red dashed line", True),
                ],
            }
        )

    visibility_groups.append(
        {
            "title": "Glitch markers",
            "description": "Vertical green markers show the glitch epochs GLEP that are included in the model display.",
            "options": [
                ("glitches", "Glitch epochs · green vertical markers", True),
            ],
        }
    )

    trace_visibility = render_grouped_trace_controls(
        "spin_evolution",
        records,
        visibility_groups,
        title="Plot layer selector · Spin Evolution",
        expanded=True,
        columns=3,
        help_text=(
            "Use these controls to isolate each physical layer. The Plotly legend can also be clicked, "
            "but this selector makes clear which curve belongs to F0, F1, the original model, or the edited model."
        ),
    )

    fig = plot_timing_models(
        records,
        show_original=state.get("show_original"),
        show_edited=state.get("show_edited"),
        use_glitches=state.get("use_glitches"),
        trace_visibility=trace_visibility,
    )
    st.plotly_chart(fig, use_container_width=True)
