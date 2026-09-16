import numpy as np
from src.dipole import dipole_field

dipole1 = np.array([0,0,.1])
moment = np.array([0,0,1])

# shape must be (N, 3) --> 1 sensor requires 3 dimensions
#sensor = np.array([[0, 0, 0]])

d = .02
sensor = np.array([
    [-d, -d, 0],
    [0, -d, 0],
    [d, -d, 0],
    [-d, 0, 0],
    [0, 0, 0],
    [d, 0, 0],
    [-d, d, 0],
    [0, d, 0],
    [d, d, 0],
])

B = dipole_field(sensor, dipole1, moment)

print("Magnetic field vector (Tesla):")
print(B)
print("Shape:", B.shape)  # (1, 3)
