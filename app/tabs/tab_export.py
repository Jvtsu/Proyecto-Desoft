from __future__ import annotations

import streamlit as st

import app.state as state
from app.callbacks import compute_dataset, edited_par_text, model_dataframe
from plotting.matplotlib_export import figure_timing_model


def render_export_tab() -> None:
    if not state.is_data_loaded():
        st.info("No datasets loaded.")
        return

    datasets = state.datasets()
    labels = [record.get("name", key) for key, record in datasets.items()]
    keys = list(datasets.keys())
    selected_label = st.selectbox("Dataset to export", labels)
    dataset_id = keys[labels.index(selected_label)]
    record = datasets[dataset_id]
    compute_dataset(record)

    st.subheader("Export")
    st.download_button(
        "Download edited .par file",
        data=edited_par_text(dataset_id),
        file_name=f"{record.get('name', dataset_id).replace(' ', '_')}_edited.par",
        mime="text/plain",
        use_container_width=True,
    )

    csv_data = model_dataframe(dataset_id).to_csv(index=False)
    st.download_button(
        "Download model and residual table (.csv)",
        data=csv_data,
        file_name=f"{record.get('name', dataset_id).replace(' ', '_')}_model_residuals.csv",
        mime="text/csv",
        use_container_width=True,
    )

    png = figure_timing_model(record)
    st.download_button(
        "Download publication-style timing figure (.png)",
        data=png,
        file_name=f"{record.get('name', dataset_id).replace(' ', '_')}_timing_model.png",
        mime="image/png",
        use_container_width=True,
    )
