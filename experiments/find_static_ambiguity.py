import os
import numpy as np

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


# Candidate source positions
position_values = np.linspace(-0.50, 0.50, 21)

# Candidate moment orientations
theta_values = np.linspace(0, np.pi, 19)
phi_values = np.linspace(0, 2 * np.pi, 36, endpoint=False)

# Candidate moment magnitudes
moment_magnitudes = np.linspace(0.25, 2.0, 15)

# Don't accept candidates too close to the reference
minimum_position_difference = 0.05


# ============================================================
# Sensor positions
# ============================================================

sensor_world = transform_sensors(
    sensor_local,
    position=array_position
)


# ============================================================
# Measurement
# ============================================================

def get_bz(position, moment):

    B = dipole_field(
        sensor_world,
        np.asarray(position),
        np.asarray(moment)
    )

    return B[:, 2]


# ============================================================
# Moment orientations
# ============================================================

def generate_moment_directions():

    directions = []

    for theta in theta_values:
        for phi in phi_values:

            direction = np.array([
                np.sin(theta) * np.cos(phi),
                np.sin(theta) * np.sin(phi),
                np.cos(theta)
            ])

            directions.append(direction)

    return directions


# ============================================================
# Reference measurement
# ============================================================

reference_bz = get_bz(
    reference_position,
    reference_moment
)


# ============================================================
# Search candidates
# ============================================================

moment_directions = generate_moment_directions()

best = []

for x in position_values:
    for y in position_values:

        candidate_position = np.array([
            x,
            y,
            reference_position[2]
        ])

        position_difference = np.linalg.norm(
            candidate_position - reference_position
        )

        if position_difference < minimum_position_difference:
            continue

        for direction in moment_directions:

            for magnitude in moment_magnitudes:

                candidate_moment = (
                    direction * magnitude
                )

                candidate_bz = get_bz(
                    candidate_position,
                    candidate_moment
                )

                # Absolute measurement error
                residual = candidate_bz - reference_bz

                rmse = np.sqrt(
                    np.mean(residual ** 2)
                )

                # Relative RMSE
                reference_rms = np.sqrt(
                    np.mean(reference_bz ** 2)
                )

                relative_rmse = rmse / reference_rms

                best.append((
                    relative_rmse,
                    rmse,
                    position_difference,
                    candidate_position.copy(),
                    candidate_moment.copy(),
                    candidate_bz.copy()
                ))


# ============================================================
# Sort candidates
# ============================================================

best.sort(key=lambda x: x[0])


# ============================================================
# Print results
# ============================================================

print()
print("=" * 70)
print("STATIC ARRAY ABSOLUTE-MEASUREMENT AMBIGUITY SEARCH")
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

for i, result in enumerate(best[:10]):

    (
        relative_rmse,
        rmse,
        position_difference,
        position,
        moment,
        bz
    ) = result

    print(f"Candidate {i + 1}")
    print(f"  Relative RMSE:       {relative_rmse:.6e}")
    print(f"  Absolute RMSE:       {rmse:.6e} T")
    print(f"  Absolute RMSE:       {rmse * 1e9:.6f} nT")
    print(f"  Position difference: {position_difference:.4f} m")
    print(f"  Position:            {position}")
    print(f"  Moment:              {moment}")
    print()


# ============================================================
# Save best candidate
# ============================================================

best_result = best[0]

(
    relative_rmse,
    rmse,
    position_difference,
    candidate_position,
    candidate_moment,
    candidate_bz
) = best_result


figure_dir = "figures/find_static_ambiguity"
os.makedirs(figure_dir, exist_ok=True)

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
print(f"Best candidate saved to:")
print(f"  {figure_dir}/ambiguity_pair.npz")