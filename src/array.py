import numpy as np

def create_planar_array(rows, cols, spacing):
    x = (np.arange(cols) - (cols - 1) / 2) * spacing
    y = (np.arange(rows) - (rows - 1) / 2) * spacing

    xx, yy = np.meshgrid(x, y)

    positions = np.column_stack((
        xx.ravel(),
        yy.ravel(),
        np.zeros(rows * cols)
    ))

    return positions

def transform_sensors(sensor_local, position=None, rotation=None):
    """
    Transform sensor coordinates from array-local coordinates
    into world coordinates.

    Parameters
    ----------
    sensor_local : ndarray, shape (N, 3)
        Sensor positions relative to the array origin.

    position : ndarray, shape (3,), optional
        Array position in world coordinates.

    rotation : ndarray, shape (3, 3), optional
        Rotation matrix from array-local to world coordinates.

    Returns
    -------
    ndarray, shape (N, 3)
        Sensor positions in world coordinates.
    """
    sensor_local = np.asarray(sensor_local, dtype=float)

    if position is None:
        position = np.zeros(3)

    if rotation is None:
        rotation = np.eye(3)

    position = np.asarray(position, dtype=float)
    rotation = np.asarray(rotation, dtype=float)

    return sensor_local @ rotation.T + position