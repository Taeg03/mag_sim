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
