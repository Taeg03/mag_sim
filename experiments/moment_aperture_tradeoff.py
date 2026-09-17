import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


# --------------------------------------------------
# Configuration
# --------------------------------------------------

# Source moments to test
moment_magnitudes = np.logspace(
    -3,
    1,
    9
)
# 1e-3 through 10 A*m^2

# Source depths
z_values = [
    0.10,
    0.20,
    0.50,
    1.00
]

# Array aperture relative to source depth
aperture_ratios = np.geomspace(
    0.5,
    5.0,
    15
)

# Lateral source region, normalized by depth
normalized_xy = np.linspace(
    -2.0,
    2.0,
    41
)

# Hardware detection limit
detection_threshold = 10e-9  # 10 nT

# Observability threshold
# This is still a visualization criterion, not a
# physical requirement.
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
#
# Dimensions:
#   depth × moment × aperture
# --------------------------------------------------

detectable_fraction = np.zeros(
    (
        len(z_values),
        len(moment_magnitudes),
        len(aperture_ratios)
    )
)

observable_fraction = np.zeros_like(
    detectable_fraction
)


# --------------------------------------------------
# Main sweep
# --------------------------------------------------

for iz, z in enumerate(z_values):

    print()
    print("=" * 65)
    print(f"z = {z:.2f} m")
    print("=" * 65)

    for im, moment_magnitude in enumerate(
        moment_magnitudes
    ):

        moment = np.array([
            0.0,
            0.0,
            moment_magnitude
        ])

        for ia, ratio in enumerate(
            aperture_ratios
        ):

            aperture = ratio * z

            spacing = aperture / 2

            sensor_positions = create_planar_array(
                rows=3,
                cols=3,
                spacing=spacing
            )

            detectable_count = 0
            observable_count = 0
            total_count = 0

            for nx in normalized_xy:

                for ny in normalized_xy:

                    position = np.array([
                        nx * z,
                        ny * z,
                        z
                    ])

                    # ----------------------------------
                    # Detectability
                    # ----------------------------------

                    Bz = measurements(
                        sensor_positions,
                        position,
                        moment
                    )

                    max_field = np.max(
                        np.abs(Bz)
                    )

                    detectable = (
                        max_field >=
                        detection_threshold
                    )

                    if detectable:
                        detectable_count += 1


                    # ----------------------------------
                    # Observability
                    # ----------------------------------

                    J = numerical_jacobian(
                        sensor_positions,
                        position,
                        moment
                    )

                    parameter_scales = np.array([
                        z,
                        z,
                        z,
                        moment_magnitude,
                        moment_magnitude,
                        moment_magnitude
                    ])

                    J_normalized = (
                        J *
                        parameter_scales[None, :]
                    )

                    singular_values = np.linalg.svd(
                        J_normalized,
                        compute_uv=False
                    )

                    condition_number = (
                        singular_values[0]
                        / singular_values[-1]
                    )

                    observable = (
                        condition_number
                        <= condition_threshold
                    )

                    if detectable and observable:
                        observable_count += 1

                    total_count += 1


            detectable_fraction[
                iz, im, ia
            ] = (
                detectable_count
                / total_count
            )

            observable_fraction[
                iz, im, ia
            ] = (
                observable_count
                / total_count
            )

            print(
                f"m={moment_magnitude:.3e}"
                f" | L/z={ratio:.3f}"
                f" | detectable={detectable_fraction[iz, im, ia]:.3f}"
                f" | both={observable_fraction[iz, im, ia]:.3f}"
            )


# --------------------------------------------------
# Summary: best aperture for each moment/depth
# --------------------------------------------------

print()
print("=" * 70)
print("Best combined detectable + observable fraction")
print("=" * 70)

for iz, z in enumerate(z_values):

    print()
    print(f"z = {z:.2f} m")

    for im, moment_magnitude in enumerate(
        moment_magnitudes
    ):

        values = observable_fraction[
            iz, im, :
        ]

        best_index = np.argmax(values)

        print(
            f"  m={moment_magnitude:.3e}"
            f" | best L/z={aperture_ratios[best_index]:.3f}"
            f" | fraction={values[best_index]:.3f}"
        )


# --------------------------------------------------
# Plot combined usable fraction
#
# One plot per depth
# --------------------------------------------------

for iz, z in enumerate(z_values):

    plt.figure(figsize=(8, 6))

    for im, moment_magnitude in enumerate(
        moment_magnitudes
    ):

        plt.plot(
            aperture_ratios,
            observable_fraction[iz, im],
            marker="o",
            label=f"m = {moment_magnitude:.0e}"
        )

    plt.xscale("log")

    plt.xlabel("Aperture-to-depth ratio L/z")
    plt.ylabel(
        "Fraction detectable + κ < 100"
    )

    plt.title(
        f"Combined Detection + Observability at z = {z:.2f} m"
    )

    plt.legend()

    plt.grid(
        True,
        which="both",
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        f"moment_tradeoff_z{z:.2f}.png",
        dpi=300
    )

    plt.show()