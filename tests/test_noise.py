"""
Unit and statistical verification tests for the modular synthetic noise framework.
"""

import unittest
import numpy as np

from src.noise import NoiseConfig, SyntheticNoiseGenerator
from src.array import create_planar_array


class TestNoiseFramework(unittest.TestCase):
    """Test functional and statistical properties of the noise generator."""

    def setUp(self):
        self.sensors = create_planar_array(3, 3, 0.02)  # 9 sensors
        self.clean_snapshot_vec = np.ones((9, 3)) * 1e-6
        self.clean_snapshot_sca = np.ones(9) * 1e-6
        self.clean_ts_vec = np.ones((100, 9, 3)) * 1e-6
        self.clean_ts_sca = np.ones((100, 9)) * 1e-6

    def test_zero_noise_mode(self):
        """When all noise flags are False, output must equal clean field bitwise."""
        gen = SyntheticNoiseGenerator(NoiseConfig())

        # Test snapshots
        noisy_vec = gen.apply_noise(self.clean_snapshot_vec)
        self.assertTrue(np.array_equal(noisy_vec, self.clean_snapshot_vec))

        noisy_sca = gen.apply_noise(self.clean_snapshot_sca)
        self.assertTrue(np.array_equal(noisy_sca, self.clean_snapshot_sca))

        # Test time series
        noisy_ts_vec = gen.apply_noise(self.clean_ts_vec, dt=0.01)
        self.assertTrue(np.array_equal(noisy_ts_vec, self.clean_ts_vec))

        noisy_ts_sca = gen.apply_noise(self.clean_ts_sca, dt=0.01)
        self.assertTrue(np.array_equal(noisy_ts_sca, self.clean_ts_sca))

    def test_seed_reproducibility(self):
        """Identical seeds must yield identical noise; different seeds must differ."""
        cfg1 = NoiseConfig(seed=42, enable_white=True, white_sigma=1e-8)
        cfg2 = NoiseConfig(seed=42, enable_white=True, white_sigma=1e-8)
        cfg3 = NoiseConfig(seed=999, enable_white=True, white_sigma=1e-8)

        gen1 = SyntheticNoiseGenerator(cfg1)
        gen2 = SyntheticNoiseGenerator(cfg2)
        gen3 = SyntheticNoiseGenerator(cfg3)

        out1 = gen1.apply_noise(self.clean_snapshot_vec)
        out2 = gen2.apply_noise(self.clean_snapshot_vec)
        out3 = gen3.apply_noise(self.clean_snapshot_vec)

        self.assertTrue(np.array_equal(out1, out2))
        self.assertFalse(np.array_equal(out1, out3))

    def test_independent_toggling(self):
        """Enabling one component should not contaminate other components."""
        # 1. White noise only -> mean across long time series should approach zero
        cfg_white = NoiseConfig(seed=1, enable_white=True, white_sigma=1e-8)
        gen_white = SyntheticNoiseGenerator(cfg_white)
        ts_white = gen_white.apply_noise(np.zeros((1000, 9)), dt=0.01)
        self.assertAlmostEqual(np.mean(ts_white), 0.0, delta=1e-9)

        # 2. Offset only -> std across time for any sensor must be exactly 0
        cfg_offset = NoiseConfig(seed=1, enable_offset=True, offset_sigma=1e-8)
        gen_offset = SyntheticNoiseGenerator(cfg_offset)
        ts_offset = gen_offset.apply_noise(np.zeros((100, 9)), dt=0.01)
        time_std_per_sensor = np.std(ts_offset, axis=0)
        np.testing.assert_allclose(time_std_per_sensor, 0.0, atol=1e-15)

        # 3. Static Earth field only -> spatial variance and temporal variance must both be exactly 0
        cfg_earth = NoiseConfig(
            seed=1,
            enable_earth_field=True,
            earth_field_vector=np.array([1e-5, 2e-5, 5e-5]),
        )
        gen_earth = SyntheticNoiseGenerator(cfg_earth)
        ts_earth = gen_earth.apply_noise(np.zeros((50, 9, 3)), dt=0.01)
        # Spatial std across sensors must be 0
        np.testing.assert_allclose(np.std(ts_earth, axis=1), 0.0, atol=1e-15)
        # Temporal std across time must be 0
        np.testing.assert_allclose(np.std(ts_earth, axis=0), 0.0, atol=1e-15)

        # 4. AC interference only -> spatial variance across sensors is 0, temporal variance > 0
        cfg_ac = NoiseConfig(
            seed=1,
            enable_ac_interference=True,
            ac_interference_amplitude=5e-9,
            ac_interference_freq=60.0,
        )
        gen_ac = SyntheticNoiseGenerator(cfg_ac)
        ts_ac = gen_ac.apply_noise(np.zeros((100, 9)), dt=0.005)
        np.testing.assert_allclose(np.std(ts_ac, axis=1), 0.0, atol=1e-15)
        self.assertGreater(np.mean(np.std(ts_ac, axis=0)), 1e-9)

    def test_white_noise_statistics(self):
        """Monte Carlo verification of white Gaussian noise mean and variance."""
        sigma = 1e-8  # 10 nT
        n_samples = 100000
        cfg = NoiseConfig(seed=123, enable_white=True, white_sigma=sigma)
        gen = SyntheticNoiseGenerator(cfg)

        clean = np.zeros(n_samples)
        noisy = gen.apply_noise(clean)

        sample_mean = np.mean(noisy)
        sample_std = np.std(noisy)

        # Standard error of the mean = sigma / sqrt(N)
        sem = sigma / np.sqrt(n_samples)
        self.assertLess(abs(sample_mean), 3.0 * sem)
        # Standard deviation within 2% of true value
        self.assertAlmostEqual(sample_std, sigma, delta=0.02 * sigma)

    def test_sensor_offset_constancy_and_distribution(self):
        """DC offsets remain constant over time and match requested spread across sensors."""
        sigma_offset = 2e-8  # 20 nT
        n_sensors = 5000
        n_times = 20

        cfg = NoiseConfig(seed=456, enable_offset=True, offset_sigma=sigma_offset)
        gen = SyntheticNoiseGenerator(cfg)

        clean = np.zeros((n_times, n_sensors))
        noisy = gen.apply_noise(clean, dt=0.01)

        # Each sensor's reading must be constant across all time steps
        sensor_time_stds = np.std(noisy, axis=0)
        np.testing.assert_allclose(sensor_time_stds, 0.0, atol=1e-15)

        # Offsets across the sensor ensemble must follow N(0, sigma_offset^2)
        offsets = noisy[0]
        self.assertAlmostEqual(np.mean(offsets), 0.0, delta=3 * sigma_offset / np.sqrt(n_sensors))
        self.assertAlmostEqual(np.std(offsets), sigma_offset, delta=0.05 * sigma_offset)

    def test_gauss_markov_drift_autocorrelation(self):
        """Verify Gauss-Markov drift stationary variance and exponential autocorrelation decay."""
        sigma_drift = 1e-8
        tau = 2.0  # 2 seconds
        dt = 0.05  # 50 ms
        n_times = 40000

        cfg = NoiseConfig(
            seed=789,
            enable_drift=True,
            drift_sigma=sigma_drift,
            drift_tau=tau,
        )
        gen = SyntheticNoiseGenerator(cfg)

        clean = np.zeros((n_times, 1))
        drift_series = gen.apply_noise(clean, dt=dt)[:, 0]

        # Stationary variance
        self.assertAlmostEqual(np.std(drift_series), sigma_drift, delta=0.05 * sigma_drift)

        # Empirical autocorrelation at lag k*dt
        def autocorr_at_lag(series, lag):
            s0 = series[:-lag] - np.mean(series)
            s1 = series[lag:] - np.mean(series)
            return np.mean(s0 * s1) / np.var(series)

        # Theoretical autocorrelation: R(t) = exp(-t / tau)
        lags_to_test = [1, 5, 20, 40]  # lag times: 0.05s, 0.25s, 1.0s, 2.0s
        for lag in lags_to_test:
            lag_time = lag * dt
            expected_rho = np.exp(-lag_time / tau)
            empirical_rho = autocorr_at_lag(drift_series, lag)
            self.assertAlmostEqual(empirical_rho, expected_rho, delta=0.05)

    def test_common_mode_spatial_gradient(self):
        """Earth background and AC interference produce zero differential signal across the array."""
        cfg = NoiseConfig(
            seed=101,
            enable_earth_field=True,
            earth_field_vector=np.array([1e-5, 2e-5, 5e-5]),
            enable_ac_interference=True,
            ac_interference_amplitude=5e-8,
            ac_interference_freq=60.0,
        )
        gen = SyntheticNoiseGenerator(cfg)

        clean = np.zeros((100, 9, 3))
        noisy = gen.apply_noise(clean, dt=0.001)

        # Check difference between sensor 0 and sensor 8 at all times
        diff = noisy[:, 0, :] - noisy[:, 8, :]
        np.testing.assert_allclose(diff, 0.0, atol=1e-15)

    def test_spatial_correlation_distance_decay(self):
        """Empirical correlation between sensor pairs decays with physical distance."""
        l_corr = 0.05  # 5 cm correlation length
        sigma_sp = 1e-8
        cfg = NoiseConfig(
            seed=202,
            enable_spatial_correlation=True,
            spatial_sigma=sigma_sp,
            spatial_length_scale=l_corr,
        )
        gen = SyntheticNoiseGenerator(cfg)

        n_times = 50000
        clean = np.zeros((n_times, 9))
        noisy = gen.apply_noise(clean, sensor_positions=self.sensors, dt=0.01)

        # Correlation between center sensor (idx 4, at 0,0,0) and:
        # 1. Neighbor at 2 cm (idx 5, at 0.02, 0, 0) -> distance 0.02m
        # 2. Diagonal corner at 2.83 cm (idx 8, at 0.02, 0.02, 0) -> distance 0.0283m
        corr_matrix = np.corrcoef(noisy, rowvar=False)

        # Theoretical correlation = exp(-dist^2 / (2 * l_corr^2))
        d_close = 0.02
        rho_close_expected = np.exp(-(d_close**2) / (2.0 * l_corr**2))  # exp(-0.02^2 / 0.005) = exp(-0.08) ~ 0.923
        rho_close_actual = corr_matrix[4, 5]

        d_far = np.sqrt(0.02**2 + 0.02**2)  # ~0.0283m
        rho_far_expected = np.exp(-(d_far**2) / (2.0 * l_corr**2))   # exp(-0.16) ~ 0.852
        rho_far_actual = corr_matrix[4, 8]

        self.assertAlmostEqual(rho_close_actual, rho_close_expected, delta=0.05)
        self.assertAlmostEqual(rho_far_actual, rho_far_expected, delta=0.05)
        # Closer pair must have strictly higher correlation than farther pair
        self.assertGreater(rho_close_actual, rho_far_actual)


if __name__ == "__main__":
    unittest.main()
