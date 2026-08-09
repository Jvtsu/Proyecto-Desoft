import numpy as np

from core.spin_model import compute_model


def test_spin_model_polynomial_without_glitches():
    """Valida F0(t) y F1(t) para el polinomio de spin sin glitches."""
    pepoch = 58000.0
    params = {
        "PEPOCH": pepoch,
        "F0": 10.0,
        "F1": -1.0e-5,
        "F2": 1.0e-10,
        "F3": -1.0e-15,
        "glitches": [],
    }

    # 0, 0.5 y 1 día después de PEPOCH.
    mjd = np.array([58000.0, 58000.5, 58001.0])
    t = np.array([0.0, 43200.0, 86400.0])

    f0_result, f1_result = compute_model(mjd, params, include_glitches=False)

    expected_f0 = (
        params["F0"]
        + params["F1"] * t
        + 0.5 * params["F2"] * t**2
        + (1.0 / 6.0) * params["F3"] * t**3
    )

    expected_f1 = (
        params["F1"]
        + params["F2"] * t
        + 0.5 * params["F3"] * t**2
    )

    np.testing.assert_allclose(f0_result, expected_f0, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(f1_result, expected_f1, rtol=1e-12, atol=1e-15)
