from unittest import TestCase

from Entities.Rule import Rule
from Entities.SigfoxProfile import SigfoxProfile
from config import schc


class TestRule(TestCase):

    def test_init(self):
        rule_0 = Rule(0, 0)
        profile = SigfoxProfile("UPLINK", schc.FR_MODE, rule_0)

        expected = {
            '110': 0,
            '101': 1,
            '100': 2,
            '011': 3,
            '010': 4,
            '001': 5,
            '000': 6
        }

        self.assertEqual(expected, profile.FCN_DICT)

        rule_0 = Rule(0, 1)
        profile = SigfoxProfile("UPLINK", schc.FR_MODE, rule_0)

        expected = {
            '1011': 0,
            '1010': 1,
            '1001': 2,
            '1000': 3,
            '0111': 4,
            '0110': 5,
            '0101': 6,
            '0100': 7,
            '0011': 8,
            '0010': 9,
            '0001': 10,
            '0000': 11
        }

        self.assertEqual(expected, profile.FCN_DICT)

        rule_0 = Rule(0, 2)
        profile = SigfoxProfile("UPLINK", schc.FR_MODE, rule_0)

        expected = {
            '00000': 30,
            '00001': 29,
            '00010': 28,
            '00011': 27,
            '00100': 26,
            '00101': 25,
            '00110': 24,
            '00111': 23,
            '01000': 22,
            '01001': 21,
            '01010': 20,
            '01011': 19,
            '01100': 18,
            '01101': 17,
            '01110': 16,
            '01111': 15,
            '10000': 14,
            '10001': 13,
            '10010': 12,
            '10011': 11,
            '10100': 10,
            '10101': 9,
            '10110': 8,
            '10111': 7,
            '11000': 6,
            '11001': 5,
            '11010': 4,
            '11011': 3,
            '11100': 2,
            '11101': 1,
            '11110': 0
        }

        self.assertEqual(expected, profile.FCN_DICT)
