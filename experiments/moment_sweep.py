import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


detection_limit = 1e-8

sensor_positions = create_planar_array(
    rows=3,
    cols=3,
    spacing=0.02
)

moments = np.logspace(-3, 3, 100)
distances = np.linspace(0.01, 100, 5000)

detection_ranges = []


for moment_magnitude in moments:

    moment = np.array([0, 0, moment_magnitude])

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

    detectable = center_bz >= detection_limit

    if np.any(detectable):
        detection_ranges.append(distances[detectable][-1])
    else:
        detection_ranges.append(np.nan)


detection_ranges = np.array(detection_ranges)


# Plot
plt.figure()

plt.loglog(moments, detection_ranges)

plt.xlabel("Dipole moment (A m²)")
plt.ylabel("Detection range (m)")
plt.title("Detection Range vs Magnetic Dipole Moment")

plt.grid(True, which="both")

plt.savefig(
    "moment_sweep.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

log_moments = np.log(moments)
log_ranges = np.log(detection_ranges)

slope, intercept = np.polyfit(log_moments, log_ranges, 1)

print(f"Fitted slope: {slope:.4f}")
print("Expected slope: 0.3333")
