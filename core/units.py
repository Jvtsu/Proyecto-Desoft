"""
core.units
==========
Shared unit conversions used by the pulsar timing backend.
"""

SECONDS_PER_DAY: float = 86400.0
F1_SCALE: float = 1e-15
F2_SCALE: float = 1e-24
F1_DISPLAY_SCALE: float = 1e15
F2_DISPLAY_SCALE: float = 1e24

UNITS: dict[str, str] = {
    "mjd": "MJD [days]",
    "f0": "Hz",
    "err_f0": "Hz",
    "f1": "Hz s^-1",
    "err_f1": "Hz s^-1",
    "f2": "Hz s^-2",
    "err_f2": "Hz s^-2",
    "phase": "cycles",
}
