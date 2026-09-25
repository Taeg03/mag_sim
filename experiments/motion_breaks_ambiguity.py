import os
import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import transform_sensors


# ============================================================
# Configuration
# ============================================================

spacing = 0.10

sensor_local = np.array([
    [x, y, 0.0]
    for y in [-spacing, 0.0, spacing]
    for x in [-spacing, 0.0, spacing]
])


# ============================================================
# The two fixed source configurations
# ============================================================

source_a_position = np.array([
    0.0, 0.0, 0.50
])

source_a_moment = np.array([
    0.0, 0.0, 1.0
])


source_b_position = np.array([
    0.05, 0.0, 0.50
])

source_b_moment = np.array([
    0.37205381,
    0.0,
    0.97340704
])


# ============================================================
# Array trajectory
# ============================================================

array_x = np.linspace(
    -0.25,
    0.25,
    101
)


# ============================================================
# Calculate measurements
# ============================================================

def get_bz(array_position, source_position, source_moment):

    sensors_world = transform_sensors(
        sensor_local,
        position=array_position
    )

    B = dipole_field(
        sensors_world,
        source_position,
        source_moment
    )

    return B[:, 2]


# ============================================================
# Evaluate ambiguity during motion
# ============================================================

rmse_values = []
max_difference_values = []

all_measurements_a = []
all_measurements_b = []

for x in array_x:

    array_position = np.array([
        x,
        0.0,
        0.0
    ])

    bz_a = get_bz(
        array_position,
        source_a_position,
        source_a_moment
    )

    bz_b = get_bz(
        array_position,
        source_b_position,
        source_b_moment
    )

    difference = bz_a - bz_b

    rmse = np.sqrt(
        np.mean(difference ** 2)
    )

    max_difference = np.max(
        np.abs(difference)
    )

    rmse_values.append(rmse)
    max_difference_values.append(max_difference)

    all_measurements_a.append(bz_a)
    all_measurements_b.append(bz_b)


rmse_values = np.array(rmse_values)
max_difference_values = np.array(max_difference_values)

all_measurements_a = np.array(all_measurements_a)
all_measurements_b = np.array(all_measurements_b)


# ============================================================
# Output directory
# ============================================================

figure_dir = "figures/motion_breaks_ambiguity"
os.makedirs(figure_dir, exist_ok=True)


# ============================================================
# Print results
# ============================================================

initial_index = np.argmin(
    np.abs(array_x - 0.0)
)

maximum_index = np.argmax(
    rmse_values
)

print()
print("=" * 70)
print("MOTION BREAKS STATIC AMBIGUITY")
print("=" * 70)

print()
print("Source A:")
print(f"  Position: {source_a_position}")
print(f"  Moment:   {source_a_moment}")

print()
print("Source B:")
print(f"  Position: {source_b_position}")
print(f"  Moment:   {source_b_moment}")

print()
print("At array x = 0:")
print(
    f"  Measurement RMSE: "
    f"{rmse_values[initial_index] * 1e9:.6f} nT"
)

print()
print("Maximum measurement separation:")
print(
    f"  Array x: {array_x[maximum_index]:.3f} m"
)

print(
    f"  RMSE: "
    f"{rmse_values[maximum_index] * 1e9:.6f} nT"
)

print(
    f"  Maximum sensor difference: "
    f"{max_difference_values[maximum_index] * 1e9:.6f} nT"
)


# ============================================================
# Plot 1: measurement separation
# ============================================================

plt.figure(figsize=(9, 5))

plt.plot(
    array_x,
    rmse_values * 1e9
)

plt.xlabel("Array x position (m)")
plt.ylabel("Bz measurement RMSE (nT)")
plt.title("Separation of Previously Ambiguous Sources")
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig(
    f"{figure_dir}/measurement_separation.png",
    dpi=200
)

plt.close()


# ============================================================
# Plot 2: individual sensor measurements
# ============================================================

plt.figure(figsize=(9, 5))

for sensor_index in range(9):

    plt.plot(
        array_x,
        all_measurements_a[:, sensor_index] * 1e9,
        alpha=0.35
    )

    plt.plot(
        array_x,
        all_measurements_b[:, sensor_index] * 1e9,
        "--",
        alpha=0.35
    )

plt.xlabel("Array x position (m)")
plt.ylabel("Bz (nT)")
plt.title("Sensor Measurements During Array Translation")
plt.grid(True, alpha=0.3)

from matplotlib.lines import Line2D
custom_lines = [
    Line2D([0], [0], color="black", linestyle="-", label="Source A (centered vertical)"),
    Line2D([0], [0], color="black", linestyle="--", label="Source B (off-center tilted)")
]
plt.legend(handles=custom_lines, loc="upper right")

plt.tight_layout()

plt.savefig(
    f"{figure_dir}/sensor_measurements.png",
    dpi=200
)

plt.close()


print()
print(f"Figures saved to: {figure_dir}/")