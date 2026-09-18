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
reference_magnitude = 1.0

# Candidate search region
position_values = np.linspace(-0.50, 0.50, 21)

# Moment orientation grid
theta_values = np.linspace(0, np.pi, 19)
phi_values = np.linspace(0, 2 * np.pi, 36, endpoint=False)


# ============================================================
# Sensor positions
# ============================================================

sensor_world = transform_sensors(
    sensor_local,
    position=array_position
)


# ============================================================
# Dipole measurement
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

def generate_moments():

    moments = []

    for theta in theta_values:
        for phi in phi_values:

            mx = np.sin(theta) * np.cos(phi)
            my = np.sin(theta) * np.sin(phi)
            mz = np.cos(theta)

            moments.append(
                np.array([mx, my, mz]) * reference_magnitude
            )

    return moments


# ============================================================
# Normalize measurement pattern
# ============================================================

def normalize(v):

    norm = np.linalg.norm(v)

    if norm == 0:
        return v

    return v / norm


# ============================================================
# Reference measurement
# ============================================================

reference_moment = np.array([
    0.0,
    0.0,
    reference_magnitude
])

reference_bz = get_bz(
    reference_position,
    reference_moment
)

reference_pattern = normalize(reference_bz)


# ============================================================
# Search candidates
# ============================================================

moments = generate_moments()

best = []

for x in position_values:
    for y in position_values:

        candidate_position = np.array([
            x,
            y,
            reference_position[2]
        ])

        # Skip the reference position
        if np.linalg.norm(
            candidate_position - reference_position
        ) < 1e-9:
            continue

        for moment in moments:

            candidate_bz = get_bz(
                candidate_position,
                moment
            )

            candidate_pattern = normalize(
                candidate_bz
            )

            # Pattern similarity
            error = np.linalg.norm(
                candidate_pattern - reference_pattern
            )

            position_difference = np.linalg.norm(
                candidate_position - reference_position
            )

            best.append((
                error,
                position_difference,
                candidate_position.copy(),
                moment.copy(),
                candidate_bz.copy()
            ))


# ============================================================
# Sort candidates
# ============================================================

best.sort(key=lambda x: x[0])


# ============================================================
# Print best candidates
# ============================================================

print()
print("=" * 70)
print("STATIC ARRAY AMBIGUITY SEARCH")
print("=" * 70)

print()
print("Reference:")
print(f"  Position: {reference_position}")
print(f"  Moment:   {reference_moment}")
print()

print("Closest candidates:")
print()

for i, result in enumerate(best[:10]):

    error, position_difference, position, moment, bz = result

    print(f"Candidate {i + 1}")
    print(f"  Pattern error:       {error:.6e}")
    print(f"  Position difference: {position_difference:.4f} m")
    print(f"  Position:            {position}")
    print(f"  Moment:              {moment}")
    print()


# ============================================================
# Save best candidate
# ============================================================

best_result = best[0]

error, position_difference, candidate_position, candidate_moment, candidate_bz = best_result

figure_dir = "figures/find_static_ambiguity"
os.makedirs(figure_dir, exist_ok=True)

np.savez(
    f"{figure_dir}/ambiguity_pair.npz",
    reference_position=reference_position,
    reference_moment=reference_moment,
    reference_bz=reference_bz,
    candidate_position=candidate_position,
    candidate_moment=candidate_moment,
    candidate_bz=candidate_bz
)

print()
print(f"Best candidate saved to:")
print(f"  {figure_dir}/ambiguity_pair.npz")