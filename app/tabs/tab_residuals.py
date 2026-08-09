from __future__ import annotations

import pandas as pd
import streamlit as st

from app.callbacks import compute_visible_datasets
from app.plot_visibility import render_trace_controls
from plotting.plot_residuals import plot_residuals_comparison


def render_residuals_tab() -> None:
    records = compute_visible_datasets()
    if not records:
        st.info("No visible datasets selected.")
        return

    st.subheader("Residuals")
    st.caption(
        "Residuals are defined as observation minus model. Original-model residuals are drawn as open white markers; edited-model residuals are shown in purple. "
        "Use the checkbox legend below to isolate each residual series."
    )

    has_f1 = any("res_f1" in record.get("cache", {}).get("residual_stats_edit", {}) for record in records)
    options = [
        ("f0_original", "F0 original residual", True),
        ("f0_edited", "F0 edited residual", True),
    ]
    if has_f1:
        options.extend([
            ("f1_original", "F1 original residual", True),
            ("f1_edited", "F1 edited residual", True),
        ])

    trace_visibility = render_trace_controls(
        "residuals",
        records,
        options,
        title="Checkbox legend · Residuals",
        expanded=True,
        columns=2,
    )

    st.plotly_chart(plot_residuals_comparison(records, trace_visibility=trace_visibility), use_container_width=True)

    rows = []
    for record in records:
        cache = record.get("cache", {})
        for model_label, key in [("Original", "residual_stats_orig"), ("Edited", "residual_stats_edit")]:
            stats = cache.get(key, {})
            if stats:
                rows.append({
                    "Dataset": record.get("name"),
                    "Model": model_label,
                    "RMSE F0 [Hz]": stats.get("rmse_f0"),
                    "Chi2 F0": stats.get("chi2_f0"),
                    "RMSE F1 [Hz/s]": stats.get("rmse_f1"),
                    "Chi2 F1": stats.get("chi2_f1"),
                })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
