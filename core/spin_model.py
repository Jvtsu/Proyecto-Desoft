"""
core.spin_model
===============
Spin-frequency evolution model for pulsar timing parameters.
"""

from __future__ import annotations

from typing import Any
import numpy as np

from core.units import SECONDS_PER_DAY
from core.glitches import apply_glitches_f0, apply_glitches_f1


def mjd_to_seconds(mjd: np.ndarray, reference_mjd: float) -> np.ndarray:
    return (np.asarray(mjd, dtype=float) - float(reference_mjd)) * SECONDS_PER_DAY


def compute_model(
    mjd: np.ndarray | dict[str, Any],
    params: dict[str, Any] | np.ndarray,
    include_glitches: bool = True,
    active_glitches: set[int] | list[int] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute F0(t) and F1(t). Accepts both argument orders for backward compatibility:
        compute_model(mjd, params)
        compute_model(params, mjd)
    """
    if isinstance(mjd, dict):
        params, mjd = mjd, params

    params = dict(params)  # type: ignore[arg-type]
    mjd = np.asarray(mjd, dtype=float)  # type: ignore[arg-type]

    pepoch = float(params.get("PEPOCH", mjd[0] if len(mjd) else 0.0))
    t = mjd_to_seconds(mjd, pepoch)

    f0 = float(params.get("F0", 0.0))
    f1 = float(params.get("F1", 0.0))
    f2 = float(params.get("F2", 0.0))
    f3 = float(params.get("F3", 0.0))

    f0_model = f0 + f1 * t + 0.5 * f2 * t**2 + (1.0 / 6.0) * f3 * t**3
    f1_model = f1 + f2 * t + 0.5 * f3 * t**2

    if include_glitches:
        glitches = params.get("glitches", [])
        f0_model = f0_model + apply_glitches_f0(glitches, t, pepoch, active_glitches)
        f1_model = f1_model + apply_glitches_f1(glitches, t, pepoch, active_glitches)

    return f0_model, f1_model


def compute_f0(
    params: dict[str, Any],
    mjd: np.ndarray,
    use_glitches: bool = True,
    active_glitches: set[int] | list[int] | None = None,
) -> np.ndarray:
    return compute_model(mjd, params, use_glitches, active_glitches)[0]


def compute_f1(
    params: dict[str, Any],
    mjd: np.ndarray,
    use_glitches: bool = True,
    active_glitches: set[int] | list[int] | None = None,
) -> np.ndarray:
    return compute_model(mjd, params, use_glitches, active_glitches)[1]
