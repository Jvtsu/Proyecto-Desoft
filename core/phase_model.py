"""
core.phase_model
================
Analytic phase evolution and analytic phase derivatives.

The phase is evaluated from the timing-model polynomial plus glitch phase
contributions. The first and second phase derivatives are returned analytically
as F0(t) and F1(t), respectively, instead of using numerical gradients. This is
more stable for irregular MJD sampling and avoids misleading derivative plots.
"""

from __future__ import annotations

from typing import Any
import numpy as np

from core.spin_model import mjd_to_seconds, compute_model
from core.glitches import apply_glitches_phase


def compute_phase(
    params: dict[str, Any],
    mjd: np.ndarray,
    use_glitches: bool = True,
    active_glitch_indices: set[int] | list[int] | None = None,
) -> np.ndarray:
    mjd = np.asarray(mjd, dtype=float)
    pepoch = float(params.get("PEPOCH", mjd[0] if len(mjd) else 0.0))
    t = mjd_to_seconds(mjd, pepoch)

    f0 = float(params.get("F0", 0.0))
    f1 = float(params.get("F1", 0.0))
    f2 = float(params.get("F2", 0.0))
    f3 = float(params.get("F3", 0.0))

    phase = f0 * t + 0.5 * f1 * t**2 + (1.0 / 6.0) * f2 * t**3 + (1.0 / 24.0) * f3 * t**4

    if use_glitches:
        phase += apply_glitches_phase(params.get("glitches", []), t, pepoch, active_glitch_indices)

    return phase


def compute_phase_derivatives(
    params: dict[str, Any],
    mjd: np.ndarray,
    use_glitches: bool = True,
    active_glitch_indices: set[int] | list[int] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Return phase, dphase/dt and d²phase/dt².

    dphase/dt is the spin frequency F0(t), and d²phase/dt² is F1(t). Both are
    evaluated analytically from the same timing model used in the spin plots.
    """
    mjd = np.asarray(mjd, dtype=float)
    phase = compute_phase(params, mjd, use_glitches, active_glitch_indices)
    f0_model, f1_model = compute_model(mjd, params, include_glitches=use_glitches, active_glitches=active_glitch_indices)
    return phase, f0_model, f1_model
