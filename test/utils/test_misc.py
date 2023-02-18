import os
import unittest

from utils.misc import zfill, zpad, replace_char, find, is_monochar, \
    section_string, generate_packet, invert_dict, \
    round_to_next_multiple


class TestMisc(unittest.TestCase):

    def test_zfill(self):
        s = "test"
        z = zfill(s, 9)

        self.assertEqual("00000test", z)

        w = zfill(s, 2)
        self.assertEqual(s, w)

    def test_zpad(self):
        s = "test"
        z = zpad(s, 9)

        self.assertEqual("test00000", z)

        w = zpad(s, 2)
        self.assertEqual(s, w)

    def test_replace_char(self):
        s = "1001111"
        z = replace_char(s, 2, '1')

        self.assertEqual("1011111", z)

        s = "1001111"
        z = replace_char(s, 10, '1')

        self.assertEqual(s + '1', z)

    def test_find(self):
        s = "1001011"
        o = find(s, '1')

        self.assertEqual([0, 3, 5, 6], o)

        s = "0000000"
        o = find(s, '1')

        self.assertEqual([], o)

    def test_is_monochar(self):
        s = "1111111"

        self.assertTrue(is_monochar(s))
        self.assertTrue(is_monochar(s), '1')
        self.assertFalse(is_monochar(s, '0'))

        s = ''

        self.assertFalse(is_monochar(s))

    def test_section_string(self):
        s = "AAAABBCCCDDDDDD"
        idx = [0, 4, 6, 9]

        sections = section_string(s, idx)

        self.assertEqual(["AAAA", "BB", "CCC", "DDDDDD"], sections)

    def test_generate_packet(self):
        s = generate_packet(40)

        self.assertEqual(40, len(s))

        _ = generate_packet(1000, 'debug/packet')

        with open("debug/packet", 'r', encoding="utf-8") as f:
            p = f.read()

        self.assertEqual(1000, len(p))

        os.remove('debug/packet')

    def test_invert_dict(self):
        d = {
            "a": 1,
            "b": 2,
            "c": 3
        }

        b = invert_dict(d)

        self.assertEqual({
            1: 'a',
            2: 'b',
            3: 'c'
        }, b)

        with self.assertRaises(ValueError):
            d = {
                "a": 1,
                "b": 2,
                "c": 2
            }

            b = invert_dict(d)

    def test_next_multiple(self):
        self.assertEqual(14, round_to_next_multiple(8, 7))
        self.assertEqual(14, round_to_next_multiple(14, 7))
        self.assertEqual(21, round_to_next_multiple(15, 7))
        self.assertEqual(0, round_to_next_multiple(0, 7))
        self.assertEqual(-14, round_to_next_multiple(-20, 7))
