import numpy as np

from core.glitches import glitch_delta_f0
from core.units import SECONDS_PER_DAY


def test_exponential_post_glitch_recovery():
    """Valida GLF0D*exp(-dt/tau) y que no actúe antes de GLEP."""
    pepoch = 58000.0
    glf0d = 1.0e-6
    gltd_days = 10.0
    tau = gltd_days * SECONDS_PER_DAY

    glitch = {
        "GLEP": pepoch,
        "GLF0": 0.0,
        "GLF1": 0.0,
        "GLF2": 0.0,
        "GLF0D": glf0d,
        "GLTD": gltd_days,
    }

    t_seconds = np.array([-1.0, 0.0, tau, 5.0 * tau])

    result = glitch_delta_f0(glitch, t_seconds, pepoch)

    expected = np.array([
        0.0,
        glf0d,
        glf0d * np.exp(-1.0),
        glf0d * np.exp(-5.0),
    ])

    np.testing.assert_allclose(result, expected, rtol=1e-12, atol=1e-18)
