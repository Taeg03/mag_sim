import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


# --------------------------------------------------
# Configuration
# --------------------------------------------------

moment = np.array([
    0.0,
    0.0,
    1.0
])

z_values = [
    0.10,
    0.20,
    0.50,
    1.00
]

# Dense sweep around the interesting region
aperture_ratios = np.geomspace(
    0.5,
    5.0,
    25
)

# Lateral source positions, normalized by depth
normalized_xy = np.linspace(
    -2.0,
    2.0,
    41
)

condition_threshold = 100.0


# --------------------------------------------------
# Measurement function
# --------------------------------------------------

def measurements(
    sensor_positions,
    position,
    moment
):

    B = dipole_field(
        sensor_positions,
        position,
        moment
    )

    return B[:, 2]


# --------------------------------------------------
# Numerical Jacobian
# --------------------------------------------------

def numerical_jacobian(
    sensor_positions,
    position,
    moment
):

    theta = np.concatenate([
        position,
        moment
    ])

    J = np.zeros(
        (len(sensor_positions), 6)
    )

    position_step = 1e-6
    moment_step = 1e-6

    steps = np.array([
        position_step,
        position_step,
        position_step,
        moment_step,
        moment_step,
        moment_step
    ])

    for i in range(6):

        theta_plus = theta.copy()
        theta_minus = theta.copy()

        theta_plus[i] += steps[i]
        theta_minus[i] -= steps[i]

        B_plus = measurements(
            sensor_positions,
            theta_plus[:3],
            theta_plus[3:]
        )

        B_minus = measurements(
            sensor_positions,
            theta_minus[:3],
            theta_minus[3:]
        )

        J[:, i] = (
            B_plus - B_minus
        ) / (2 * steps[i])

    return J


# --------------------------------------------------
# Storage
# --------------------------------------------------

best_condition = np.zeros(
    (len(z_values), len(aperture_ratios))
)

median_condition = np.zeros_like(
    best_condition
)

worst_condition = np.zeros_like(
    best_condition
)

good_fraction = np.zeros_like(
    best_condition
)


# --------------------------------------------------
# Main sweep
# --------------------------------------------------

for iz, z in enumerate(z_values):

    print()
    print("=" * 55)
    print(f"z = {z:.2f} m")
    print("=" * 55)

    for ia, ratio in enumerate(aperture_ratios):

        aperture = ratio * z

        spacing = aperture / 2

        sensor_positions = create_planar_array(
            rows=3,
            cols=3,
            spacing=spacing
        )

        condition_values = []

        for nx in normalized_xy:

            for ny in normalized_xy:

                position = np.array([
                    nx * z,
                    ny * z,
                    z
                ])

                J = numerical_jacobian(
                    sensor_positions,
                    position,
                    moment
                )

                # Normalize parameters by characteristic scales
                parameter_scales = np.array([
                    z,
                    z,
                    z,
                    np.linalg.norm(moment),
                    np.linalg.norm(moment),
                    np.linalg.norm(moment)
                ])

                J_normalized = (
                    J * parameter_scales[None, :]
                )

                singular_values = np.linalg.svd(
                    J_normalized,
                    compute_uv=False
                )

                condition_number = (
                    singular_values[0]
                    / singular_values[-1]
                )

                condition_values.append(
                    condition_number
                )

        condition_values = np.asarray(
            condition_values
        )

        best = np.min(condition_values)
        median = np.median(condition_values)
        worst = np.max(condition_values)

        fraction = np.mean(
            condition_values <= condition_threshold
        )

        best_condition[iz, ia] = best
        median_condition[iz, ia] = median
        worst_condition[iz, ia] = worst
        good_fraction[iz, ia] = fraction

        print(
            f"L/z = {ratio:.3f}"
            f" | best = {best:.2f}"
            f" | median = {median:.2f}"
            f" | worst = {worst:.2e}"
            f" | κ<100 = {fraction:.3f}"
        )


# --------------------------------------------------
# Verify scale invariance
# --------------------------------------------------

print()
print("=" * 55)
print("Scale invariance check")
print("=" * 55)

for ia, ratio in enumerate(aperture_ratios):

    values = best_condition[:, ia]

    spread = (
        np.max(values)
        - np.min(values)
    )

    print(
        f"L/z = {ratio:.3f}"
        f" | best κ values = {values}"
        f" | spread = {spread:.3e}"
    )


# --------------------------------------------------
# Plot: best conditioning
# --------------------------------------------------

plt.figure(figsize=(8, 6))

for iz, z in enumerate(z_values):

    plt.plot(
        aperture_ratios,
        best_condition[iz],
        marker="o",
        label=f"z = {z:.2f} m"
    )

plt.xscale("log")
plt.yscale("log")

plt.xlabel("Aperture-to-depth ratio L/z")
plt.ylabel("Best condition number")

plt.title(
    "Best Conditioning vs Normalized Aperture"
)

plt.legend()

plt.grid(
    True,
    which="both",
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    "robustness_best_condition.png",
    dpi=300
)

plt.show()


# --------------------------------------------------
# Plot: median conditioning
# --------------------------------------------------

plt.figure(figsize=(8, 6))

for iz, z in enumerate(z_values):

    plt.plot(
        aperture_ratios,
        median_condition[iz],
        marker="o",
        label=f"z = {z:.2f} m"
    )

plt.xscale("log")
plt.yscale("log")

plt.xlabel("Aperture-to-depth ratio L/z")
plt.ylabel("Median condition number")

plt.title(
    "Median Conditioning vs Normalized Aperture"
)

plt.legend()

plt.grid(
    True,
    which="both",
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    "robustness_median_condition.png",
    dpi=300
)

plt.show()


# --------------------------------------------------
# Plot: fraction with κ < 100
# --------------------------------------------------

plt.figure(figsize=(8, 6))

for iz, z in enumerate(z_values):

    plt.plot(
        aperture_ratios,
        good_fraction[iz],
        marker="o",
        label=f"z = {z:.2f} m"
    )

plt.xscale("log")

plt.xlabel("Aperture-to-depth ratio L/z")
plt.ylabel("Fraction of lateral region with κ < 100")

plt.title(
    "Robustly Conditioned Region vs Normalized Aperture"
)

plt.legend()

plt.grid(
    True,
    which="both",
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    "robustness_good_fraction.png",
    dpi=300
)

plt.show()