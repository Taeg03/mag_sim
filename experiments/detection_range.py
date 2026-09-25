import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


# Parameters
moment = np.array([0, 0, 1])
detection_limit = 1e-8

sensor_positions = create_planar_array(
    rows=3,
    cols=3,
    spacing=0.02
)

distances = np.linspace(0.1, 40, 1000)

center_bz = []


for distance in distances:

    source_position = np.array([0, 0, distance])

    B = dipole_field(
        sensor_positions,
        source_position,
        moment
    )

    center_bz.append(abs(B[4, 2]))


center_bz = np.array(center_bz)


# Find where field crosses detection limit
above_limit = center_bz >= detection_limit

if np.any(above_limit):
    max_detectable_distance = distances[above_limit][-1]
    print(f"Maximum detectable distance: {max_detectable_distance:.2f} m")
else:
    print("Source never exceeds detection limit.")


# Plot
plt.figure()

plt.loglog(distances, center_bz, label=r"$|B_z|$ at Center Sensor")
plt.axhline(detection_limit, linestyle="--", color="gray", label=f"Detection Limit ({detection_limit * 1e9:.0f} nT)")

if np.any(above_limit):
    plt.plot(
        max_detectable_distance,
        detection_limit,
        marker="o",
        color="red",
        markersize=6,
        label=f"Max Range: {max_detectable_distance:.2f} m"
    )

plt.xlabel("Source distance (m)")
plt.ylabel("|Bz| (T)")
plt.title("Dipole Detection Range")
plt.legend()

plt.grid(True, which="both")

import os
figure_dir = "figures/detection_range"
os.makedirs(figure_dir, exist_ok=True)

plt.savefig(
    f"{figure_dir}/detection_range.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()
