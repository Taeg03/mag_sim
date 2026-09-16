import numpy as np
import matplotlib.pyplot as plt
from src.dipole import dipole_field
from src.array import create_planar_array

dipole1 = np.array([0,0,.2])
moment = np.array([0,0,1])

# shape must be (N, 3) --> 1 sensor requires 3 dimensions
#sensor = np.array([[0, 0, 0]])

# rows, col, spacing
sensor = create_planar_array(3,3,.02)

#
B = dipole_field(sensor, dipole1, moment)

print("Magnetic field vector (Tesla):")
print(B)
print("Shape:", B.shape)  # (1, 3)

Bz = B[:, 2].reshape(3, 3)

plt.imshow(Bz * 1e6, origin="lower")
plt.colorbar(label="Bz (µT)")
plt.xlabel("Sensor x")
plt.ylabel("Sensor y")
plt.title("Dipole Bz Field")

plt.savefig("bfield.png", dpi=300, bbox_inches="tight")
plt.close()
