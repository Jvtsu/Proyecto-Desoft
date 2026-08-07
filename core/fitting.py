"""
core.fitting
============
Least-squares fitting helpers for selected spin parameters.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np
from scipy.optimize import curve_fit

from core.spin_model import compute_f0, compute_f1

BASE_FIT_PARAMS = ["F0", "F1", "F2", "F3"]


def _error_column(data: dict, *names: str):
    for name in names:
        if name in data:
            arr = np.asarray(data[name], dtype=float)
            if np.any(np.isfinite(arr) & (arr > 0)):
                return arr
    return None


def _build_model(params_ref: dict, fit_keys: list[str], quantity: str):
    def model(mjd: np.ndarray, *values) -> np.ndarray:
        params = deepcopy(params_ref)
        for key, value in zip(fit_keys, values):
            params[key] = float(value)
        if quantity == "f0":
            return compute_f0(params, mjd, use_glitches=True)
        return compute_f1(params, mjd, use_glitches=True)
    return model


def fit_f0(
    params: dict[str, Any],
    data: dict[str, np.ndarray],
    fit_keys: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, float], str]:
    if fit_keys is None:
        fit_keys = ["F0", "F1"]

    sigma = _error_column(data, "err_f0", "f0_err")
    p0 = [float(params.get(key, 0.0)) for key in fit_keys]

    try:
        popt, pcov = curve_fit(
            _build_model(params, fit_keys, "f0"),
            data["mjd"],
            data["f0"],
            p0=p0,
            sigma=sigma,
            absolute_sigma=sigma is not None,
            maxfev=20000,
        )
    except Exception as exc:
        return deepcopy(params), {}, f"F0 fit failed: {exc}"

    fitted = deepcopy(params)
    uncertainties: dict[str, float] = {}
    perr = np.sqrt(np.diag(pcov)) if pcov.size else np.full(len(fit_keys), np.nan)
    for key, value, error in zip(fit_keys, popt, perr):
        fitted[key] = float(value)
        uncertainties[key] = float(error)

    return fitted, uncertainties, "F0 fit completed successfully."


def fit_f1(
    params: dict[str, Any],
    data: dict[str, np.ndarray],
    fit_keys: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, float], str]:
    if "f1" not in data:
        return deepcopy(params), {}, "F1 fit skipped: observational F1 column is not available."
    if fit_keys is None:
        fit_keys = ["F1", "F2"]

    sigma = _error_column(data, "err_f1", "f1_err")
    p0 = [float(params.get(key, 0.0)) for key in fit_keys]

    try:
        popt, pcov = curve_fit(
            _build_model(params, fit_keys, "f1"),
            data["mjd"],
            data["f1"],
            p0=p0,
            sigma=sigma,
            absolute_sigma=sigma is not None,
            maxfev=20000,
        )
    except Exception as exc:
        return deepcopy(params), {}, f"F1 fit failed: {exc}"

    fitted = deepcopy(params)
    uncertainties: dict[str, float] = {}
    perr = np.sqrt(np.diag(pcov)) if pcov.size else np.full(len(fit_keys), np.nan)
    for key, value, error in zip(fit_keys, popt, perr):
        fitted[key] = float(value)
        uncertainties[key] = float(error)

    return fitted, uncertainties, "F1 fit completed successfully."


def fit_joint(
    params: dict[str, Any],
    data: dict[str, np.ndarray],
    fit_keys: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, float], str]:
    if "f1" not in data:
        return fit_f0(params, data, fit_keys or ["F0", "F1"])
    if fit_keys is None:
        fit_keys = ["F0", "F1", "F2"]

    mjd = data["mjd"]
    y = np.concatenate([data["f0"], data["f1"]])
    sigma_f0 = _error_column(data, "err_f0", "f0_err")
    sigma_f1 = _error_column(data, "err_f1", "f1_err")
    sigma = None
    if sigma_f0 is not None and sigma_f1 is not None:
        sigma = np.concatenate([sigma_f0, sigma_f1])

    def model(mjd_twice: np.ndarray, *values) -> np.ndarray:
        params_tmp = deepcopy(params)
        for key, value in zip(fit_keys, values):
            params_tmp[key] = float(value)
        n = len(mjd_twice) // 2
        f0 = compute_f0(params_tmp, mjd_twice[:n], use_glitches=True)
        f1 = compute_f1(params_tmp, mjd_twice[:n], use_glitches=True)
        return np.concatenate([f0, f1])

    p0 = [float(params.get(key, 0.0)) for key in fit_keys]
    try:
        popt, pcov = curve_fit(
            model,
            np.concatenate([mjd, mjd]),
            y,
            p0=p0,
            sigma=sigma,
            absolute_sigma=sigma is not None,
            maxfev=30000,
        )
    except Exception as exc:
        return deepcopy(params), {}, f"Joint fit failed: {exc}"

    fitted = deepcopy(params)
    uncertainties: dict[str, float] = {}
    perr = np.sqrt(np.diag(pcov)) if pcov.size else np.full(len(fit_keys), np.nan)
    for key, value, error in zip(fit_keys, popt, perr):
        fitted[key] = float(value)
        uncertainties[key] = float(error)

    return fitted, uncertainties, "Joint F0/F1 fit completed successfully."
