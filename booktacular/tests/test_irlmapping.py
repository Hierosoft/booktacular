from __future__ import print_function
from __future__ import division

import os
import sys
import unittest

my_dir = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.dirname(my_dir)
repo_dir = os.path.dirname(module_dir)

# if __name__ == "__main__":
sys.path.insert(0, repo_dir)

from booktacular.irlmapping import (
    clean_coords,
    get_precision,
)


class CoordsTests(unittest.TestCase):
    def test_gps(self):
        self.assertEqual(
            clean_coords("38.4812499,42.5199286"),
            (38.4812499, 42.5199286)
        )
        self.assertEqual(
            clean_coords("31.63417, 45.79974"),
            (31.63417, 45.79974)
        )

    def test_gps_and_elevation(self):
        self.assertEqual(
            clean_coords("40.284893,-109.9369981,24708m"),
            (40.284893, -109.9369981, 24708.0)
        )

    def test_degrees_w(self):
        self.assertEqual(
            clean_coords("60°N, 73°W"),
            (60.0, -73.0)
        )

    def test_degrees_s(self):
        self.assertEqual(
            clean_coords("60°S, 73°E"),
            (-60.0, 73.0)
        )

    def test_deg_min_sec(self):
        self.assertEqual(
            clean_coords("29°17′35″N 76°6′51″E"),
            (round(29 + (17 / 60) + (35 / 60 / 60), 5),
             round(76 + (6 / 60) + (51 / 60 / 60), 5))
        )
        # ^ round to 5 since the detected precision of seconds should be 5
        #   (since 1 second is .0002 repeating 7 degrees)

    def test_deg_min(self):
        self.assertEqual(
            clean_coords("29°17′N 76°6′E"),
            (round(29 + (17 / 60), 3),
             round(76 + (6 / 60), 3))
        )
        # ^ round to 3 since the detected precision of minutes should be 3
        #   (since 1 minute is .01 repeating 6 degrees)

    def test_deg_min_sec_slash(self):
        self.assertEqual(
            clean_coords("25 39' 22.42\" S / 30 17' 03.25\" E", digits=6),
            (-25.656228, 30.284236)
            # from <https://www.rapidtables.com/convert/number/
            #   degrees-minutes-seconds-to-degrees.html>
        )

    def test_precision(self):
        self.assertEqual(get_precision("F"), 0)
        self.assertEqual(get_precision("1"), 0)
        self.assertEqual(get_precision("10"), 0)
        self.assertEqual(get_precision("10."), 0)
        self.assertEqual(get_precision("10.1"), 1)
        self.assertEqual(get_precision("10.10"), 2)
        self.assertEqual(get_precision("10.101"), 3)
        self.assertEqual(get_precision("10.100"), 3)


if __name__ == "__main__":
    unittest.main()
