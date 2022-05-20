import json
import os
import shutil
from unittest import TestCase

from Entities.Rule import Rule
from Entities.SCHCReceiver import SCHCReceiver
from Entities.SigfoxProfile import SigfoxProfile
from Messages.CompoundACK import CompoundACK
from Messages.Fragment import Fragment
from Messages.FragmentHeader import FragmentHeader
from Messages.ReceiverAbort import ReceiverAbort
from Messages.SenderAbort import SenderAbort
from db.LocalStorage import LocalStorage


class TestSCHCReceiver(TestCase):
    PATH = "debug/testSCHCReceiver"

    @classmethod
    def setUpClass(cls) -> None:
        if os.path.exists(cls.PATH):
            shutil.rmtree(cls.PATH)
        os.makedirs(cls.PATH)
        with open(f"{cls.PATH}/STORAGE.json", 'w') as j:
            j.write(json.dumps({}))

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(f"{cls.PATH}/STORAGE.json"):
            os.remove(f"{cls.PATH}/STORAGE.json")

        if os.path.exists(cls.PATH):
            shutil.rmtree(cls.PATH)

    def test_init(self):
        storage = LocalStorage()
        rule = Rule(0, 0)
        storage.change_root(f"simulator/1a2b3c/rule_{rule.ID}")
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule)
        receiver = SCHCReceiver(profile, storage)

        self.assertEqual({
            "simulator": {
                "1a2b3c": {
                    "rule_0": {}
                }
            }
        }, storage.JSON)

        self.assertEqual(storage.JSON, receiver.STORAGE.JSON)
        self.assertEqual({}, receiver.STORAGE.read())

    def test_session_was_aborted(self):
        j = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "ABORT": True
                        }
                    }
                }
            }
        }

        with open(f"{self.PATH}/STORAGE.json", 'w') as f:
            f.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()
        self.assertEqual(j, storage.JSON)

        rule = Rule(0, 0)
        storage.change_root(f"simulator/1a2b3c/rule_{rule.ID}")
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule)
        receiver = SCHCReceiver(profile, storage)

        self.assertTrue(receiver.session_was_aborted())

    def test_inactivity_timer_expired(self):
        j = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "TIMESTAMP": 1652922950
                        }
                    }
                }
            }
        }

        with open(f"{self.PATH}/STORAGE.json", 'w') as f:
            f.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()

        rule = Rule(0, 0)
        storage.change_root(f"simulator/1a2b3c/rule_{rule.ID}")
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule)
        profile.INACTIVITY_TIMEOUT = 10
        receiver = SCHCReceiver(profile, storage)

        self.assertTrue(receiver.inactivity_timer_expired(1652923050))

    def test_generate_receiver_abort(self):
        j = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "TIMESTAMP": 1652922950
                        }
                    }
                }
            }
        }

        with open(f"{self.PATH}/STORAGE.json", 'w') as f:
            f.write(json.dumps(j))

        h = '15888888'
        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()

        rule = Rule(0, 0)
        storage.change_root(f"simulator/1a2b3c/rule_{rule.ID}")
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule)
        profile.INACTIVITY_TIMEOUT = 10
        receiver = SCHCReceiver(profile, storage)

        abort = receiver.generate_receiver_abort(Fragment.from_hex(h).HEADER)

        self.assertIsInstance(abort, ReceiverAbort)
        self.assertTrue(receiver.STORAGE.exists("state/ABORT"))
        self.assertEqual("1fff000000000000", receiver.STORAGE.read("state/ABORT"))

    def test_fragment_is_requested(self):
        j = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "REQUESTED": {
                                "W0": [0, 1, 2],
                                "W2": [6]}
                        }
                    }
                }
            }
        }

        with open(f"{self.PATH}/STORAGE.json", 'w') as f:
            f.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()

        rule = Rule(0, 0)
        storage.change_root(f"simulator/1a2b3c/rule_{rule.ID}")
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule)
        receiver = SCHCReceiver(profile, storage)

        header = FragmentHeader(profile, '', '00', '110')
        f = Fragment(header, b'\x1a\x2b\x3c\x4d')
        self.assertTrue(receiver.fragment_is_requested(f))

        header = FragmentHeader(profile, '', '00', '101')
        f = Fragment(header, b'\x1a\x2b\x3c\x4d')
        self.assertTrue(receiver.fragment_is_requested(f))

        header = FragmentHeader(profile, '', '00', '100')
        f = Fragment(header, b'\x1a\x2b\x3c\x4d')
        self.assertTrue(receiver.fragment_is_requested(f))
        header = FragmentHeader(profile, '', '10', '000')
        f = Fragment(header, b'\x1a\x2b\x3c\x4d')
        self.assertTrue(receiver.fragment_is_requested(f))

    def test_fragment_is_receivable(self):
        j = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                        }
                    }
                }
            }
        }

        with open(f"{self.PATH}/STORAGE.json", 'w') as f:
            f.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()
        rule = Rule(0, 0)
        storage.change_root(f"simulator/1a2b3c/rule_{rule.ID}")
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule)
        receiver = SCHCReceiver(profile, storage)

        header = FragmentHeader(profile, '', '00', '110')
        f = Fragment(header, b'\x1a\x2b\x3c\x4d')
        all_1 = Fragment(FragmentHeader(profile, '', '11', '111', '001'), b'\x1a\x2b\x3c\x4d')
        complete_ack = CompoundACK(profile, '', ['11'], '1', ['0000000'])
        receiver.STORAGE.write(complete_ack.to_hex(), "state/LAST_ACK")
        receiver.STORAGE.write(all_1.to_hex(), "state/LAST_FRAGMENT")
        receiver.STORAGE.write('0000000', f"state/bitmaps/w{all_1.WINDOW}")

        self.assertTrue(receiver.STORAGE.exists("state/LAST_FRAGMENT"))
        self.assertTrue(receiver.STORAGE.exists("state/LAST_ACK"))
        self.assertTrue(complete_ack.is_complete())
        self.assertTrue(receiver.fragment_is_receivable(f))

        self.assertTrue(receiver.fragment_was_already_received(all_1))
        self.assertTrue(receiver.fragment_is_receivable(all_1))
        receiver.STORAGE.delete("state/bitmaps")
        receiver.STORAGE.delete("state/LAST_ACK")
        receiver.STORAGE.delete("state/LAST_FRAGMENT")
        self.assertFalse(receiver.STORAGE.exists("state/LAST_FRAGMENT"))

        receiver.STORAGE.write('1111111', f"state/bitmaps/w{f.WINDOW}")
        self.assertFalse(receiver.fragment_is_receivable(f))
        receiver.STORAGE.write('0000000', f"state/bitmaps/w{f.WINDOW}")
        self.assertTrue(receiver.fragment_is_receivable(f))

        abort = SenderAbort(f.HEADER)
        receiver.STORAGE.write(abort.to_hex(), "state/LAST_FRAGMENT")

        self.assertTrue(receiver.STORAGE.exists("state/LAST_FRAGMENT"))
        self.assertTrue(receiver.fragment_is_receivable(f))

        requested = {
            "W0": [0, 3, 4]
        }
        last_fragment = Fragment(FragmentHeader(profile, '', '01', '011'), b'\x1a\x2b\x3c\x4d')
        receiver.STORAGE.write(last_fragment.to_hex(), "state/LAST_FRAGMENT")

        receiver.STORAGE.write(requested, "state/REQUESTED")
        self.assertTrue(receiver.STORAGE.exists("state/REQUESTED"))
        self.assertTrue(receiver.fragment_is_requested(f))
        self.assertTrue(receiver.fragment_is_receivable(f))
        unrequested = Fragment(FragmentHeader(profile, '', '00', '101'), b'\x1a\x2b\x3c\x4d')
        self.assertFalse(receiver.fragment_is_receivable(unrequested))

        fragment_of_superior_window = Fragment(FragmentHeader(profile, '', '11', '011'), b'\x1a\x2b\x3c\x4d')
        self.assertTrue(receiver.fragment_is_receivable(fragment_of_superior_window))

        fragment_of_inferior_window = Fragment(FragmentHeader(profile, '', '00', '001'), b'\x1a\x2b\x3c\x4d')
        self.assertFalse(receiver.fragment_is_receivable(fragment_of_inferior_window))

        fragment_of_superior_index = Fragment(FragmentHeader(profile, '', '01', '001'), b'\x1a\x2b\x3c\x4d')
        self.assertTrue(receiver.fragment_is_receivable(fragment_of_superior_index))

        fragment_of_inferior_index = Fragment(FragmentHeader(profile, '', '01', '110'), b'\x1a\x2b\x3c\x4d')
        self.assertFalse(receiver.fragment_is_receivable(fragment_of_inferior_index))

        fragment_of_same_index = Fragment(FragmentHeader(profile, '', '01', '011'), b'\x1a\x2b\x3c\x4d')
        self.assertFalse(receiver.fragment_is_receivable(fragment_of_same_index))

        receiver.STORAGE.write(all_1.to_hex(), "state/LAST_FRAGMENT")
        self.assertTrue(receiver.fragment_is_receivable(all_1))

    def test_start_new_session(self):
        self.fail()

    def test_get_pending_ack(self):
        self.fail()

    def test_update_bitmap(self):
        self.fail()

    def test_fragment_was_already_received(self):
        self.fail()

    def test_generate_compound_ack(self):
        self.fail()

    def test_schc_recv(self):
        self.fail()
