import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array


# --------------------------------------------------
# Configuration
# --------------------------------------------------

sensor_spacing = 0.10  # meters

sensor_positions = create_planar_array(
    rows=3,
    cols=3,
    spacing=sensor_spacing
)

moment = np.array([
    0.0,
    0.0,
    1.0
])

detection_threshold = 10e-9  # 10 nT

# Conditioning threshold used only for visualization
condition_threshold = 100.0

x_values = np.linspace(-0.5, 0.5, 51)
y_values = np.linspace(-0.5, 0.5, 51)

z_values = [
    0.10,
    0.20,
    0.50,
    1.00
]


# --------------------------------------------------
# Measurement function
# --------------------------------------------------

def measurements(position, moment):

    B = dipole_field(
        sensor_positions,
        position,
        moment
    )

    return B[:, 2]


# --------------------------------------------------
# Numerical Jacobian
# --------------------------------------------------

def numerical_jacobian(position, moment):

    theta = np.concatenate([
        position,
        moment
    ])

    J = np.zeros(
        (len(sensor_positions), 6)
    )

    position_step = 1e-6
    moment_step = 1e-6

    steps = np.array([
        position_step,
        position_step,
        position_step,
        moment_step,
        moment_step,
        moment_step
    ])

    for i in range(6):

        theta_plus = theta.copy()
        theta_minus = theta.copy()

        theta_plus[i] += steps[i]
        theta_minus[i] -= steps[i]

        B_plus = measurements(
            theta_plus[:3],
            theta_plus[3:]
        )

        B_minus = measurements(
            theta_minus[:3],
            theta_minus[3:]
        )

        J[:, i] = (
            B_plus - B_minus
        ) / (2 * steps[i])

    return J


# --------------------------------------------------
# Calculate maps
# --------------------------------------------------

for z in z_values:

    condition_map = np.full(
        (len(y_values), len(x_values)),
        np.nan
    )

    smallest_sv_map = np.full(
        (len(y_values), len(x_values)),
        np.nan
    )

    max_field_map = np.zeros(
        (len(y_values), len(x_values))
    )

    detectable_map = np.zeros(
        (len(y_values), len(x_values))
    )

    observable_map = np.zeros(
        (len(y_values), len(x_values))
    )


    # --------------------------------------------------
    # Sweep source position
    # --------------------------------------------------

    for iy, y in enumerate(y_values):

        for ix, x in enumerate(x_values):

            position = np.array([
                x,
                y,
                z
            ])

            # ------------------------------------------
            # Magnetic field
            # ------------------------------------------

            Bz = measurements(
                position,
                moment
            )

            max_field = np.max(
                np.abs(Bz)
            )

            max_field_map[iy, ix] = max_field

            detectable = (
                max_field >= detection_threshold
            )

            detectable_map[iy, ix] = detectable


            # ------------------------------------------
            # Jacobian
            # ------------------------------------------

            J = numerical_jacobian(
                position,
                moment
            )

            # Normalize parameter columns
            parameter_scales = np.array([
                z,
                z,
                z,
                np.linalg.norm(moment),
                np.linalg.norm(moment),
                np.linalg.norm(moment)
            ])

            J_normalized = (
                J * parameter_scales[None, :]
            )

            singular_values = np.linalg.svd(
                J_normalized,
                compute_uv=False
            )

            condition_number = (
                singular_values[0]
                / singular_values[-1]
            )

            condition_map[iy, ix] = condition_number

            smallest_sv_map[iy, ix] = (
                singular_values[-1]
            )


            # ------------------------------------------
            # Combined practical observability
            # ------------------------------------------

            well_conditioned = (
                condition_number <= condition_threshold
            )

            observable_map[iy, ix] = (
                detectable and well_conditioned
            )


    # --------------------------------------------------
    # Condition number
    # --------------------------------------------------

    plt.figure(figsize=(8, 6))

    image = plt.imshow(
        np.log10(condition_map),
        extent=[
            x_values[0],
            x_values[-1],
            y_values[0],
            y_values[-1]
        ],
        origin="lower",
        aspect="equal"
    )

    plt.xlabel("Source x position (m)")
    plt.ylabel("Source y position (m)")

    plt.title(
        f"Normalized Jacobian Conditioning at z = {z:.2f} m"
    )

    plt.colorbar(
        image,
        label=r"$\log_{10}(\kappa)$"
    )

    plt.tight_layout()

    plt.savefig(
        f"observability_condition_z{z:.2f}.png",
        dpi=300
    )

    plt.show()


    # --------------------------------------------------
    # Smallest singular value
    # --------------------------------------------------

    plt.figure(figsize=(8, 6))

    image = plt.imshow(
        np.log10(smallest_sv_map),
        extent=[
            x_values[0],
            x_values[-1],
            y_values[0],
            y_values[-1]
        ],
        origin="lower",
        aspect="equal"
    )

    plt.xlabel("Source x position (m)")
    plt.ylabel("Source y position (m)")

    plt.title(
        f"Weakest Observable Direction at z = {z:.2f} m"
    )

    plt.colorbar(
        image,
        label=r"$\log_{10}(\sigma_\mathrm{min})$"
    )

    plt.tight_layout()

    plt.savefig(
        f"observability_smallest_sv_z{z:.2f}.png",
        dpi=300
    )

    plt.show()


    # --------------------------------------------------
    # Maximum |Bz| / detection threshold
    # --------------------------------------------------

    plt.figure(figsize=(8, 6))

    image = plt.imshow(
        np.log10(
            max_field_map / detection_threshold
        ),
        extent=[
            x_values[0],
            x_values[-1],
            y_values[0],
            y_values[-1]
        ],
        origin="lower",
        aspect="equal"
    )

    plt.xlabel("Source x position (m)")
    plt.ylabel("Source y position (m)")

    plt.title(
        f"Maximum Sensor |Bz| Relative to Detection Threshold at z = {z:.2f} m"
    )

    plt.colorbar(
        image,
        label=r"$\log_{10}(|B_z|_\mathrm{max}/B_\mathrm{threshold})$"
    )

    plt.tight_layout()

    plt.savefig(
        f"detectability_z{z:.2f}.png",
        dpi=300
    )

    plt.show()


    # --------------------------------------------------
    # Detectability mask
    # --------------------------------------------------

    plt.figure(figsize=(8, 6))

    image = plt.imshow(
        detectable_map,
        extent=[
            x_values[0],
            x_values[-1],
            y_values[0],
            y_values[-1]
        ],
        origin="lower",
        aspect="equal"
    )

    plt.xlabel("Source x position (m)")
    plt.ylabel("Source y position (m)")

    plt.title(
        f"Detection Region at z = {z:.2f} m"
    )

    plt.colorbar(
        image,
        label="Detectable (1 = yes)"
    )

    plt.tight_layout()

    plt.savefig(
        f"detection_region_z{z:.2f}.png",
        dpi=300
    )

    plt.show()


    # --------------------------------------------------
    # Combined practical observability
    # --------------------------------------------------

    plt.figure(figsize=(8, 6))

    image = plt.imshow(
        observable_map,
        extent=[
            x_values[0],
            x_values[-1],
            y_values[0],
            y_values[-1]
        ],
        origin="lower",
        aspect="equal"
    )

    plt.xlabel("Source x position (m)")
    plt.ylabel("Source y position (m)")

    plt.title(
        f"Detectable + Well-Conditioned Region at z = {z:.2f} m"
    )

    plt.colorbar(
        image,
        label=f"Observable (κ ≤ {condition_threshold:.0f})"
    )

    plt.tight_layout()

    plt.savefig(
        f"practical_observability_z{z:.2f}.png",
        dpi=300
    )

    plt.show()


    # --------------------------------------------------
    # Print summary
    # --------------------------------------------------

    total_points = observable_map.size

    detectable_fraction = (
        np.sum(detectable_map)
        / total_points
    )

    observable_fraction = (
        np.sum(observable_map)
        / total_points
    )

    print()
    print(f"z = {z:.2f} m")
    print(
        f"  Detectable area fraction: "
        f"{detectable_fraction:.3f}"
    )
    print(
        f"  Detectable + well-conditioned: "
        f"{observable_fraction:.3f}"
    )

    # --------------------------------------------------
    # Best-conditioned location
    # --------------------------------------------------

    valid = np.isfinite(condition_map)

    best_index = np.unravel_index(
        np.nanargmin(condition_map),
        condition_map.shape
    )

    best_y_index, best_x_index = best_index

    best_x = x_values[best_x_index]
    best_y = y_values[best_y_index]

    best_condition = condition_map[best_index]
    best_smallest_sv = smallest_sv_map[best_index]

    print()
    print(f"z = {z:.2f} m")
    print(f"  Best condition number: {best_condition:.3f}")
    print(f"  Best location: x = {best_x:.3f} m, y = {best_y:.3f} m")
    print(f"  Smallest singular value there: {best_smallest_sv:.6e}")
    print(
        f"  Detectable area fraction: "
        f"{np.mean(detectable_map):.3f}"
    )