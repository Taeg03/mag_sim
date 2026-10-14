"""
Characterization and demonstration of the modular synthetic noise framework.

Simulates a stationary magnetic target observed by a 3x3 sensor array over time.
Demonstrates isolated and combined noise components:
  1. Clean target field
  2. Sensor-independent white Gaussian noise
  3. Fixed per-sensor DC offset (calibration bias)
  4. Low-frequency drift (Gauss-Markov / AR(1) process)
  5. Common-mode background and powerline AC hum (60 Hz)
  6. Spatially correlated sensor noise
  7. Combined synthetic measurement time series
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch

from src.dipole import dipole_field
from src.array import create_planar_array
from src.noise import NoiseConfig, SyntheticNoiseGenerator


def run_noise_characterization():
    output_dir = "figures/noise_characterization"
    os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------
    # Setup: 3x3 array observing a stationary target
    # ------------------------------------------------------------
    sensors = create_planar_array(rows=3, cols=3, spacing=0.02)
    center_idx = 4  # sensor at (0, 0, 0)
    source_pos = np.array([0.0, 0.0, 0.30])  # 30 cm above array center
    moment = np.array([0.0, 0.0, 1.0])       # 1 A*m^2 vertical dipole

    # Static clean field at all 9 sensors
    B_clean_snapshot = dipole_field(sensors, source_pos, moment)  # (9, 3)

    # Time series parameters: 10 seconds at 200 Hz = 2000 samples
    # fs = 200 Hz ensures Nyquist frequency is 100 Hz, faithfully capturing 60 Hz AC hum without aliasing
    fs = 200.0  # Hz
    dt = 1.0 / fs
    t_total = 10.0
    timestamps = np.arange(0, t_total, dt)
    n_times = len(timestamps)

    # Replicate clean field across time: (n_times, 9, 3)
    B_clean_ts = np.tile(B_clean_snapshot[None, :, :], (n_times, 1, 1))

    # ------------------------------------------------------------
    # Configure Individual Synthetic Noise Components
    # ------------------------------------------------------------
    seed_base = 42

    # 1. Broadband White Noise only (10 nT)
    cfg_white = NoiseConfig(seed=seed_base, enable_white=True, white_sigma=10e-9)
    gen_white = SyntheticNoiseGenerator(cfg_white)
    B_white_only = gen_white.apply_noise(B_clean_ts, timestamps=timestamps)

    # 2. Fixed DC Offset only (20 nT spread across sensors)
    cfg_offset = NoiseConfig(seed=seed_base, enable_offset=True, offset_sigma=20e-9)
    gen_offset = SyntheticNoiseGenerator(cfg_offset)
    B_offset_only = gen_offset.apply_noise(B_clean_ts, timestamps=timestamps)

    # 3. Gauss-Markov Low-Frequency Drift only (15 nT stationary std, tau = 2.0 s)
    cfg_drift = NoiseConfig(
        seed=seed_base,
        enable_drift=True,
        drift_sigma=15e-9,
        drift_tau=2.0,
    )
    gen_drift = SyntheticNoiseGenerator(cfg_drift)
    B_drift_only = gen_drift.apply_noise(B_clean_ts, timestamps=timestamps)

    # 4. Ambient Geomagnetic Background (Earth's Field only: 50 uT static along z)
    cfg_earth = NoiseConfig(
        seed=seed_base,
        enable_earth_field=True,
        earth_field_vector=np.array([0.0, 0.0, 50e-6]),
    )
    gen_earth = SyntheticNoiseGenerator(cfg_earth)
    B_earth_only = gen_earth.apply_noise(B_clean_ts, timestamps=timestamps)

    # 5. Narrowband AC Harmonic Interference only (5 nT peak at 60 Hz along z)
    cfg_ac = NoiseConfig(
        seed=seed_base,
        enable_ac_interference=True,
        ac_interference_amplitude=5e-9,
        ac_interference_freq=60.0,
    )
    gen_ac = SyntheticNoiseGenerator(cfg_ac)
    B_ac_only = gen_ac.apply_noise(B_clean_ts, timestamps=timestamps)

    # 6. Spatially Correlated Noise only (10 nT, l_corr = 0.05 m)
    cfg_spatial = NoiseConfig(
        seed=seed_base,
        enable_spatial_correlation=True,
        spatial_sigma=10e-9,
        spatial_length_scale=0.05,
    )
    gen_spatial = SyntheticNoiseGenerator(cfg_spatial)
    B_spatial_only = gen_spatial.apply_noise(
        B_clean_ts, sensor_positions=sensors, timestamps=timestamps
    )

    # 7. Combined Realistic Simulation: All components active together
    cfg_combined = NoiseConfig(
        seed=seed_base,
        enable_white=True,
        white_sigma=10e-9,
        enable_offset=True,
        offset_sigma=20e-9,
        enable_drift=True,
        drift_sigma=15e-9,
        drift_tau=2.0,
        enable_earth_field=True,
        earth_field_vector=np.array([0.0, 0.0, 50e-6]),
        enable_ac_interference=True,
        ac_interference_amplitude=5e-9,
        ac_interference_freq=60.0,
        enable_spatial_correlation=True,
        spatial_sigma=10e-9,
        spatial_length_scale=0.05,
    )
    gen_combined = SyntheticNoiseGenerator(cfg_combined)
    B_combined = gen_combined.apply_noise(
        B_clean_ts, sensor_positions=sensors, timestamps=timestamps
    )

    # ------------------------------------------------------------
    # Plot 1: Time-Series Breakdown (Center Sensor Bz)
    # ------------------------------------------------------------
    fig, axes = plt.subplots(7, 1, figsize=(10, 14), sharex=True)

    # Clean Target Signal
    axes[0].plot(timestamps, B_clean_ts[:, center_idx, 2] * 1e6, "k-", linewidth=1.5)
    axes[0].set_ylabel("Clean (µT)")
    axes[0].set_title("Synthetic Sensor Noise Decomposition (Center Sensor Bz)", fontsize=12, pad=8)
    axes[0].grid(True, alpha=0.3)

    # White Noise perturbation
    axes[1].plot(timestamps, (B_white_only[:, center_idx, 2] - B_clean_ts[:, center_idx, 2]) * 1e9, "tab:blue", linewidth=0.8)
    axes[1].set_ylabel("White (nT)")
    axes[1].set_title("Broadband Sensor/Electronics Noise (σ = 10 nT)", fontsize=10)
    axes[1].grid(True, alpha=0.3)

    # Fixed DC Offset (showing sensors 0, 4, 8)
    for s_idx, col, lbl in [(0, "tab:green", "Sensor 0"), (4, "k", "Sensor 4 (Center)"), (8, "tab:orange", "Sensor 8")]:
        axes[2].plot(timestamps, (B_offset_only[:, s_idx, 2] - B_clean_ts[:, s_idx, 2]) * 1e9, color=col, label=lbl)
    axes[2].set_ylabel("Offset (nT)")
    axes[2].set_title("Fixed Per-Sensor DC Calibration Offsets (Constant over time)", fontsize=10)
    axes[2].legend(loc="upper right", fontsize=8)
    axes[2].grid(True, alpha=0.3)

    # Gauss-Markov Drift
    axes[3].plot(timestamps, (B_drift_only[:, center_idx, 2] - B_clean_ts[:, center_idx, 2]) * 1e9, "tab:purple", linewidth=1.2)
    axes[3].set_ylabel("Drift (nT)")
    axes[3].set_title("Temporally Correlated Low-Frequency Drift (Gauss-Markov, τ = 2.0 s, σ = 15 nT)", fontsize=10)
    axes[3].grid(True, alpha=0.3)

    # Narrowband AC Harmonic Interference
    axes[4].plot(timestamps[:400], (B_ac_only[:400, center_idx, 2] - B_clean_ts[:400, center_idx, 2]) * 1e9, "tab:red", linewidth=1.0)
    axes[4].set_ylabel("AC Hum (nT)")
    axes[4].set_title("Narrowband AC Interference (60 Hz, 5 nT peak, zoomed 0-2s)", fontsize=10)
    axes[4].grid(True, alpha=0.3)

    # Spatially Correlated Noise
    axes[5].plot(timestamps, (B_spatial_only[:, center_idx, 2] - B_clean_ts[:, center_idx, 2]) * 1e9, "tab:cyan", linewidth=0.8)
    axes[5].set_ylabel("Spatial (nT)")
    axes[5].set_title("Spatially Correlated Disturbance (σ = 10 nT, l_corr = 5 cm)", fontsize=10)
    axes[5].grid(True, alpha=0.3)

    # Combined Total Measurement
    axes[6].plot(timestamps, B_combined[:, center_idx, 2] * 1e6, "k-", linewidth=0.8)
    axes[6].set_ylabel("Total (µT)")
    axes[6].set_title("Combined Measurement (Target + Earth Background 50µT + All Noise Terms)", fontsize=10)
    axes[6].set_xlabel("Time (s)", fontsize=11)
    axes[6].grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(f"{output_dir}/noise_time_series_breakdown.png", dpi=300)
    plt.close(fig)

    # ------------------------------------------------------------
    # Plot 2: Power Spectral Density Comparison
    # ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))

    # Center sensor noise traces
    noise_white = (B_white_only[:, center_idx, 2] - B_clean_ts[:, center_idx, 2]) * 1e9
    noise_drift = (B_drift_only[:, center_idx, 2] - B_clean_ts[:, center_idx, 2]) * 1e9
    noise_ac = (B_ac_only[:, center_idx, 2] - B_clean_ts[:, center_idx, 2]) * 1e9
    noise_comb = (B_combined[:, center_idx, 2] - B_clean_ts[:, center_idx, 2] - 50e-6) * 1e9

    f_w, p_w = welch(noise_white, fs=fs, nperseg=512)
    f_d, p_d = welch(noise_drift, fs=fs, nperseg=512)
    f_ac, p_ac = welch(noise_ac, fs=fs, nperseg=512)
    f_tot, p_tot = welch(noise_comb, fs=fs, nperseg=512)

    ax.semilogy(f_w, p_w, label="White Noise (Flat spectrum)", color="tab:blue")
    ax.semilogy(f_d, p_d, label="Gauss-Markov Drift (Low-freq roll-off)", color="tab:purple", linewidth=1.5)
    ax.semilogy(f_ac, p_ac, label="Narrowband AC Hum (60 Hz peak)", color="tab:red")
    ax.semilogy(f_tot, p_tot, label="Combined Total Noise", color="k", linewidth=1.5, linestyle="--")

    ax.set_xlabel("Frequency (Hz)", fontsize=11)
    ax.set_ylabel("Power Spectral Density (nT² / Hz)", fontsize=11)
    ax.set_title("Spectral Characteristics of Synthetic Noise Components", fontsize=12, pad=10)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="upper right")

    plt.tight_layout()
    fig.savefig(f"{output_dir}/noise_power_spectral_density.png", dpi=300)
    plt.close(fig)

    # ------------------------------------------------------------
    # Plot 3: Spatial Correlation Matrix Heatmap
    # ------------------------------------------------------------
    # Extract spatial noise fluctuations across all 9 sensors
    spatial_noise_only = B_spatial_only[:, :, 2] - B_clean_ts[:, :, 2]
    corr_empirical = np.corrcoef(spatial_noise_only, rowvar=False)

    # Theoretical spatial correlation matrix
    diff = sensors[:, None, :] - sensors[None, :, :]
    dist_matrix = np.linalg.norm(diff, axis=-1)
    corr_theoretical = np.exp(-dist_matrix**2 / (2.0 * 0.05**2))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    im1 = ax1.imshow(corr_theoretical, cmap="viridis", vmin=0.5, vmax=1.0)
    ax1.set_title("Theoretical Spatial Correlation Matrix\n(l_corr = 5 cm)", fontsize=10)
    ax1.set_xlabel("Sensor Index")
    ax1.set_ylabel("Sensor Index")
    fig.colorbar(im1, ax=ax1, label="Correlation")

    im2 = ax2.imshow(corr_empirical, cmap="viridis", vmin=0.5, vmax=1.0)
    ax2.set_title("Empirical Sensor Correlation Matrix\n(Sampled via Cholesky decomposition)", fontsize=10)
    ax2.set_xlabel("Sensor Index")
    ax2.set_ylabel("Sensor Index")
    fig.colorbar(im2, ax=ax2, label="Correlation")

    plt.tight_layout()
    fig.savefig(f"{output_dir}/spatial_correlation_heatmap.png", dpi=300)
    plt.close(fig)

    # ------------------------------------------------------------
    # Statistical Validation Summary
    # ------------------------------------------------------------
    print("\n" + "=" * 80)
    print("SYNTHETIC NOISE FRAMEWORK STATISTICAL VALIDATION")
    print("=" * 80)
    print(f"{'Component':<25} | {'Metric':<25} | {'Expected':<12} | {'Measured':<12}")
    print("-" * 80)

    # White noise stats
    w_std = np.std(noise_white)
    print(f"{'Broadband White Noise':<25} | {'Std Dev':<25} | {'10.00 nT':<12} | {f'{w_std:.2f} nT':<12}")

    # Offset stats
    offsets_extracted = (B_offset_only[0, :, 2] - B_clean_ts[0, :, 2]) * 1e9
    off_time_std = np.max(np.std(B_offset_only[:, :, 2], axis=0))
    print(f"{'Fixed DC Offset':<25} | {'Max Time Std Dev':<25} | {'0.00 nT':<12} | {f'{off_time_std*1e9:.2e} nT':<12}")

    # Drift stats
    d_std = np.std(noise_drift)
    print(f"{'Gauss-Markov Drift':<25} | {'Stationary Std Dev':<25} | {'15.00 nT':<12} | {f'{d_std:.2f} nT':<12}")

    # Earth field stats
    earth_val = B_earth_only[0, center_idx, 2] - B_clean_ts[0, center_idx, 2]
    print(f"{'Earth Field Baseline':<25} | {'Static Bz':<25} | {'50.00 µT':<12} | {f'{earth_val*1e6:.2f} µT':<12}")

    # AC interference stats
    ac_amp_est = (np.max(B_ac_only[:, center_idx, 2]) - np.min(B_ac_only[:, center_idx, 2])) / 2.0 * 1e9
    print(f"{'Narrowband AC Hum':<25} | {'Peak Amplitude':<25} | {'5.00 nT':<12} | {f'{ac_amp_est:.2f} nT':<12}")

    # Spatial correlation stats
    max_corr_diff = np.max(np.abs(corr_empirical - corr_theoretical))
    print(f"{'Spatial Covariance':<25} | {'Max Corr Error':<25} | {'< 0.05':<12} | {f'{max_corr_diff:.4f}':<12}")
    print("=" * 80)
    print(f"Figures saved to: {output_dir}/\n")


if __name__ == "__main__":
    run_noise_characterization()
