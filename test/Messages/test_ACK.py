from unittest import TestCase

from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import LengthMismatchError
from Messages.ACK import ACK
from utils.casting import bin_to_hex, hex_to_bin


class TestACK(TestCase):

    def test_from_hex(self):
        b = '0001001111001000000000000000000000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        ack = ACK.from_hex(as_hex)

        self.assertEqual(SigfoxProfile.DOWNLINK_MTU, len(hex_to_bin(ack.to_hex())))
        self.assertEqual('000', ack.HEADER.RULE_ID)
        self.assertEqual('', ack.HEADER.DTAG)
        self.assertEqual('10', ack.HEADER.W)
        self.assertEqual('0', ack.HEADER.C)
        self.assertEqual('1111001', ack.BITMAP)
        self.assertEqual('000000000000000000000000000000000000000000000000000', ack.PADDING)

        b = '00010011110010000000000'
        as_hex = bin_to_hex(b)
        with self.assertRaises(LengthMismatchError):
            _ = ACK.from_hex(as_hex)

    def test_to_hex(self):
        b = '0001001111001000000000000000000000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        ack = ACK.from_hex(as_hex)

        self.assertEqual('13c8000000000000', ack.to_hex())

    def test_is_receiver_abort(self):
        b = '0001111111111111000000000000000000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        ack = ACK.from_hex(as_hex)
        self.assertTrue(ack.is_receiver_abort())

        b = '0001110000000000000000000000000000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        ack = ACK.from_hex(as_hex)
        self.assertFalse(ack.is_receiver_abort())

    def test_is_compound_ack(self):
        b = '0000001110001101110011111111001000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        ack = ACK.from_hex(as_hex)
        self.assertTrue(ack.is_compound_ack())

        b = '0001110000000000000000000000000000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        ack = ACK.from_hex(as_hex)
        self.assertFalse(ack.is_compound_ack())

    def test_is_complete(self):
        b = '0001110000000000000000000000000000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        ack = ACK.from_hex(as_hex)
        self.assertTrue(ack.is_complete())
