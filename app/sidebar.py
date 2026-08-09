"""
app.sidebar
===========
Instrument-style sidebar for loading and controlling up to two pulsar datasets.
"""

from __future__ import annotations

import streamlit as st

import app.state as state
from app.callbacks import load_dataset_pair, reset_to_original


def _slot_signature(par_file, dat_file) -> tuple[str, str, int, int] | None:
    if par_file is None or dat_file is None:
        return None
    return (par_file.name, dat_file.name, par_file.size, dat_file.size)



def _dataset_card(record: dict) -> str:
    data = record.get("data", {})
    raw_data = record.get("raw_data", data)
    validity = record.get("par_validity", {})

    mjd_text = "No data inside model interval"
    if data.get("mjd") is not None and len(data["mjd"]):
        mjd_text = f"Data used: MJD {float(data['mjd'].min()):.1f} – {float(data['mjd'].max()):.1f}"

    model_start = validity.get("model_start")
    model_finish = validity.get("model_finish")
    model_text = "Model interval: not specified"
    if model_start is not None and model_finish is not None:
        model_text = f"Model interval: MJD {float(model_start):.1f} – {float(model_finish):.1f}"

    total_obs = len(raw_data.get("mjd", [])) if isinstance(raw_data, dict) else len(data.get("mjd", []))
    used_obs = len(data.get("mjd", [])) if isinstance(data, dict) else 0
    ignored_obs = validity.get("observations_outside_model_range", max(total_obs - used_obs, 0))

    pulsar_name = record.get("pulsar_name") or "Unidentified pulsar"
    glitches = record.get("params_original", {}).get("glitches", [])
    glitch_count = len(glitches)
    return f"""
    <div style="
        padding:0.72rem 0.8rem; border-radius:12px;
        background:rgba(15,24,38,0.92); border:1px solid rgba(103,126,157,0.28);
        margin-bottom:0.5rem;">
        <div style="font-size:0.74rem; color:#8FA6BE; letter-spacing:0.08em; text-transform:uppercase;">{pulsar_name}</div>
        <div style="font-size:0.92rem; font-weight:700; color:#EAF2FF; margin-top:0.10rem;">{record.get('name')}</div>
        <div style="font-size:0.74rem; color:#8FA6BE; margin-top:0.18rem;">{record.get('par_filename')}</div>
        <div style="font-size:0.74rem; color:#8FA6BE;">{record.get('dat_filename')}</div>
        <div style="font-size:0.75rem; color:#A6BED3; margin-top:0.35rem;">{model_text}</div>
        <div style="font-size:0.75rem; color:#A6BED3;">{mjd_text}</div>
        <div style="font-size:0.75rem; color:#A6BED3;">{used_obs}/{total_obs} obs used · {ignored_obs} outside model range · {glitch_count} components</div>
    </div>
    """

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div style="padding:0.3rem 0 0.85rem 0;">
                <div style="font-size:0.75rem; color:#8FA6BE; letter-spacing:0.12em; text-transform:uppercase;">Instrument Panel</div>
                <div style="font-size:1.45rem; font-weight:800; color:#F2F7FF; letter-spacing:0.06em; margin-top:0.15rem;">PULSAR TIMING WORKBENCH</div>
                <div style="font-size:0.78rem; color:#8FA6BE; margin-top:0.35rem; line-height:1.35;">
                    Observatory-inspired workspace for spin evolution, phase analysis,
                    glitch modelling, and figure preparation.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown("#### Dataset Loading")
        st.caption("Each slot accepts one .par timing model and one .dat observational dataset. Slots are collapsible to keep the instrument panel compact.")

        for slot in [1, 2]:
            dataset_id = f"dataset_{slot}"
            loaded_record = state.datasets().get(dataset_id)
            title = f"Dataset Slot {slot}"
            if loaded_record is not None:
                title += f" · {loaded_record.get('pulsar_name') or loaded_record.get('name')}"

            with st.expander(title, expanded=(slot == 1 and loaded_record is None)):
                name = st.text_input(
                    "Display label",
                    value=state.datasets().get(dataset_id, {}).get("name", f"Dataset {slot}"),
                    key=f"name_{dataset_id}",
                )
                par_file = st.file_uploader(
                    "Timing model (.par)",
                    type=["par"],
                    key=f"par_{dataset_id}",
                    help="TEMPO/TEMPO2 timing model containing rotational and glitch parameters.",
                )
                dat_file = st.file_uploader(
                    "Observational data (.dat or .txt)",
                    type=["dat", "txt"],
                    key=f"dat_{dataset_id}",
                    help="Expected numeric columns: MJD F0 err_F0 [F1 err_F1] [F2 err_F2].",
                )
                signature = _slot_signature(par_file, dat_file)
                if signature is not None:
                    if st.button("Load or update dataset", key=f"load_{dataset_id}", use_container_width=True):
                        ok, message = load_dataset_pair(
                            dataset_id=dataset_id,
                            par_bytes=par_file.getvalue(),
                            par_filename=par_file.name,
                            dat_bytes=dat_file.getvalue(),
                            dat_filename=dat_file.name,
                            display_name=name,
                        )
                        if ok:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.caption("Waiting for both files.")

        st.divider()
        st.markdown("#### Loaded Datasets")
        datasets = state.datasets()
        if not datasets:
            st.caption("No datasets loaded yet.")
        else:
            for dataset_id, record in datasets.items():
                with st.expander(record.get("pulsar_name") or record.get("name", dataset_id), expanded=True):
                    st.markdown(_dataset_card(record), unsafe_allow_html=True)
                    visible = st.checkbox("Show in plots", value=record.get("visible", True), key=f"visible_{dataset_id}")
                    state.set_dataset_visible(dataset_id, visible)

            active_options = {record.get("name", dataset_id): dataset_id for dataset_id, record in datasets.items()}
            active_label = next((label for label, did in active_options.items() if did == state.get("active_dataset_id")), list(active_options.keys())[0])
            selected_label = st.selectbox("Editable dataset", options=list(active_options.keys()), index=list(active_options.keys()).index(active_label))
            state.set("active_dataset_id", active_options[selected_label])

        if state.is_data_loaded():
            st.divider()
            st.markdown("#### Visualization Settings")
            use_glitches = st.toggle(
                "Enable glitch contributions",
                value=state.get("use_glitches"),
                help="Disable this option to suppress all glitch terms in the timing model.",
            )
            if use_glitches != state.get("use_glitches"):
                state.set("use_glitches", use_glitches)
                state.reset_model_cache()

            show_orig = st.toggle("Show original timing model", value=state.get("show_original"))
            state.set("show_original", show_orig)
            show_edit = st.toggle("Show edited timing model", value=state.get("show_edited"))
            state.set("show_edited", show_edit)

            st.markdown("<div class='section-label'>Analysis Window</div>", unsafe_allow_html=True)
            window_enabled = st.toggle(
                "Restrict plots to a sub-interval",
                value=state.get("time_window_enabled"),
                help="The full analysis range is the .par validity interval. Use this to inspect a smaller MJD window.",
            )
            state.set("time_window_enabled", window_enabled)
            global_start, global_end = state.global_mjd_bounds()
            if state.get("time_window_start") is None or state.get("time_window_end") is None:
                state.set_full_time_window()
            col1, col2 = st.columns(2)
            with col1:
                start = st.number_input("MJD start", value=float(state.get("time_window_start") or global_start or 0.0), step=1.0, format="%.3f", disabled=not window_enabled)
            with col2:
                end = st.number_input("MJD end", value=float(state.get("time_window_end") or global_end or 0.0), step=1.0, format="%.3f", disabled=not window_enabled)
            if start > end:
                start, end = end, start
            state.set("time_window_start", start)
            state.set("time_window_end", end)
            if st.button("Use full .par model span", use_container_width=True):
                state.set_full_time_window()
                st.rerun()

            st.divider()
            if st.button("Restore original parameters", use_container_width=True, type="secondary"):
                reset_to_original(state.get("active_dataset_id"))
                st.success("Editable parameters restored for the selected dataset.")
                st.rerun()

        st.divider()
        st.markdown(
            """
            <div style="font-size:0.72rem; color:#6F88A4; text-align:center; line-height:1.5;">
                Pulsar Timing Workbench · Research Interface<br>
                Optimized for rotational evolution, phase derivatives, and glitch diagnostics
            </div>
            """,
            unsafe_allow_html=True,
        )
