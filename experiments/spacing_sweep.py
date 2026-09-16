import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


threshold = 10e-9  # 10 nT
moment_magnitude = 1.0  # A*m^2

spacings = np.logspace(
    np.log10(0.005),
    np.log10(1.0),
    100
)

distances = np.logspace(
    np.log10(0.05),
    np.log10(20.0),
    400
)

orientations = {
    "Vertical (0°)": np.array([0.0, 0.0, 1.0]),
    "Horizontal (90°)": np.array([1.0, 0.0, 0.0]),
}

results = {
    name: []
    for name in orientations
}


for spacing in spacings:

    sensor_positions = create_planar_array(
        rows=3,
        cols=3,
        spacing=spacing
    )

    for name, direction in orientations.items():

        moment = moment_magnitude * direction

        detectable_distances = []

        for distance in distances:

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

            if max_bz >= threshold:
                detectable_distances.append(distance)

        if detectable_distances:
            results[name].append(
                max(detectable_distances)
            )
        else:
            results[name].append(np.nan)


# --------------------------------------------------
# Plot
# --------------------------------------------------

plt.figure(figsize=(9, 6))

for name, ranges in results.items():

    plt.plot(
        spacings,
        ranges,
        label=name
    )

plt.xscale("log")
plt.yscale("log")

plt.xlabel("Sensor spacing (m)")
plt.ylabel("Maximum detectable distance (m)")
plt.title(
    "Detection Range vs Sensor Array Spacing"
)

plt.grid(True, which="both")
plt.legend()

plt.tight_layout()

plt.savefig(
    "spacing_detection_range.png",
    dpi=300
)

plt.show()


# --------------------------------------------------
# Print representative values
# --------------------------------------------------

print("\nMaximum detectable distance:")

for spacing_target in [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]:

    index = np.argmin(
        np.abs(spacings - spacing_target)
    )

    print(f"\nSpacing: {spacings[index]:.3f} m")

    for name in orientations:
        print(
            f"  {name}: "
            f"{results[name][index]:.3f} m"
        )