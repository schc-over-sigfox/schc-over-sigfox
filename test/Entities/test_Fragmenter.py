import json
import os
import shutil
import unittest

from Entities.Fragmenter import Fragmenter
from Entities.Rule import Rule
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import LengthMismatchError
from utils.casting import bin_to_hex, bin_to_bytes
from utils.misc import generate_packet


class TestFragmenter(unittest.TestCase):

    def test_init(self):
        rule_0 = Rule('000')
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule_0)
        _ = Fragmenter(profile, "debug/unittest/sd")

        self.assertTrue(os.path.exists("debug/unittest/sd"))
        self.assertTrue(os.path.exists("debug/unittest/sd/rule_0"))
        self.assertTrue(os.path.exists("debug/unittest/sd/rule_0/fragments"))

        shutil.rmtree("debug/unittest/sd")

    def test_generate_fragment(self):
        rule_0 = Rule('000')
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule_0)
        fragmenter = Fragmenter(profile, "debug/unittest/sd")

        self.assertEqual(0, fragmenter.CURRENT_FRAGMENT_NUMBER)

        fragment = fragmenter.generate_fragment(b'\xde\xad\xca\xfe',
                                                all_1=False)
        self.assertEqual(rule_0.ID, fragment.PROFILE.RULE.ID)
        self.assertEqual('', fragment.HEADER.DTAG)
        self.assertEqual('00', fragment.HEADER.W)
        self.assertEqual('110', fragment.HEADER.FCN)
        self.assertEqual('', fragment.HEADER.RCS)

        with open("debug/unittest/sd/rule_0/fragments/fragment_w0f0", 'r',
                  encoding="utf-8") as f:
            fragment_data = json.load(f)

        self.assertEqual({
            "hex": bin_to_hex("00000110") + "deadcafe",
            "sent": False
        }, fragment_data)

        self.assertEqual(1, fragmenter.CURRENT_FRAGMENT_NUMBER)

        _ = fragmenter.generate_fragment(b'\xde\xad\xca\xfe', all_1=False)
        _ = fragmenter.generate_fragment(b'\xde\xad\xca\xfe', all_1=False)
        _ = fragmenter.generate_fragment(b'\xde\xad\xca\xfe', all_1=False)
        _ = fragmenter.generate_fragment(b'\xde\xad\xca\xfe', all_1=False)
        _ = fragmenter.generate_fragment(b'\xde\xad\xca\xfe', all_1=False)
        all_0 = fragmenter.generate_fragment(b'\xde\xad\xca\xfe', all_1=False)

        self.assertTrue(all_0.is_all_0())
        self.assertEqual('00', fragment.HEADER.W)

        all_1 = fragmenter.generate_fragment(b'\xde\xad\xca\xfe', all_1=True)
        self.assertTrue(all_1.is_all_1())
        self.assertEqual('01', all_1.HEADER.W)
        self.assertEqual('001', all_1.HEADER.RCS)

        eleven_byte = '1' * 88
        with self.assertRaises(LengthMismatchError):
            all_1 = fragmenter.generate_fragment(bin_to_bytes(eleven_byte),
                                                 all_1=True)

    def test_fragment(self):
        randbytes = b'\xf8\xdb\x80\x1b~!\x11?\x87<\xb1\xe3/I\xe2\xf5\x13\xcd\xdb\xdc`4\xe85MU\xbb!FC\xb96\xee:gH:' \
                    b'\t\xbc\xbde\xc2\x18\xce\xe5:"J\x140\xd8=\xc1@S8\x9aJ\xf1\xa1E2\x9d&\xaf\xd8\xc0\\\xc3\xd8T ' \
                    b'\xcaK\x07\xa5\xd9\xab\xfa>\x01e\xbb\xa1v\x9a\xa1\xbe\xfav\xbe\x04T\xee\xae\xa4\xd1|\xd7\x8b' \
                    b'Z;U\xa8LM\x10zY\x04W$}\xf4\xe940\xff\x02\x11\x9a\x89y>\xbe\xea\x83\x190\x1bm\x8d\xae\xcaeV' \
                    b'\x9b\xd9\x1b\xf9*\x03C;NR\x8c\x12\xc6\x87\xb2i~`<uw}\x14\xd9qj\xe7Gx\xee\x80L}\t\x8d\x0cxZt' \
                    b'\xe1e\xb4\xf6\xf3\x85\xa6}\x8eJ\x90\x1c4/\xff\xd5\x18$\x81}\xae\xae{\x1b\xcd#\x18r\n\xf9\x14#_' \
                    b'\x87/.\xa2^\x06\xce\xbf_\x84\x13P\xb8i\xe7\x82KK\x0e\x8eH\xdf\x90\xa5i\xf0\x97w\x87>\xf8\xa1Sj' \
                    b'\x88\xe1\xaa\x07\x87\xf1X\xdak\x85\x1fMw&\x84\x08q(Q\xf3\xa1\xfe\n\xb6e\xdc\xf9\x9e\xebq}|\x9e' \
                    b'\x0e\x98\x81\xca\xaf\xf1\x07B\x83\x85\x8d4@v\x84\x87VV\x11\xb2\xb5\xc9p\xc9\xe5'

        rule_0 = Rule('000')
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule_0)
        fragmenter = Fragmenter(profile, "debug/unittest/sd")
        fragments = fragmenter.fragment(randbytes)

        payload_max_length = (
                                         profile.UPLINK_MTU - profile.RULE.HEADER_LENGTH) // 8
        number_of_fragments = -(len(randbytes) // -payload_max_length)

        self.assertTrue(number_of_fragments, len(fragments))

        for i in range(number_of_fragments):
            if i % 7 == 6 and not i == len(fragments) - 1:
                self.assertTrue(fragments[i].is_all_0())
                self.assertFalse(fragments[i].is_all_1())
            elif i == len(fragments) - 1:
                self.assertFalse(fragments[i].is_all_0())
                self.assertTrue(fragments[i].is_all_1())
            else:
                self.assertFalse(fragments[i].is_all_0())
                self.assertFalse(fragments[i].is_all_1())

        multiple_eleven = b'-\xf2}\x1d\x01\xefg\xe7+\xb3\x16\x12\xedf\xdf^\xe65\xcd\x144f'
        fragmenter = Fragmenter(profile, "debug/unittest/sd")
        fragments = fragmenter.fragment(multiple_eleven)

        payload_max_length = (
                                     profile.UPLINK_MTU - profile.RULE.HEADER_LENGTH) // 8
        number_of_fragments = -(
                len(multiple_eleven) // -payload_max_length) + 1

        self.assertEqual(22, len(multiple_eleven))
        self.assertEqual(3, number_of_fragments)
        self.assertEqual(len(fragments), number_of_fragments)
        self.assertTrue(fragments[-1].is_all_1())

        for i in range(number_of_fragments):
            if i == len(fragments) - 1:
                self.assertEqual(0, len(fragments[i].PAYLOAD))
            else:
                self.assertEqual(11, len(fragments[i].PAYLOAD))

        eleven = b'01234567890'
        fragmenter = Fragmenter(profile, "debug/unittest/sd")
        fragments = fragmenter.fragment(eleven)

        payload_max_length = (
                                     profile.UPLINK_MTU - profile.RULE.HEADER_LENGTH) // 8
        number_of_fragments = -(len(multiple_eleven) // -payload_max_length)

        self.assertEqual(2, number_of_fragments)
        self.assertTrue(fragments[-1].is_all_1())
        self.assertFalse(fragments[-1].is_sender_abort())

        long_packet = generate_packet(308)
        fragmenter = Fragmenter(profile, "debug/unittest/sd")
        with self.assertRaises(LengthMismatchError):
            _ = fragmenter.fragment(long_packet)

    def test_clear_fragment_directory(self):
        packet = b'-\xf2}\x1d\x01\xefg\xe7+\xb3\x16\x12\xedf\xdf^\xe65\xcd\x144f'
        rule_0 = Rule('000')
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule_0)
        fragmenter = Fragmenter(profile, "debug/unittest/sd")
        _ = fragmenter.fragment(packet)

        self.assertTrue(fragmenter.STORAGE.list_files("fragments") != [])
        fragmenter.clear_fragment_directory()
        self.assertTrue(fragmenter.STORAGE.list_files("fragments") == [])
