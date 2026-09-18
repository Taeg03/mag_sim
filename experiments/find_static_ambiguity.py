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

array_position = np.array([0.0, 0.0, 0.0])

# Reference source
reference_position = np.array([0.0, 0.0, 0.50])
reference_moment = np.array([0.0, 0.0, 1.0])

# Search region
x_values = np.linspace(-0.50, 0.50, 101)
y_values = np.linspace(-0.50, 0.50, 101)

# Don't consider positions too close to reference
minimum_position_difference = 0.05


# ============================================================
# Sensor positions
# ============================================================

sensor_world = transform_sensors(
    sensor_local,
    position=array_position
)


# ============================================================
# Field model
# ============================================================

def get_bz(position, moment):

    B = dipole_field(
        sensor_world,
        position,
        moment
    )

    return B[:, 2]


# ============================================================
# Reference measurement
# ============================================================

reference_bz = get_bz(
    reference_position,
    reference_moment
)

reference_rms = np.sqrt(
    np.mean(reference_bz ** 2)
)


# ============================================================
# Build moment response matrix
# ============================================================

def moment_matrix(position):
    """
    Construct A such that:

        Bz = A @ m

    where m = [mx, my, mz].
    """

    A = np.zeros((len(sensor_world), 3))

    for i in range(3):

        moment = np.zeros(3)
        moment[i] = 1.0

        A[:, i] = get_bz(
            position,
            moment
        )

    return A


# ============================================================
# Search
# ============================================================

errors = []
best = None

for x in x_values:
    for y in y_values:

        position = np.array([
            x,
            y,
            reference_position[2]
        ])

        position_difference = np.linalg.norm(
            position - reference_position
        )

        if position_difference < minimum_position_difference:
            continue

        A = moment_matrix(position)

        # Best-fit magnetic moment
        moment, _, _, _ = np.linalg.lstsq(
            A,
            reference_bz,
            rcond=None
        )

        predicted_bz = A @ moment

        residual = predicted_bz - reference_bz

        rmse = np.sqrt(
            np.mean(residual ** 2)
        )

        relative_rmse = rmse / reference_rms

        errors.append((
            relative_rmse,
            rmse,
            position_difference,
            position.copy(),
            moment.copy(),
            predicted_bz.copy()
        ))

        if best is None or relative_rmse < best[0]:
            best = errors[-1]


# ============================================================
# Sort results
# ============================================================

errors.sort(key=lambda x: x[0])


# ============================================================
# Print results
# ============================================================

print()
print("=" * 70)
print("STATIC ARRAY BEST-FIT MOMENT AMBIGUITY SEARCH")
print("=" * 70)

print()
print("Reference:")
print(f"  Position: {reference_position}")
print(f"  Moment:   {reference_moment}")

print()
print("Reference Bz measurements (nT):")
print(reference_bz * 1e9)

print()
print("Closest candidates:")
print()

for i, result in enumerate(errors[:10]):

    (
        relative_rmse,
        rmse,
        position_difference,
        position,
        moment,
        predicted_bz
    ) = result

    print(f"Candidate {i + 1}")
    print(f"  Relative RMSE:       {relative_rmse:.6e}")
    print(f"  Absolute RMSE:       {rmse * 1e9:.6f} nT")
    print(f"  Position difference: {position_difference:.4f} m")
    print(f"  Position:            {position}")
    print(f"  Best-fit moment:     {moment}")
    print(f"  Moment magnitude:    {np.linalg.norm(moment):.6f}")
    print()


# ============================================================
# Build error map
# ============================================================

error_map = np.full(
    (len(y_values), len(x_values)),
    np.nan
)

for result in errors:

    relative_rmse, _, _, position, _, _ = result

    ix = np.argmin(
        np.abs(x_values - position[0])
    )

    iy = np.argmin(
        np.abs(y_values - position[1])
    )

    error_map[iy, ix] = relative_rmse


# ============================================================
# Output directory
# ============================================================

figure_dir = "figures/find_static_ambiguity"
os.makedirs(figure_dir, exist_ok=True)


# ============================================================
# Plot residual map
# ============================================================

plt.figure(figsize=(8, 6))

plt.imshow(
    error_map,
    extent=[
        x_values[0],
        x_values[-1],
        y_values[0],
        y_values[-1]
    ],
    origin="lower",
    aspect="equal"
)

plt.colorbar(
    label="Relative RMSE"
)

plt.scatter(
    reference_position[0],
    reference_position[1],
    marker="x",
    s=100,
    label="Reference"
)

plt.scatter(
    best[3][0],
    best[3][1],
    marker="o",
    facecolors="none",
    edgecolors="black",
    s=100,
    label="Best candidate"
)

plt.xlabel("Source x position (m)")
plt.ylabel("Source y position (m)")
plt.title("Static Array Ambiguity")
plt.legend()
plt.tight_layout()

plt.savefig(
    f"{figure_dir}/static_ambiguity_map.png",
    dpi=200
)

plt.close()


# ============================================================
# Save best pair
# ============================================================

(
    relative_rmse,
    rmse,
    position_difference,
    candidate_position,
    candidate_moment,
    candidate_bz
) = best

np.savez(
    f"{figure_dir}/ambiguity_pair.npz",

    reference_position=reference_position,
    reference_moment=reference_moment,
    reference_bz=reference_bz,

    candidate_position=candidate_position,
    candidate_moment=candidate_moment,
    candidate_bz=candidate_bz,

    relative_rmse=relative_rmse,
    absolute_rmse=rmse
)

print()
print(f"Figures saved to: {figure_dir}/")
print(f"Best pair saved to: {figure_dir}/ambiguity_pair.npz")