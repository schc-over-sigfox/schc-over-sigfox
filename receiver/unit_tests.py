import unittest

from Entities.Fragmenter import Fragmenter
from Entities.SigfoxProfile import SigfoxProfile
from Messages.ACK import ACK
from Messages.ACKHeader import ACKHeader
from Messages.CompoundACK import CompoundACK
from Messages.Fragment import Fragment
from Messages.FragmentHeader import FragmentHeader
from Messages.ReceiverAbort import ReceiverAbort
from Messages.SenderAbort import SenderAbort
from schc_utils import bitstring_to_bytes, is_monochar


class TestFragmentHeader(unittest.TestCase):
    def test_to_string(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        rule_id = "0" * profile.RULE_ID_SIZE
        dtag = "0" * profile.T
        w = "0" * profile.M
        fcn = "0" * profile.N
        header = FragmentHeader(profile, rule_id, dtag, w, fcn)
        s = header.to_string()

        self.assertEqual(s, "00000000")

    def test_to_bytes(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        rule_id = "0" * profile.RULE_ID_SIZE
        dtag = "0" * profile.T
        w = "0" * profile.M
        fcn = "1" * profile.N
        header = FragmentHeader(profile, rule_id, dtag, w, fcn)
        b = header.to_bytes()
        self.assertEqual(b, b"\x07")


class TestACKHeader(unittest.TestCase):
    def test_to_string(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        rule_id = "0" * profile.RULE_ID_SIZE
        dtag = "0" * profile.T
        w = "0" * profile.M
        c = "0"
        header = ACKHeader(profile, rule_id, dtag, w, c)
        s = header.to_string()

        self.assertEqual(s, "000000")


class TestFragment(unittest.TestCase):
    def test_is_all_0(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        rule_id = "0" * profile.RULE_ID_SIZE
        dtag = "0" * profile.T
        w = "0" * profile.M
        fcn = "0" * profile.N
        header = bitstring_to_bytes(rule_id + dtag + w + fcn)
        payload = bytearray.fromhex("3131313231333134313531")
        fragment = Fragment(profile, [header, payload])

        self.assertTrue(fragment.is_all_0())

    def test_is_all_1(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        rule_id = "0" * profile.RULE_ID_SIZE
        dtag = "0" * profile.T
        w = "0" * profile.M
        fcn = "1" * profile.N
        header = bitstring_to_bytes(rule_id + dtag + w + fcn)
        payload = bytearray.fromhex("3131313231333134313531")
        fragment = Fragment(profile, [header, payload])

        self.assertTrue(fragment.is_all_1())


class TestAck(unittest.TestCase):
    def test_from_hex(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        h = "0f08000000000000"
        ack = ACK.parse_from_hex(profile, h)
        self.assertEqual(ack.to_string(), "0000111100001000000000000000000000000000000000000000000000000000")
        self.assertEqual(ack.HEADER.RULE_ID, "000")
        self.assertEqual(ack.HEADER.DTAG, "")
        self.assertEqual(ack.HEADER.W, "01")
        self.assertEqual(ack.HEADER.C, "1")
        self.assertEqual(ack.BITMAP, "1100001")
        self.assertTrue(is_monochar(ack.PADDING) and ack.PADDING[0] == '0')


class TestSenderAbort(unittest.TestCase):
    def test_init(self):
        hex_data = "053131313231333134313531"
        header = bytes.fromhex(hex_data[:2])
        payload = bytearray.fromhex(hex_data[2:])
        data = [header, payload]
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        fragment = Fragment(profile, data)
        abort = SenderAbort(profile, fragment.HEADER)

        self.assertEqual(type(abort.PROFILE), SigfoxProfile)
        self.assertEqual(abort.HEADER.RULE_ID, fragment.HEADER.RULE_ID)
        self.assertEqual(abort.HEADER.DTAG, fragment.HEADER.DTAG)
        self.assertEqual(abort.HEADER.W, fragment.HEADER.W)
        self.assertTrue(abort.HEADER.FCN[0] == '1' and all(abort.HEADER.FCN),
                        msg=f"{abort.HEADER.FCN[0] == '1'} and {all(abort.HEADER.FCN)}")
        self.assertTrue(abort.PAYLOAD.decode()[0] == '0' and all(abort.PAYLOAD.decode()),
                        msg=f"{abort.PAYLOAD[0] == '0'} and {all(abort.PAYLOAD)}")
        self.assertFalse(abort.is_all_1())
        self.assertTrue(abort.is_sender_abort())

        hex_data = "1f353235"
        header = bytes.fromhex(hex_data[:2])
        payload = bytearray.fromhex(hex_data[2:])
        data = [header, payload]
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        fragment = Fragment(profile, data)

        self.assertFalse(fragment.is_sender_abort())

        hex_string = "1f3030303030303030303030"
        fragment_sent = Fragment.from_hex(SigfoxProfile("UPLINK", "ACK ON ERROR", 1), hex_string)
        abort = SenderAbort(fragment_sent.PROFILE, fragment_sent.HEADER)

        self.assertTrue(abort.is_sender_abort())


class TestReceiverAbort(unittest.TestCase):
    def test_init(self):
        hex_data = "053131313231333134313531"
        header = bytes.fromhex(hex_data[:2])
        payload = bytearray.fromhex(hex_data[2:])
        data = [header, payload]
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        fragment = Fragment(profile, data)
        abort = ReceiverAbort(profile, fragment.HEADER)

        self.assertEqual(type(abort.PROFILE), SigfoxProfile)
        self.assertEqual(abort.HEADER.RULE_ID, fragment.HEADER.RULE_ID)
        self.assertEqual(abort.HEADER.DTAG, fragment.HEADER.DTAG)
        self.assertEqual(abort.HEADER.W, fragment.HEADER.W)
        self.assertEqual(len(abort.to_string()), 64)
        self.assertTrue(issubclass(type(abort), ACK))
        self.assertTrue(abort.is_receiver_abort())

    def test_receive(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        ack = "0000111111111111100000000000000000000000000000000000000000000000"
        ack_index_dtag = profile.RULE_ID_SIZE
        ack_index_w = ack_index_dtag + profile.T
        ack_index_c = ack_index_w + profile.M
        ack_index_bitmap = ack_index_c + 1
        ack_index_padding = ack_index_bitmap + profile.BITMAP_SIZE

        received_ack = ACK(profile,
                           rule_id=ack[:ack_index_dtag],
                           dtag=ack[ack_index_dtag:ack_index_w],
                           w=ack[ack_index_w:ack_index_c],
                           c=ack[ack_index_c],
                           bitmap=ack[ack_index_bitmap:ack_index_padding],
                           padding=ack[ack_index_padding:])

        self.assertTrue(received_ack.is_receiver_abort())

    def test_from_hex(self):
        ack = ACK.parse_from_hex(SigfoxProfile("UPLINK", "ACK ON ERROR", 1), "07ff800000000000")
        self.assertEqual(ack.to_string(),
                         "0000011111111111100000000000000000000000000000000000000000000000")
        self.assertEqual(ack.HEADER.RULE_ID, "000")
        self.assertEqual(ack.HEADER.DTAG, "")
        self.assertEqual(ack.HEADER.W, "00")
        self.assertEqual(ack.HEADER.C, "1")
        self.assertTrue(ack.is_receiver_abort())


class TestCompoundACK(unittest.TestCase):
    def test_inheritance(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        h = "0f08000000000000"
        ack = CompoundACK.parse_from_hex(profile, h)
        self.assertEqual(ack.to_string(), "0000111100001000000000000000000000000000000000000000000000000000")
        self.assertIsInstance(ack, ACK)
        self.assertIsInstance(ack, CompoundACK)
        self.assertFalse(ack.is_compound_ack())

    def test_example(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        s = "00000011110110111110110000000000000000000000000000000000000000000"
        ack = CompoundACK.parse_from_string(profile, s)

        self.assertEqual(ack.TUPLES, [("00", "1111011"), ("01", "1111011")])


class TestFragmenter(unittest.TestCase):
    def test_300B(self):

        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        with open("testing/Packets/300", 'r') as f:
            packet = f.read()
        fragmenter = Fragmenter(profile, packet)
        fragments = fragmenter.fragment()

        self.assertEqual(len(fragments), profile.MAX_FRAGMENT_NUMBER)

        i = 0
        for fragment in fragments:
            self.assertEqual(fragment.NUMBER, i)
            i = (i + 1) % profile.WINDOW_SIZE


if __name__ == '__main__':
    unittest.main()
