"""
core.validation
===============
Non-fatal validation for timing models and observational datasets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def summary(self) -> str:
        lines = [f"ERROR: {msg}" for msg in self.errors]
        lines.extend(f"WARNING: {msg}" for msg in self.warnings)
        return "\n".join(lines) if lines else "No validation issues detected."


def validate_params(params: dict[str, Any]) -> ValidationReport:
    report = ValidationReport()

    for key in ["F0", "PEPOCH"]:
        if key not in params:
            report.add_error(f"Required parameter missing: {key}")

    for key in ["F1", "F2", "F3"]:
        if key not in params:
            report.add_warning(f"Optional spin parameter {key} is missing; zero will be used.")

    f0 = float(params.get("F0", 0.0))
    if f0 <= 0:
        report.add_error(f"F0 must be positive. Current value: {f0}")

    pepoch = float(params.get("PEPOCH", 0.0))
    if 0 < pepoch < 40000:
        report.add_warning(f"PEPOCH={pepoch} is earlier than MJD 40000. Verify the epoch.")

    for idx, glitch in enumerate(params.get("glitches", []), start=1):
        if "GLEP" not in glitch:
            report.add_warning(f"Glitch {idx} has no GLEP epoch and will not affect the model.")
        has_permanent = any(key in glitch for key in ["GLPH", "GLF0", "GLF1", "GLF2"])
        has_exponential = any(key in glitch for key in ["GLF0D", "GLTD"])
        if not has_permanent and not has_exponential:
            report.add_warning(f"Glitch {idx} has no permanent or exponential timing terms.")
        if "GLF0D" in glitch and "GLTD" not in glitch:
            report.add_warning(f"Glitch {idx} has GLF0D but no GLTD decay time-scale.")
        if "GLTD" in glitch and "GLF0D" not in glitch:
            report.add_warning(f"Glitch {idx} has GLTD but no GLF0D amplitude.")
        if "GLTD" in glitch and float(glitch.get("GLTD", 0.0)) <= 0:
            report.add_warning(f"Glitch {idx} has non-positive GLTD; exponential recovery will be ignored.")

    if "START" in params and "FINISH" in params:
        try:
            if float(params["START"]) >= float(params["FINISH"]):
                report.add_warning("START is greater than or equal to FINISH. The interval will be reordered internally.")
        except (TypeError, ValueError):
            report.add_warning("START/FINISH could not be parsed as numeric MJD values.")

    return report


def validate_data(data: dict[str, Any]) -> ValidationReport:
    report = ValidationReport()

    for key in ["mjd", "f0", "err_f0"]:
        if key not in data:
            report.add_error(f"Required data column missing: {key}")

    if report.errors:
        return report

    n = len(data["mjd"])
    if n == 0:
        report.add_error("The dataset contains no valid observations.")
        return report

    for key, value in data.items():
        if hasattr(value, "__len__") and len(value) != n:
            report.add_error(f"Column {key} has length {len(value)}, expected {n}.")

    if np.any(np.asarray(data["err_f0"]) <= 0):
        report.add_warning("Some F0 uncertainties are non-positive. Weighted statistics may be affected.")

    if "err_f1" in data and np.any(np.asarray(data["err_f1"]) <= 0):
        report.add_warning("Some F1 uncertainties are non-positive. Weighted statistics may be affected.")

    if n < 5:
        report.add_warning("The dataset contains fewer than five observations; derivative and fit diagnostics may be unstable.")

    return report
