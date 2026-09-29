"""
Automated unit tests for finite magnetic sources (cuboid and cylinder)
and quantitative verification of the dipole approximation breakdown regime.
"""

import unittest
import numpy as np
from scipy.spatial.transform import Rotation

from src.dipole import dipole_field
from src.array import create_planar_array
from src.magpylib_backend import (
    magpylib_dipole_field,
    magpylib_cuboid_field,
    magpylib_cylinder_field,
)


class TestFiniteSources(unittest.TestCase):
    """Test finite magnetic sources and dipole breakdown characteristics."""

    def setUp(self):
        self.L = 0.01  # 10 mm characteristic size
        self.moment = np.array([0.0, 0.0, 1.0])
        self.cuboid_dim = (self.L, self.L, self.L)
        self.cylinder_dim = (self.L, self.L)
        self.sensors = create_planar_array(3, 3, 0.02)

    def test_near_field_breakdown(self):
        """In the near-field (z <= 1.0 * L), dipole error must exceed 5%."""
        z_near = 0.01  # 1.0 * L
        pos = np.array([0.0, 0.0, z_near])

        B_dip = dipole_field(self.sensors, pos, self.moment)
        B_cub = magpylib_cuboid_field(
            self.sensors, pos, dimension=self.cuboid_dim, moment=self.moment
        )

        norm_dip = np.linalg.norm(B_dip)
        rel_err = np.linalg.norm(B_cub - B_dip) / norm_dip

        # Dipole model breaks down significantly in the near field
        self.assertGreater(rel_err, 0.05, f"Expected >5% error, got {rel_err*100:.2f}%")

    def test_far_field_convergence(self):
        """In the far-field (z >= 50 * L), dipole error must be below 0.01%."""
        z_far = 0.50  # 50 * L
        pos = np.array([0.0, 0.0, z_far])

        B_dip = dipole_field(self.sensors, pos, self.moment)
        B_cub = magpylib_cuboid_field(
            self.sensors, pos, dimension=self.cuboid_dim, moment=self.moment
        )
        B_cyl = magpylib_cylinder_field(
            self.sensors, pos, dimension=self.cylinder_dim, moment=self.moment
        )

        norm_dip = np.linalg.norm(B_dip)
        rel_cub = np.linalg.norm(B_cub - B_dip) / norm_dip
        rel_cyl = np.linalg.norm(B_cyl - B_dip) / norm_dip

        self.assertLess(rel_cub, 1e-4, f"Cuboid far-field error {rel_cub*100:.4f}% >= 0.01%")
        self.assertLess(rel_cyl, 1e-3, f"Cylinder far-field error {rel_cyl*100:.4f}% >= 0.1%")

    def test_orientation_consistency_horizontal(self):
        """Rotating a finite magnet 90 degrees must match a horizontal dipole."""
        rot = Rotation.from_euler("y", 90, degrees=True)
        mom_horiz = rot.apply(self.moment)
        z = 0.30  # 30 * L (dipole regime)
        pos = np.array([0.0, 0.0, z])

        B_dip = dipole_field(self.sensors, pos, mom_horiz)
        B_cub = magpylib_cuboid_field(
            self.sensors, pos, dimension=self.cuboid_dim, moment=self.moment, orientation=rot
        )
        B_cyl = magpylib_cylinder_field(
            self.sensors, pos, dimension=self.cylinder_dim, moment=self.moment, orientation=rot
        )

        norm_dip = np.linalg.norm(B_dip)
        rel_cub = np.linalg.norm(B_cub - B_dip) / norm_dip
        rel_cyl = np.linalg.norm(B_cyl - B_dip) / norm_dip

        self.assertLess(rel_cub, 1e-3)
        self.assertLess(rel_cyl, 1e-3)

        # Center sensor on-axis Bz must be approximately zero by symmetry
        self.assertAlmostEqual(B_cub[4, 2], 0.0, places=7)
        self.assertAlmostEqual(B_cyl[4, 2], 0.0, places=7)

    def test_size_scaling_shifts_breakdown(self):
        """Doubling the magnet size shifts the breakdown distance proportionally."""
        L1 = 0.01  # 10 mm
        L2 = 0.02  # 20 mm

        sensor = np.array([[0.0, 0.0, 0.0]])
        # Test at proportional distances z/L = 1.0
        z1 = 1.0 * L1
        z2 = 1.0 * L2

        B_dip1 = dipole_field(sensor, np.array([0.0, 0.0, z1]), self.moment)[0, 2]
        B_cub1 = magpylib_cuboid_field(
            sensor, np.array([0.0, 0.0, z1]), (L1, L1, L1), moment=self.moment
        )[0, 2]

        B_dip2 = dipole_field(sensor, np.array([0.0, 0.0, z2]), self.moment)[0, 2]
        B_cub2 = magpylib_cuboid_field(
            sensor, np.array([0.0, 0.0, z2]), (L2, L2, L2), moment=self.moment
        )[0, 2]

        err1 = abs(B_cub1 - B_dip1) / abs(B_dip1)
        err2 = abs(B_cub2 - B_dip2) / abs(B_dip2)

        # At identical normalized distance z/L, error should be identical
        self.assertAlmostEqual(err1, err2, places=6)

    def test_near_field_shape_discrimination(self):
        """Cuboid and cylinder with identical moment produce distinguishable near fields."""
        z_near = 0.01  # 1.0 * L
        pos = np.array([0.0, 0.0, z_near])

        B_cub = magpylib_cuboid_field(
            self.sensors, pos, dimension=self.cuboid_dim, moment=self.moment
        )
        B_cyl = magpylib_cylinder_field(
            self.sensors, pos, dimension=self.cylinder_dim, moment=self.moment
        )

        # Shape difference must be physically detectable in near field
        shape_diff = np.linalg.norm(B_cub - B_cyl) / np.linalg.norm(B_cub)
        self.assertGreater(shape_diff, 0.05, "Cuboid and cylinder should differ by >5% in near field")


if __name__ == "__main__":
    unittest.main()
