"""
Unit tests verifying that the analytical dipole model reproduces exact theoretical
predictions and baseline simulation results.
"""

import unittest
import numpy as np

from src.dipole import dipole_field, MU0
from src.array import create_planar_array


class TestAnalyticalDipole(unittest.TestCase):
    """Verify analytical dipole calculations."""

    def test_on_axis_field_exact(self):
        """On-axis vertical dipole field must follow Bz = (mu_0 / 4pi) * 2m / z^3."""
        z = 0.5
        m = 1.0
        sensor = np.array([[0.0, 0.0, 0.0]])
        source = np.array([0.0, 0.0, z])
        moment = np.array([0.0, 0.0, m])

        B = dipole_field(sensor, source, moment)

        expected_bz = (MU0 / (4 * np.pi)) * (2.0 * m) / (z ** 3)
        self.assertEqual(B.shape, (1, 3))
        self.assertAlmostEqual(B[0, 0], 0.0, places=15)
        self.assertAlmostEqual(B[0, 1], 0.0, places=15)
        self.assertAlmostEqual(B[0, 2], expected_bz, places=15)

    def test_first_dipole_test_baseline(self):
        """Reproduce baseline values from experiments/first_dipole_test.py."""
        d = 0.02
        sensor = np.array([
            [-d, -d, 0],
            [0, -d, 0],
            [d, -d, 0],
            [-d, 0, 0],
            [0, 0, 0],
            [d, 0, 0],
            [-d, d, 0],
            [0, d, 0],
            [d, d, 0],
        ])
        dipole1 = np.array([0.0, 0.0, 0.1])
        moment = np.array([0.0, 0.0, 1.0])

        B = dipole_field(sensor, dipole1, moment)

        self.assertEqual(B.shape, (9, 3))
        # Center sensor (index 4) at (0,0,0):
        expected_center_bz = 1e-7 * 2.0 / (0.1 ** 3)  # 2.000000e-4 T
        self.assertAlmostEqual(B[4, 2], expected_center_bz, delta=1e-15)
        self.assertAlmostEqual(B[4, 0], 0.0, delta=1e-15)
        self.assertAlmostEqual(B[4, 1], 0.0, delta=1e-15)

        # Symmetry checks:
        # Bx at (-d, 0) should be -Bx at (d, 0)
        self.assertAlmostEqual(B[3, 0], -B[5, 0], delta=1e-15)
        # By at (0, -d) should be -By at (0, d)
        self.assertAlmostEqual(B[1, 1], -B[7, 1], delta=1e-15)
        # Bz should be symmetric across all corners
        self.assertAlmostEqual(B[0, 2], B[2, 2], delta=1e-15)
        self.assertAlmostEqual(B[0, 2], B[6, 2], delta=1e-15)
        self.assertAlmostEqual(B[0, 2], B[8, 2], delta=1e-15)

    def test_inverse_cube_scaling(self):
        """Test 1/r^3 scaling across multiple distances."""
        sensor = np.array([[0.0, 0.0, 0.0]])
        moment = np.array([0.0, 0.0, 1.0])
        distances = np.array([0.1, 0.2, 0.5, 1.0, 2.0])

        fields = [dipole_field(sensor, np.array([0.0, 0.0, z]), moment)[0, 2] for z in distances]

        # Ratio between z=0.2 and z=0.1 should be exactly (0.1/0.2)^3 = 1/8
        self.assertAlmostEqual(fields[1] / fields[0], 0.125, places=10)
        # Ratio between z=1.0 and z=0.1 should be exactly (0.1/1.0)^3 = 1e-3
        self.assertAlmostEqual(fields[3] / fields[0], 1e-3, places=10)


if __name__ == "__main__":
    unittest.main()
