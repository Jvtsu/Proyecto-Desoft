"""
core.residuals
==============
Residual and goodness-of-fit diagnostics.
"""

from __future__ import annotations

import numpy as np


def _first(data: dict, *keys: str):
    for key in keys:
        if key in data:
            return data[key]
    return None


def compute_rmse(residuals: np.ndarray) -> float:
    residuals = np.asarray(residuals, dtype=float)
    return float(np.sqrt(np.nanmean(residuals**2)))


def compute_chi2(residuals: np.ndarray, errors: np.ndarray | None = None) -> float:
    residuals = np.asarray(residuals, dtype=float)
    if errors is None:
        return float(np.nansum(residuals**2))
    errors = np.asarray(errors, dtype=float)
    mask = np.isfinite(residuals) & np.isfinite(errors) & (errors > 0)
    if not np.any(mask):
        return float("nan")
    return float(np.nansum((residuals[mask] / errors[mask]) ** 2))


def _stats(prefix: str, residuals: np.ndarray, errors: np.ndarray | None) -> dict:
    residuals = np.asarray(residuals, dtype=float)
    out = {
        f"res_{prefix}": residuals,
        f"{prefix}_residuals": residuals,
        f"mean_{prefix}": float(np.nanmean(residuals)),
        f"std_{prefix}": float(np.nanstd(residuals)),
        f"rmse_{prefix}": compute_rmse(residuals),
        f"chi2_{prefix}": compute_chi2(residuals, errors),
    }
    if errors is not None:
        errors = np.asarray(errors, dtype=float)
        mask = np.isfinite(errors) & (errors > 0)
        out[f"reduced_chi2_{prefix}"] = (
            float(out[f"chi2_{prefix}"] / max(int(np.sum(mask)) - 1, 1)) if np.any(mask) else float("nan")
        )
    return out


def compute_all_residual_stats(data: dict, model_f0: np.ndarray, model_f1: np.ndarray | None = None) -> dict:
    stats: dict = {}

    residual_f0 = np.asarray(data["f0"], dtype=float) - np.asarray(model_f0, dtype=float)
    err_f0 = _first(data, "err_f0", "f0_err")
    stats.update(_stats("f0", residual_f0, err_f0))
    stats["residuals"] = residual_f0
    stats["mean"] = stats["mean_f0"]
    stats["std"] = stats["std_f0"]
    stats["rmse"] = stats["rmse_f0"]
    stats["chi2"] = stats["chi2_f0"]

    if model_f1 is not None and "f1" in data:
        residual_f1 = np.asarray(data["f1"], dtype=float) - np.asarray(model_f1, dtype=float)
        err_f1 = _first(data, "err_f1", "f1_err")
        stats.update(_stats("f1", residual_f1, err_f1))

    return stats
