import json
import os
from unittest import TestCase

from Entities.exceptions import BadProfileError
from Messages.Fragment import Fragment
from utils.casting import bin_to_hex, bytes_to_bin


class TestFragment(TestCase):

    def test_from_hex(self):
        b = '00010101100010001000100010001000'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)

        self.assertEqual('000', fragment.HEADER.RULE_ID)
        self.assertEqual('', fragment.HEADER.DTAG)
        self.assertEqual('10', fragment.HEADER.W)
        self.assertEqual('101', fragment.HEADER.FCN)
        self.assertEqual('100010001000100010001000', bytes_to_bin(fragment.PAYLOAD))

        b = '00010111100010001000100010001000'
        h = bin_to_hex(b)
        with self.assertRaises(BadProfileError):
            fragment = Fragment.from_hex(h)

        b = '00010111100000000100010001000100'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)
        self.assertEqual('000', fragment.HEADER.RULE_ID)
        self.assertEqual('', fragment.HEADER.DTAG)
        self.assertEqual('10', fragment.HEADER.W)
        self.assertEqual('111', fragment.HEADER.FCN)
        self.assertEqual('100', fragment.HEADER.RCS)
        self.assertEqual('0100010001000100', bytes_to_bin(fragment.PAYLOAD))

    def test_from_file(self):
        fragment_data = {
            "hex": "15888888",
            "sent": False
        }

        with open("debug/fragment", 'w') as f:
            json.dump(fragment_data, f)

        fragment = Fragment.from_file("debug/fragment")
        self.assertEqual('000', fragment.HEADER.RULE_ID)
        self.assertEqual('', fragment.HEADER.DTAG)
        self.assertEqual('10', fragment.HEADER.W)
        self.assertEqual('101', fragment.HEADER.FCN)
        self.assertEqual('100010001000100010001000', bytes_to_bin(fragment.PAYLOAD))

        os.remove("debug/fragment")

    def test_to_bytes(self):
        b = '00010111100000000100010001000100'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)

        self.assertEqual(b'\x17\x80DD', fragment.to_bytes())

    def test_to_hex(self):
        b = '00010101100010001000100010001000'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)

        self.assertEqual("15888888", fragment.to_hex())

    def test_is_all_1(self):
        b = '00010111100000000100010001000100'
        h = bin_to_hex(b)
        all_1 = Fragment.from_hex(h)

        self.assertTrue(all_1.is_all_1())

        b = '00010010100000000100010001000100'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)

        self.assertFalse(fragment.is_all_1())

    def test_is_all_0(self):
        b = '00010000100000000100010001000100'
        h = bin_to_hex(b)
        all_0 = Fragment.from_hex(h)

        self.assertTrue(all_0.is_all_0())

        b = '00010101100000000100010001000100'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)

        self.assertFalse(fragment.is_all_0())

    def test_expects_ack(self):
        b = '00010000100000000100010001000100'
        h = bin_to_hex(b)
        all_0 = Fragment.from_hex(h)
        self.assertTrue(all_0.expects_ack())

        b = '00010111100000000100010001000100'
        h = bin_to_hex(b)
        all_1 = Fragment.from_hex(h)
        self.assertTrue(all_1.expects_ack())

        b = '00010101100000000100010001000100'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)
        self.assertFalse(fragment.expects_ack())

    def test_is_sender_abort(self):
        b = '00011111'
        h = bin_to_hex(b)
        sender_abort = Fragment.from_hex(h)
        self.assertTrue(sender_abort.is_sender_abort())

        b = '00011111100000000100010001000100'
        h = bin_to_hex(b)
        all_1 = Fragment.from_hex(h)
        self.assertFalse(all_1.is_sender_abort())
