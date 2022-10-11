import json
import shutil
import unittest
from unittest import TestCase

from Entities.Fragmenter import Fragmenter
from Entities.Rule import Rule
from Entities.SCHCSender import SCHCSender
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import SCHCTimeoutError
from Messages.Fragment import Fragment
from utils.casting import bin_to_hex

PORT = 1313


@unittest.skip
class TestSCHCSender(TestCase):

    def test_send(self):
        rule = Rule("000")
        profile = SigfoxProfile(direction="UPLINK", mode="ACK ON ERROR", rule=rule)
        sender = SCHCSender(profile)
        sender.SOCKET.ENDPOINT = f'http://127.0.0.1:{PORT}/test'

        self.assertEqual(0, sender.LOGGER.SENT)
        self.assertEqual(0, sender.SOCKET.SEQNUM)
        self.assertEqual('', sender.LOGGER.SEQUENCE)

        b = '00010110100010001000100010001000'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)

        indices = fragment.get_indices()
        with open(f"debug/sd/rule_0/fragments/fragment_w{indices[0]}f{indices[1]}", 'w', encoding="utf-8") as f:
            f.write(json.dumps({"hex": fragment.to_hex(), "sent": False}))

        sender.send(fragment)

        self.assertEqual(1, sender.LOGGER.SENT)
        self.assertEqual(1, sender.SOCKET.SEQNUM)
        self.assertEqual('W2F0', sender.LOGGER.SEQUENCE)

        sender.LOSS_RATE = 100

        b = '00010101100010001000100010001000'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)

        indices = fragment.get_indices()
        with open(f"debug/sd/rule_0/fragments/fragment_w{indices[0]}f{indices[1]}", 'w', encoding="utf-8") as f:
            f.write(json.dumps({"hex": fragment.to_hex(), "sent": False}))

        sender.send(fragment)

        self.assertEqual(1, sender.LOGGER.SENT)
        self.assertEqual(2, sender.SOCKET.SEQNUM)
        self.assertEqual('W2F0', sender.LOGGER.SEQUENCE)

        sender.LOSS_RATE = 0
        sender.LOSS_MASK = {
            "fragment": {
                "2": "0010000"
            }
        }

        b = '00010100100010001000100010001000'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)

        indices = fragment.get_indices()
        with open(f"debug/sd/rule_0/fragments/fragment_w{indices[0]}f{indices[1]}", 'w', encoding="utf-8") as f:
            f.write(json.dumps({"hex": fragment.to_hex(), "sent": False}))

        sender.send(fragment)

        self.assertEqual(1, sender.LOGGER.SENT)
        self.assertEqual(3, sender.SOCKET.SEQNUM)
        self.assertEqual('W2F0', sender.LOGGER.SEQUENCE)
        self.assertEqual({
            "fragment": {
                "2": "0000000"
            }
        }, sender.LOSS_MASK)

        shutil.rmtree("debug/sd")

    def test_recv(self):
        rule = Rule("000")
        profile = SigfoxProfile(direction="UPLINK", mode="ACK ON ERROR", rule=rule)
        sender = SCHCSender(profile)
        sender.SOCKET.ENDPOINT = f'http://127.0.0.1:{PORT}/test'

        self.assertEqual(0, sender.LOGGER.SENT)
        self.assertEqual(0, sender.SOCKET.SEQNUM)
        self.assertEqual('', sender.LOGGER.SEQUENCE)

        b = '00011111100000000100010001000100'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)
        self.assertTrue(fragment.is_all_1())

        indices = fragment.get_indices()
        with open(f"debug/sd/rule_0/fragments/fragment_w{indices[0]}f{indices[1]}", 'w', encoding="utf-8") as f:
            f.write(json.dumps({"hex": fragment.to_hex(), "sent": False}))

        sender.SOCKET.set_reception(True)
        sender.send(fragment)
        ack = sender.recv(SigfoxProfile.DOWNLINK_MTU)

        self.assertTrue(ack is not None)
        self.assertEqual('1c00000000000000', ack.to_hex())
        self.assertEqual(1, sender.LOGGER.RECEIVED)
        self.assertTrue(sender.SOCKET.BUFFER.empty())

        with open(f"debug/sd/rule_0/fragments/fragment_w{indices[0]}f{indices[1]}", 'w', encoding="utf-8") as f:
            f.write(json.dumps({"hex": fragment.to_hex(), "sent": False}))

        sender.send(fragment)
        sender.LOSS_RATE = 100

        with self.assertRaises(SCHCTimeoutError):
            ack = sender.recv(SigfoxProfile.DOWNLINK_MTU)
        self.assertTrue(sender.SOCKET.BUFFER.empty())

        sender.LOSS_RATE = 0
        sender.LOSS_MASK = {
            "fragment": {
                "3": "0000000"
            },
            "ack": {
                "3": "10000"
            }
        }

        with open(f"debug/sd/rule_0/fragments/fragment_w{indices[0]}f{indices[1]}", 'w', encoding="utf-8") as f:
            f.write(json.dumps({"hex": fragment.to_hex(), "sent": False}))

        sender.send(fragment)
        with self.assertRaises(SCHCTimeoutError):
            ack = sender.recv(SigfoxProfile.DOWNLINK_MTU)
        self.assertTrue(sender.SOCKET.BUFFER.empty())
        self.assertEqual({
            "fragment": {
                "3": "0000000"
            },
            "ack": {
                "3": "0000"
            }
        }, sender.LOSS_MASK)
        sender.ATTEMPTS += 1

        sender.send(fragment)
        ack = sender.recv(SigfoxProfile.DOWNLINK_MTU)
        self.assertTrue(ack is not None)
        self.assertEqual({
            "fragment": {
                "3": "0000000"
            },
            "ack": {
                "3": "000"
            }
        }, sender.LOSS_MASK)

        shutil.rmtree("debug/sd")

    def test_schc_send(self):
        randbytes = b'\xf8\xdb\x80\x1b~!\x11?\x87<\xb1\xe3/I\xe2\xf5\x13\xcd' \
                    b'\xdb\xdc`4\xe85MU\xbb!FC\xb96\xee:gH:\t\xbc\xbde\xc2' \
                    b'\x18\xce\xe5:"J\x140\xd8=\xc1@S8\x9aJ\xf1\xa1E2\x9d&' \
                    b'\xaf\xd8\xc0\\\xc3\xd8T \xcaK\x07\xa5\xd9\xab\xfa>' \
                    b'\x01e\xbb\xa1v\x9a\xa1\xbe\xfav\xbe\x04T\xee\xae\xa4' \
                    b'\xd1|\xd7\x8bZ;U\xa8LM\x10zY\x04W$}\xf4\xe940\xff\x02' \
                    b'\x11\x9a\x89y>\xbe\xea\x83\x190\x1bm\x8d\xae\xcaeV' \
                    b'\x9b\xd9\x1b\xf9*\x03C;NR\x8c\x12\xc6\x87\xb2i~`<uw}' \
                    b'\x14\xd9qj\xe7Gx\xee\x80L}\t\x8d\x0cxZt\xe1e\xb4\xf6' \
                    b'\xf3\x85\xa6}\x8eJ\x90\x1c4/\xff\xd5\x18$\x81}\xae\xae' \
                    b'{\x1b\xcd#\x18r\n\xf9\x14#_\x87/.\xa2^\x06\xce\xbf_' \
                    b'\x84\x13P\xb8i\xe7\x82KK\x0e\x8eH\xdf\x90\xa5i\xf0\x97' \
                    b'w\x87>\xf8\xa1Sj\x88\xe1\xaa\x07\x87\xf1X\xdak\x85\x1f' \
                    b'Mw&\x84\x08q(Q\xf3\xa1\xfe\n\xb6e\xdc\xf9\x9e\xebq}|' \
                    b'\x9e\x0e\x98\x81\xca\xaf\xf1\x07B\x83\x85\x8d4@v\x84' \
                    b'\x87VV\x11\xb2\xb5\xc9p\xc9\xe5'

        rule_0 = Rule("000")
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule_0)
        profile.SIGFOX_DL_TIMEOUT = 1
        profile.SIGFOX_DL_TIMEOUT = 2
        fragmenter = Fragmenter(profile, "debug/sd")
        fragments = fragmenter.fragment(randbytes)
        sender = SCHCSender(profile)
        sender.SOCKET.ENDPOINT = f'http://127.0.0.1:{PORT}/test'
        sender.LAST_WINDOW = fragments[-1].HEADER.WINDOW_NUMBER

        self.assertEqual(0, sender.CURRENT_FRAGMENT_INDEX)

        windows = [fragments[0:7], fragments[7:14], fragments[14:21], fragments[21:28]]

        for fragment in windows[0][:-1]:
            sender.schc_send(fragment)
            self.assertEqual(60, sender.SOCKET.TIMEOUT)
            self.assertEqual(fragment.NUMBER + 1, sender.CURRENT_FRAGMENT_INDEX)
            self.assertEqual(0, sender.CURRENT_WINDOW_INDEX)

        sender.schc_send(windows[0][-1])
        self.assertEqual(profile.SIGFOX_DL_TIMEOUT, sender.SOCKET.TIMEOUT)
        self.assertEqual(7, sender.CURRENT_FRAGMENT_INDEX)
        self.assertEqual(1, sender.CURRENT_WINDOW_INDEX)

        for fragment in windows[1][:-1]:
            sender.schc_send(fragment)
            self.assertEqual(60, sender.SOCKET.TIMEOUT)
            self.assertEqual(fragment.NUMBER + 1, sender.CURRENT_FRAGMENT_INDEX)
            self.assertEqual(1, sender.CURRENT_WINDOW_INDEX)

        sender.schc_send(windows[1][-1])
        self.assertEqual(profile.SIGFOX_DL_TIMEOUT, sender.SOCKET.TIMEOUT)
        self.assertEqual(14, sender.CURRENT_FRAGMENT_INDEX)
        self.assertEqual(2, sender.CURRENT_WINDOW_INDEX)

        for fragment in windows[2][:-1]:
            sender.schc_send(fragment)
            self.assertEqual(60, sender.SOCKET.TIMEOUT)
            self.assertEqual(fragment.NUMBER + 1, sender.CURRENT_FRAGMENT_INDEX)
            self.assertEqual(2, sender.CURRENT_WINDOW_INDEX)

        sender.schc_send(windows[2][-1])
        self.assertEqual(profile.SIGFOX_DL_TIMEOUT, sender.SOCKET.TIMEOUT)
        self.assertEqual(21, sender.CURRENT_FRAGMENT_INDEX)
        self.assertEqual(3, sender.CURRENT_WINDOW_INDEX)

        for fragment in windows[3][:-1]:
            sender.schc_send(fragment)
            self.assertEqual(60, sender.SOCKET.TIMEOUT)
            self.assertEqual(fragment.NUMBER + 1, sender.CURRENT_FRAGMENT_INDEX)
            self.assertEqual(3, sender.CURRENT_WINDOW_INDEX)

        sender.schc_send(windows[3][-1])
        self.assertEqual(profile.RETRANSMISSION_TIMEOUT, sender.SOCKET.TIMEOUT)
        self.assertEqual(28, sender.CURRENT_FRAGMENT_INDEX)
        self.assertEqual(3, sender.CURRENT_WINDOW_INDEX)
        self.assertTrue(sender.LOGGER.FINISHED)

    def test_start_session(self):
        randbytes = b'\xf8\xdb\x80\x1b~!\x11?\x87<\xb1\xe3/I\xe2\xf5\x13\xcd' \
                    b'\xdb\xdc`4\xe85MU\xbb!FC\xb96\xee:gH:\t\xbc\xbde\xc2' \
                    b'\x18\xce\xe5:"J\x140\xd8=\xc1@S8\x9aJ\xf1\xa1E2\x9d&' \
                    b'\xaf\xd8\xc0\\\xc3\xd8T \xcaK\x07\xa5\xd9\xab\xfa>' \
                    b'\x01e\xbb\xa1v\x9a\xa1\xbe\xfav\xbe\x04T\xee\xae\xa4' \
                    b'\xd1|\xd7\x8bZ;U\xa8LM\x10zY\x04W$}\xf4\xe940\xff\x02' \
                    b'\x11\x9a\x89y>\xbe\xea\x83\x190\x1bm\x8d\xae\xcaeV' \
                    b'\x9b\xd9\x1b\xf9*\x03C;NR\x8c\x12\xc6\x87\xb2i~`<uw}' \
                    b'\x14\xd9qj\xe7Gx\xee\x80L}\t\x8d\x0cxZt\xe1e\xb4\xf6' \
                    b'\xf3\x85\xa6}\x8eJ\x90\x1c4/\xff\xd5\x18$\x81}\xae\xae' \
                    b'{\x1b\xcd#\x18r\n\xf9\x14#_\x87/.\xa2^\x06\xce\xbf_' \
                    b'\x84\x13P\xb8i\xe7\x82KK\x0e\x8eH\xdf\x90\xa5i\xf0\x97' \
                    b'w\x87>\xf8\xa1Sj\x88\xe1\xaa\x07\x87\xf1X\xdak\x85\x1f' \
                    b'Mw&\x84\x08q(Q\xf3\xa1\xfe\n\xb6e\xdc\xf9\x9e\xebq}|' \
                    b'\x9e\x0e\x98\x81\xca\xaf\xf1\x07B\x83\x85\x8d4@v\x84' \
                    b'\x87VV\x11\xb2\xb5\xc9p\xc9\xe5'

        rule_0 = Rule("000")
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule_0)
        profile.SIGFOX_DL_TIMEOUT = 1
        profile.SIGFOX_DL_TIMEOUT = 2
        sender = SCHCSender(profile)
        sender.SOCKET.ENDPOINT = f'http://127.0.0.1:{PORT}/test'
        sender.start_session(randbytes)

        self.assertEqual(28, len(sender.FRAGMENT_LIST))
        self.assertEqual(3, sender.LAST_WINDOW)
