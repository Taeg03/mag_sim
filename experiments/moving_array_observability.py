import os
import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import transform_sensors


# ============================================================
# Configuration
# ============================================================

# 3x3 planar array, 10 cm sensor spacing
spacing = 0.10

sensor_local = np.array([
    [x, y, 0.0]
    for y in [-spacing, 0.0, spacing]
    for x in [-spacing, 0.0, spacing]
])

# Stationary dipole
source_position = np.array([0.0, 0.0, 0.50])
moment = np.array([0.0, 0.0, 1.0])

# Nominal array position
array_position = np.array([0.0, 0.0, 0.0])


# ============================================================
# Numerical Jacobian
# ============================================================

def measurements(sensor_positions):
    """Return Bz measurements for all sensors."""

    B = dipole_field(
        sensor_positions,
        source_position,
        moment
    )

    return B[:, 2]


def numerical_jacobian(sensor_positions, eps=1e-5):
    """
    Numerical Jacobian of Bz measurements with respect to:

        [source_x, source_y, source_z,
         moment_x, moment_y, moment_z]
    """

    theta = np.concatenate([
        source_position,
        moment
    ])

    J = np.zeros((len(sensor_positions), 6))

    for i in range(6):

        theta_plus = theta.copy()
        theta_minus = theta.copy()

        theta_plus[i] += eps
        theta_minus[i] -= eps

        pos_plus = theta_plus[:3]
        mom_plus = theta_plus[3:]

        pos_minus = theta_minus[:3]
        mom_minus = theta_minus[3:]

        B_plus = dipole_field(
            sensor_positions,
            pos_plus,
            mom_plus
        )[:, 2]

        B_minus = dipole_field(
            sensor_positions,
            pos_minus,
            mom_minus
        )[:, 2]

        J[:, i] = (B_plus - B_minus) / (2 * eps)

    return J


# ============================================================
# Array trajectories
# ============================================================

def static_trajectory():
    return [
        array_position.copy()
    ]


def z_translation():
    """
    Move the array along z.

    Total number of poses: 21
    Range: -0.10 m to +0.10 m
    """

    offsets = np.linspace(-0.10, 0.10, 21)

    return [
        array_position + np.array([0.0, 0.0, dz])
        for dz in offsets
    ]


def x_translation():
    """
    Move the array along x.

    Total number of poses: 21
    Range: -0.10 m to +0.10 m
    """

    offsets = np.linspace(-0.10, 0.10, 21)

    return [
        array_position + np.array([dx, 0.0, 0.0])
        for dx in offsets
    ]


# ============================================================
# Build stacked Jacobian
# ============================================================

def stacked_jacobian(trajectory):

    jacobians = []

    for position in trajectory:

        sensors_world = transform_sensors(
            sensor_local,
            position=position
        )

        J = numerical_jacobian(sensors_world)

        jacobians.append(J)

    return np.vstack(jacobians)


# ============================================================
# Analyze
# ============================================================

def analyze(name, trajectory):

    J = stacked_jacobian(trajectory)

    singular_values = np.linalg.svd(
        J,
        compute_uv=False
    )

    condition_number = (
        singular_values[0] / singular_values[-1]
    )

    rank = np.linalg.matrix_rank(J)

    print()
    print("=" * 60)
    print(name)
    print("=" * 60)
    print(f"Number of poses:       {len(trajectory)}")
    print(f"Number of measurements: {J.shape[0]}")
    print(f"Jacobian shape:        {J.shape}")
    print(f"Rank:                  {rank}")
    print(f"Condition number:      {condition_number:.6e}")
    print()
    print("Singular values:")
    for i, s in enumerate(singular_values):
        print(f"  σ{i + 1}: {s:.6e}")

    return singular_values, condition_number


# ============================================================
# Run experiments
# ============================================================

results = {}

results["Static"] = analyze(
    "STATIC ARRAY",
    static_trajectory()
)

results["Z translation"] = analyze(
    "Z TRANSLATION",
    z_translation()
)

results["X translation"] = analyze(
    "X TRANSLATION",
    x_translation()
)


# ============================================================
# Plot singular values
# ============================================================

figure_dir = "figures/moving_array_observability"
os.makedirs(figure_dir, exist_ok=True)

labels = list(results.keys())
singular_values = np.array([
    results[label][0]
    for label in labels
])

x = np.arange(6)
width = 0.25

plt.figure(figsize=(9, 5))

for i, label in enumerate(labels):
    plt.semilogy(
        x,
        singular_values[i],
        marker="o",
        label=label
    )

plt.xticks(
    x,
    ["x", "y", "z", "mx", "my", "mz"]
)

plt.xlabel("Parameter")
plt.ylabel("Singular value")
plt.title("Six-Parameter Observability")
plt.grid(True, which="both", alpha=0.3)
plt.legend()
plt.tight_layout()

plt.savefig(
    f"{figure_dir}/singular_values.png",
    dpi=200
)

plt.close()


# ============================================================
# Condition number comparison
# ============================================================

condition_numbers = [
    results[label][1]
    for label in labels
]

plt.figure(figsize=(8, 5))

plt.bar(
    labels,
    condition_numbers
)

plt.yscale("log")

plt.ylabel("Condition number")
plt.title("Jacobian Conditioning")
plt.grid(True, axis="y", which="both", alpha=0.3)
plt.tight_layout()

plt.savefig(
    f"{figure_dir}/condition_numbers.png",
    dpi=200
)

plt.close()


print()
print(f"Figures saved to: {figure_dir}/")