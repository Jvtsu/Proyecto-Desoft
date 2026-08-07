"""
core.glitches
=============
Glitch contributions for pulsar timing models.

The implementation includes both permanent glitch terms and transient
exponential recovery terms:

Permanent terms:
    GLPH, GLF0, GLF1, GLF2

Exponential terms:
    GLF0D : transient frequency amplitude in Hz
    GLTD  : decay time-scale in days in TEMPO/TEMPO2 .par files

For t >= GLEP, the exponential phase term is
    GLF0D * tau * (1 - exp(-dt/tau)),
where tau is converted from days to seconds. Differentiating gives the
frequency and frequency-derivative contributions used below.
"""

from __future__ import annotations

import numpy as np

from core.units import SECONDS_PER_DAY


def _active(index: int, active_indices: set[int] | list[int] | None) -> bool:
    if active_indices is None:
        return True
    return index in set(active_indices)


def _glitch_mask_and_dt(
    glitch: dict[str, float],
    t_seconds: np.ndarray,
    pepoch: float,
) -> tuple[np.ndarray, np.ndarray]:
    mask = np.zeros_like(t_seconds, dtype=bool)
    dt = np.array([], dtype=float)
    if "GLEP" not in glitch:
        return mask, dt

    tg = (float(glitch["GLEP"]) - pepoch) * SECONDS_PER_DAY
    mask = t_seconds >= tg
    if np.any(mask):
        dt = t_seconds[mask] - tg
    return mask, dt


def _tau_seconds(glitch: dict[str, float]) -> float | None:
    if "GLTD" not in glitch:
        return None
    tau_days = float(glitch.get("GLTD", 0.0))
    if tau_days <= 0:
        return None
    return tau_days * SECONDS_PER_DAY


def glitch_delta_f0(glitch: dict[str, float], t_seconds: np.ndarray, pepoch: float) -> np.ndarray:
    """Return the glitch contribution to spin frequency F0(t) in Hz."""
    delta = np.zeros_like(t_seconds, dtype=float)
    mask, dt = _glitch_mask_and_dt(glitch, t_seconds, pepoch)
    if not np.any(mask):
        return delta

    # Permanent frequency terms.
    delta[mask] += (
        float(glitch.get("GLF0", 0.0))
        + float(glitch.get("GLF1", 0.0)) * dt
        + 0.5 * float(glitch.get("GLF2", 0.0)) * dt**2
    )

    # Transient exponential recovery term.
    tau_s = _tau_seconds(glitch)
    glf0d = float(glitch.get("GLF0D", 0.0))
    if tau_s is not None and glf0d != 0.0:
        delta[mask] += glf0d * np.exp(-dt / tau_s)

    return delta


def glitch_delta_f1(glitch: dict[str, float], t_seconds: np.ndarray, pepoch: float) -> np.ndarray:
    """Return the glitch contribution to first frequency derivative F1(t)."""
    delta = np.zeros_like(t_seconds, dtype=float)
    mask, dt = _glitch_mask_and_dt(glitch, t_seconds, pepoch)
    if not np.any(mask):
        return delta

    # Permanent derivative terms.
    delta[mask] += float(glitch.get("GLF1", 0.0)) + float(glitch.get("GLF2", 0.0)) * dt

    # Derivative of GLF0D * exp(-dt/tau).
    tau_s = _tau_seconds(glitch)
    glf0d = float(glitch.get("GLF0D", 0.0))
    if tau_s is not None and glf0d != 0.0:
        delta[mask] += -(glf0d / tau_s) * np.exp(-dt / tau_s)

    return delta


def glitch_delta_phase(glitch: dict[str, float], t_seconds: np.ndarray, pepoch: float) -> np.ndarray:
    """Return the glitch contribution to rotational phase in cycles."""
    delta = np.zeros_like(t_seconds, dtype=float)
    mask, dt = _glitch_mask_and_dt(glitch, t_seconds, pepoch)
    if not np.any(mask):
        return delta

    # Permanent phase terms.
    delta[mask] += (
        float(glitch.get("GLPH", 0.0))
        + float(glitch.get("GLF0", 0.0)) * dt
        + 0.5 * float(glitch.get("GLF1", 0.0)) * dt**2
        + (1.0 / 6.0) * float(glitch.get("GLF2", 0.0)) * dt**3
    )

    # Exponential phase term from professor's expression:
    # GLF0D * tau * (1 - exp(-dt/tau)).
    tau_s = _tau_seconds(glitch)
    glf0d = float(glitch.get("GLF0D", 0.0))
    if tau_s is not None and glf0d != 0.0:
        delta[mask] += glf0d * tau_s * (1.0 - np.exp(-dt / tau_s))

    return delta


def apply_glitches_f0(
    glitches: list[dict[str, float]],
    t_seconds: np.ndarray,
    pepoch: float,
    active_indices: set[int] | list[int] | None = None,
) -> np.ndarray:
    total = np.zeros_like(t_seconds, dtype=float)
    for idx, glitch in enumerate(glitches, start=1):
        if _active(idx, active_indices):
            total += glitch_delta_f0(glitch, t_seconds, pepoch)
    return total


def apply_glitches_f1(
    glitches: list[dict[str, float]],
    t_seconds: np.ndarray,
    pepoch: float,
    active_indices: set[int] | list[int] | None = None,
) -> np.ndarray:
    total = np.zeros_like(t_seconds, dtype=float)
    for idx, glitch in enumerate(glitches, start=1):
        if _active(idx, active_indices):
            total += glitch_delta_f1(glitch, t_seconds, pepoch)
    return total


def apply_glitches_phase(
    glitches: list[dict[str, float]],
    t_seconds: np.ndarray,
    pepoch: float,
    active_indices: set[int] | list[int] | None = None,
) -> np.ndarray:
    total = np.zeros_like(t_seconds, dtype=float)
    for idx, glitch in enumerate(glitches, start=1):
        if _active(idx, active_indices):
            total += glitch_delta_phase(glitch, t_seconds, pepoch)
    return total


def has_exponential_component(glitch: dict[str, float]) -> bool:
    return "GLF0D" in glitch and "GLTD" in glitch and float(glitch.get("GLTD", 0.0)) > 0.0


def default_glitch(reference_mjd: float = 0.0) -> dict[str, float]:
    return {"GLEP": float(reference_mjd), "GLF0": 0.0, "GLF1": 0.0, "GLF2": 0.0}
