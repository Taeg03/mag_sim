import numpy as np

MU0 = 4 * np.pi * 1e-7

def dipole_field(sensor_positions, source_position, moment):
    """
    Parameters
        sensor_positions: (N, 3)
        source_positions: (3,)
        moment: (3,)
    Returns: (N,3)
    """

    r = sensor_positions - source_position
    r_mag = np.linalg.norm(r, axis=1)
    m_dot_r = r @ moment

    B = (MU0 / (4 * np.pi)) * (
        3 * r * m_dot_r[:, None] / r_mag[:, None]**5
        - moment / r_mag[:, None]**3
    )

    return B
