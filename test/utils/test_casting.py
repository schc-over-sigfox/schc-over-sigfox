import unittest

from utils.casting import bin_to_int, bin_to_hex, bin_to_bytes, bin_to_string, \
    hex_to_bin, hex_to_bytes, bytes_to_bin, \
    bytes_to_hex, int_to_bin, int_to_hex, int_to_bytes, string_to_bin


class TestCasting(unittest.TestCase):

    def test_bin_to_int(self):
        b = '11010010'
        self.assertEqual(210, bin_to_int(b))

    def test_bin_to_hex(self):
        b = '11010010'
        self.assertEqual('d2', bin_to_hex(b))
        b = '000000011010010'
        self.assertEqual('0d2', bin_to_hex(b))

    def test_bin_to_bytes(self):
        b = '11010010'
        self.assertEqual(b'\xd2', bin_to_bytes(b))

    def test_bin_to_string(self):
        b = '01110100011001010111001101110100'
        self.assertEqual('test', bin_to_string(b, 'utf-8'))
        self.assertEqual('test', bin_to_string(b, 'ascii'))

    def test_hex_to_bin(self):
        h = 'cafe'
        self.assertEqual('1100101011111110', hex_to_bin(h))
        self.assertEqual('000000001100101011111110', hex_to_bin(h, 24))

    def test_hex_to_bytes(self):
        h = 'aaacadcc'
        self.assertEqual(b'\xaa\xac\xad\xcc', hex_to_bytes(h))

    def test_bytes_to_bin(self):
        by = b'\xd2'
        self.assertEqual('11010010', bytes_to_bin(by))
        by = b''
        self.assertEqual('', bytes_to_bin(by))

    def test_bytes_to_hex(self):
        by = b'\xaa\xac\xad\xcc'
        self.assertEqual('aaacadcc', bytes_to_hex(by))

    def test_int_to_bin(self):
        n = 210
        self.assertEqual('11010010', int_to_bin(n))
        self.assertEqual('000011010010', int_to_bin(n, 12))

    def test_int_to_hex(self):
        n = 210
        self.assertEqual('d2', int_to_hex(n))

    def test_int_to_bytes(self):
        n = 210
        self.assertEqual(b'\xd2', int_to_bytes(n))

    def test_string_to_bin(self):
        s = 'test'
        self.assertEqual('01110100011001010111001101110100', string_to_bin(s))
