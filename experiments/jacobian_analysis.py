import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


# --------------------------------------------------
# Configuration
# --------------------------------------------------

sensor_spacing = 0.02  # meters
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

sensor_positions = create_planar_array(
    rows=3,
    cols=3,
    spacing=sensor_spacing
)


# --------------------------------------------------
# Measurement function
# --------------------------------------------------

def measurements(position, moment):
    """
    Return Bz measurements from the sensor array.
    """

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
    """
    Numerically calculate the Jacobian of the Bz
    measurements with respect to:

        [x, y, z, mx, my, mz]

    Returns
    -------
    J : ndarray, shape (N, 6)
    """

    theta = np.concatenate([
        position,
        moment
    ])

    J = np.zeros(
        (len(sensor_positions), 6)
    )

    # Perturbation sizes
    position_step = 1e-6      # meters
    moment_step = 1e-6        # A*m^2

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
# Calculate Jacobian
# --------------------------------------------------

J = numerical_jacobian(
    source_position,
    moment
)

print("\nJacobian shape:")
print(J.shape)

print("\nJacobian:")
print(J)


# --------------------------------------------------
# Singular value decomposition
# --------------------------------------------------

U, singular_values, Vt = np.linalg.svd(
    J,
    full_matrices=False
)

print("\nSingular values:")

for i, value in enumerate(singular_values):

    print(
        f"  σ{i + 1}: "
        f"{value:.6e}"
    )


# --------------------------------------------------
# Rank and raw condition number
# --------------------------------------------------

rank = np.linalg.matrix_rank(J)

print(f"\nJacobian rank: {rank}")

if singular_values[-1] > 0:

    condition_number = (
        singular_values[0]
        / singular_values[-1]
    )

    print(
        f"Raw condition number: "
        f"{condition_number:.6e}"
    )


# --------------------------------------------------
# Column sensitivity
# --------------------------------------------------

column_norms = np.linalg.norm(
    J,
    axis=0
)

parameter_names = [
    "x",
    "y",
    "z",
    "mx",
    "my",
    "mz"
]

print("\nJacobian column norms:")

for name, value in zip(
    parameter_names,
    column_norms
):

    print(
        f"  {name:>2}: "
        f"{value:.6e}"
    )


# --------------------------------------------------
# Plot singular values
# --------------------------------------------------

plt.figure(figsize=(8, 5))

plt.semilogy(
    range(1, len(singular_values) + 1),
    singular_values,
    marker="o"
)

plt.xlabel("Singular value index")
plt.ylabel("Singular value")
plt.title(
    "Jacobian Singular Values"
)

plt.grid(True, which="both")

plt.tight_layout()

plt.savefig(
    "jacobian_singular_values.png",
    dpi=300
)

plt.show()

# --------------------------------------------------
# Singular vectors
# --------------------------------------------------

print("\nRight singular vectors:")

for i, vector in enumerate(Vt):

    print(
        f"\nσ{i + 1:.0f} = "
        f"{singular_values[i]:.6e}"
    )

    for name, value in zip(
        parameter_names,
        vector
    ):
        print(
            f"  {name:>2}: "
            f"{value:+.4f}"
        )