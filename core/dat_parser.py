"""
core.dat_parser
===============
Parser for observational pulsar `.dat` files.

Supported numeric formats:
    MJD F0 err_F0
    MJD F0 err_F0 F1 err_F1
    MJD F0 err_F0 F1 err_F1 F2 err_F2

If F1/F2 columns appear to be stored in display units, they are converted to SI:
    F1: x 1e-15 Hz/s
    F2: x 1e-24 Hz/s^2
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import tempfile

import numpy as np

from core.units import F1_SCALE, F2_SCALE


@dataclass
class DatParseReport:
    lines_read: int = 0
    lines_used: int = 0
    skipped_lines: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def lineas_usadas(self) -> int:
        return self.lines_used

    @property
    def errores(self) -> list[str]:
        return self.errors

    @property
    def advertencias(self) -> list[str]:
        return self.warnings


def _read_lines(source: str | Path | bytes) -> list[str]:
    if isinstance(source, bytes):
        return source.decode("utf-8", errors="replace").splitlines()
    path = Path(source)
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _maybe_scale_derivative(values: np.ndarray, scale: float, threshold: float) -> np.ndarray:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return values
    # If the median absolute value is much larger than physical SI values, assume display units.
    if np.nanmedian(np.abs(finite)) > threshold:
        return values * scale
    return values


def parse_dat(source: str | Path | bytes) -> tuple[dict[str, np.ndarray], DatParseReport]:
    report = DatParseReport()
    rows: list[list[float]] = []

    for raw_line in _read_lines(source):
        report.lines_read += 1
        line = raw_line.strip()
        if not line or line.startswith(("#", "C", "//")):
            continue

        line = line.replace(",", " ")
        parts = line.split()
        numeric: list[float] = []
        for part in parts:
            try:
                numeric.append(float(part))
            except ValueError:
                break

        if len(numeric) < 3:
            report.skipped_lines += 1
            continue

        rows.append(numeric)

    if not rows:
        report.errors.append("No valid numeric observations were found in the .dat file.")
        return {}, report

    max_cols = max(len(row) for row in rows)
    arr = np.full((len(rows), max_cols), np.nan, dtype=float)
    for i, row in enumerate(rows):
        arr[i, : len(row)] = row

    data: dict[str, np.ndarray] = {
        "mjd": arr[:, 0].astype(float),
        "f0": arr[:, 1].astype(float),
        "err_f0": arr[:, 2].astype(float),
    }
    data["f0_err"] = data["err_f0"]

    if max_cols >= 5 and np.isfinite(arr[:, 3]).any():
        f1 = _maybe_scale_derivative(arr[:, 3].astype(float), F1_SCALE, threshold=1e-8)
        err_f1 = _maybe_scale_derivative(np.abs(arr[:, 4].astype(float)), F1_SCALE, threshold=1e-8)
        data["f1"] = f1
        data["err_f1"] = err_f1
        data["f1_err"] = err_f1

    if max_cols >= 7 and np.isfinite(arr[:, 5]).any():
        f2 = _maybe_scale_derivative(arr[:, 5].astype(float), F2_SCALE, threshold=1e-18)
        err_f2 = _maybe_scale_derivative(np.abs(arr[:, 6].astype(float)), F2_SCALE, threshold=1e-18)
        data["f2"] = f2
        data["err_f2"] = err_f2
        data["f2_err"] = err_f2

    order = np.argsort(data["mjd"])
    for key, value in list(data.items()):
        data[key] = value[order]

    report.lines_used = len(data["mjd"])
    if "f1" not in data:
        report.warnings.append("The observational file does not contain F1 measurements. F1 residuals will not be shown.")

    return data, report


def parse_dat_file(source: str | Path | bytes) -> dict[str, np.ndarray]:
    data, report = parse_dat(source)
    if not report.ok:
        raise ValueError("; ".join(report.errors))
    return data


def write_temp_dat(file_bytes: bytes) -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".dat")
    with tmp:
        tmp.write(file_bytes)
    return Path(tmp.name)
