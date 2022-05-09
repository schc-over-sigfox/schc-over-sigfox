from Entities.SigfoxProfile import SigfoxProfile
from Messages.CompoundACK import CompoundACK
from test.Messages.test_ACK import TestACK
from utils.casting import bin_to_hex, hex_to_bin


class TestCompoundACK(TestACK):

    def test_from_hex(self):
        b = '0000001110001101110011111111001000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        ack = CompoundACK.from_hex(as_hex)

        self.assertEqual(SigfoxProfile.DOWNLINK_MTU, len(hex_to_bin(ack.to_hex())))
        self.assertEqual('000', ack.HEADER.RULE_ID)
        self.assertEqual('', ack.HEADER.DTAG)
        self.assertEqual('00', ack.HEADER.W)
        self.assertEqual('0', ack.HEADER.C)
        self.assertEqual('1110001', ack.BITMAP)

        self.assertEqual(
            [('00', '1110001'), ('10', '1110011'), ('11', '1111001')], ack.TUPLES
        )

        self.assertEqual('101110011111111001000000000000000000000000000000000', ack.PADDING)

    def test_to_hex(self):
        b = '0000001110001101110011111111001000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        ack = CompoundACK.from_hex(as_hex)
        self.assertEqual('038dcff200000000', ack.to_hex())

    def test_is_receiver_abort(self):
        b = '0000001110001101110011111111001000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        ack = CompoundACK.from_hex(as_hex)
        self.assertFalse(ack.is_receiver_abort())

    def test_is_compound_ack(self):
        b = '0000001110001101110011111111001000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        ack = CompoundACK.from_hex(as_hex)
        self.assertTrue(ack.is_compound_ack())
