"""
Modular, seed-controlled synthetic noise framework for the magnetic sensing simulator.

Measurement Model:
    B_measured(t) = B_target(t) + B_earth + B_ac_interference(t) + b_offset + n_drift(t) + n_white(t) + n_spatial(t)

Disclaimer:
    These models are synthetic simulation tools for observability, conditioning,
    and algorithm robustness studies. Noise parameters (such as 10 nT) are simulation
    settings, NOT measured hardware parameters, unless explicitly calibrated against
    physical sensor data.

Mathematical Formulations & Phenomenological Models:
    1. White Noise:
       A phenomenological model representing broadband sensor/electronics noise,
       including effects that may arise from thermal, amplifier, and quantization sources:
       n_white ~ N(0, sigma_white^2)

    2. Static DC Offset:
       A phenomenological model for fixed, per-sensor calibration biases, fabrication
       tolerances, and mounting stress constant over time:
       b_offset ~ N(0, sigma_offset^2) (drawn once per sensor/axis)

    3. Low-Frequency Drift (First-Order Gauss-Markov / AR(1)):
       A phenomenological model for temporally correlated low-frequency drift,
       representing slow variations that may arise from thermal, mechanical, or
       flicker-like relaxation processes. Modeled rigorously as a stationary discrete
       Ornstein-Uhlenbeck / AR(1) process with correlation time tau:
       n[k] = alpha * n[k-1] + sqrt(1 - alpha^2) * sigma_drift * w[k]
       where alpha = exp(-dt / tau), w[k] ~ N(0, 1), and n[0] ~ N(0, sigma_drift^2).
       Guarantees stationary variance sigma_drift^2 and autocorrelation R(dt) = exp(-dt / tau).
       (Explicitly distinct from a true 1/f fractional noise process).

    4. Ambient Geomagnetic Background (Earth's Field):
       Uniform static ambient magnetic background (e.g. ~50 uT geomagnetic field).

    5. Narrowband AC Harmonic Interference:
       Spatially uniform harmonic electromagnetic interference (e.g. 50/60 Hz powerline hum):
       B_ac(t) = A_ac * sin(2*pi*f_ac*t + phi) * u_dir

    6. Spatially Correlated Noise:
       A phenomenological model for spatially correlated disturbances, allowing the
       simulator to study the effect of non-independent sensor errors:
       Sigma_ij = sigma_spatial^2 * exp(-||r_i - r_j||^2 / (2 * l_corr^2))
       Sampled via Cholesky factor L: n_spatial = L * z, z ~ N(0, I).
"""

from dataclasses import dataclass, field
from typing import Optional, Union, Tuple
import numpy as np


@dataclass
class NoiseConfig:
    """Configuration for synthetic magnetic sensor noise components."""

    seed: Optional[int] = None

    # 1. Sensor-independent broadband white Gaussian noise
    enable_white: bool = False
    white_sigma: float = 0.0  # Tesla [T]

    # 2. Fixed per-sensor DC offset (calibration bias)
    enable_offset: bool = False
    offset_sigma: float = 0.0  # Tesla [T]
    sensor_offsets: Optional[np.ndarray] = None  # Explicit custom offsets

    # 3. Temporally correlated low-frequency drift (Gauss-Markov / AR(1))
    enable_drift: bool = False
    drift_sigma: float = 0.0  # Stationary standard deviation [T]
    drift_tau: float = 10.0   # Correlation time constant [s]

    # 4. Ambient static geomagnetic background field (Earth's field)
    enable_earth_field: bool = False
    earth_field_vector: Optional[np.ndarray] = None  # Baseline [Bx, By, Bz] in T (e.g. [0, 0, 50e-6])

    # 5. Narrowband AC harmonic interference (e.g. 50/60 Hz powerline hum)
    enable_ac_interference: bool = False
    ac_interference_amplitude: float = 0.0           # Peak AC amplitude in T
    ac_interference_freq: float = 60.0               # AC frequency in Hz
    ac_interference_dir: Optional[np.ndarray] = None # AC unit vector direction

    # 6. Spatially correlated sensor noise
    enable_spatial_correlation: bool = False
    spatial_sigma: float = 0.0        # Perturbation standard deviation [T]
    spatial_length_scale: float = 0.1  # Correlation length l_corr [m]

    # Backward compatibility aliases for common-mode
    enable_common_mode: bool = False
    common_mode_static: Optional[np.ndarray] = None
    common_mode_ac_amplitude: float = 0.0
    common_mode_ac_freq: float = 0.0
    common_mode_ac_dir: Optional[np.ndarray] = None


class SyntheticNoiseGenerator:
    """
    Seed-controlled generator for synthetic magnetic sensor noise.

    Uses an isolated `np.random.Generator` instance (via `default_rng`)
    to ensure full reproducibility without altering global NumPy RNG state.
    """

    def __init__(self, config: Optional[NoiseConfig] = None):
        self.config = config if config is not None else NoiseConfig()
        self.rng = np.random.default_rng(self.config.seed)
        self._cached_offsets = None

    def reset_seed(self, seed: Optional[int] = None):
        """Reset the internal random number generator with a specific seed."""
        if seed is not None:
            self.config.seed = seed
        self.rng = np.random.default_rng(self.config.seed)
        self._cached_offsets = None

    def _get_sensor_offsets(self, n_sensors: int, n_axes: int) -> np.ndarray:
        """Retrieve or generate fixed static per-sensor offsets."""
        if self.config.sensor_offsets is not None:
            offsets = np.asarray(self.config.sensor_offsets, dtype=float)
            if offsets.shape != (n_sensors, n_axes):
                offsets = offsets.reshape((n_sensors, n_axes))
            return offsets

        if self._cached_offsets is None or self._cached_offsets.shape != (n_sensors, n_axes):
            self._cached_offsets = self.rng.normal(
                loc=0.0,
                scale=self.config.offset_sigma,
                size=(n_sensors, n_axes),
            )
        return self._cached_offsets

    def apply_noise(
        self,
        clean_field: np.ndarray,
        sensor_positions: Optional[np.ndarray] = None,
        timestamps: Optional[np.ndarray] = None,
        dt: Optional[float] = None,
        is_timeseries: Optional[bool] = None,
    ) -> np.ndarray:
        """
        Apply configured synthetic noise terms to a clean magnetic field.

        Parameters
        ----------
        clean_field : ndarray
            Clean field array. Supported shapes:
            - (N_sensors, 3): static snapshot 3-axis vectors
            - (N_sensors,): static snapshot scalar (e.g. Bz)
            - (N_times, N_sensors, 3): time-series 3-axis vectors
            - (N_times, N_sensors): time-series scalar
        sensor_positions : ndarray, optional
            Sensor positions (N_sensors, 3) in meters. Required if spatial
            correlation is enabled.
        timestamps : ndarray, optional
            Time vector of shape (N_times,) in seconds.
        dt : float, optional
            Time step in seconds. If timestamps is not provided, timestamps
            will be generated as np.arange(N_times) * dt.
        is_timeseries : bool, optional
            Explicitly specify whether a 2D array represents a time series (N_times, N_sensors)
            or a static vector snapshot (N_sensors, N_axes). If None, automatically inferred
            from dt, timestamps, or shape[1] == 3.

        Returns
        -------
        noisy_field : ndarray
            Field with synthetic noise added, identical shape to `clean_field`.
        """
        clean_arr = np.asarray(clean_field, dtype=float)
        shape = clean_arr.shape

        # If no noise components are enabled, return clean field bitwise untouched
        if not (
            self.config.enable_white
            or self.config.enable_offset
            or self.config.enable_drift
            or self.config.enable_earth_field
            or self.config.enable_ac_interference
            or self.config.enable_common_mode
            or self.config.enable_spatial_correlation
        ):
            return clean_arr.copy()

        # Parse dimensionality
        if clean_arr.ndim == 1:
            # (N_sensors,) static scalar
            is_ts = False
            n_times = 1
            n_sensors = shape[0]
            n_axes = 1
            working_shape = (1, n_sensors, 1)
        elif clean_arr.ndim == 2:
            # Disambiguate (N_sensors, 3) static vs (N_times, N_sensors) scalar time series
            if is_timeseries is not None:
                is_ts = is_timeseries
            elif timestamps is not None or dt is not None:
                is_ts = True
            elif shape[1] == 3:
                is_ts = False
            elif sensor_positions is not None and len(sensor_positions) == shape[0]:
                is_ts = False
            else:
                is_ts = True

            if is_ts:
                n_times, n_sensors = shape
                n_axes = 1
                working_shape = (n_times, n_sensors, 1)
            else:
                n_times = 1
                n_sensors, n_axes = shape
                working_shape = (1, n_sensors, n_axes)
        elif clean_arr.ndim == 3:
            # (N_times, N_sensors, n_axes)
            is_ts = True
            n_times, n_sensors, n_axes = shape
            working_shape = shape
        else:
            raise ValueError(f"Unsupported clean_field shape: {shape}")

        is_timeseries = is_ts

        # Setup time array
        if is_timeseries:
            if timestamps is not None:
                t = np.asarray(timestamps, dtype=float)
                if len(t) != n_times:
                    raise ValueError(f"timestamps length {len(t)} != N_times {n_times}")
                if dt is None and n_times > 1:
                    dt = float(np.mean(np.diff(t)))
            elif dt is not None:
                t = np.arange(n_times, dtype=float) * dt
            else:
                dt = 1.0
                t = np.arange(n_times, dtype=float) * dt
        else:
            t = np.array([0.0])
            dt = 1.0

        # Total noise accumulator of shape (n_times, n_sensors, n_axes)
        noise_total = np.zeros(working_shape, dtype=float)

        # 1. White Gaussian Noise
        if self.config.enable_white and self.config.white_sigma > 0:
            noise_total += self.rng.normal(
                loc=0.0,
                scale=self.config.white_sigma,
                size=working_shape,
            )

        # 2. Static DC Offset (constant over time for each sensor)
        if self.config.enable_offset and (self.config.offset_sigma > 0 or self.config.sensor_offsets is not None):
            offsets = self._get_sensor_offsets(n_sensors, n_axes)  # (n_sensors, n_axes)
            noise_total += offsets[None, :, :]  # broadcast across n_times

        # 3. Temporally Correlated Low-Frequency Drift (Gauss-Markov / AR(1))
        if self.config.enable_drift and self.config.drift_sigma > 0:
            drift_arr = np.zeros(working_shape, dtype=float)
            tau = max(self.config.drift_tau, 1e-6)
            alpha = np.exp(-dt / tau)
            sigma_w = self.config.drift_sigma * np.sqrt(max(0.0, 1.0 - alpha**2))

            # Initial state drawn from stationary distribution N(0, drift_sigma^2)
            drift_arr[0] = self.rng.normal(
                loc=0.0,
                scale=self.config.drift_sigma,
                size=(n_sensors, n_axes),
            )

            # Step AR(1) process
            for k in range(1, n_times):
                w = self.rng.normal(loc=0.0, scale=sigma_w, size=(n_sensors, n_axes))
                drift_arr[k] = alpha * drift_arr[k - 1] + w

            noise_total += drift_arr

        # 4. Ambient Static Geomagnetic Background Field (Earth's Field)
        has_earth = self.config.enable_earth_field or (
            self.config.enable_common_mode and self.config.common_mode_static is not None
        )
        if has_earth:
            earth_vec = (
                self.config.earth_field_vector
                if self.config.enable_earth_field
                else self.config.common_mode_static
            )
            if earth_vec is not None:
                cm_static = np.asarray(earth_vec, dtype=float)
                if n_axes == 1 and cm_static.ndim > 0:
                    cm_static = cm_static[-1]  # Use z-component for scalar Bz
                noise_total += cm_static  # Broadcasts across (n_times, n_sensors, n_axes)

        # 5. Narrowband AC Harmonic Interference (e.g. 50/60 Hz powerline hum)
        has_ac = self.config.enable_ac_interference or (
            self.config.enable_common_mode and self.config.common_mode_ac_amplitude > 0
        )
        if has_ac:
            ac_amp = (
                self.config.ac_interference_amplitude
                if self.config.enable_ac_interference
                else self.config.common_mode_ac_amplitude
            )
            ac_freq = (
                self.config.ac_interference_freq
                if self.config.enable_ac_interference
                else self.config.common_mode_ac_freq
            )
            ac_dir = (
                self.config.ac_interference_dir
                if self.config.enable_ac_interference
                else self.config.common_mode_ac_dir
            )
            if ac_amp > 0 and ac_freq > 0:
                ac_wave = ac_amp * np.sin(2.0 * np.pi * ac_freq * t)  # shape (n_times,)
                if n_axes == 3:
                    direction = (
                        np.array([0.0, 0.0, 1.0])
                        if ac_dir is None
                        else np.asarray(ac_dir, dtype=float)
                    )
                    direction = direction / np.linalg.norm(direction)
                    ac_signal = ac_wave[:, None, None] * direction[None, None, :]
                else:
                    ac_signal = ac_wave[:, None, None]
                noise_total += ac_signal

        # 5. Spatially Correlated Noise
        if self.config.enable_spatial_correlation and self.config.spatial_sigma > 0:
            if sensor_positions is None:
                raise ValueError("sensor_positions must be provided when enable_spatial_correlation is True.")
            sensors = np.asarray(sensor_positions, dtype=float)
            if len(sensors) != n_sensors:
                raise ValueError(f"sensor_positions length {len(sensors)} != n_sensors {n_sensors}")

            # Compute distance matrix and covariance kernel
            diff = sensors[:, None, :] - sensors[None, :, :]
            dist_sq = np.sum(diff**2, axis=-1)
            l_corr = max(self.config.spatial_length_scale, 1e-6)
            cov = self.config.spatial_sigma**2 * np.exp(-dist_sq / (2.0 * l_corr**2))

            # Regularize slightly for numerical positive-definiteness
            cov += np.eye(n_sensors) * (1e-12 * self.config.spatial_sigma**2)
            L_cov = np.linalg.cholesky(cov)  # (n_sensors, n_sensors)

            # Sample spatial noise for each time step and axis
            spatial_noise = np.zeros(working_shape, dtype=float)
            for k in range(n_times):
                for ax in range(n_axes):
                    z_uncorr = self.rng.normal(loc=0.0, scale=1.0, size=n_sensors)
                    spatial_noise[k, :, ax] = L_cov @ z_uncorr

            noise_total += spatial_noise

        # Reshape to match input
        return clean_arr + noise_total.reshape(shape)
