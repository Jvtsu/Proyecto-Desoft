import numpy as np

from core.residuals import compute_rmse


def test_rmse_calculation():
    """Valida el RMSE usado para cuantificar los residuos del modelo."""
    residuals = np.array([1.0, -1.0, 2.0, -2.0])

    result = compute_rmse(residuals)
    expected = np.sqrt(2.5)

    np.testing.assert_allclose(result, expected, rtol=1e-12, atol=1e-12)
