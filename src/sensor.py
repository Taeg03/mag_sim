import numpy as np

"""
measurements: ndarray of ideal sensor measurements (T)
noise_std: std dev of noise (T)
return: ndarray of measurements w/ noise
"""
def add_noise(measurements, noise_std):
    noise = np.random.normal(
        loc=0.0,
        scale=noise_std,
        size=measurements.shape
    )

    return measurements + noise
