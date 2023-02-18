from Messages.ACK import ACK
from Messages.CompoundACK import CompoundACK
from Messages.ReceiverAbort import ReceiverAbort
from test.Messages.test_ACK import TestACK
from utils.casting import bin_to_hex


class TestReceiverAbort(TestACK):

    def test_is_receiver_abort(self):
        b = '0001001111001000000000000000000000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        ack = ACK.from_hex(as_hex)
        abort = ReceiverAbort(ack.HEADER)
        self.assertFalse(abort.is_compound_ack())

        b = '0000001110001101110011111111001000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        c_ack = CompoundACK.from_hex(as_hex)
        abort = ReceiverAbort(c_ack.HEADER)
        self.assertTrue(abort.is_receiver_abort())

    def test_to_hex(self):
        b = '0000001110001101110011111111001000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        c_ack = CompoundACK.from_hex(as_hex)
        abort = ReceiverAbort(c_ack.HEADER)

        self.assertEqual('1fff000000000000', abort.to_hex())

    def test_is_compound_ack(self):
        b = '0000001110001101110011111111001000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        c_ack = CompoundACK.from_hex(as_hex)
        abort = ReceiverAbort(c_ack.HEADER)

        self.assertFalse(abort.is_compound_ack())

    def test_is_complete(self):
        b = '0000001110001101110011111111001000000000000000000000000000000000'
        as_hex = bin_to_hex(b)
        c_ack = CompoundACK.from_hex(as_hex)
        abort = ReceiverAbort(c_ack.HEADER)

        self.assertFalse(abort.is_complete())
