"""
Quantitative comparison of ideal point dipole vs finite cuboid and cylindrical magnets.

Evaluates field magnitude, array RMSE, and relative error across source-to-sensor
distances and orientations to identify the regime where the dipole approximation
breaks down.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation

from src.dipole import dipole_field
from src.array import create_planar_array
from src.magpylib_backend import (
    magpylib_dipole_field,
    magpylib_cuboid_field,
    magpylib_cylinder_field,
)


def run_finite_source_comparison():
    # ------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------
    output_dir = "figures/finite_source_comparison"
    os.makedirs(output_dir, exist_ok=True)

    # 3x3 sensor array, 2 cm spacing (4 cm aperture)
    sensors = create_planar_array(rows=3, cols=3, spacing=0.02)
    center_idx = 4  # sensor at (0, 0, 0)

    # Magnet specifications: 10 mm characteristic size
    L_mag = 0.01  # 10 mm = 0.01 m
    moment_mag = 1.0  # 1.0 A*m^2
    cuboid_dim = np.array([L_mag, L_mag, L_mag])
    cylinder_dim = np.array([L_mag, L_mag])  # diameter=10mm, height=10mm

    # Source distances: from near-field (0.6 * L_mag) to far-field (100 * L_mag)
    # At z=0.006 m, bottom edge of 10 mm magnet is 1 mm above z=0 plane
    distances = np.logspace(np.log10(0.006), np.log10(1.0), 60)

    # ------------------------------------------------------------
    # Study 1: Vertical Dipole vs Cuboid vs Cylinder across Distance
    # ------------------------------------------------------------
    base_moment = np.array([0.0, 0.0, moment_mag])

    dipole_center_bz = []
    cuboid_center_bz = []
    cylinder_center_bz = []

    cuboid_rel_err_center = []
    cylinder_rel_err_center = []

    cuboid_rel_err_array = []
    cylinder_rel_err_array = []

    cuboid_rmse_array = []
    cylinder_rmse_array = []

    for z in distances:
        pos = np.array([0.0, 0.0, z])

        # Point dipole
        B_dip = dipole_field(sensors, pos, base_moment)
        # Cuboid
        B_cub = magpylib_cuboid_field(
            sensors, pos, dimension=cuboid_dim, moment=base_moment
        )
        # Cylinder
        B_cyl = magpylib_cylinder_field(
            sensors, pos, dimension=cylinder_dim, moment=base_moment
        )

        # Center sensor fields
        bz_dip_c = B_dip[center_idx, 2]
        bz_cub_c = B_cub[center_idx, 2]
        bz_cyl_c = B_cyl[center_idx, 2]

        dipole_center_bz.append(abs(bz_dip_c))
        cuboid_center_bz.append(abs(bz_cub_c))
        cylinder_center_bz.append(abs(bz_cyl_c))

        # Center sensor relative error
        cuboid_rel_err_center.append(abs(bz_cub_c - bz_dip_c) / abs(bz_dip_c))
        cylinder_rel_err_center.append(abs(bz_cyl_c - bz_dip_c) / abs(bz_dip_c))

        # Full array vector relative error (Frobenius norm)
        norm_dip = np.linalg.norm(B_dip)
        cuboid_rel_err_array.append(np.linalg.norm(B_cub - B_dip) / norm_dip)
        cylinder_rel_err_array.append(np.linalg.norm(B_cyl - B_dip) / norm_dip)

        # Full array vector RMSE (Tesla)
        cuboid_rmse_array.append(np.sqrt(np.mean(np.sum((B_cub - B_dip) ** 2, axis=1))))
        cylinder_rmse_array.append(np.sqrt(np.mean(np.sum((B_cyl - B_dip) ** 2, axis=1))))

    dipole_center_bz = np.array(dipole_center_bz)
    cuboid_center_bz = np.array(cuboid_center_bz)
    cylinder_center_bz = np.array(cylinder_center_bz)
    cuboid_rel_err_center = np.array(cuboid_rel_err_center)
    cylinder_rel_err_center = np.array(cylinder_rel_err_center)
    cuboid_rel_err_array = np.array(cuboid_rel_err_array)
    cylinder_rel_err_array = np.array(cylinder_rel_err_array)

    # ------------------------------------------------------------
    # Study 2: Orientation Sensitivity (0 deg, 45 deg, 90 deg)
    # ------------------------------------------------------------
    angles = [0, 45, 90]
    orientation_results = {}

    for angle in angles:
        rot = Rotation.from_euler("y", angle, degrees=True)
        mom_rot = rot.apply(base_moment)

        cub_errs = []
        cyl_errs = []

        for z in distances:
            pos = np.array([0.0, 0.0, z])
            B_dip = dipole_field(sensors, pos, mom_rot)
            B_cub = magpylib_cuboid_field(
                sensors, pos, dimension=cuboid_dim, moment=base_moment, orientation=rot
            )
            B_cyl = magpylib_cylinder_field(
                sensors, pos, dimension=cylinder_dim, moment=base_moment, orientation=rot
            )

            norm_dip = np.linalg.norm(B_dip)
            cub_errs.append(np.linalg.norm(B_cub - B_dip) / norm_dip)
            cyl_errs.append(np.linalg.norm(B_cyl - B_dip) / norm_dip)

        orientation_results[angle] = {
            "cuboid": np.array(cub_errs),
            "cylinder": np.array(cyl_errs),
        }

    # ------------------------------------------------------------
    # Generate Plots
    # ------------------------------------------------------------

    # Plot 1: Center Bz and Relative Error vs Distance
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

    ax1.loglog(distances, dipole_center_bz * 1e6, "k-", linewidth=2, label="Point Dipole")
    ax1.loglog(distances, cuboid_center_bz * 1e6, "r--", linewidth=1.5, label="Finite Cuboid (10mm)")
    ax1.loglog(distances, cylinder_center_bz * 1e6, "b-.", linewidth=1.5, label="Finite Cylinder (Ø10x10mm)")
    ax1.axvline(L_mag, color="gray", linestyle=":", label=f"Magnet Size L={L_mag*1e3:.0f}mm")
    ax1.set_ylabel("|Bz| at Center Sensor (µT)", fontsize=11)
    ax1.set_title("Magnetic Field & Dipole Model Breakdown vs Distance", fontsize=12, pad=10)
    ax1.grid(True, which="both", alpha=0.3)
    ax1.legend(loc="upper right")

    ax2.loglog(distances, cuboid_rel_err_center * 100, "r-", linewidth=1.8, label="Cuboid (Center |Bz| Error)")
    ax2.loglog(distances, cylinder_rel_err_center * 100, "b-", linewidth=1.8, label="Cylinder (Center |Bz| Error)")
    ax2.loglog(distances, cuboid_rel_err_array * 100, "r--", alpha=0.7, label="Cuboid (Array Vector Error)")
    ax2.loglog(distances, cylinder_rel_err_array * 100, "b--", alpha=0.7, label="Cylinder (Array Vector Error)")
    ax2.axhline(5.0, color="orange", linestyle="--", label="5% Inadequacy Threshold")
    ax2.axhline(1.0, color="green", linestyle="--", label="1% Precision Threshold")
    ax2.axvline(L_mag, color="gray", linestyle=":")
    ax2.set_xlabel("Source Distance z (m)", fontsize=11)
    ax2.set_ylabel("Relative Error (%)", fontsize=11)
    ax2.grid(True, which="both", alpha=0.3)
    ax2.legend(loc="upper right")

    plt.tight_layout()
    fig.savefig(f"{output_dir}/distance_comparison.png", dpi=300)
    plt.close(fig)

    # Plot 2: Relative Error vs Normalized Distance z / L_mag
    normalized_z = distances / L_mag
    fig, ax = plt.subplots(figsize=(8, 6))

    ax.loglog(normalized_z, cuboid_rel_err_array * 100, "r-", linewidth=2, label="Cuboid (Array Vector)")
    ax.loglog(normalized_z, cylinder_rel_err_array * 100, "b-", linewidth=2, label="Cylinder (Array Vector)")

    # Reference 1 / (z/L)^2 line
    ref_x = np.linspace(2, 50, 50)
    ref_y = 5.0 * (2.0 / ref_x) ** 2
    ax.loglog(ref_x, ref_y, "k:", label=r"$\propto (z/L)^{-2}$ Multipole Decay")

    ax.axhline(5.0, color="orange", linestyle="--", label="5% Threshold (Dipole Inadequate)")
    ax.axhline(1.0, color="green", linestyle="--", label="1% Threshold (Approximation Regime)")
    ax.axvline(1.0, color="gray", linestyle=":", label="z = L (Near-field Boundary)")

    ax.set_xlabel("Normalized Distance (z / L_mag)", fontsize=11)
    ax.set_ylabel("Relative Error vs Dipole (%)", fontsize=11)
    ax.set_title("Dipole Approximation Error Scaling (L_mag = 10 mm)", fontsize=12, pad=10)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="upper right")

    plt.tight_layout()
    fig.savefig(f"{output_dir}/error_scaling_vs_normalized_distance.png", dpi=300)
    plt.close(fig)

    # Plot 3: Orientation Sensitivity
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = {0: "tab:blue", 45: "tab:purple", 90: "tab:red"}

    for angle in angles:
        ax.loglog(
            normalized_z,
            orientation_results[angle]["cuboid"] * 100,
            color=colors[angle],
            linestyle="-",
            linewidth=1.8,
            label=f"Cuboid θ = {angle}°",
        )
        ax.loglog(
            normalized_z,
            orientation_results[angle]["cylinder"] * 100,
            color=colors[angle],
            linestyle="--",
            linewidth=1.8,
            label=f"Cylinder θ = {angle}°",
        )

    ax.axhline(1.0, color="green", linestyle=":", label="1% Error Level")
    ax.set_xlabel("Normalized Distance (z / L_mag)", fontsize=11)
    ax.set_ylabel("Array Vector Relative Error (%)", fontsize=11)
    ax.set_title("Orientation Sensitivity: Dipole Approximation Error", fontsize=12, pad=10)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="upper right")

    plt.tight_layout()
    fig.savefig(f"{output_dir}/orientation_sensitivity.png", dpi=300)
    plt.close(fig)

    # ------------------------------------------------------------
    # Quantitative Summary Table
    # ------------------------------------------------------------
    check_z_indices = [0, 6, 13, 20, 29, 39, 49, 59]
    print("\n" + "=" * 92)
    print("QUANTITATIVE COMPARISON: POINT DIPOLE vs FINITE MAGNETS (L = 10 mm, m = 1.0 A*m^2)")
    print("=" * 92)
    header = (
        f"{'z (m)':>8} | {'z / L':>6} | {'Dipole Bz':>11} | {'Cuboid Bz':>11} | "
        f"{'Cyl Bz':>11} | {'Cub Err(%)':>11} | {'Cyl Err(%)':>11} | {'Array Err(%)':>12}"
    )
    print(header)
    print("-" * 92)

    for idx in check_z_indices:
        z = distances[idx]
        z_norm = z / L_mag
        b_dip = dipole_center_bz[idx]
        b_cub = cuboid_center_bz[idx]
        b_cyl = cylinder_center_bz[idx]
        e_cub = cuboid_rel_err_center[idx] * 100
        e_cyl = cylinder_rel_err_center[idx] * 100
        e_arr = cuboid_rel_err_array[idx] * 100

        print(
            f"{z:8.4f} | {z_norm:6.1f} | {b_dip:11.4e} | {b_cub:11.4e} | "
            f"{b_cyl:11.4e} | {e_cub:10.4f}% | {e_cyl:10.4f}% | {e_arr:11.4f}%"
        )
    print("=" * 92)

    # Calculate threshold distances where error crosses 5% and 1%
    cub_5pct = distances[cuboid_rel_err_array >= 0.05]
    cub_1pct = distances[cuboid_rel_err_array >= 0.01]
    cyl_5pct = distances[cylinder_rel_err_array >= 0.05]
    cyl_1pct = distances[cylinder_rel_err_array >= 0.01]

    z_thresh_cub_5 = cub_5pct[-1] if len(cub_5pct) > 0 else distances[0]
    z_thresh_cub_1 = cub_1pct[-1] if len(cub_1pct) > 0 else distances[0]
    z_thresh_cyl_5 = cyl_5pct[-1] if len(cyl_5pct) > 0 else distances[0]
    z_thresh_cyl_1 = cyl_1pct[-1] if len(cyl_1pct) > 0 else distances[0]

    print("\nDIPOLE APPROXIMATION BREAKDOWN THRESHOLDS:")
    print(f"  Cuboid   5% error boundary: z = {z_thresh_cub_5*1000:5.1f} mm ({z_thresh_cub_5/L_mag:4.1f} * L_mag)")
    print(f"  Cuboid   1% error boundary: z = {z_thresh_cub_1*1000:5.1f} mm ({z_thresh_cub_1/L_mag:4.1f} * L_mag)")
    print(f"  Cylinder 5% error boundary: z = {z_thresh_cyl_5*1000:5.1f} mm ({z_thresh_cyl_5/L_mag:4.1f} * L_mag)")
    print(f"  Cylinder 1% error boundary: z = {z_thresh_cyl_1*1000:5.1f} mm ({z_thresh_cyl_1/L_mag:4.1f} * L_mag)")
    print(f"Figures saved to: {output_dir}/\n")


if __name__ == "__main__":
    run_finite_source_comparison()
