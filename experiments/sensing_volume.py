import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


# ==================================================
# Configuration
# ==================================================

# Fixed physical 3x3 array
sensor_spacing = 0.10  # m
sensor_positions = create_planar_array(
    rows=3,
    cols=3,
    spacing=sensor_spacing
)

# Source moments to investigate
moment_magnitudes = [
    1e-3,
    1e-2,
    1e-1,
    1.0
]

# Fixed +z source orientation
moment_direction = np.array([
    0.0,
    0.0,
    1.0
])

# Detection limit
detection_threshold = 10e-9  # 10 nT

# Observability criterion
condition_threshold = 100.0

# 3D search volume
x_values = np.linspace(-1.0, 1.0, 41)
y_values = np.linspace(-1.0, 1.0, 41)

# Only source positions above the array
z_values = np.linspace(
    0.05,
    2.00,
    40
)


# ==================================================
# Measurement function
# ==================================================

def measurements(position, moment):

    B = dipole_field(
        sensor_positions,
        position,
        moment
    )

    return B[:, 2]


# ==================================================
# Numerical Jacobian
# ==================================================

def numerical_jacobian(position, moment):

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
            theta_plus[:3],
            theta_plus[3:]
        )

        B_minus = measurements(
            theta_minus[:3],
            theta_minus[3:]
        )

        J[:, i] = (
            B_plus - B_minus
        ) / (2 * steps[i])

    return J


# ==================================================
# Storage
# ==================================================

# Results:
#
# 0 = not detectable
# 1 = detectable but poorly conditioned
# 2 = detectable + well conditioned

classification = np.zeros(
    (
        len(moment_magnitudes),
        len(z_values),
        len(y_values),
        len(x_values)
    ),
    dtype=np.uint8
)


# ==================================================
# Main 3D sweep
# ==================================================

for im, moment_magnitude in enumerate(
    moment_magnitudes
):

    moment = (
        moment_magnitude
        * moment_direction
    )

    print()
    print("=" * 65)
    print(
        f"Moment = {moment_magnitude:.3e} A*m^2"
    )
    print("=" * 65)

    for iz, z in enumerate(z_values):

        for iy, y in enumerate(y_values):

            for ix, x in enumerate(x_values):

                position = np.array([
                    x,
                    y,
                    z
                ])

                # ------------------------------------------
                # Detection
                # ------------------------------------------

                Bz = measurements(
                    position,
                    moment
                )

                max_field = np.max(
                    np.abs(Bz)
                )

                detectable = (
                    max_field
                    >= detection_threshold
                )

                if not detectable:
                    classification[
                        im, iz, iy, ix
                    ] = 0

                    continue


                # ------------------------------------------
                # Jacobian
                # ------------------------------------------

                J = numerical_jacobian(
                    position,
                    moment
                )

                # Normalize parameter perturbations
                parameter_scales = np.array([
                    z,
                    z,
                    z,
                    moment_magnitude,
                    moment_magnitude,
                    moment_magnitude
                ])

                J_normalized = (
                    J
                    * parameter_scales[None, :]
                )

                singular_values = np.linalg.svd(
                    J_normalized,
                    compute_uv=False
                )

                condition_number = (
                    singular_values[0]
                    / singular_values[-1]
                )

                # ------------------------------------------
                # Classification
                # ------------------------------------------

                if condition_number <= condition_threshold:

                    classification[
                        im, iz, iy, ix
                    ] = 2

                else:

                    classification[
                        im, iz, iy, ix
                    ] = 1


# ==================================================
# Summary statistics
# ==================================================

print()
print("=" * 70)
print("3D sensing-volume summary")
print("=" * 70)

for im, moment_magnitude in enumerate(
    moment_magnitudes
):

    data = classification[im]

    total = data.size

    detectable = np.sum(
        data >= 1
    )

    usable = np.sum(
        data == 2
    )

    print()
    print(
        f"Moment = {moment_magnitude:.3e} A*m^2"
    )

    print(
        f"  Detectable volume fraction: "
        f"{detectable / total:.4f}"
    )

    print(
        f"  Detectable + observable fraction: "
        f"{usable / total:.4f}"
    )


# ==================================================
# Depth-dependent cross sections
# ==================================================

# Pick representative depths
slice_indices = [
    0,
    len(z_values) // 4,
    len(z_values) // 2,
    3 * len(z_values) // 4
]


for im, moment_magnitude in enumerate(
    moment_magnitudes
):

    for iz in slice_indices:

        z = z_values[iz]

        plt.figure(figsize=(8, 6))

        image = plt.imshow(
            classification[
                im, iz
            ],
            extent=[
                x_values[0],
                x_values[-1],
                y_values[0],
                y_values[-1]
            ],
            origin="lower",
            aspect="equal",
            vmin=0,
            vmax=2
        )

        plt.xlabel(
            "Source x position (m)"
        )

        plt.ylabel(
            "Source y position (m)"
        )

        plt.title(
            f"Sensing classification"
            f"\nm = {moment_magnitude:.1e} A*m²,"
            f" z = {z:.2f} m"
        )

        colorbar = plt.colorbar(
            image
        )

        colorbar.set_ticks([
            0,
            1,
            2
        ])

        colorbar.set_ticklabels([
            "Not detectable",
            "Detectable / poor conditioning",
            "Detectable / well conditioned"
        ])

        plt.tight_layout()

        plt.savefig(
            f"sensing_m{moment_magnitude:.0e}_z{z:.2f}.png",
            dpi=300
        )

        plt.show()


# ==================================================
# Maximum useful depth
# ==================================================

print()
print("=" * 70)
print("Maximum useful depth")
print("=" * 70)

for im, moment_magnitude in enumerate(
    moment_magnitudes
):

    useful_by_depth = np.any(
        classification[im] == 2,
        axis=(1, 2)
    )

    detectable_by_depth = np.any(
        classification[im] >= 1,
        axis=(1, 2)
    )

    useful_indices = np.where(
        useful_by_depth
    )[0]

    detectable_indices = np.where(
        detectable_by_depth
    )[0]

    print()
    print(
        f"Moment = {moment_magnitude:.3e} A*m^2"
    )

    if len(detectable_indices) > 0:

        print(
            f"  Maximum detectable z: "
            f"{z_values[detectable_indices[-1]]:.3f} m"
        )

    else:

        print(
            "  No detectable locations"
        )

    if len(useful_indices) > 0:

        print(
            f"  Maximum well-conditioned z: "
            f"{z_values[useful_indices[-1]]:.3f} m"
        )

    else:

        print(
            "  No well-conditioned locations"
        )