import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


# --------------------------------------------------
# Configuration
# --------------------------------------------------

source_distance = 0.20  # meters

source_position = np.array([
    0.0,
    0.0,
    source_distance
])

moment = np.array([
    0.0,
    0.0,
    1.0
])

spacings = np.logspace(
    np.log10(0.005),
    np.log10(1.0),
    100
)


# --------------------------------------------------
# Measurement function
# --------------------------------------------------

def measurements(sensor_positions, position, moment):

    B = dipole_field(
        sensor_positions,
        position,
        moment
    )

    return B[:, 2]


# --------------------------------------------------
# Numerical Jacobian
# --------------------------------------------------

def numerical_jacobian(sensor_positions, position, moment):

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

aperture_ratio = []

condition_numbers = []

smallest_singular_values = []

largest_singular_values = []

ranks = []


# --------------------------------------------------
# Sweep aperture
# --------------------------------------------------

for spacing in spacings:

    sensor_positions = create_planar_array(
        rows=3,
        cols=3,
        spacing=spacing
    )

    J = numerical_jacobian(
        sensor_positions,
        source_position,
        moment
    )

    # Normalize each parameter by characteristic scale
    parameter_scales = np.array([
        source_distance,
        source_distance,
        source_distance,
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

    L = 2 * spacing

    aperture_ratio.append(
        L / source_distance
    )

    condition_numbers.append(
        condition_number
    )

    smallest_singular_values.append(
        singular_values[-1]
    )

    largest_singular_values.append(
        singular_values[0]
    )

    ranks.append(
        np.linalg.matrix_rank(J)
    )


# --------------------------------------------------
# Convert to arrays
# --------------------------------------------------

aperture_ratio = np.array(
    aperture_ratio
)

condition_numbers = np.array(
    condition_numbers
)

smallest_singular_values = np.array(
    smallest_singular_values
)

largest_singular_values = np.array(
    largest_singular_values
)

ranks = np.array(
    ranks
)


# --------------------------------------------------
# Plot condition number
# --------------------------------------------------

plt.figure(figsize=(9, 6))

plt.loglog(
    aperture_ratio,
    condition_numbers
)

plt.xlabel(r"Array aperture / source distance ($L/z$)")
plt.ylabel("Normalized condition number")

plt.title(
    "Jacobian Conditioning vs Array Aperture"
)

plt.grid(True, which="both")

plt.tight_layout()

plt.savefig(
    "aperture_condition_number.png",
    dpi=300
)

plt.show()


# --------------------------------------------------
# Plot smallest singular value
# --------------------------------------------------

plt.figure(figsize=(9, 6))

plt.loglog(
    aperture_ratio,
    smallest_singular_values
)

plt.xlabel(r"Array aperture / source distance ($L/z$)")
plt.ylabel("Smallest normalized singular value")

plt.title(
    "Weakest Observable Direction vs Array Aperture"
)

plt.grid(True, which="both")

plt.tight_layout()

plt.savefig(
    "aperture_smallest_singular_value.png",
    dpi=300
)

plt.show()


# --------------------------------------------------
# Print representative results
# --------------------------------------------------

print("\nAperture observability:")

for spacing_target in [
    0.01,
    0.02,
    0.05,
    0.10,
    0.20,
    0.50,
    1.00
]:

    index = np.argmin(
        np.abs(spacings - spacing_target)
    )

    print(
        f"\nSpacing: "
        f"{spacings[index]:.4f} m"
    )

    print(
        f"  Aperture L/z: "
        f"{aperture_ratio[index]:.4f}"
    )

    print(
        f"  Condition number: "
        f"{condition_numbers[index]:.6e}"
    )

    print(
        f"  Smallest singular value: "
        f"{smallest_singular_values[index]:.6e}"
    )

    print(
        f"  Rank: "
        f"{ranks[index]}"
    )