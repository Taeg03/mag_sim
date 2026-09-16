import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


# --------------------------------------------------
# Configuration
# --------------------------------------------------

sensor_spacing = 0.10  # meters
sensor_positions = create_planar_array(
    rows=3,
    cols=3,
    spacing=sensor_spacing
)

moment = np.array([
    0.0,
    0.0,
    1.0
])

# Source position range
x_values = np.linspace(-0.5, 0.5, 51)
y_values = np.linspace(-0.5, 0.5, 51)

# Depth slices
z_values = [
    0.10,
    0.20,
    0.50,
    1.00
]


# --------------------------------------------------
# Measurement function
# --------------------------------------------------

def measurements(position, moment):

    B = dipole_field(
        sensor_positions,
        position,
        moment
    )

    return B[:, 2]


# --------------------------------------------------
# Numerical Jacobian
# --------------------------------------------------

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


# --------------------------------------------------
# Calculate observability map
# --------------------------------------------------

for z in z_values:

    condition_map = np.full(
        (len(y_values), len(x_values)),
        np.nan
    )

    smallest_sv_map = np.full(
        (len(y_values), len(x_values)),
        np.nan
    )

    rank_map = np.zeros(
        (len(y_values), len(x_values))
    )

    for iy, y in enumerate(y_values):

        for ix, x in enumerate(x_values):

            position = np.array([
                x,
                y,
                z
            ])

            J = numerical_jacobian(
                position,
                moment
            )

            # Normalize parameter columns
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

            rank = np.linalg.matrix_rank(J)

            rank_map[iy, ix] = rank

            if rank == 6:

                condition_map[iy, ix] = (
                    singular_values[0]
                    / singular_values[-1]
                )

                smallest_sv_map[iy, ix] = (
                    singular_values[-1]
                )


    # --------------------------------------------------
    # Condition number map
    # --------------------------------------------------

    plt.figure(figsize=(8, 6))

    image = plt.imshow(
        np.log10(condition_map),
        extent=[
            x_values[0],
            x_values[-1],
            y_values[0],
            y_values[-1]
        ],
        origin="lower",
        aspect="equal"
    )

    plt.xlabel("Source x position (m)")
    plt.ylabel("Source y position (m)")

    plt.title(
        f"Normalized Jacobian Conditioning at z = {z:.2f} m"
    )

    plt.colorbar(
        image,
        label=r"$\log_{10}(\kappa)$"
    )

    plt.tight_layout()

    plt.savefig(
        f"observability_condition_z{z:.2f}.png",
        dpi=300
    )

    plt.show()


    # --------------------------------------------------
    # Smallest singular value map
    # --------------------------------------------------

    plt.figure(figsize=(8, 6))

    image = plt.imshow(
        np.log10(smallest_sv_map),
        extent=[
            x_values[0],
            x_values[-1],
            y_values[0],
            y_values[-1]
        ],
        origin="lower",
        aspect="equal"
    )

    plt.xlabel("Source x position (m)")
    plt.ylabel("Source y position (m)")

    plt.title(
        f"Weakest Observable Direction at z = {z:.2f} m"
    )

    plt.colorbar(
        image,
        label=r"$\log_{10}(\sigma_\mathrm{min})$"
    )

    plt.tight_layout()

    plt.savefig(
        f"observability_smallest_sv_z{z:.2f}.png",
        dpi=300
    )

    plt.show()


    # --------------------------------------------------
    # Rank map
    # --------------------------------------------------

    plt.figure(figsize=(8, 6))

    image = plt.imshow(
        rank_map,
        extent=[
            x_values[0],
            x_values[-1],
            y_values[0],
            y_values[-1]
        ],
        origin="lower",
        aspect="equal"
    )

    plt.xlabel("Source x position (m)")
    plt.ylabel("Source y position (m)")

    plt.title(
        f"Jacobian Rank at z = {z:.2f} m"
    )

    plt.colorbar(
        image,
        label="Rank"
    )

    plt.tight_layout()

    plt.savefig(
        f"observability_rank_z{z:.2f}.png",
        dpi=300
    )

    plt.show()