"""
app.autoload
============

Load a dataset automatically when PulsarLab is launched from the `plab`
terminal command.

The CLI passes file paths through environment variables:

    PULSARLAB_CLI_PAR
    PULSARLAB_CLI_DAT
    PULSARLAB_CLI_DATASET_NAME

This keeps the Streamlit UI and the terminal interface connected without
duplicating parsing or modelling logic.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

import app.state as state
from app.callbacks import load_dataset_pair


def _read_file_bytes(path_text: str) -> tuple[bytes, str]:
    path = Path(path_text).expanduser().resolve()
    return path.read_bytes(), path.name


def load_cli_dataset_once() -> None:
    """Preload the dataset provided by the `plab` command, if any."""

    if os.environ.get("PULSARLAB_CLI_MODE") != "1":
        return

    if st.session_state.get("_pulsarlab_cli_dataset_loaded"):
        return

    par_path = os.environ.get("PULSARLAB_CLI_PAR")
    dat_path = os.environ.get("PULSARLAB_CLI_DAT")
    dataset_name = os.environ.get("PULSARLAB_CLI_DATASET_NAME", "Dataset 1")

    if not par_path or not dat_path:
        st.warning(
            "PulsarLab was launched in CLI mode, but no .par/.dat paths were provided."
        )
        st.session_state["_pulsarlab_cli_dataset_loaded"] = True
        return

    try:
        par_bytes, par_filename = _read_file_bytes(par_path)
        dat_bytes, dat_filename = _read_file_bytes(dat_path)
    except OSError as exc:
        st.error(f"Could not read CLI input files: {exc}")
        st.session_state["_pulsarlab_cli_dataset_loaded"] = True
        return

    ok, message = load_dataset_pair(
        dataset_id="dataset_1",
        par_bytes=par_bytes,
        par_filename=par_filename,
        dat_bytes=dat_bytes,
        dat_filename=dat_filename,
        display_name=dataset_name,
    )

    st.session_state["_pulsarlab_cli_dataset_loaded"] = True

    if ok:
        state.set_dataset_visible("dataset_1", True)
        state.set("active_dataset_id", "dataset_1")
        st.success(message)
    else:
        st.error(message)
