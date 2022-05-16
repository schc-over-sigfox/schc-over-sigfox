import json
import shutil
from unittest import TestCase

from Entities.Rule import Rule
from Entities.SCHCSender import SCHCSender
from Entities.SigfoxProfile import SigfoxProfile
from Messages.Fragment import Fragment
from utils.casting import bin_to_hex

PORT = 1313


class TestSCHCSender(TestCase):

    def test_send(self):
        rule = Rule(0, 0)
        profile = SigfoxProfile(direction="UPLINK", mode="ACK ON ERROR", rule=rule)
        sender = SCHCSender(profile)
        sender.SOCKET.ENDPOINT = f'http://127.0.0.1:{PORT}/test'

        self.assertEqual(0, sender.SENT)
        self.assertEqual(0, sender.SOCKET.SEQNUM)
        self.assertEqual('', sender.LOGGER.BEHAVIOR)

        b = '00010110100010001000100010001000'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)

        with open("debug/sd/rule_0/fragments/fragment_w2f0", 'w') as f:
            f.write(json.dumps({"hex": fragment.to_hex(), "sent": False}))

        sender.send(fragment)

        self.assertEqual(1, sender.SENT)
        self.assertEqual(1, sender.SOCKET.SEQNUM)
        self.assertEqual('W2F0', sender.LOGGER.BEHAVIOR)

        sender.LOSS_RATE = 100

        b = '00010101100010001000100010001000'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)

        with open(f"debug/sd/rule_0/fragments/fragment_{fragment.get_indices()}", 'w') as f:
            f.write(json.dumps({"hex": fragment.to_hex(), "sent": False}))

        sender.send(fragment)

        self.assertEqual(1, sender.SENT)
        self.assertEqual(2, sender.SOCKET.SEQNUM)
        self.assertEqual('W2F0', sender.LOGGER.BEHAVIOR)

        sender.LOSS_RATE = 0
        sender.LOSS_MASK = {
            "fragment": {
                "2": "0010000"
            }
        }

        b = '00010100100010001000100010001000'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)

        with open("debug/sd/rule_0/fragments/fragment_w2f2", 'w') as f:
            f.write(json.dumps({"hex": fragment.to_hex(), "sent": False}))

        sender.send(fragment)

        self.assertEqual(1, sender.SENT)
        self.assertEqual(3, sender.SOCKET.SEQNUM)
        self.assertEqual('W2F0', sender.LOGGER.BEHAVIOR)
        self.assertEqual({
            "fragment": {
                "2": "0000000"
            }
        }, sender.LOSS_MASK)

        shutil.rmtree("debug/sd")

    def test_recv(self):
        self.fail()

    def test_schc_send(self):
        self.fail()

    def test_start_session(self):
        self.fail()
