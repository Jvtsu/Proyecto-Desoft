"""
plotting.matplotlib_export
==========================
Publication-oriented matplotlib exports.
"""

from __future__ import annotations

import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from core.units import F1_DISPLAY_SCALE


def figure_timing_model(record: dict) -> bytes:
    data = record["data"]
    cache = record.get("cache", {})
    has_f1 = "f1" in data
    model_mjd = cache.get("model_mjd", data["mjd"])

    if has_f1:
        fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    else:
        fig, ax = plt.subplots(1, 1, figsize=(8, 4))
        axes = [ax]

    axes[0].errorbar(data["mjd"], data["f0"], yerr=data.get("err_f0"), fmt="o", ms=3, lw=0.6, label="Observations")
    if "f0_model_edit" in cache:
        axes[0].plot(model_mjd, cache["f0_model_edit"], lw=1.2, label="Edited model")
    axes[0].set_ylabel(r"$F_0$ [Hz]")
    axes[0].grid(alpha=0.25)
    axes[0].legend(frameon=False)

    if has_f1:
        axes[1].errorbar(data["mjd"], data["f1"] * F1_DISPLAY_SCALE, yerr=data.get("err_f1") * F1_DISPLAY_SCALE if "err_f1" in data else None, fmt="o", ms=3, lw=0.6)
        if "f1_model_edit" in cache:
            axes[1].plot(model_mjd, cache["f1_model_edit"] * F1_DISPLAY_SCALE, lw=1.2)
        axes[1].set_ylabel(r"$F_1$ [$10^{-15}$ Hz s$^{-1}$]")
        axes[1].grid(alpha=0.25)
        axes[1].set_xlabel("MJD [days]")
    else:
        axes[0].set_xlabel("MJD [days]")

    fig.suptitle(record.get("name", "Pulsar dataset"))
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()
