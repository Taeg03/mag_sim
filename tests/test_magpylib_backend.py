"""
Unit tests for the Magpylib backend and verification against the analytical dipole model.
"""

import unittest
import numpy as np

from src.dipole import dipole_field
from src.array import create_planar_array
from src.magpylib_backend import (
    is_magpylib_available,
    magpylib_dipole_field,
    magpylib_cuboid_field,
    magpylib_cylinder_field,
)


class TestMagpylibBackend(unittest.TestCase):
    """Verify Magpylib backend integration and equivalence to analytical dipole."""

    def setUp(self):
        self.assertTrue(
            is_magpylib_available(),
            "magpylib should be installed in the test environment."
        )

    def test_output_shape(self):
        """Output shape must be (N, 3) for any N >= 1."""
        sensor_single = np.array([[0.0, 0.0, 0.0]])
        sensor_many = create_planar_array(3, 3, 0.02)
        pos = np.array([0.0, 0.0, 0.2])
        moment = np.array([0.0, 0.0, 1.0])

        B_single = magpylib_dipole_field(sensor_single, pos, moment)
        B_many = magpylib_dipole_field(sensor_many, pos, moment)

        self.assertEqual(B_single.shape, (1, 3))
        self.assertEqual(B_many.shape, (9, 3))

    def test_numerical_agreement_vertical_dipole(self):
        """Magpylib dipole and analytical dipole must agree to within 1e-9 relative error."""
        sensors = create_planar_array(3, 3, 0.05)
        pos = np.array([0.0, 0.0, 0.25])
        moment = np.array([0.0, 0.0, 1.0])

        B_ana = dipole_field(sensors, pos, moment)
        B_mag = magpylib_dipole_field(sensors, pos, moment)

        # The tiny ~1.32e-10 relative difference is due to the 2018 SI redefinition of mu_0 in Magpylib
        abs_diff = np.max(np.abs(B_mag - B_ana))
        nonzero = np.abs(B_ana) > 1e-15
        rel_diff = np.max(np.abs(B_mag[nonzero] - B_ana[nonzero]) / np.abs(B_ana[nonzero]))

        self.assertLess(abs_diff, 1e-13)
        self.assertLess(rel_diff, 1e-9)

    def test_numerical_agreement_arbitrary_pose_and_moment(self):
        """Verify agreement for arbitrary 3D position and moment vector."""
        sensors = create_planar_array(3, 3, 0.04)
        pos = np.array([-0.12, 0.08, 0.35])
        moment = np.array([0.45, -0.62, 0.88])

        B_ana = dipole_field(sensors, pos, moment)
        B_mag = magpylib_dipole_field(sensors, pos, moment)

        abs_diff = np.max(np.abs(B_mag - B_ana))
        rel_diff = np.max(np.abs(B_mag - B_ana) / np.abs(B_ana))

        self.assertLess(abs_diff, 1e-13)
        self.assertLess(rel_diff, 1e-9)

    def test_horizontal_dipole_conventions(self):
        """Verify coordinate conventions for horizontal dipoles."""
        # For a dipole along x at (0, 0, z), on the z-axis (sensor at 0, 0, 0):
        # r = sensor - source = (0, 0, -z).
        # m = (m, 0, 0).
        # m . r = 0, so B = (mu0 / 4pi) * (-m / r^3) = (-mu0 * m / (4pi * z^3), 0, 0).
        # Specifically, Bz must be zero on-axis.
        z = 0.30
        sensor = np.array([[0.0, 0.0, 0.0]])
        pos = np.array([0.0, 0.0, z])
        moment_x = np.array([1.0, 0.0, 0.0])

        B_ana = dipole_field(sensor, pos, moment_x)
        B_mag = magpylib_dipole_field(sensor, pos, moment_x)

        self.assertAlmostEqual(B_mag[0, 2], 0.0, places=15)
        self.assertAlmostEqual(B_ana[0, 2], 0.0, places=15)
        self.assertLess(abs(B_mag[0, 0] - B_ana[0, 0]) / abs(B_ana[0, 0]), 1e-9)

    def test_finite_cuboid_approaches_dipole(self):
        """A small finite cuboid with equivalent moment must converge to the point dipole far away."""
        moment = np.array([0.0, 0.0, 1.0])
        pos = np.array([0.0, 0.0, 0.0])
        # 5mm cube
        a, b, c = 0.005, 0.005, 0.005

        # Near field (z = 4 * side length = 0.02 m): noticeable difference
        obs_near = np.array([[0.0, 0.0, 0.02]])
        B_dip_near = dipole_field(obs_near, pos, moment)[0, 2]
        B_cub_near = magpylib_cuboid_field(
            obs_near, pos, dimension=(a, b, c), moment=moment
        )[0, 2]
        rel_near = abs(B_cub_near - B_dip_near) / abs(B_dip_near)
        self.assertGreater(rel_near, 1e-4)  # ~8.4e-4

        # Far field (z = 0.50 m = 100 * side length): excellent agreement
        obs_far = np.array([[0.0, 0.0, 0.50]])
        B_dip_far = dipole_field(obs_far, pos, moment)[0, 2]
        B_cub_far = magpylib_cuboid_field(
            obs_far, pos, dimension=(a, b, c), moment=moment
        )[0, 2]
        rel_far = abs(B_cub_far - B_dip_far) / abs(B_dip_far)
        self.assertLess(rel_far, 1e-7)

    def test_finite_cylinder_approaches_dipole(self):
        """A small finite cylinder with equivalent moment must converge to the point dipole far away."""
        moment = np.array([0.0, 0.0, 1.0])
        pos = np.array([0.0, 0.0, 0.0])
        # 5mm diameter, 5mm height cylinder
        d, h = 0.005, 0.005

        # Near field (z = 0.02 m)
        obs_near = np.array([[0.0, 0.0, 0.02]])
        B_dip_near = dipole_field(obs_near, pos, moment)[0, 2]
        B_cyl_near = magpylib_cylinder_field(
            obs_near, pos, dimension=(d, h), moment=moment
        )[0, 2]
        rel_near = abs(B_cyl_near - B_dip_near) / abs(B_dip_near)
        self.assertGreater(rel_near, 1e-3)  # ~7.1e-3

        # Far field (z = 1.00 m = 200 * size)
        obs_far = np.array([[0.0, 0.0, 1.00]])
        B_dip_far = dipole_field(obs_far, pos, moment)[0, 2]
        B_cyl_far = magpylib_cylinder_field(
            obs_far, pos, dimension=(d, h), moment=moment
        )[0, 2]
        rel_far = abs(B_cyl_far - B_dip_far) / abs(B_dip_far)
        self.assertLess(rel_far, 1e-5)

    def test_missing_magpylib_raises_importerror(self):
        """When Magpylib is unavailable, calling backend functions must raise ImportError."""
        from unittest.mock import patch
        import src.magpylib_backend as mb

        with patch.object(mb, "_MAGPYLIB_AVAILABLE", False):
            self.assertFalse(mb.is_magpylib_available())
            with self.assertRaises(ImportError) as ctx:
                mb.magpylib_dipole_field([[0, 0, 0]], [0, 0, 1], [0, 0, 1])
            self.assertIn("pip install magpylib", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

