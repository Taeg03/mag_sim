import unittest

import numpy as np

from frontend.server import simulate


class TestFrontendSimulation(unittest.TestCase):
    def test_simulate_returns_nine_sensor_vectors(self):
        result = simulate({
            "source_position": [0.0, 0.0, 0.5],
            "moment": [0.0, 0.0, 1.0],
            "sensor_spacing": 0.1,
        })

        self.assertEqual(len(result["sensor_positions_m"]), 9)
        self.assertEqual(np.asarray(result["field_vectors_t"]).shape, (9, 3))
        self.assertEqual(len(result["bz_t"]), 9)
        self.assertTrue(result["detectable"])

    def test_invalid_source_position_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly 3"):
            simulate({"source_position": [0.0, 0.0], "moment": [0.0, 0.0, 1.0]})


if __name__ == "__main__":
    unittest.main()
