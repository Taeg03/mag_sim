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

# Dimensionless aperture-to-depth ratios
aperture_ratios = [
    0.1,
    0.2,
    0.5,
    1.0,
    2.0,
    5.0
]

# Physical source depths
z_values = [
    0.10,
    0.20,
    0.50,
    1.00
]

# Lateral sweep expressed relative to source depth.
# This keeps the search region geometrically comparable
# across different depths.
normalized_xy = np.linspace(-2.0, 2.0, 41)


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

    # Use relative perturbations
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
# Main sweep
# --------------------------------------------------

best_condition = np.zeros(
    (len(z_values), len(aperture_ratios))
)

best_smallest_sv = np.zeros_like(
    best_condition
)

best_x = np.zeros_like(
    best_condition
)

best_y = np.zeros_like(
    best_condition
)


for iz, z in enumerate(z_values):

    print()
    print(f"========== z = {z:.2f} m ==========")

    for ia, ratio in enumerate(aperture_ratios):

        # L = ratio * z
        aperture = ratio * z

        # For a 3x3 array:
        #
        # L = 2 * spacing
        #
        spacing = aperture / 2

        sensor_positions = create_planar_array(
            rows=3,
            cols=3,
            spacing=spacing
        )

        minimum_condition = np.inf
        minimum_sv = np.nan
        minimum_position = None

        # Sweep lateral position relative to depth
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

                # Normalize position parameters by z
                # and moment parameters by |m|.
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

                if condition_number < minimum_condition:

                    minimum_condition = condition_number

                    minimum_sv = singular_values[-1]

                    minimum_position = (
                        position.copy()
                    )

        best_condition[iz, ia] = (
            minimum_condition
        )

        best_smallest_sv[iz, ia] = (
            minimum_sv
        )

        best_x[iz, ia] = (
            minimum_position[0]
            / z
        )

        best_y[iz, ia] = (
            minimum_position[1]
            / z
        )

        print(
            f"L/z = {ratio:.1f}"
            f" | spacing = {spacing:.4f} m"
            f" | best κ = {minimum_condition:.3f}"
            f" | best x/z = {best_x[iz, ia]:.2f}"
            f" | best y/z = {best_y[iz, ia]:.2f}"
        )


# --------------------------------------------------
# Print comparison table
# --------------------------------------------------

print()
print("==============================================")
print("Best conditioning versus L/z")
print("==============================================")

for ia, ratio in enumerate(aperture_ratios):

    print()
    print(f"L/z = {ratio:.1f}")

    for iz, z in enumerate(z_values):

        print(
            f"  z = {z:.2f} m:"
            f"  κ = {best_condition[iz, ia]:.3f}"
        )


# --------------------------------------------------
# Plot best condition number
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
    "Best Observability vs Normalized Array Aperture"
)

plt.legend()

plt.grid(
    True,
    which="both",
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    "scaled_best_condition.png",
    dpi=300
)

plt.show()


# --------------------------------------------------
# Plot best smallest singular value
# --------------------------------------------------

plt.figure(figsize=(8, 6))

for iz, z in enumerate(z_values):

    plt.plot(
        aperture_ratios,
        best_smallest_sv[iz],
        marker="o",
        label=f"z = {z:.2f} m"
    )

plt.xscale("log")
plt.yscale("log")

plt.xlabel("Aperture-to-depth ratio L/z")
plt.ylabel("Best smallest singular value")

plt.title(
    "Best Weakest-Direction Observability vs L/z"
)

plt.legend()

plt.grid(
    True,
    which="both",
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    "scaled_best_smallest_sv.png",
    dpi=300
)

plt.show()