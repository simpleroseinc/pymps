from .context import pymps as ppm

import numpy as np
import unittest
import copy
import os
import json


class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    @classmethod
    def setUpClass(cls):
        '''Called only once'''

        cls.mps = os.path.abspath('tests/data/example.mps')
        cls.mps2 = os.path.abspath('tests/data/example2.mps')
        cls.mps3 = os.path.abspath('tests/data/example3.mps')
        cls.mps4 = os.path.abspath('tests/data/example4.mps')
        cls.mps_errors1 = os.path.abspath('tests/data/bad_example1.mps')
        cls.mps_errors2 = os.path.abspath('tests/data/bad_example2.mps')
        cls.mps_errors3 = os.path.abspath('tests/data/bad_example3.mps')
        cls.mps_errors4 = os.path.abspath('tests/data/bad_example4.mps')
        cls.mps_errors5 = os.path.abspath('tests/data/bad_example5.mps')
        cls.mps_errors6 = os.path.abspath('tests/data/bad_example6.mps')
        cls.mps_errors7 = os.path.abspath('tests/data/bad_example7.mps')
        cls.mps_errors8 = os.path.abspath('tests/data/bad_example8.mps')
        cls.mps_errors9 = os.path.abspath('tests/data/bad_example9.mps')
        expected_no_fill = {
            "NAME": "EXAMPLE",
            "ROWS": {
                "R01": "L",
                "R02": "E",
                "R03": "G",
                "R04": "E",
                "COST": "N"
            },
            "COLUMNS": {
                "R01": {
                    "C01": 30.0,
                    "C02": -10.0,
                    "C03": 50.0
                },
                "R02": {
                    "C01": 5000.0,
                    "C02": 0.0,
                    "C03": -3.0
                },
                "R03": {
                    "C01": 0.2,
                    "C02": 0.1,
                    "C03": 0.0
                },
                "COST": {
                    "C01": 10.0,
                    "C02": 5.0,
                    "C03": 5.5
                },
                "R04": {
                    "C02": 0.2,
                    "C03": 0.3
                }
            },
            "RHS": {
                "R01": 1500.0,
                "R02": 200.0,
                "R03": 12.0,
                "R04": 0.0,
            },
            "BOUNDS": {
                "C01": {
                    "upper": 0.0
                },
                "C02": {
                    "lower": 0.0,
                    "upper": 0.0,
                },
                "C03": {
                    "lower": 0.0,
                }
            },
            "RANGES": {
                "R01": {
                    "lower": 1486.0,
                    "upper": 1500.0
                },
                "R02": {
                    "lower": 200.0,
                    "upper": 214.0
                },
                "R03": {
                    "lower": 12.0,
                    "upper": 26.0
                },
                "R04": {
                    "lower": -14.0,
                    "upper": 0.0
                }
            },
            "ALL_COLUMNS": [
                "C01",
                "C02",
                "C03"
            ],
            "OBJ_ROW": "COST",
            "RHS_id": "B",
            "RANGES_id": 'rhs',
            "BOUNDS_id": "BOUND"
        }
        expected_fill = copy.deepcopy(expected_no_fill)
        expected_fill['COLUMNS']['R04']['C01'] = 0
        expected_fill['RHS']['R04'] = 0
        expected_fill['BOUNDS']['C01']['lower'] = np.NINF
        expected_fill['BOUNDS']['C03']['upper'] = np.Inf
        cls.parsed_mps_fill = expected_fill
        cls.parsed_mps_no_fill = expected_no_fill
        cls.dual = os.path.abspath('tests/data/dual.mps')
        cls.dual2 = os.path.abspath('tests/data/dual2.mps')
        cls.dual3 = os.path.abspath('tests/data/dual3.mps')
        expected_dual = {
            "NAME": "EXAMPLE_DUAL",
            "OBJSENSE": "MAX",
            "OBJNAME": "DL",
            "ROWS": {
                "C01": "L",
                "C02": "L",
                "C03": "E",
                "DL": "N"
            },
            "COLUMNS": {
                "C01": {
                    "R01": -1.0,
                    "R02": 4.0,
                    "R03": 7.0
                },
                "C02": {
                    "R01": 2.0,
                    "R02": -5.0,
                    "R03": -8.0
                },
                "C03": {
                    "R01": -3.0,
                    "R02": 6.0,
                    "R03": 9.0
                },
                "DL": {
                    "R01": -13.0,
                    "R02": 14.0,
                    "R03": 15.0
                }
            },
            "RHS": {
                "C01": 10.0,
                "C02": -11.0,
                "C03": 12.0,
            },
            "BOUNDS": {
                "R01": {
                    "lower": 0
                },
                "R02": {
                    "lower": 0
                },
                "R03": {
                    "lower": np.NINF,
                    "upper": np.Inf
                }
            },
        }
        expected_dual2 = copy.deepcopy(expected_dual)
        expected_dual2['COLUMNS']["DL"] = {
            "R01": 1.0,
            "R02": -27.0,
            "R03": -53.0
        }
        expected_dual2["RHS"]["DL"] = -95.0
        expected_dual2["BOUNDS"]["C02_db"] = {
            "lower": 0
        }
        expected_dual2["COLUMNS"]["C01"]["C02_db"] = 0.0
        expected_dual2["COLUMNS"]["C02"]["C02_db"] = -1.0
        expected_dual2["COLUMNS"]["DL"]["C02_db"] = -3.0
        expected_dual3 = copy.deepcopy(expected_dual2)
        del expected_dual2["COLUMNS"]["C03"]
        del expected_dual2["RHS"]["C03"]
        del expected_dual2["ROWS"]["C03"]
        new_rl = "C01_db"
        expected_dual3['COLUMNS']["DL"] = {
            "R01": -8.0,
            "R02": -6.0,
            "R03": -20.0,
            new_rl: -4.0
        }
        expected_dual3["COLUMNS"]["C01"] = {
            "R01": 1.0,
            "R02": -4.0,
            "R03": -7.0,
            new_rl: -1.0
        }
        expected_dual3["COLUMNS"]["C02"] = {
            "R01": 2.0,
            "R02": -5.0,
            "R03": -8.0,
            new_rl: 0.0
        }
        expected_dual3["RHS"] = {
            "C01": -10.0,
            "C02": -11.0,
            "C03": 12.0,
            "DL": -50.0
        }
        expected_dual3["COLUMNS"]["C03"][new_rl] = 0.0
        expected_dual3["BOUNDS"][new_rl] = {
            "lower": 0
        }
        del expected_dual3["BOUNDS"]["C02_db"]

        cls.parsed_dual = expected_dual
        cls.parsed_dual2 = expected_dual2
        cls.parsed_dual3 = expected_dual3

    def test_make_dual(self):

        # test dual on problem already in standard canonical form
        mps = ppm.parse_mps(self.dual, fill=True)
        dual = ppm.make_dual(mps)
        self.assertDictEqual(dual, self.parsed_dual)

    def test_make_dual2(self):

        # test dual on problem with UP, LO and FX variables
        mps = ppm.parse_mps(self.dual2, fill=True)
        dual = ppm.make_dual(mps)
        self.assertDictEqual(dual, self.parsed_dual2)

    def test_make_dual3(self):

        # test dual on problem with a single LO <= x <= UP variable
        self.maxDiff = None
        mps = ppm.parse_mps(self.dual3, fill=True)
        dual = ppm.make_dual(mps)
        self.assertDictEqual(dual, self.parsed_dual3)

    def test_parsed_as_mps(self):

        self.maxDiff = None
        mps = ppm.parse_mps(self.dual, fill=True)
        dual = ppm.make_dual(mps)
        dual_mps = ppm.parsed_as_mps(dual)

        with open('tests/data/dual_dual.mps', 'r') as fin:
            dat = fin.read()

        self.assertEqual(dual_mps, dat)

    def test_parse_mps_no_fill(self):

        mps = ppm.parse_mps(self.mps, fill=False)
        self.assertDictEqual(mps, self.parsed_mps_no_fill)

    def test_parse_mps_fill(self):

        mps = ppm.parse_mps(self.mps, fill=True)
        self.assertDictEqual(mps['ROWS'], self.parsed_mps_fill['ROWS'])

    def test_parse_mps_bounds(self):

        # test bounds where LO is omitted and UP is either <0 or >0
        mps = ppm.parse_mps(self.mps2, fill=True)
        b_expected = {
            "C01": {
                "lower": 0,
                "upper": 2.0
            },
            "C02": {
                "lower": np.NINF,
                "upper": 0.0,
            },
            "C03": {
                "lower": np.NINF,
                "upper": np.Inf
            }
        }
        rhs_expected = {
            "R01": 1500.0,
            "R02": 200.0,
            "R03": 12.0,
            "R04": 0.0,
        }
        self.assertDictEqual(mps['BOUNDS'], b_expected)
        self.assertDictEqual(mps['RHS'], rhs_expected)

        # test bounds MI & PL
        mps = ppm.parse_mps(self.mps3, fill=True)
        # note: field 4 for MI should be ignored, and the expected value
        # for C01 is a free variable
        expected = {
            "C01": {
                "lower": np.NINF,
                "upper": np.Inf,
            },
            "C02": {
                "lower": 0,
                "upper": np.Inf,
            },
            "C03": {
                "lower": 0,
                "upper": np.Inf
            }
        }
        self.assertDictEqual(mps['BOUNDS'], expected)

        # test funky bounds
        mps = ppm.parse_mps(self.mps4, fill=True)
        expected = {
            "C01": {
                "lower": 0,
                "upper": 2,
            },
            "C02": {
                "lower": 0,
                "upper": np.Inf,
            },
            "C03": {
                "lower": 0,
                "upper": np.Inf
            }
        }
        self.assertDictEqual(mps['BOUNDS'], expected)

    def test_prase_mps_example_with_errors(self):

        # test float value parse fail in ROW
        with self.assertRaises(ValueError) as context:
            mps = ppm.parse_mps(self.mps_errors1)
        self.assertEqual(
            "ROW value must be a float, found: moo",
            str(context.exception)
        )

        # test unknown indicator
        with self.assertRaises(ValueError) as context:
            mps = ppm.parse_mps(self.mps_errors2)
        self.assertEqual(
            "Unknown indicator CATS found.",
            str(context.exception)
        )

        # test float value parse fail in RHS
        with self.assertRaises(ValueError) as context:
            mps = ppm.parse_mps(self.mps_errors3)
        self.assertEqual(
            "RHS value must be a float, found: moo",
            str(context.exception)
        )

        # test bad bound (lower > upper)
        with self.assertRaises(ValueError) as context:
            mps = ppm.parse_mps(self.mps_errors4)
        self.assertEqual(
            "Lower bound is greater than upper bound: lower -> 10.0, upper -> 0.0",
            str(context.exception)
        )

        # test duplicated BOUNDs
        with self.assertRaises(ValueError) as context:
            mps = ppm.parse_mps(self.mps_errors5)
        self.assertEqual(
            "BOUND on COLUMN C03 specified twice!",
            str(context.exception)
        )

        # test missing idicator
        with self.assertRaises(ValueError) as context:
            mps = ppm.parse_mps(self.mps_errors6)
        self.assertEqual(
            "Indicator record 'COLUMNS' is missing!",
            str(context.exception)
        )

        # reference non-existant row
        with self.assertRaises(AssertionError) as context:
            mps = ppm.parse_mps(self.mps_errors7)
        self.assertEqual(
            "COLUMNS makes reference to non-existant ROW(s) {'R05'}!",
            str(context.exception)
        )

        # test missing RHS if RANGE set
        with self.assertRaises(AssertionError) as context:
            mps = ppm.parse_mps(self.mps_errors8)
        self.assertEqual(
            "You must specify a RHS for R04 if setting a RANGE on it.",
            str(context.exception)
        )

        # ambiguous bound
        with self.assertRaises(ValueError) as context:
            mps = ppm.parse_mps(self.mps_errors9)
        self.assertEqual(
            "The BOUND ['UP', '01', '2'] is ambiguous.",
            str(context.exception)
        )


if __name__ == '__main__':
    unittest.main()
