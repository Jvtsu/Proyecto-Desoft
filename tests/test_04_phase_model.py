import numpy as np

from core.phase_model import compute_phase


def test_phase_polynomial_without_glitches():
    """Valida la fase analítica generada por F0, F1, F2 y F3."""
    pepoch = 58000.0
    params = {
        "PEPOCH": pepoch,
        "F0": 10.0,
        "F1": -1.0e-5,
        "F2": 1.0e-10,
        "F3": -1.0e-15,
        "glitches": [],
    }

    mjd = np.array([58000.0, 58000.5, 58001.0])
    t = np.array([0.0, 43200.0, 86400.0])

    result = compute_phase(params, mjd, use_glitches=False)

    expected = (
        params["F0"] * t
        + 0.5 * params["F1"] * t**2
        + (1.0 / 6.0) * params["F2"] * t**3
        + (1.0 / 24.0) * params["F3"] * t**4
    )

    np.testing.assert_allclose(result, expected, rtol=1e-12, atol=1e-9)
