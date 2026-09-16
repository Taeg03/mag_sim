import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


# --------------------------------------------------
# Configuration
# --------------------------------------------------

threshold = 10e-9       # 10 nT
moment_magnitude = 1.0  # A*m^2

spacings = np.logspace(
    np.log10(0.005),
    np.log10(1.0),
    100
)

# Coarse grid used only to find the outer threshold crossing
distances = np.logspace(
    np.log10(0.05),
    np.log10(20.0),
    500
)

orientations = {
    "Vertical (0°)": np.array([0.0, 0.0, 1.0]),
    "Horizontal (90°)": np.array([1.0, 0.0, 0.0]),
}


# --------------------------------------------------
# Calculate maximum |Bz| for one configuration
# --------------------------------------------------

def max_bz_at_distance(sensor_positions, distance, moment):
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

    return np.max(np.abs(B[:, 2]))


# --------------------------------------------------
# Find outermost detection boundary
# --------------------------------------------------

def find_detection_range(sensor_positions, moment):
    """
    Find the outermost distance at which max |Bz|
    reaches the detection threshold.

    A coarse logarithmic sweep identifies the final
    detectable/undetectable transition, then bisection
    refines the threshold crossing.
    """

    fields = np.array([
        max_bz_at_distance(
            sensor_positions,
            distance,
            moment
        )
        for distance in distances
    ])

    detectable = fields >= threshold

    # Find transitions from detectable -> undetectable
    transitions = np.where(
        detectable[:-1] & ~detectable[1:]
    )[0]

    if len(transitions) == 0:
        return np.nan

    # Use the OUTERMOST transition
    i = transitions[-1]

    low = distances[i]
    high = distances[i + 1]

    # --------------------------------------------------
    # Bisection
    # --------------------------------------------------

    for _ in range(60):

        mid = 0.5 * (low + high)

        field = max_bz_at_distance(
            sensor_positions,
            mid,
            moment
        )

        if field >= threshold:
            low = mid
        else:
            high = mid

    return 0.5 * (low + high)


# --------------------------------------------------
# Sweep spacing and orientation
# --------------------------------------------------

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

        detection_range = find_detection_range(
            sensor_positions,
            moment
        )

        results[name].append(
            detection_range
        )


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

for spacing_target in [
    0.01,
    0.02,
    0.05,
    0.1,
    0.2,
    0.5,
    1.0
]:

    index = np.argmin(
        np.abs(spacings - spacing_target)
    )

    print(
        f"\nSpacing: "
        f"{spacings[index]:.4f} m"
    )

    for name in orientations:

        print(
            f"  {name}: "
            f"{results[name][index]:.4f} m"
        )