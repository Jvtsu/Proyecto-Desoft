"""
app.plot_visibility
===================
Streamlit controls that act as a readable, persistent plot-layer selector.

Plotly legends can already hide/show traces by clicking, but this module adds
clear checkbox panels with scientific labels so the user can identify exactly
which quantity and model layer is being displayed.
"""

from __future__ import annotations

from typing import Iterable, TypedDict

import streamlit as st


Option = tuple[str, str, bool]


class VisibilityGroup(TypedDict, total=False):
    title: str
    description: str
    options: list[Option]


def record_key(record: dict) -> str:
    """Stable key for a loaded dataset record."""
    return str(record.get("id") or record.get("name") or id(record))


def _record_label(record: dict) -> str:
    """Human-readable dataset label."""
    name = record.get("name") or record.get("pulsar_name") or record_key(record)
    pulsar = record.get("pulsar_name") or record.get("params_original", {}).get("PSRJ")
    if pulsar and str(pulsar) not in str(name):
        return f"{name} · {pulsar}"
    return str(name)


def _inject_visibility_css() -> None:
    st.markdown(
        """
        <style>
        .layer-control-card {
            padding: 0.78rem 0.9rem;
            border: 1px solid rgba(103,126,157,0.28);
            border-radius: 0.8rem;
            background: rgba(10, 17, 28, 0.72);
            margin-bottom: 0.7rem;
        }
        .layer-control-title {
            font-size: 0.92rem;
            font-weight: 750;
            color: #E8EEF8;
            letter-spacing: 0.02em;
            margin-bottom: 0.1rem;
        }
        .layer-control-description {
            font-size: 0.78rem;
            color: #9DB2C7;
            line-height: 1.35;
            margin-bottom: 0.45rem;
        }
        .layer-dataset-label {
            font-size: 0.95rem;
            font-weight: 750;
            color: #F2F7FF;
            margin: 0.25rem 0 0.7rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_trace_controls(
    tab_key: str,
    records: list[dict],
    options: Iterable[Option],
    *,
    title: str = "Plot layer controls",
    expanded: bool = True,
    columns: int = 3,
) -> dict[str, dict[str, bool]]:
    """
    Backward-compatible flat checkbox controls.

    New tabs should prefer :func:`render_grouped_trace_controls` because it is
    clearer for multi-panel plots.
    """
    options = list(options)
    groups: list[VisibilityGroup] = [
        {
            "title": "Plot layers",
            "description": "Select which traces should remain visible in the current plot.",
            "options": options,
        }
    ]
    return render_grouped_trace_controls(
        tab_key,
        records,
        groups,
        title=title,
        expanded=expanded,
        columns=columns,
    )


def render_grouped_trace_controls(
    tab_key: str,
    records: list[dict],
    groups: list[VisibilityGroup],
    *,
    title: str = "Plot layer controls",
    expanded: bool = True,
    columns: int = 3,
    help_text: str | None = None,
) -> dict[str, dict[str, bool]]:
    """
    Render grouped checkbox controls for plot traces.

    Parameters
    ----------
    tab_key:
        Unique prefix for Streamlit widget keys.
    records:
        Visible dataset records.
    groups:
        List of groups. Each group has a title, description, and options.
        Options are tuples: (option_key, label, default_value).
    title:
        Label for the expander that contains the controls.

    Returns
    -------
    dict
        Mapping {dataset_id: {option_key: visible_bool}}.
    """
    _inject_visibility_css()

    visibility: dict[str, dict[str, bool]] = {}

    with st.expander(title, expanded=expanded):
        st.caption(
            help_text
            or "Select the exact plot layers to display. The labels identify the physical quantity, data source, and visual style."
        )

        for record in records:
            key = record_key(record)
            visibility[key] = {}
            st.markdown(f"<div class='layer-dataset-label'>{_record_label(record)}</div>", unsafe_allow_html=True)

            for group_index, group in enumerate(groups):
                group_title = group.get("title", "Plot layers")
                group_description = group.get("description", "")
                group_options = group.get("options", [])

                st.markdown(
                    f"""
                    <div class='layer-control-card'>
                        <div class='layer-control-title'>{group_title}</div>
                        <div class='layer-control-description'>{group_description}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                cols = st.columns(max(1, min(columns, len(group_options))))
                for option_index, (option_key, option_label, default) in enumerate(group_options):
                    with cols[option_index % len(cols)]:
                        visibility[key][option_key] = st.checkbox(
                            option_label,
                            value=default,
                            key=f"trace_visibility_{tab_key}_{key}_{group_index}_{option_key}",
                        )

    return visibility
