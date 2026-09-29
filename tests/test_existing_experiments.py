"""
Tests verifying that existing geometry, conditioning, and sweep experiments
continue to run and reproduce their exact numerical results.
"""

import unittest
import numpy as np

from src.dipole import dipole_field
from src.array import create_planar_array, transform_sensors
from src.sensor import add_noise


class TestExistingExperiments(unittest.TestCase):
    """Verify that existing experiment logic continues to produce exact results."""

    def test_planar_array_geometry(self):
        """Test 3x3 planar array construction and sensor positions."""
        sensors = create_planar_array(3, 3, 0.02)
        self.assertEqual(sensors.shape, (9, 3))
        # Center sensor must be at (0, 0, 0)
        np.testing.assert_allclose(sensors[4], [0.0, 0.0, 0.0])
        # Grid range should be [-0.02, 0.02]
        self.assertAlmostEqual(np.min(sensors[:, 0]), -0.02)
        self.assertAlmostEqual(np.max(sensors[:, 0]), 0.02)
        self.assertAlmostEqual(np.min(sensors[:, 1]), -0.02)
        self.assertAlmostEqual(np.max(sensors[:, 1]), 0.02)
        # All z should be 0
        np.testing.assert_allclose(sensors[:, 2], 0.0)

    def test_transform_sensors(self):
        """Test array rigid transformation."""
        sensors = create_planar_array(3, 3, 0.05)
        translation = np.array([1.0, 2.0, 3.0])
        transformed = transform_sensors(sensors, position=translation)
        # Center sensor should be at translation
        np.testing.assert_allclose(transformed[4], translation)

    def test_distance_sweep_slope(self):
        """Distance sweep log-log slope must be exactly -3.0000."""
        moment = np.array([0, 0, 1])
        sensors = create_planar_array(3, 3, 0.02)
        distances = np.linspace(0.05, 1.0, 100)

        center_bz = []
        for dist in distances:
            B = dipole_field(sensors, np.array([0, 0, dist]), moment)
            center_bz.append(B[4, 2])

        log_distance = np.log(distances)
        log_field = np.log(np.abs(center_bz))
        slope, _ = np.polyfit(log_distance, log_field, 1)

        self.assertAlmostEqual(slope, -3.0000, places=4)

    def test_jacobian_svd_baseline(self):
        """Jacobian analysis SVD and condition number must match established baseline."""
        sensor_spacing = 0.02
        source_distance = 0.20
        source_position = np.array([0.0, 0.0, source_distance])
        moment = np.array([0.0, 0.0, 1.0])
        sensors = create_planar_array(3, 3, sensor_spacing)

        def measurements(pos, mom):
            return dipole_field(sensors, pos, mom)[:, 2]

        theta = np.concatenate([source_position, moment])
        J = np.zeros((9, 6))
        steps = np.full(6, 1e-6)

        for i in range(6):
            th_plus = theta.copy()
            th_minus = theta.copy()
            th_plus[i] += steps[i]
            th_minus[i] -= steps[i]
            b_plus = measurements(th_plus[:3], th_plus[3:])
            b_minus = measurements(th_minus[:3], th_minus[3:])
            J[:, i] = (b_plus - b_minus) / (2 * steps[i])

        U, s, Vt = np.linalg.svd(J, full_matrices=False)

        # Baseline singular values from README and experiments/jacobian_analysis.py
        self.assertAlmostEqual(s[0], 1.056222e-03, delta=1e-8)
        self.assertAlmostEqual(s[1], 1.729468e-04, delta=1e-8)
        self.assertAlmostEqual(s[2], 1.729468e-04, delta=1e-8)
        self.assertAlmostEqual(s[3], 9.771935e-07, delta=1e-10)
        self.assertAlmostEqual(s[4], 5.180952e-08, delta=1e-11)
        self.assertAlmostEqual(s[5], 5.180952e-08, delta=1e-11)

        # Normalized condition number
        parameter_scales = np.array([
            source_distance, source_distance, source_distance,
            1.0, 1.0, 1.0
        ])
        J_norm = J * parameter_scales[None, :]
        _, s_norm, _ = np.linalg.svd(J_norm, full_matrices=False)
        cond_norm = s_norm[0] / s_norm[-1]

        self.assertAlmostEqual(cond_norm, 4.431278e+03, delta=1e-2)

    def test_add_noise(self):
        """Noise addition should add perturbations with expected standard deviation."""
        np.random.seed(42)
        base = np.zeros(10000)
        noise_std = 1e-8
        noisy = add_noise(base, noise_std)
        self.assertAlmostEqual(np.mean(noisy), 0.0, delta=1e-9)
        self.assertAlmostEqual(np.std(noisy), noise_std, delta=5e-10)


if __name__ == "__main__":
    unittest.main()
