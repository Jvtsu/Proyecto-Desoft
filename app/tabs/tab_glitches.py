from __future__ import annotations

import pandas as pd
import streamlit as st

import app.state as state
from app.callbacks import compute_visible_datasets, update_glitch_param, add_glitch, remove_glitch, toggle_glitch
from plotting.plot_glitches import plot_glitch_timeline, plot_glitch_amplitudes


def _component_type(glitch: dict) -> str:
    has_perm = any(key in glitch for key in ["GLPH", "GLF0", "GLF1", "GLF2"])
    has_exp = any(key in glitch for key in ["GLF0D", "GLTD"])
    if has_perm and has_exp:
        return "Permanent + exponential"
    if has_exp:
        return "Exponential"
    if has_perm:
        return "Permanent"
    return "No frequency terms"


def _glitch_rows(records: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for record in records:
        active = record.get("active_glitch_indices")
        for idx, glitch in enumerate(record.get("params_edited", {}).get("glitches", []), start=1):
            glep = glitch.get("GLEP")
            rows.append(
                {
                    "Pulsar": record.get("pulsar_name") or "Unidentified pulsar",
                    "Dataset": record.get("name"),
                    "Component": f"G{idx}",
                    "Event GLEP [MJD]": float(glep) if glep is not None else None,
                    "Type": _component_type(glitch),
                    "GLF0 [Hz]": float(glitch.get("GLF0", 0.0)),
                    "GLF1 [Hz/s]": float(glitch.get("GLF1", 0.0)),
                    "GLF2 [Hz/s^2]": float(glitch.get("GLF2", 0.0)),
                    "GLF0D [Hz]": float(glitch.get("GLF0D", 0.0)),
                    "GLTD [days]": float(glitch.get("GLTD", 0.0)),
                    "Included in model": active is None or idx in active,
                }
            )
    return rows


def render_glitches_tab() -> None:
    records = compute_visible_datasets()
    if not records:
        st.info("No visible datasets selected.")
        return

    st.subheader("Glitch Analysis")
    st.caption(
        "Green markers identify glitch epochs from the timing model. If multiple components share the same GLEP, "
        "they are interpreted as components of the same physical glitch event, for example several exponential recovery "
        "terms with different GLTD time-scales."
    )

    st.plotly_chart(plot_glitch_timeline(records), use_container_width=True)

    rows = _glitch_rows(records)
    if rows:
        st.markdown("#### Glitch component catalogue")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No glitches are listed in the visible timing models.")

    active_id = state.get("active_dataset_id")
    record = state.get_dataset(active_id)
    if record is None:
        st.info("Select a dataset in the instrument panel to edit glitch parameters.")
        return

    st.markdown(f"#### Editable glitch components · {record.get('pulsar_name') or record.get('name', active_id)}")
    st.caption("GLTD is interpreted in days, while GLF0D is interpreted in Hz. These terms describe transient exponential recovery.")
    st.plotly_chart(plot_glitch_amplitudes(record), use_container_width=True)

    glitches = record["params_edited"].setdefault("glitches", [])
    if not glitches:
        st.info("The selected timing model contains no glitches.")

    active_indices = record.get("active_glitch_indices")
    for idx, glitch in enumerate(glitches):
        glep = glitch.get("GLEP")
        title = f"Component G{idx + 1}"
        if glep is not None:
            title += f" · GLEP {float(glep):.6f}"
        if "GLTD" in glitch:
            title += f" · tau {float(glitch.get('GLTD', 0.0)):.3g} d"
        active_default = active_indices is None or (idx + 1) in active_indices
        with st.expander(title, expanded=False):
            active = st.checkbox("Include component in model", value=active_default, key=f"active_{active_id}_{idx}")
            toggle_glitch(active_id, idx + 1, active)

            st.markdown("Permanent terms")
            cols = st.columns(4)
            for col, key in zip(cols, ["GLEP", "GLF0", "GLF1", "GLF2"]):
                with col:
                    value = float(glitch.get(key, 0.0))
                    new_value = st.number_input(key, value=value, format="%.12e", key=f"{active_id}_{idx}_{key}")
                    if new_value != value:
                        update_glitch_param(active_id, idx, key, new_value)
                        st.rerun()

            st.markdown("Exponential recovery terms")
            cols = st.columns(2)
            for col, key in zip(cols, ["GLF0D", "GLTD"]):
                with col:
                    value = float(glitch.get(key, 0.0))
                    new_value = st.number_input(key, value=value, format="%.12e", key=f"{active_id}_{idx}_{key}")
                    if new_value != value:
                        update_glitch_param(active_id, idx, key, new_value)
                        st.rerun()

            if st.button("Remove component", key=f"remove_{active_id}_{idx}"):
                remove_glitch(active_id, idx)
                st.rerun()

    if st.button("Add glitch component to selected dataset", use_container_width=True):
        add_glitch(active_id)
        st.rerun()
