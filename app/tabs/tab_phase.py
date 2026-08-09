from __future__ import annotations

import streamlit as st

import app.state as state
from app.callbacks import compute_visible_datasets
from app.plot_visibility import render_trace_controls
from plotting.plot_phase import plot_phase_evolution, plot_phase_consistency


def render_phase_tab() -> None:
    records = compute_visible_datasets()
    if not records:
        st.info("No visible datasets selected.")
        return

    st.subheader("Phase Evolution")
    st.caption(
        "Phase is shown in cyan, the first derivative in blue, and the second derivative in orange. "
        "Use the checkbox legend below to show or hide each model component."
    )

    phase_visibility = render_trace_controls(
        "phase_evolution",
        records,
        [
            ("phase_original", "Phase original", True),
            ("phase_edited", "Phase edited", True),
            ("derivative1_original", "dPhase/dt original", True),
            ("derivative1_edited", "dPhase/dt edited", True),
            ("derivative2_original", "d²Phase/dt² original", True),
            ("derivative2_edited", "d²Phase/dt² edited", True),
        ],
        title="Checkbox legend · Phase Evolution",
        expanded=True,
        columns=3,
    )

    fig = plot_phase_evolution(
        records,
        show_original=state.get("show_original"),
        show_edited=state.get("show_edited"),
        trace_visibility=phase_visibility,
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Phase-model consistency diagnostic", expanded=False):
        st.caption(
            "These curves show the agreement between analytic phase derivatives and the edited timing model. "
            "Use the controls below to isolate each diagnostic trace."
        )
        consistency_visibility = render_trace_controls(
            "phase_consistency",
            records,
            [
                ("consistency_d1", "dPhase/dt − F0", True),
                ("consistency_d2", "d²Phase/dt² − F1", True),
            ],
            title="Checkbox legend · Consistency diagnostic",
            expanded=True,
            columns=2,
        )
        st.plotly_chart(plot_phase_consistency(records, trace_visibility=consistency_visibility), use_container_width=True)
