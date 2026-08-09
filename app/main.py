from __future__ import annotations

import streamlit as st

import app.state as state
from app.autoload import load_cli_dataset_once
from app.sidebar import render_sidebar
from app.tabs.tab_model import render_model_tab
from app.tabs.tab_phase import render_phase_tab
from app.tabs.tab_glitches import render_glitches_tab
from app.tabs.tab_residuals import render_residuals_tab
from app.tabs.tab_data import render_data_tab
from app.tabs.tab_export import render_export_tab


def _inject_observatory_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(47,94,158,0.08), transparent 22%),
                radial-gradient(circle at 85% 10%, rgba(119,232,81,0.06), transparent 18%),
                linear-gradient(180deg, #050B14 0%, #08101B 40%, #09111D 100%);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0A111C 0%, #0D1624 100%);
            border-right: 1px solid rgba(120, 140, 170, 0.18);
        }
        .hero-title {font-size: 2.35rem; font-weight: 800; color: #F2F7FF; letter-spacing: 0.03em;}
        .hero-subtitle {font-size: 0.98rem; color: #9DB2C7; margin-top: 0.35rem;}
        .hero-strip {padding: 0.6rem 0 0.9rem 0;}
        .dataset-badge {
            display:inline-block; margin:0 0.45rem 0.45rem 0; padding:0.42rem 0.75rem;
            border-radius:999px; background:rgba(18,28,45,0.92); border:1px solid rgba(103,126,157,0.35);
            color:#DCE7F5; font-size:0.84rem; font-weight:600;
        }
        .dataset-badge span {color:#8FB4D9; font-weight:500;}
        .summary-card {
            background: linear-gradient(180deg, rgba(15,24,38,0.95), rgba(18,28,45,0.92));
            border: 1px solid rgba(103,126,157,0.35);
            border-radius: 14px; padding: 0.95rem 1rem; min-height: 118px;
            box-shadow: 0 0 0 1px rgba(255,255,255,0.02), 0 12px 24px rgba(0,0,0,0.16);
        }
        .summary-label {font-size: 0.78rem; color:#8FA6BE; text-transform:uppercase; letter-spacing:0.08em;}
        .summary-value {font-size:1.55rem; font-weight:800; color:#F2F7FF; margin-top:0.18rem;}
        .summary-caption {font-size:0.82rem; color:#9DB2C7; margin-top:0.28rem; line-height:1.35;}
        .section-label {font-size:0.86rem; color:#9DB2C7; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.25rem;}
        .stTabs [data-baseweb="tab-list"] {gap: 0.35rem;}
        .stTabs [data-baseweb="tab"] {
            background: rgba(15,24,38,0.95); border: 1px solid rgba(103,126,157,0.22);
            border-radius: 10px 10px 0 0; padding: 0.55rem 0.95rem;
        }
        .stTabs [aria-selected="true"] {
            background: rgba(18,28,45,1.0); border-bottom-color: rgba(100,181,246,0.60);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    st.markdown(
        """
        <div class="hero-strip">
            <div class="hero-title">Pulsar Timing Workbench</div>
            <div class="hero-subtitle">
                Observatory-style environment for rotational evolution, phase derivatives,
                glitch diagnostics, and publication-quality pulsar figures.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_dataset_badges(records: list[dict]) -> None:
    if not records:
        return
    badges = []
    for record in records:
        data = record.get("data", {})
        mjd = data.get("mjd")
        glitches = len(record.get("params_original", {}).get("glitches", []))
        if mjd is not None and len(mjd):
            pulsar_name = record.get("pulsar_name") or "Unidentified pulsar"
            badge = (
                f"<div class='dataset-badge'>{pulsar_name} · <span>{record.get('name')}</span> · "
                f"<span>{len(mjd)} obs in model span</span> · "
                f"<span>MJD {float(mjd.min()):.1f}–{float(mjd.max()):.1f}</span> · "
                f"<span>{glitches} glitch components</span></div>"
            )
            badges.append(badge)
    st.markdown("".join(badges), unsafe_allow_html=True)


def _render_summary_cards(records: list[dict]) -> None:
    loaded = len(records)
    total_obs = sum(len(record.get("data", {}).get("mjd", [])) for record in records)
    total_raw_obs = sum(len(record.get("raw_data", record.get("data", {})).get("mjd", [])) for record in records)
    total_glitches = sum(len(record.get("params_original", {}).get("glitches", [])) for record in records)

    starts = []
    ends = []
    for record in records:
        validity = record.get("par_validity", {})
        if validity.get("model_start") is not None and validity.get("model_finish") is not None:
            starts.append(float(validity["model_start"]))
            ends.append(float(validity["model_finish"]))
        elif len(record["data"]["mjd"]):
            starts.append(float(record["data"]["mjd"].min()))
            ends.append(float(record["data"]["mjd"].max()))
    start = min(starts)
    end = max(ends)
    active = state.get("active_dataset_id") or "—"

    cols = st.columns(4)
    cards = [
        ("Visible datasets", str(loaded), f"Active editing target: {active}"),
        ("Observations", f"{total_obs}/{total_raw_obs}", "Measurements retained inside the .par validity interval"),
        ("Model MJD span", f"{start:.1f}–{end:.1f}", "Combined START-FINISH timing-model baseline"),
        ("Glitch components", str(total_glitches), "Timing-model glitch components, including exponential recoveries"),
    ]
    for col, (label, value, caption) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="summary-card">
                    <div class="summary-label">{label}</div>
                    <div class="summary-value">{value}</div>
                    <div class="summary-caption">{caption}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def run() -> None:
    st.set_page_config(
        page_title="Pulsar Timing Workbench",
        page_icon="🔭",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    state.init_state()
    load_cli_dataset_once()
    _inject_observatory_css()
    render_sidebar()
    _render_header()

    if not state.is_data_loaded():
        st.info("Load one or two complete pulsar datasets in the instrument panel to begin the analysis.")
        return

    records = [record for record in state.visible_datasets() if record.get("visible", True)]
    _render_dataset_badges(records)
    _render_summary_cards(records)
    st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)

    tabs = st.tabs([
        "Spin Evolution",
        "Phase Evolution",
        "Glitch Analysis",
        "Residuals",
        "Dataset Inspector",
        "Publication Export",
    ])

    with tabs[0]:
        render_model_tab()
    with tabs[1]:
        render_phase_tab()
    with tabs[2]:
        render_glitches_tab()
    with tabs[3]:
        render_residuals_tab()
    with tabs[4]:
        render_data_tab()
    with tabs[5]:
        render_export_tab()
