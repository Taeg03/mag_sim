import numpy as np
import matplotlib.pyplot as plt

from src.dipole import dipole_field
from src.array import create_planar_array
from src.sensor import add_noise


moment = np.array([0, 0, 1])

sensor_positions = create_planar_array(
    rows=3,
    cols=3,
    spacing=0.02
)

source_position = np.array([0, 0, 2.0])

B = dipole_field(
    sensor_positions,
    source_position,
    moment
)

Bz = B[:, 2]

noise_std = 1e-8  # 10 nT

measurements = add_noise(
    Bz,
    noise_std
)

print("True Bz (nT):")
print(Bz * 1e9)

print("\nMeasured Bz (nT):")
print(measurements * 1e9)
