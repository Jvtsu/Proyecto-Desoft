"""
app.state
=========
Centralized Streamlit session-state management for PulsarLab.

The application supports up to two dataset slots. Each dataset contains one
parameter file (.par), one observational dataset (.dat), editable parameters,
visibility state, and cached model products.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import streamlit as st


_DEFAULTS: dict[str, Any] = {
    "datasets": {},
    "active_dataset_id": None,
    "show_original": True,
    "show_edited": True,
    "use_glitches": True,
    "time_window_enabled": False,
    "time_window_start": None,
    "time_window_end": None,
    "fit_message": "",
    "fit_result": None,
}


def init_state() -> None:
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)


def get(key: str, default: Any = None) -> Any:
    return st.session_state.get(key, _DEFAULTS.get(key, default))


def set(key: str, value: Any) -> None:
    st.session_state[key] = value


def datasets() -> dict[str, dict[str, Any]]:
    return st.session_state.setdefault("datasets", {})


def make_dataset_record(
    dataset_id: str,
    name: str,
    par_filename: str,
    dat_filename: str,
    params: dict[str, Any],
    data: dict[str, Any],
    par_report: Any,
    dat_report: Any,
) -> dict[str, Any]:
    return {
        "id": dataset_id,
        "name": name,
        "pulsar_name": None,
        "par_filename": par_filename,
        "dat_filename": dat_filename,
        "params_original": deepcopy(params),
        "params_edited": deepcopy(params),
        "data": data,
        "par_report": par_report,
        "dat_report": dat_report,
        "visible": True,
        "active_glitch_indices": None,
        "cache": {},
    }


def add_or_update_dataset(dataset_id: str, record: dict[str, Any]) -> None:
    datasets()[dataset_id] = record
    if st.session_state.get("active_dataset_id") is None:
        st.session_state["active_dataset_id"] = dataset_id


def get_dataset(dataset_id: str | None = None) -> dict[str, Any] | None:
    if dataset_id is None:
        dataset_id = st.session_state.get("active_dataset_id")
    if dataset_id is None:
        return None
    return datasets().get(dataset_id)


def remove_dataset(dataset_id: str) -> None:
    datasets().pop(dataset_id, None)
    if st.session_state.get("active_dataset_id") == dataset_id:
        st.session_state["active_dataset_id"] = next(iter(datasets()), None)


def set_dataset_visible(dataset_id: str, visible: bool) -> None:
    if dataset_id in datasets():
        datasets()[dataset_id]["visible"] = visible


def visible_dataset_ids() -> list[str]:
    return [dataset_id for dataset_id, record in datasets().items() if record.get("visible", True)]


def visible_datasets() -> list[dict[str, Any]]:
    return [datasets()[dataset_id] for dataset_id in visible_dataset_ids()]


def is_data_loaded() -> bool:
    return bool(datasets())


def reset_dataset_cache(dataset_id: str) -> None:
    record = get_dataset(dataset_id)
    if record is not None:
        record["cache"] = {}


def reset_model_cache() -> None:
    for record in datasets().values():
        record["cache"] = {}


def reset_edited_params(dataset_id: str | None = None) -> None:
    record = get_dataset(dataset_id)
    if record is None:
        return
    record["params_edited"] = deepcopy(record["params_original"])
    record["active_glitch_indices"] = None
    record["cache"] = {}


def apply_fit_to_edited(fitted_params: dict[str, Any], dataset_id: str | None = None) -> None:
    record = get_dataset(dataset_id)
    if record is None:
        return
    record["params_edited"] = deepcopy(fitted_params)
    record["cache"] = {}


def global_mjd_bounds() -> tuple[float | None, float | None]:
    """Return the global analysis range.

    Prefer the .par validity interval (START/FINISH) when it is available,
    because timing-model plots should not be driven by a broader .dat span.
    """
    if not datasets():
        return None, None
    mins: list[float] = []
    maxs: list[float] = []
    for record in datasets().values():
        validity = record.get("par_validity", {})
        start = validity.get("model_start")
        finish = validity.get("model_finish")
        if start is not None and finish is not None:
            mins.append(float(start))
            maxs.append(float(finish))
            continue

        data = record.get("data")
        if not data or "mjd" not in data or len(data["mjd"]) == 0:
            continue
        mins.append(float(data["mjd"].min()))
        maxs.append(float(data["mjd"].max()))
    if not mins:
        return None, None
    return min(mins), max(maxs)


def set_full_time_window() -> None:
    start, end = global_mjd_bounds()
    st.session_state["time_window_start"] = start
    st.session_state["time_window_end"] = end


# ---------------------------------------------------------------------------
# Backward-compatible accessors for older tabs/code paths.
# ---------------------------------------------------------------------------
_ACTIVE_MAP = {
    "params_original": "params_original",
    "params_edited": "params_edited",
    "data": "data",
    "par_filename": "par_filename",
    "dat_filename": "dat_filename",
    "par_report": "par_report",
    "dat_report": "dat_report",
    "active_glitch_indices": "active_glitch_indices",
}

_CACHE_KEYS = {
    "model_mjd", "f0_model_orig", "f1_model_orig", "f0_model_edit", "f1_model_edit",
    "f0_model_orig_at_data", "f1_model_orig_at_data", "f0_model_edit_at_data", "f1_model_edit_at_data",
    "phi_orig", "phi_dot_orig", "phi_ddot_orig",
    "phi_edit", "phi_dot_edit", "phi_ddot_edit",
    "residual_stats_orig", "residual_stats_edit",
}


def get_legacy(key: str) -> Any:
    record = get_dataset()
    if record is None:
        return None
    if key in _ACTIVE_MAP:
        return record.get(_ACTIVE_MAP[key])
    if key in _CACHE_KEYS:
        return record.get("cache", {}).get(key)
    return None


def set_legacy(key: str, value: Any) -> bool:
    record = get_dataset()
    if record is None:
        return False
    if key in _ACTIVE_MAP:
        record[_ACTIVE_MAP[key]] = value
        return True
    if key in _CACHE_KEYS:
        record.setdefault("cache", {})[key] = value
        return True
    return False


def get(key: str, default: Any = None) -> Any:  # type: ignore[no-redef]
    if key in _ACTIVE_MAP or key in _CACHE_KEYS:
        value = get_legacy(key)
        return default if value is None else value
    return st.session_state.get(key, _DEFAULTS.get(key, default))


def set(key: str, value: Any) -> None:  # type: ignore[no-redef]
    if set_legacy(key, value):
        return
    st.session_state[key] = value
