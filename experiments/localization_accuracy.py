import numpy as np

from src.dipole import dipole_field
from src.array import create_planar_array


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

ROWS = 3
COLS = 3
SPACING = 0.10          # 10 cm sensor spacing -> 20 cm aperture

MOMENT = np.array([0.0, 0.0, 1.0])   # A*m^2

DETECTION_THRESHOLD = 1e-8             # 10 nT

# Assumed measurement uncertainty.
# This is NOT being claimed as the actual sensor noise.
NOISE_LEVELS = [
    1e-9,    # 1 nT
    3e-9,    # 3 nT
    1e-8,    # 10 nT
]

# Source search volume
X_RANGE = (-0.5, 0.5)
Y_RANGE = (-0.5, 0.5)
Z_RANGE = (0.05, 2.0)

N_X = 31
N_Y = 31
N_Z = 40

# Finite-difference step for position derivatives
DELTA = 1e-5


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def get_bz(sensor_positions, source_position, moment):
    """
    Return Bz at every sensor.
    """
    B = dipole_field(
        sensor_positions,
        source_position,
        moment
    )
    return B[:, 2]


def position_jacobian(sensor_positions, source_position, moment):
    """
    Numerical Jacobian of Bz with respect to source x, y, z.

    Returns
    -------
    J : ndarray, shape (N_sensors, 3)
        dBz/d[x,y,z]
    """

    J = np.zeros((len(sensor_positions), 3))

    for i in range(3):
        offset = np.zeros(3)
        offset[i] = DELTA

        B_plus = get_bz(
            sensor_positions,
            source_position + offset,
            moment
        )

        B_minus = get_bz(
            sensor_positions,
            source_position - offset,
            moment
        )

        J[:, i] = (B_plus - B_minus) / (2 * DELTA)

    return J


def localization_std(sensor_positions, source_position, moment, sigma_B):
    """
    Estimate 1-sigma position uncertainty.

    Assumes independent sensors with identical uncertainty sigma_B.
    """

    J = position_jacobian(
        sensor_positions,
        source_position,
        moment
    )

    F = J.T @ J

    try:
        covariance = sigma_B**2 * np.linalg.inv(F)
    except np.linalg.LinAlgError:
        return np.full(3, np.inf)

    std = np.sqrt(np.maximum(np.diag(covariance), 0.0))

    return std


# ------------------------------------------------------------
# Main experiment
# ------------------------------------------------------------

def main():

    sensors = create_planar_array(
        ROWS,
        COLS,
        SPACING
    )

    xs = np.linspace(*X_RANGE, N_X)
    ys = np.linspace(*Y_RANGE, N_Y)
    zs = np.linspace(*Z_RANGE, N_Z)

    X, Y, Z = np.meshgrid(
        xs,
        ys,
        zs,
        indexing="ij"
    )

    positions = np.column_stack((
        X.ravel(),
        Y.ravel(),
        Z.ravel()
    ))

    print("3D localization-accuracy experiment")
    print(f"Array: {ROWS}x{COLS}")
    print(f"Spacing: {SPACING:.3f} m")
    print(f"Aperture: {(COLS - 1) * SPACING:.3f} m")
    print(f"Moment: {np.linalg.norm(MOMENT):.3g} A*m^2")
    print()

    # Store results for each noise assumption
    all_results = {}

    for sigma_B in NOISE_LEVELS:

        print(
            f"Measurement uncertainty = "
            f"{sigma_B * 1e9:.1f} nT"
        )

        results = np.full(
            (len(positions), 3),
            np.inf
        )

        detectable = 0

        for i, source_position in enumerate(positions):

            bz = get_bz(
                sensors,
                source_position,
                MOMENT
            )

            # Detection criterion:
            # at least one sensor exceeds threshold
            if np.max(np.abs(bz)) < DETECTION_THRESHOLD:
                continue

            detectable += 1

            results[i] = localization_std(
                sensors,
                source_position,
                MOMENT,
                sigma_B
            )

        all_results[sigma_B] = results

        print(
            f"  Detectable: "
            f"{detectable / len(positions):.3f}"
        )

        finite = np.isfinite(results[:, 0])

        if np.any(finite):

            std_xyz = results[finite]

            print(
                f"  Median σx: "
                f"{np.median(std_xyz[:, 0]) * 100:.2f} cm"
            )

            print(
                f"  Median σy: "
                f"{np.median(std_xyz[:, 1]) * 100:.2f} cm"
            )

            print(
                f"  Median σz: "
                f"{np.median(std_xyz[:, 2]) * 100:.2f} cm"
            )

            print(
                f"  90th percentile σx: "
                f"{np.percentile(std_xyz[:, 0], 90) * 100:.2f} cm"
            )

            print(
                f"  90th percentile σy: "
                f"{np.percentile(std_xyz[:, 1], 90) * 100:.2f} cm"
            )

            print(
                f"  90th percentile σz: "
                f"{np.percentile(std_xyz[:, 2], 90) * 100:.2f} cm"
            )

        print()

    # --------------------------------------------------------
    # Scaling check
    # --------------------------------------------------------

    print("Noise scaling check")
    print("(Localization uncertainty should scale linearly with sigma_B.)")

    sigma_ref = NOISE_LEVELS[0]
    ref = all_results[sigma_ref]

    finite = np.all(np.isfinite(ref), axis=1)

    if np.any(finite):

        median_ref = np.median(ref[finite], axis=0)

        for sigma_B in NOISE_LEVELS:

            result = all_results[sigma_B]

            finite = np.all(np.isfinite(result), axis=1)

            median_result = np.median(result[finite], axis=0)

            ratio = median_result / median_ref

            print(
                f"{sigma_B * 1e9:5.1f} nT -> "
                f"σx ratio={ratio[0]:.2f}, "
                f"σy ratio={ratio[1]:.2f}, "
                f"σz ratio={ratio[2]:.2f}"
            )


if __name__ == "__main__":
    main()