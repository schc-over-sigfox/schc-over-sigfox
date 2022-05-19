import json
import os
import shutil
from unittest import TestCase

from Entities.Rule import Rule
from Entities.SCHCReceiver import SCHCReceiver
from Entities.SigfoxProfile import SigfoxProfile
from Messages.Fragment import Fragment
from Messages.ReceiverAbort import ReceiverAbort
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
        h = '15888888'
        storage = LocalStorage()
        rule = Rule.from_hex(h)
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

        h = '15888888'
        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()
        self.assertEqual(j, storage.JSON)

        rule = Rule.from_hex(h)
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

        h = '15888888'
        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()

        rule = Rule.from_hex(h)
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

        rule = Rule.from_hex(h)
        storage.change_root(f"simulator/1a2b3c/rule_{rule.ID}")
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule)
        profile.INACTIVITY_TIMEOUT = 10
        receiver = SCHCReceiver(profile, storage)

        abort = receiver.generate_receiver_abort(Fragment.from_hex(h).HEADER)

        self.assertIsInstance(abort, ReceiverAbort)
        self.assertTrue(receiver.STORAGE.exists("state/ABORT"))
        self.assertEqual("1fff000000000000", receiver.STORAGE.read("state/ABORT"))

    def test_fragment_was_requested(self):
        self.fail()

    def test_fragment_is_receivable(self):
        self.fail()

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
