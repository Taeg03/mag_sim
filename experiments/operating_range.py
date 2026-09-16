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
    150
)

moments = np.logspace(
    np.log10(1e-3),
    np.log10(10),
    150
)

# Dipole orientation: +z
moment_direction = np.array([0.0, 0.0, 1.0])


# --------------------------------------------------
# Sweep
# --------------------------------------------------

detectable = np.zeros(
    (len(moments), len(distances)),
    dtype=bool
)

max_bz = np.zeros_like(detectable, dtype=float)

for i, moment_magnitude in enumerate(moments):

    moment = moment_magnitude * moment_direction

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

        bz = np.abs(B[:, 2]) # Check all sensors in the array (not just center)

        max_bz[i, j] = np.max(bz)

        detectable[i, j] = np.max(bz) >= threshold


# --------------------------------------------------
# Plot detectability
# --------------------------------------------------

plt.figure(figsize=(9, 6))

plt.pcolormesh(
    distances,
    moments,
    detectable,
    shading="auto"
)

plt.xscale("log")
plt.yscale("log")

plt.xlabel("Source distance (m)")
plt.ylabel("Dipole moment (A·m²)")
plt.title("Magnetic Sensor Operating Range")

plt.colorbar(
    label="Detectable"
)

plt.tight_layout()
plt.savefig(
    "operating_range.png",
    dpi=300
)

plt.show()


# --------------------------------------------------
# Plot maximum Bz
# --------------------------------------------------

plt.figure(figsize=(9, 6))

plt.pcolormesh(
    distances,
    moments,
    max_bz * 1e9,
    shading="auto"
)

plt.xscale("log")
plt.yscale("log")

plt.xlabel("Source distance (m)")
plt.ylabel("Dipole moment (A·m²)")
plt.title("Maximum |Bz| Across Sensor Array")

plt.colorbar(
    label="|Bz| (nT)"
)

plt.tight_layout()
plt.savefig(
    "operating_range_field.png",
    dpi=300
)

plt.show()
