import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

MOMENT = np.array([0.0, 0.0, 1.0])  # A*m^2
SIGMA_B = 1e-9                       # 1 nT assumed measurement uncertainty
DETECTION_THRESHOLD = 1e-8           # 10 nT

# Physical array apertures to compare.
# For a 3x3 array, aperture = 2 * spacing.
APERTURES = [0.05, 0.10, 0.20, 0.40, 0.80]

# Source-plane coordinates.
# Kept fixed in physical units so the plots answer:
# "How does changing the physical array aperture affect the
# same region of space?"
X_RANGE = (-0.5, 0.5)
Y_RANGE = (-0.5, 0.5)

N_X = 51
N_Y = 51

DEPTHS = [0.10, 0.20, 0.50, 1.00]

DELTA = 1e-5

# Precision thresholds for useful localization.
POSITION_THRESHOLDS = [0.05, 0.10]  # 5 cm and 10 cm


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def get_bz(sensor_positions, source_position, moment):
    B = dipole_field(sensor_positions, source_position, moment)
    return B[:, 2]


def position_jacobian(sensor_positions, source_position, moment):
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

    xs = np.linspace(*X_RANGE, N_X)
    ys = np.linspace(*Y_RANGE, N_Y)

    # One figure for each depth.
    # Each figure contains one map per aperture.
    # Each map shows total 3D position uncertainty.
    for z in DEPTHS:

        fig, axes = plt.subplots(
            1,
            len(APERTURES),
            figsize=(20, 4)
        )

        all_results = []

        for aperture, ax in zip(APERTURES, axes):

            spacing = aperture / 2.0

            sensors = create_planar_array(
                3,
                3,
                spacing
            )

            sigma_pos = np.full(
                (N_Y, N_X),
                np.nan
            )

            detectable = np.zeros(
                (N_Y, N_X),
                dtype=bool
            )

            for iy, y in enumerate(ys):
                for ix, x in enumerate(xs):

                    source_position = np.array([
                        x,
                        y,
                        z
                    ])

                    bz = get_bz(
                        sensors,
                        source_position,
                        MOMENT
                    )

                    # Detection requires at least one sensor
                    # to exceed the 10 nT threshold.
                    if np.max(np.abs(bz)) < DETECTION_THRESHOLD:
                        continue

                    detectable[iy, ix] = True

                    std = localization_std(
                        sensors,
                        source_position,
                        MOMENT,
                        SIGMA_B
                    )

                    if np.all(np.isfinite(std)):
                        sigma_pos[iy, ix] = np.linalg.norm(std)

            all_results.append(
                (aperture, sigma_pos, detectable)
            )

            # Plot in centimeters.
            image = sigma_pos * 100

            im = ax.imshow(
                image,
                origin="lower",
                extent=[
                    X_RANGE[0],
                    X_RANGE[1],
                    Y_RANGE[0],
                    Y_RANGE[1]
                ],
                aspect="equal",
                interpolation="nearest",
                vmin=0,
                vmax=50
            )

            # Show the 5 cm and 10 cm contours.
            finite = np.isfinite(image)

            if np.any(finite):
                X_grid, Y_grid = np.meshgrid(xs, ys)

                ax.contour(
                    X_grid,
                    Y_grid,
                    np.where(finite, image, np.nan),
                    levels=np.asarray(POSITION_THRESHOLDS) * 100,
                    linewidths=1
                )

            ax.set_title(
                f"L = {aperture:.2f} m"
            )
            ax.set_xlabel("Source x (m)")

            if ax is axes[0]:
                ax.set_ylabel("Source y (m)")

        fig.suptitle(
            f"3D position uncertainty at z = {z:.2f} m "
            f"(σB = {SIGMA_B * 1e9:.0f} nT)"
        )

        cbar = fig.colorbar(
            im,
            ax=axes,
            shrink=0.85
        )
        cbar.set_label("1σ position uncertainty (cm)")

        plt.tight_layout()

        filename = f"localization_z_{z:.2f}.png"
        plt.savefig(filename, dpi=200)
        plt.show()

        # ----------------------------------------------------
        # Summary for this depth
        # ----------------------------------------------------

        print()
        print(f"z = {z:.2f} m")
        print("-" * 65)
        print(
            "Aperture | Detectable | Median σpos | "
            "90% σpos | <5 cm | <10 cm"
        )

        for aperture, sigma_pos, detectable in all_results:

            valid = np.isfinite(sigma_pos)

            if not np.any(valid):
                print(
                    f"{aperture:7.2f} | "
                    f"{0.0:10.3f} | "
                    f"{'N/A':>12} | "
                    f"{'N/A':>9} | "
                    f"{0.0:5.3f} | "
                    f"{0.0:6.3f}"
                )
                continue

            values = sigma_pos[valid]

            detectable_fraction = np.mean(detectable)

            median = np.median(values)
            percentile90 = np.percentile(values, 90)

            fraction_5cm = np.mean(values <= 0.05)
            fraction_10cm = np.mean(values <= 0.10)

            print(
                f"{aperture:7.2f} | "
                f"{detectable_fraction:10.3f} | "
                f"{median * 100:10.2f} cm | "
                f"{percentile90 * 100:7.2f} cm | "
                f"{fraction_5cm:5.3f} | "
                f"{fraction_10cm:6.3f}"
            )


if __name__ == "__main__":
    main()
