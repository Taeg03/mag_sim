"""
Magpylib field backend for the magnetic sensing simulator.

Provides optional Magpylib-based field calculation for point dipoles and
finite homogeneous magnets (cuboid, cylinder).

Units:
    - Positions: meters [m]
    - Dimensions: meters [m]
    - Magnetic field: Tesla [T]
    - Magnetic moment: A*m^2 (or J/T)
    - Magnetization: A/m
    - Polarization: Tesla [T] (mu_0 * M)

Coordinate Convention:
    Standard right-handed Cartesian coordinate system (x, y, z).
    When orientation is None, local magnet axes align with global (x, y, z).
"""

import numpy as np

try:
    import magpylib as magpy
    _MAGPYLIB_AVAILABLE = True
except ImportError:
    magpy = None
    _MAGPYLIB_AVAILABLE = False


def is_magpylib_available():
    """Return True if magpylib is installed and available."""
    return _MAGPYLIB_AVAILABLE


def _require_magpylib():
    if not _MAGPYLIB_AVAILABLE:
        raise ImportError(
            "magpylib is required to use this field backend. "
            "Install it via `pip install magpylib`."
        )


def magpylib_dipole_field(sensor_positions, source_position, moment):
    """
    Calculate magnetic field of a point dipole using Magpylib backend.

    Matches the call signature and output shape of `src.dipole.dipole_field`.

    Parameters
    ----------
    sensor_positions : array-like, shape (N, 3)
        Sensor coordinates in meters [m].
    source_position : array-like, shape (3,)
        Dipole position [x, y, z] in meters [m].
    moment : array-like, shape (3,)
        Magnetic dipole moment [mx, my, mz] in A*m^2.

    Returns
    -------
    B : ndarray, shape (N, 3)
        Magnetic field [Bx, By, Bz] in Tesla [T].
    """
    _require_magpylib()
    sensors = np.asarray(sensor_positions, dtype=float)
    source_pos = np.asarray(source_position, dtype=float)
    m = np.asarray(moment, dtype=float)

    source = magpy.misc.Dipole(position=source_pos, moment=m)
    B = np.asarray(magpy.getB(source, sensors))
    return B.reshape(-1, 3)


def magpylib_cuboid_field(
    sensor_positions,
    source_position,
    dimension,
    magnetization=None,
    moment=None,
    orientation=None,
):
    """
    Calculate magnetic field of a homogeneous cuboid magnet using Magpylib.

    Parameters
    ----------
    sensor_positions : array-like, shape (N, 3)
        Sensor coordinates in meters [m].
    source_position : array-like, shape (3,)
        Center position of cuboid [x, y, z] in meters [m].
    dimension : array-like, shape (3,)
        Side lengths (length_x, width_y, height_z) in meters [m].
    magnetization : array-like, shape (3,), optional
        Magnetization vector [Mx, My, Mz] in A/m in local coordinates.
    moment : array-like, shape (3,), optional
        Equivalent total magnetic moment [mx, my, mz] in A*m^2 in local coordinates.
        If provided and magnetization is None, magnetization = moment / volume.
    orientation : scipy.spatial.transform.Rotation or None, optional
        Orientation of the magnet relative to global coordinates.

    Returns
    -------
    B : ndarray, shape (N, 3)
        Magnetic field [Bx, By, Bz] in Tesla [T].
    """
    _require_magpylib()
    sensors = np.asarray(sensor_positions, dtype=float)
    source_pos = np.asarray(source_position, dtype=float)
    dim = np.asarray(dimension, dtype=float)
    vol = float(np.prod(dim))

    if magnetization is None:
        if moment is None:
            raise ValueError("Either magnetization or moment must be provided.")
        mag = np.asarray(moment, dtype=float) / vol
    else:
        mag = np.asarray(magnetization, dtype=float)

    source = magpy.magnet.Cuboid(
        position=source_pos,
        dimension=dim,
        magnetization=mag,
        orientation=orientation,
    )
    B = np.asarray(magpy.getB(source, sensors))
    return B.reshape(-1, 3)


def magpylib_cylinder_field(
    sensor_positions,
    source_position,
    dimension,
    magnetization=None,
    moment=None,
    orientation=None,
):
    """
    Calculate magnetic field of a homogeneous cylinder magnet using Magpylib.

    Parameters
    ----------
    sensor_positions : array-like, shape (N, 3)
        Sensor coordinates in meters [m].
    source_position : array-like, shape (3,)
        Geometric center [x, y, z] in meters [m].
        Cylinder axis aligns with local z-axis.
    dimension : array-like, shape (2,)
        Cylinder (diameter, height) in meters [m].
    magnetization : array-like, shape (3,), optional
        Magnetization vector [Mx, My, Mz] in A/m in local coordinates.
    moment : array-like, shape (3,), optional
        Equivalent total magnetic moment [mx, my, mz] in A*m^2 in local coordinates.
        If provided and magnetization is None, magnetization = moment / volume.
    orientation : scipy.spatial.transform.Rotation or None, optional
        Orientation of the magnet relative to global coordinates.

    Returns
    -------
    B : ndarray, shape (N, 3)
        Magnetic field [Bx, By, Bz] in Tesla [T].
    """
    _require_magpylib()
    sensors = np.asarray(sensor_positions, dtype=float)
    source_pos = np.asarray(source_position, dtype=float)
    dim = np.asarray(dimension, dtype=float)
    diameter, height = dim[0], dim[1]
    vol = float(np.pi * (diameter / 2.0) ** 2 * height)

    if magnetization is None:
        if moment is None:
            raise ValueError("Either magnetization or moment must be provided.")
        mag = np.asarray(moment, dtype=float) / vol
    else:
        mag = np.asarray(magnetization, dtype=float)

    source = magpy.magnet.Cylinder(
        position=source_pos,
        dimension=dim,
        magnetization=mag,
        orientation=orientation,
    )
    B = np.asarray(magpy.getB(source, sensors))
    return B.reshape(-1, 3)
