"""
app.callbacks
=============
Bridge between the Streamlit UI and the scientific timing backend.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import app.state as state

from core.par_parser import parse_par, serialize_par
from core.dat_parser import parse_dat
from core.spin_model import compute_model
from core.phase_model import compute_phase_derivatives
from core.residuals import compute_all_residual_stats
from core.validation import validate_params, validate_data
from core.fitting import fit_f0, fit_f1, fit_joint
from core.glitches import default_glitch


ARRAY_CACHE_KEYS = {
    "model_mjd",
    "f0_model_orig", "f1_model_orig", "f0_model_edit", "f1_model_edit",
    "f0_model_orig_at_data", "f1_model_orig_at_data",
    "f0_model_edit_at_data", "f1_model_edit_at_data",
    "phi_orig", "phi_dot_orig", "phi_ddot_orig",
    "phi_edit", "phi_dot_edit", "phi_ddot_edit",
}


def _dataset_name(par_filename: str, dat_filename: str, fallback: str) -> str:
    par_stem = Path(par_filename).stem if par_filename else ""
    dat_stem = Path(dat_filename).stem if dat_filename else ""
    if par_stem and par_stem == dat_stem:
        return par_stem
    if par_stem and dat_stem:
        return f"{par_stem} / {dat_stem}"
    return par_stem or dat_stem or fallback


def infer_pulsar_name(params: dict[str, Any], fallback: str = "Unidentified pulsar") -> str:
    """Infer a pulsar identifier from common TEMPO/TEMPO2 .par keys."""

    candidates = [
        "PSRJ",
        "PSRB",
        "PSR",
        "PSR_NAME",
        "PSRNAME",
        "NAME",
        "PULSAR",
        "SOURCE",
    ]

    for key in candidates:
        value = params.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() not in {"nan", "none", "0.0"}:
            return text

    return fallback


def glitch_epoch_summary(params: dict[str, Any], max_inline: int | None = None) -> str:
    """Return a compact text summary of glitch epochs in MJD."""

    glitches = params.get("glitches", [])
    entries: list[str] = []

    for index, glitch in enumerate(glitches, start=1):
        glep = glitch.get("GLEP")
        if glep is None:
            entries.append(f"G{index}: no GLEP")
        else:
            entries.append(f"G{index}: {float(glep):.6f}")

    if not entries:
        return "No glitches listed"

    if max_inline is not None and len(entries) > max_inline:
        shown = entries[:max_inline]
        shown.append(f"+{len(entries) - max_inline} more")
        return "; ".join(shown)

    return "; ".join(entries)




def par_validity_bounds(params: dict[str, Any]) -> tuple[float | None, float | None]:
    """Return the timing-model validity interval from START/FINISH when present."""
    start = params.get("START")
    finish = params.get("FINISH")
    try:
        start_f = float(start) if start is not None else None
        finish_f = float(finish) if finish is not None else None
    except (TypeError, ValueError):
        return None, None
    if start_f is not None and finish_f is not None and start_f > finish_f:
        start_f, finish_f = finish_f, start_f
    return start_f, finish_f


def _filter_array_mapping(data: dict[str, Any], mask: np.ndarray) -> dict[str, Any]:
    """Filter every array-like column with the same length as the MJD column."""
    filtered: dict[str, Any] = {}
    n = len(data["mjd"])
    for key, value in data.items():
        if hasattr(value, "__len__") and not isinstance(value, (str, bytes)) and len(value) == n:
            filtered[key] = value[mask]
        else:
            filtered[key] = value
    return filtered


def filter_data_to_par_validity(
    data: dict[str, Any],
    params: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Restrict observational data to the validity interval of the .par file.

    If START/FINISH are not present, the full .dat range is kept. The returned
    metadata is used by the UI to make clear when the .dat covers a wider span
    than the timing solution.
    """
    mjd = np.asarray(data["mjd"], dtype=float)
    dat_start = float(np.nanmin(mjd))
    dat_finish = float(np.nanmax(mjd))
    start, finish = par_validity_bounds(params)

    if start is None:
        start = dat_start
    if finish is None:
        finish = dat_finish

    mask = (mjd >= start) & (mjd <= finish)
    filtered = _filter_array_mapping(data, mask)
    metadata = {
        "dat_start": dat_start,
        "dat_finish": dat_finish,
        "model_start": float(start),
        "model_finish": float(finish),
        "has_start_finish": "START" in params or "FINISH" in params,
        "observations_total": int(len(mjd)),
        "observations_used": int(mask.sum()),
        "observations_outside_model_range": int((~mask).sum()),
    }
    return filtered, metadata


def _model_grid_for_record(record: dict[str, Any], n: int = 1200) -> np.ndarray:
    validity = record.get("par_validity", {})
    start = validity.get("model_start")
    finish = validity.get("model_finish")
    data = record.get("data", {})
    if start is None or finish is None:
        mjd = data.get("mjd")
        if mjd is None or len(mjd) == 0:
            return np.array([], dtype=float)
        start = float(np.nanmin(mjd))
        finish = float(np.nanmax(mjd))
    if float(start) == float(finish):
        return np.array([float(start)], dtype=float)
    return np.linspace(float(start), float(finish), int(n))

def load_dataset_pair(
    dataset_id: str,
    par_bytes: bytes,
    par_filename: str,
    dat_bytes: bytes,
    dat_filename: str,
    display_name: str | None = None,
) -> tuple[bool, str]:
    """Load one complete pulsar dataset: .par + .dat."""
    try:
        params, par_report = parse_par(par_bytes)
        raw_data, dat_report = parse_dat(dat_bytes)
    except Exception as exc:
        return False, f"Dataset loading failed: {exc}"

    if not par_report.ok:
        return False, "Timing model validation failed:\n" + "\n".join(par_report.errors)
    if not dat_report.ok:
        return False, "Observational dataset validation failed:\n" + "\n".join(dat_report.errors)

    param_validation = validate_params(params)
    data_validation = validate_data(raw_data)
    if param_validation.errors:
        return False, "Timing model validation failed:\n" + "\n".join(param_validation.errors)
    if data_validation.errors:
        return False, "Observational dataset validation failed:\n" + "\n".join(data_validation.errors)

    data, range_metadata = filter_data_to_par_validity(raw_data, params)
    if len(data.get("mjd", [])) == 0:
        return (
            False,
            "The .dat file contains no observations inside the .par validity interval "
            f"MJD {range_metadata['model_start']:.6f} — {range_metadata['model_finish']:.6f}."
        )

    name = display_name.strip() if display_name and display_name.strip() else _dataset_name(par_filename, dat_filename, dataset_id)
    pulsar_name = infer_pulsar_name(params, fallback=name)
    record = state.make_dataset_record(
        dataset_id=dataset_id,
        name=name,
        par_filename=par_filename,
        dat_filename=dat_filename,
        params=params,
        data=data,
        par_report=par_report,
        dat_report=dat_report,
    )
    record["pulsar_name"] = pulsar_name
    record["raw_data"] = raw_data
    record["par_validity"] = range_metadata
    state.add_or_update_dataset(dataset_id, record)

    if state.get("time_window_start") is None or state.get("time_window_end") is None:
        state.set_full_time_window()

    msg = (
        f"Dataset loaded: {name}\n"
        f"Pulsar identifier: {pulsar_name}\n"
        f"Timing model: {par_filename}\n"
        f"Observations: {dat_filename}\n"
        f"Model validity interval: MJD {range_metadata['model_start']:.6f} — {range_metadata['model_finish']:.6f}\n"
        f"Valid measurements inside .par interval: {range_metadata['observations_used']} "
        f"of {range_metadata['observations_total']}"
    )
    if range_metadata["observations_outside_model_range"]:
        msg += (
            f"\nMeasurements outside .par interval ignored for model comparisons: "
            f"{range_metadata['observations_outside_model_range']}"
        )

    warnings = param_validation.warnings + data_validation.warnings + par_report.warnings + dat_report.warnings
    if warnings:
        msg += "\n\nValidation warnings:\n" + "\n".join(warnings)
    return True, msg


# Backward-compatible single-file loaders used by older sidebar versions.
def load_par_file(file_bytes: bytes, filename: str) -> tuple[bool, str]:
    current = state.get_dataset("single") or {}
    current["_pending_par"] = (file_bytes, filename)
    state.datasets()["single"] = current
    return True, f"Timing model staged: {filename}"


def load_dat_file(file_bytes: bytes, filename: str) -> tuple[bool, str]:
    current = state.get_dataset("single") or {}
    pending = current.get("_pending_par")
    if pending is None:
        current["_pending_dat"] = (file_bytes, filename)
        state.datasets()["single"] = current
        return True, f"Observational dataset staged: {filename}"
    par_bytes, par_filename = pending
    return load_dataset_pair("single", par_bytes, par_filename, file_bytes, filename)


def compute_dataset(record: dict[str, Any]) -> dict[str, Any]:
    """Compute and cache model products for one dataset record.

    Model curves are evaluated on the .par validity interval (START-FINISH when
    present). Residuals are evaluated only at observational MJD values that fall
    inside that same validity interval.
    """
    cache = record.setdefault("cache", {})
    if cache:
        return cache

    data = record["data"]
    data_mjd = np.asarray(data["mjd"], dtype=float)
    model_mjd = _model_grid_for_record(record)

    use_glitches = state.get("use_glitches")
    active_idx = record.get("active_glitch_indices")

    params_orig = record["params_original"]
    params_edit = record["params_edited"]

    # Smooth model curves on the .par validity interval.
    f0_orig, f1_orig = compute_model(model_mjd, params_orig, include_glitches=use_glitches, active_glitches=active_idx)
    f0_edit, f1_edit = compute_model(model_mjd, params_edit, include_glitches=use_glitches, active_glitches=active_idx)

    # Model evaluated at observational times for residual diagnostics.
    f0_orig_data, f1_orig_data = compute_model(data_mjd, params_orig, include_glitches=use_glitches, active_glitches=active_idx)
    f0_edit_data, f1_edit_data = compute_model(data_mjd, params_edit, include_glitches=use_glitches, active_glitches=active_idx)

    phi_orig, phi_dot_orig, phi_ddot_orig = compute_phase_derivatives(params_orig, model_mjd, use_glitches, active_idx)
    phi_edit, phi_dot_edit, phi_ddot_edit = compute_phase_derivatives(params_edit, model_mjd, use_glitches, active_idx)

    # Display phase relative to the beginning of the .par validity interval.
    # This avoids visually misleading huge absolute phase offsets while leaving
    # analytic derivatives unchanged.
    if len(phi_orig):
        phi_orig = phi_orig - phi_orig[0]
    if len(phi_edit):
        phi_edit = phi_edit - phi_edit[0]

    cache.update({
        "model_mjd": model_mjd,
        "f0_model_orig": f0_orig,
        "f1_model_orig": f1_orig,
        "f0_model_edit": f0_edit,
        "f1_model_edit": f1_edit,
        "f0_model_orig_at_data": f0_orig_data,
        "f1_model_orig_at_data": f1_orig_data,
        "f0_model_edit_at_data": f0_edit_data,
        "f1_model_edit_at_data": f1_edit_data,
        "phi_orig": phi_orig,
        "phi_dot_orig": phi_dot_orig,
        "phi_ddot_orig": phi_ddot_orig,
        "phi_edit": phi_edit,
        "phi_dot_edit": phi_dot_edit,
        "phi_ddot_edit": phi_ddot_edit,
        "residual_stats_orig": compute_all_residual_stats(data, f0_orig_data, f1_orig_data),
        "residual_stats_edit": compute_all_residual_stats(data, f0_edit_data, f1_edit_data),
    })
    return cache

def _filter_data_mapping(data: dict[str, Any], mask: np.ndarray) -> dict[str, Any]:
    filtered: dict[str, Any] = {}
    n = len(data["mjd"])
    for key, value in data.items():
        if hasattr(value, "__len__") and not isinstance(value, (str, bytes)) and len(value) == n:
            filtered[key] = value[mask]
        else:
            filtered[key] = value
    return filtered


def _filter_cache_mapping(
    cache: dict[str, Any],
    data_mask: np.ndarray,
    grid_mask: np.ndarray,
    filtered_data: dict[str, Any],
) -> dict[str, Any]:
    filtered_cache: dict[str, Any] = {}
    data_n = len(data_mask)
    grid_n = len(grid_mask)

    for key, value in cache.items():
        if not (hasattr(value, "__len__") and not isinstance(value, (str, bytes))):
            filtered_cache[key] = value
            continue

        value_len = len(value)
        if key == "model_mjd" and value_len == grid_n:
            filtered_cache[key] = value[grid_mask]
        elif key in {"f0_model_orig", "f1_model_orig", "f0_model_edit", "f1_model_edit", "phi_orig", "phi_dot_orig", "phi_ddot_orig", "phi_edit", "phi_dot_edit", "phi_ddot_edit"} and value_len == grid_n:
            filtered_cache[key] = value[grid_mask]
        elif key in {"f0_model_orig_at_data", "f1_model_orig_at_data", "f0_model_edit_at_data", "f1_model_edit_at_data"} and value_len == data_n:
            filtered_cache[key] = value[data_mask]
        elif key not in {"residual_stats_orig", "residual_stats_edit"}:
            filtered_cache[key] = value

    if "f0_model_orig_at_data" in filtered_cache:
        filtered_cache["residual_stats_orig"] = compute_all_residual_stats(
            filtered_data,
            filtered_cache["f0_model_orig_at_data"],
            filtered_cache.get("f1_model_orig_at_data"),
        )
    if "f0_model_edit_at_data" in filtered_cache:
        filtered_cache["residual_stats_edit"] = compute_all_residual_stats(
            filtered_data,
            filtered_cache["f0_model_edit_at_data"],
            filtered_cache.get("f1_model_edit_at_data"),
        )
    return filtered_cache

def _apply_time_window(record: dict[str, Any]) -> dict[str, Any] | None:
    data = record.get("data", {})
    mjd = data.get("mjd")
    if mjd is None or len(mjd) == 0:
        return None

    if not state.get("time_window_enabled"):
        return record

    start = state.get("time_window_start")
    end = state.get("time_window_end")
    if start is None or end is None:
        return record

    start_f = float(start)
    end_f = float(end)
    if start_f > end_f:
        start_f, end_f = end_f, start_f

    data_mask = (mjd >= start_f) & (mjd <= end_f)
    if not data_mask.any():
        return None

    filtered = deepcopy(record)
    filtered_data = _filter_data_mapping(data, data_mask)
    filtered["data"] = filtered_data

    cache = record.get("cache", {})
    model_mjd = cache.get("model_mjd")
    if model_mjd is not None and len(model_mjd) > 0:
        grid_mask = (model_mjd >= start_f) & (model_mjd <= end_f)
        if not grid_mask.any():
            return None
    else:
        grid_mask = np.array([], dtype=bool)

    filtered["cache"] = _filter_cache_mapping(cache, data_mask, grid_mask, filtered_data)
    return filtered

def compute_visible_datasets() -> list[dict[str, Any]]:
    records = state.visible_datasets()
    result: list[dict[str, Any]] = []
    for record in records:
        compute_dataset(record)
        filtered = _apply_time_window(record)
        if filtered is not None:
            result.append(filtered)
    return result


def ensure_model_computed() -> bool:
    return bool(compute_visible_datasets())


def compute_models() -> None:
    compute_visible_datasets()


def update_base_param(dataset_id: str, key: str, value: float) -> None:
    record = state.get_dataset(dataset_id)
    if record is None:
        return
    record["params_edited"][key] = float(value)
    record["cache"] = {}


def update_glitch_param(dataset_id: str, glitch_idx: int, gl_key: str, value: float) -> None:
    record = state.get_dataset(dataset_id)
    if record is None:
        return
    glitches = record["params_edited"].setdefault("glitches", [])
    if 0 <= glitch_idx < len(glitches):
        glitches[glitch_idx][gl_key] = float(value)
        record["cache"] = {}


def add_glitch(dataset_id: str, glep: float | None = None) -> None:
    record = state.get_dataset(dataset_id)
    if record is None:
        return
    if glep is None:
        glep = float(record["data"]["mjd"][0])
    record["params_edited"].setdefault("glitches", []).append(default_glitch(glep))
    record["cache"] = {}


def remove_glitch(dataset_id: str, glitch_idx: int) -> None:
    record = state.get_dataset(dataset_id)
    if record is None:
        return
    glitches = record["params_edited"].setdefault("glitches", [])
    if 0 <= glitch_idx < len(glitches):
        glitches.pop(glitch_idx)
        record["cache"] = {}


def toggle_glitch(dataset_id: str, glitch_idx_1base: int, active: bool) -> None:
    record = state.get_dataset(dataset_id)
    if record is None:
        return
    n = len(record["params_edited"].get("glitches", []))
    all_indices = set(range(1, n + 1))
    current = record.get("active_glitch_indices")
    if current is None:
        current = all_indices.copy()
    else:
        current = set(current)
    if active:
        current.add(glitch_idx_1base)
    else:
        current.discard(glitch_idx_1base)
    record["active_glitch_indices"] = None if current == all_indices else current
    record["cache"] = {}


def reset_to_original(dataset_id: str | None = None) -> None:
    state.reset_edited_params(dataset_id)
    state.set("fit_message", "")
    state.set("fit_result", None)


def run_fit(dataset_id: str, fit_type: str, fit_keys: list[str]) -> str:
    record = state.get_dataset(dataset_id)
    if record is None:
        return "No dataset selected."

    params = record["params_edited"]
    data = record["data"]
    if fit_type == "f0":
        fitted, uncertainties, message = fit_f0(params, data, fit_keys)
    elif fit_type == "f1":
        fitted, uncertainties, message = fit_f1(params, data, fit_keys)
    elif fit_type == "joint":
        fitted, uncertainties, message = fit_joint(params, data, fit_keys)
    else:
        return f"Unknown fit type: {fit_type}"

    record["params_edited"] = fitted
    record["cache"] = {}
    state.set("fit_result", {"dataset_id": dataset_id, "params": fitted, "uncertainties": uncertainties})
    state.set("fit_message", message)
    return message


def edited_par_text(dataset_id: str) -> str:
    record = state.get_dataset(dataset_id)
    if record is None:
        return ""
    return serialize_par(record["params_edited"])


def model_dataframe(dataset_id: str) -> pd.DataFrame:
    record = state.get_dataset(dataset_id)
    if record is None:
        return pd.DataFrame()
    cache = compute_dataset(record)
    data = record["data"]
    frame = pd.DataFrame({
        "mjd": data["mjd"],
        "f0_obs": data["f0"],
        "f0_original": cache["f0_model_orig_at_data"],
        "f0_edited": cache["f0_model_edit_at_data"],
        "res_f0_original": cache["residual_stats_orig"]["res_f0"],
        "res_f0_edited": cache["residual_stats_edit"]["res_f0"],
    })
    if "f1" in data:
        frame["f1_obs"] = data["f1"]
        frame["f1_original"] = cache["f1_model_orig_at_data"]
        frame["f1_edited"] = cache["f1_model_edit_at_data"]
        frame["res_f1_original"] = cache["residual_stats_orig"].get("res_f1")
        frame["res_f1_edited"] = cache["residual_stats_edit"].get("res_f1")
    return frame
