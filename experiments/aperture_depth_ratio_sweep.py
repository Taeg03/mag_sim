import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


# ============================================================
# Configuration
# ============================================================

MOMENT = np.array([0.0, 0.0, 1.0])   # A*m^2

# This is an assumed measurement uncertainty, not a measured
# hardware noise figure.
SIGMA_B = 1e-9                         # 1 nT

DETECTION_THRESHOLD = 1e-8             # 10 nT

# Dimensionless aperture/depth ratios to test.
L_OVER_Z = np.array([
    0.10, 0.15, 0.20, 0.30, 0.40,
    0.50, 0.75, 1.00, 1.25, 1.50,
    2.00, 2.50, 3.00, 3.50, 4.00,
    5.00, 6.00, 8.00, 10.0
])

# Physical source depths.
DEPTHS = [0.10, 0.20, 0.50, 1.00]

# Search laterally in normalized coordinates:
# x/z and y/z from -2 to +2.
# This keeps the geometry comparable across depths.
LATERAL_LIMIT = 2.0
N_X = 41
N_Y = 41

DELTA = 1e-5


# ============================================================
# Helpers
# ============================================================

def get_bz(sensor_positions, source_position, moment):
    B = dipole_field(
        sensor_positions,
        source_position,
        moment
    )
    return B[:, 2]


def position_jacobian(sensor_positions, source_position, moment):
    J = np.zeros((len(sensor_positions), 3))

    for i in range(3):
        offset = np.zeros(3)
        offset[i] = DELTA

        B_plus = get_bz(
            sensor_positions,
            source_position + offset,
            moment
        )

        B_minus = get_bz(
            sensor_positions,
            source_position - offset,
            moment
        )

        J[:, i] = (B_plus - B_minus) / (2 * DELTA)

    return J


def localization_std(sensor_positions, source_position):
    J = position_jacobian(
        sensor_positions,
        source_position,
        MOMENT
    )

    F = J.T @ J

    try:
        covariance = SIGMA_B**2 * np.linalg.inv(F)
    except np.linalg.LinAlgError:
        return np.full(3, np.inf)

    return np.sqrt(
        np.maximum(np.diag(covariance), 0.0)
    )


# ============================================================
# Main experiment
# ============================================================

def main():

    # Normalized lateral coordinates.
    ux = np.linspace(
        -LATERAL_LIMIT,
        LATERAL_LIMIT,
        N_X
    )

    uy = np.linspace(
        -LATERAL_LIMIT,
        LATERAL_LIMIT,
        N_Y
    )

    print("Aperture-to-depth localization sweep")
    print("=" * 72)
    print(f"Moment: {np.linalg.norm(MOMENT):.3g} A*m^2")
    print(f"Assumed measurement uncertainty: {SIGMA_B * 1e9:.1f} nT")
    print(f"Detection threshold: {DETECTION_THRESHOLD * 1e9:.1f} nT")
    print(
        f"Lateral search: x/z, y/z = "
        f"[-{LATERAL_LIMIT}, {LATERAL_LIMIT}]"
    )
    print()

    # Store aggregate results.
    summary = {}

    for z in DEPTHS:

        print()
        print(f"DEPTH z = {z:.2f} m")
        print("-" * 100)
        print(
            "L/z    L(m)   Detectable   Median(cm)   "
            "90%(cm)   Min(cm)   Max(cm)   <5cm   <10cm"
        )

        depth_results = []

        for ratio in L_OVER_Z:

            aperture = ratio * z
            spacing = aperture / 2.0

            sensors = create_planar_array(
                3,
                3,
                spacing
            )

            values = []
            detectable_count = 0
            total_count = len(ux) * len(uy)

            for x_norm in ux:
                for y_norm in uy:

                    source_position = np.array([
                        x_norm * z,
                        y_norm * z,
                        z
                    ])

                    bz = get_bz(
                        sensors,
                        source_position,
                        MOMENT
                    )

                    if np.max(np.abs(bz)) < DETECTION_THRESHOLD:
                        continue

                    detectable_count += 1

                    std = localization_std(
                        sensors,
                        source_position
                    )

                    if np.all(np.isfinite(std)):
                        sigma_pos = np.linalg.norm(std)
                        values.append(sigma_pos)

            if len(values) == 0:

                result = {
                    "ratio": ratio,
                    "aperture": aperture,
                    "detectable": 0.0,
                    "median": np.inf,
                    "p90": np.inf,
                    "min": np.inf,
                    "max": np.inf,
                    "frac5": 0.0,
                    "frac10": 0.0,
                }

            else:

                values = np.asarray(values)

                result = {
                    "ratio": ratio,
                    "aperture": aperture,
                    "detectable": detectable_count / total_count,
                    "median": np.median(values),
                    "p90": np.percentile(values, 90),
                    "min": np.min(values),
                    "max": np.max(values),
                    "frac5": np.mean(values <= 0.05),
                    "frac10": np.mean(values <= 0.10),
                }

            depth_results.append(result)

            print(
                f"{ratio:4.2f}  "
                f"{aperture:6.3f}   "
                f"{result['detectable']:10.3f}   "
                f"{result['median'] * 100:10.3f}   "
                f"{result['p90'] * 100:8.3f}   "
                f"{result['min'] * 100:7.3f}   "
                f"{result['max'] * 100:7.3f}   "
                f"{result['frac5']:5.3f}   "
                f"{result['frac10']:6.3f}"
            )

        summary[z] = depth_results

    # ========================================================
    # Plot median localization uncertainty vs L/z
    # ========================================================

    plt.figure(figsize=(8, 5))

    for z in DEPTHS:

        results = summary[z]

        ratios = np.array([
            r["ratio"] for r in results
        ])

        medians = np.array([
            r["median"] for r in results
        ])

        plt.loglog(
            ratios,
            medians * 100,
            marker="o",
            label=f"z = {z:.2f} m"
        )

    plt.xlabel("Aperture / source depth (L/z)")
    plt.ylabel("Median 1σ position uncertainty (cm)")
    plt.title("Localization sensitivity vs aperture-to-depth ratio")
    plt.grid(True, which="both")
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        "aperture_depth_median_uncertainty.png",
        dpi=200
    )
    plt.show()

    # ========================================================
    # Plot 90th percentile
    # ========================================================

    plt.figure(figsize=(8, 5))

    for z in DEPTHS:

        results = summary[z]

        ratios = np.array([
            r["ratio"] for r in results
        ])

        p90 = np.array([
            r["p90"] for r in results
        ])

        plt.loglog(
            ratios,
            p90 * 100,
            marker="o",
            label=f"z = {z:.2f} m"
        )

    plt.xlabel("Aperture / source depth (L/z)")
    plt.ylabel("90th percentile 1σ position uncertainty (cm)")
    plt.title("Worst-region localization sensitivity vs L/z")
    plt.grid(True, which="both")
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        "aperture_depth_p90_uncertainty.png",
        dpi=200
    )
    plt.show()

    # ========================================================
    # Scale-invariance comparison
    # ========================================================

    print()
    print("Scale-invariance check")
    print("-" * 72)

    reference = summary[DEPTHS[0]]

    for z in DEPTHS[1:]:

        current = summary[z]

        median_diffs = []
        p90_diffs = []

        for ref, cur in zip(reference, current):

            if np.isfinite(ref["median"]) and np.isfinite(cur["median"]):
                median_diffs.append(
                    abs(
                        ref["median"] / DEPTHS[0]
                        - cur["median"] / z
                    )
                )

            if np.isfinite(ref["p90"]) and np.isfinite(cur["p90"]):
                p90_diffs.append(
                    abs(
                        ref["p90"] / DEPTHS[0]
                        - cur["p90"] / z
                    )
                )

        print(
            f"z={z:.2f} m: "
            f"max normalized median difference = "
            f"{max(median_diffs):.3e}, "
            f"max normalized p90 difference = "
            f"{max(p90_diffs):.3e}"
        )


if __name__ == "__main__":
    main()
