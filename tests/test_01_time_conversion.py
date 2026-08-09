import numpy as np

from core.spin_model import mjd_to_seconds


def test_mjd_to_seconds():
    """Convierte correctamente diferencias MJD a segundos respecto de PEPOCH."""
    pepoch = 58000.0
    mjd = np.array([58000.0, 58001.0, 58002.0])

    result = mjd_to_seconds(mjd, pepoch)
    expected = np.array([0.0, 86400.0, 172800.0])

    np.testing.assert_allclose(result, expected, rtol=0.0, atol=1e-9)
