import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


# Simulation parameters
moment = np.array([0, 0, 1])
sensor_positions = create_planar_array(
    rows=3,
    cols=3,
    spacing=0.02
)

distances = np.linspace(0.05, 1.0, 100)

center_bz = []
max_bz = []
min_bz = []


for distance in distances:

    source_position = np.array([0, 0, distance])

    B = dipole_field(
        sensor_positions,
        source_position,
        moment
    )

    Bz = B[:, 2]

    center_bz.append(Bz[4])
    max_bz.append(np.max(Bz))
    min_bz.append(np.min(Bz))


center_bz = np.array(center_bz)
max_bz = np.array(max_bz)
min_bz = np.array(min_bz)


# Plot field strength
plt.figure()

plt.loglog(distances, np.abs(center_bz) * 1e6)

plt.xlabel("Source distance (m)")
plt.ylabel("Center Bz (µT)")
plt.title("Dipole Field vs Source Distance")

plt.grid(True, which="both")
plt.savefig("distance_sweep.png", dpi=300, bbox_inches="tight")
plt.close()


# Plot spatial variation
plt.figure()

plt.loglog(
    distances,
    (max_bz - min_bz) * 1e6
)

plt.xlabel("Source distance (m)")
plt.ylabel("Bz range across array (µT)")
plt.title("Spatial Variation vs Source Distance")

plt.grid(True, which="both")
plt.savefig("spatial_variation.png", dpi=300, bbox_inches="tight")
plt.close()

log_distance = np.log(distances)
log_field = np.log(np.abs(center_bz))

slope, intercept = np.polyfit(log_distance, log_field, 1)

print(f"Fitted log-log slope: {slope:.4f}")
print("Expected slope: -3")
