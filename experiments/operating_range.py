import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


# --------------------------------------------------
# Configuration
# --------------------------------------------------

sensor_positions = create_planar_array(
    rows=3,
    cols=3,
    spacing=0.02
)

threshold = 10e-9  # 10 nT

distances = np.logspace(
    np.log10(0.05),
    np.log10(10.0),
    200
)

moments = np.logspace(
    np.log10(1e-3),
    np.log10(10),
    150
)

angles = np.linspace(0, 90, 91)


# --------------------------------------------------
# Helper
# --------------------------------------------------

def moment_vector(magnitude, angle_deg):
    """
    Create a dipole moment rotated from +z toward +x.

    angle = 0 deg  -> +z
    angle = 90 deg -> +x
    """

    theta = np.deg2rad(angle_deg)

    return magnitude * np.array([
        np.sin(theta),
        0.0,
        np.cos(theta)
    ])


# --------------------------------------------------
# Orientation sweep
# Fixed moment, vary orientation and distance
# --------------------------------------------------

test_moment = 1.0  # A*m^2

max_bz_orientation = np.zeros(
    (len(angles), len(distances))
)

detectable_orientation = np.zeros(
    (len(angles), len(distances)),
    dtype=bool
)

for i, angle in enumerate(angles):

    moment = moment_vector(
        test_moment,
        angle
    )

    for j, distance in enumerate(distances):

        source_position = np.array([
            0.0,
            0.0,
            distance
        ])

        B = dipole_field(
            sensor_positions,
            source_position,
            moment
        )

        max_bz = np.max(np.abs(B[:, 2]))

        max_bz_orientation[i, j] = max_bz

        detectable_orientation[i, j] = (
            max_bz >= threshold
        )


# --------------------------------------------------
# Find maximum detectable distance
# --------------------------------------------------

max_detectable_distance = np.full(
    len(angles),
    np.nan
)

for i, angle in enumerate(angles):

    detectable_distances = distances[
        detectable_orientation[i]
    ]

    if len(detectable_distances) > 0:
        max_detectable_distance[i] = np.max(
            detectable_distances
        )


# --------------------------------------------------
# Plot 1: Detection range vs orientation
# --------------------------------------------------

plt.figure(figsize=(9, 6))

plt.plot(
    angles,
    max_detectable_distance
)

plt.xlabel("Dipole orientation from +z (degrees)")
plt.ylabel("Maximum detectable distance (m)")
plt.title(
    f"Detection Range vs Dipole Orientation "
    f"(m = {test_moment} A·m²)"
)

plt.grid(True)

plt.tight_layout()

plt.savefig(
    "orientation_detection_range.png",
    dpi=300
)

plt.show()


# --------------------------------------------------
# Plot 2: Field relative to detection threshold
# --------------------------------------------------

field_ratio = max_bz_orientation / threshold

plt.figure(figsize=(9, 6))

plt.pcolormesh(
    distances,
    angles,
    np.log10(field_ratio),
    shading="auto"
)

plt.xscale("log")

plt.xlabel("Source distance (m)")
plt.ylabel("Dipole orientation from +z (degrees)")
plt.title(
    f"Maximum |Bz| Relative to Detection Threshold "
    f"(m = {test_moment} A·m²)"
)

plt.colorbar(
    label=r"$\log_{10}(|B_z| / B_{\mathrm{threshold}})$"
)

plt.axhline(
    0,
    linestyle="--"
)

plt.tight_layout()

plt.savefig(
    "orientation_field_ratio.png",
    dpi=300
)

plt.show()


# --------------------------------------------------
# Print selected values
# --------------------------------------------------

print("\nMaximum detectable distance:")

for angle in [0, 15, 30, 45, 60, 75, 90]:

    index = np.argmin(
        np.abs(angles - angle)
    )

    print(
        f"{angle:>3} deg: "
        f"{max_detectable_distance[index]:.3f} m"
    )