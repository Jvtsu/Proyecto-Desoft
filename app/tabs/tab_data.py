from __future__ import annotations

import pandas as pd
import streamlit as st

from app.callbacks import compute_visible_datasets
from app.plot_visibility import render_trace_controls
from plotting.plot_data import plot_data_overview


def render_data_tab() -> None:
    records = compute_visible_datasets()
    if not records:
        st.info("No visible datasets selected.")
        return

    st.subheader("Dataset Inspector")
    st.caption(
        "Direct view of the observational measurements. Cyan markers correspond to the loaded .dat files within the active temporal interval. "
        "Use the checkbox legend below to show or hide each observed quantity."
    )

    has_f1 = any("f1" in record["data"] for record in records)
    options = [("f0_data", "F0 observations", True)]
    if has_f1:
        options.append(("f1_data", "F1 observations", True))

    trace_visibility = render_trace_controls(
        "dataset_inspector",
        records,
        options,
        title="Checkbox legend · Dataset Inspector",
        expanded=True,
        columns=2,
    )

    st.plotly_chart(plot_data_overview(records, trace_visibility=trace_visibility), use_container_width=True)

    for record in records:
        with st.expander(f"Data table · {record.get('name')}", expanded=False):
            st.dataframe(pd.DataFrame(record["data"]), use_container_width=True)
