import json
import os
import shutil
import time
from unittest import TestCase

from Entities.Rule import Rule
from Entities.SCHCReceiver import SCHCReceiver
from Entities.exceptions import ReceiverAbortError, LengthMismatchError, \
    SenderAbortError
from Messages.CompoundACK import CompoundACK
from Messages.Fragment import Fragment
from Messages.FragmentHeader import FragmentHeader
from Messages.ReceiverAbort import ReceiverAbort
from Messages.SenderAbort import SenderAbort
from config.schc import UPLINK_MTU, DISABLE_INACTIVITY_TIMEOUT
from db.LocalStorage import LocalStorage


class TestSCHCReceiver(TestCase):
    PATH = "debug/testSCHCReceiver"

    @classmethod
    def setUpClass(cls) -> None:
        if os.path.exists(cls.PATH):
            shutil.rmtree(cls.PATH)
        os.makedirs(cls.PATH)
        with open(f"{cls.PATH}/STORAGE.json", 'w', encoding="utf-8") as j:
            j.write(json.dumps({}))

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(f"{cls.PATH}/STORAGE.json"):
            os.remove(f"{cls.PATH}/STORAGE.json")

        if os.path.exists(cls.PATH):
            shutil.rmtree(cls.PATH)

    def test_init(self):
        storage = LocalStorage()
        rule = Rule('000')
        storage.change_ref("simulator/1a2b3c")
        receiver = SCHCReceiver(rule, storage)

        self.assertEqual({
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "bitmaps": {},
                            "requested": {}
                        }
                    }
                }
            }
        }, receiver.STORAGE.JSON)

        self.assertEqual(storage.JSON, receiver.STORAGE.JSON)
        self.assertEqual({
            "fragments": {},
            "reassembly": {},
            "state": {
                "bitmaps": {},
                "requested": {}
            }
        }, receiver.STORAGE.read())

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

        with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as fil:
            fil.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()
        self.assertEqual(j, storage.JSON)

        rule = Rule('000')
        storage.change_ref("simulator/1a2b3c")
        receiver = SCHCReceiver(rule, storage)

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

        with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as f:
            f.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()

        rule = Rule('000')
        storage.change_ref("simulator/1a2b3c")
        rule.INACTIVITY_TIMEOUT = 10
        receiver = SCHCReceiver(rule, storage)

        if not DISABLE_INACTIVITY_TIMEOUT:
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

        with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as fil:
            fil.write(json.dumps(j))

        hexstr = '15888888'
        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()

        rule = Rule('000')
        storage.change_ref(f"simulator/1a2b3c/rule_{rule.ID}")
        rule.INACTIVITY_TIMEOUT = 10
        receiver = SCHCReceiver(rule, storage)

        abort = receiver.generate_receiver_abort(
            Fragment.from_hex(hexstr).HEADER)

        self.assertIsInstance(abort, ReceiverAbort)
        self.assertTrue(receiver.STORAGE.exists("state/ABORT"))
        self.assertEqual("1fff000000000000",
                         receiver.STORAGE.read("state/ABORT"))

    def test_fragment_is_requested(self):
        j = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "requested": {
                                "w0": [0, 1, 2],
                                "w2": [6]}
                        }
                    }
                }
            }
        }

        with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as fil:
            fil.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()

        rule = Rule('000')
        storage.change_ref("simulator/1a2b3c")
        receiver = SCHCReceiver(rule, storage)

        header = FragmentHeader(rule, '', '00', '110')
        frg = Fragment(header, b'\x1a\x2b\x3c\x4d')
        self.assertTrue(receiver.fragment_is_requested(frg))

        header = FragmentHeader(rule, '', '00', '101')
        frg = Fragment(header, b'\x1a\x2b\x3c\x4d')
        self.assertTrue(receiver.fragment_is_requested(frg))

        header = FragmentHeader(rule, '', '00', '100')
        frg = Fragment(header, b'\x1a\x2b\x3c\x4d')
        self.assertTrue(receiver.fragment_is_requested(frg))
        header = FragmentHeader(rule, '', '10', '000')
        frg = Fragment(header, b'\x1a\x2b\x3c\x4d')
        self.assertTrue(receiver.fragment_is_requested(frg))

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

        with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as fil:
            fil.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()
        rule = Rule('000')
        storage.change_ref(f"simulator/1a2b3c/rule_{rule.ID}")
        receiver = SCHCReceiver(rule, storage)

        header = FragmentHeader(rule, '', '00', '110')
        frg = Fragment(header, b'\x1a\x2b\x3c\x4d')
        all_1 = Fragment(FragmentHeader(rule, '', '11', '111', '001'),
                         b'\x1a\x2b\x3c\x4d')
        complete_ack = CompoundACK(rule, '', ['11'], '1', ['0000000'])
        receiver.STORAGE.write(complete_ack.to_hex(), "state/LAST_ACK")
        receiver.STORAGE.write(all_1.to_hex(), "state/LAST_FRAGMENT")
        receiver.STORAGE.write('0000000', f"state/bitmaps/w{all_1.WINDOW}")

        self.assertTrue(receiver.STORAGE.exists("state/LAST_FRAGMENT"))
        self.assertTrue(receiver.STORAGE.exists("state/LAST_ACK"))
        self.assertTrue(complete_ack.is_complete())
        self.assertTrue(receiver.fragment_is_receivable(frg))

        self.assertTrue(receiver.fragment_was_already_received(all_1))
        self.assertTrue(receiver.fragment_is_receivable(all_1))
        receiver.STORAGE.delete("state/bitmaps")
        receiver.STORAGE.delete("state/LAST_ACK")
        receiver.STORAGE.delete("state/LAST_FRAGMENT")
        self.assertFalse(receiver.STORAGE.exists("state/LAST_FRAGMENT"))

        receiver.STORAGE.write('1111111', f"state/bitmaps/w{frg.WINDOW}")
        self.assertFalse(receiver.fragment_is_receivable(frg))
        receiver.STORAGE.write('0000000', f"state/bitmaps/w{frg.WINDOW}")
        self.assertTrue(receiver.fragment_is_receivable(frg))

        abort = SenderAbort(frg.HEADER)
        receiver.STORAGE.write(abort.to_hex(), "state/LAST_FRAGMENT")

        self.assertTrue(receiver.STORAGE.exists("state/LAST_FRAGMENT"))
        self.assertTrue(receiver.fragment_is_receivable(frg))

        requested = {
            "w0": [0, 3, 4]
        }

        last_fragment = Fragment(FragmentHeader(rule, '', '01', '011'),
                                 b'\x1a\x2b\x3c\x4d')
        receiver.STORAGE.write(last_fragment.to_hex(), "state/LAST_FRAGMENT")

        receiver.STORAGE.write(requested, "state/requested")
        self.assertTrue(receiver.STORAGE.exists("state/requested"))
        self.assertTrue(receiver.fragment_is_requested(frg))
        self.assertTrue(receiver.fragment_is_receivable(frg))
        unrequested = Fragment(FragmentHeader(rule, '', '00', '101'),
                               b'\x1a\x2b\x3c\x4d')
        self.assertFalse(receiver.fragment_is_receivable(unrequested))

        fragment_of_superior_window = Fragment(
            FragmentHeader(rule, '', '11', '011'), b'\x1a\x2b\x3c\x4d')
        self.assertTrue(
            receiver.fragment_is_receivable(fragment_of_superior_window)
        )

        fragment_of_inferior_window = Fragment(
            FragmentHeader(rule, '', '00', '001'), b'\x1a\x2b\x3c\x4d')
        self.assertFalse(
            receiver.fragment_is_receivable(fragment_of_inferior_window)
        )

        fragment_of_superior_index = Fragment(
            FragmentHeader(rule, '', '01', '001'), b'\x1a\x2b\x3c\x4d')
        self.assertTrue(
            receiver.fragment_is_receivable(fragment_of_superior_index)
        )

        fragment_of_inferior_index = Fragment(
            FragmentHeader(rule, '', '01', '110'), b'\x1a\x2b\x3c\x4d')
        self.assertFalse(
            receiver.fragment_is_receivable(fragment_of_inferior_index)
        )

        fragment_of_same_index = Fragment(
            FragmentHeader(rule, '', '01', '011'), b'\x1a\x2b\x3c\x4d')
        self.assertFalse(
            receiver.fragment_is_receivable(fragment_of_same_index)
        )

        receiver.STORAGE.write(all_1.to_hex(), "state/LAST_FRAGMENT")
        self.assertTrue(receiver.fragment_is_receivable(all_1))

    def test_start_new_session(self):
        j = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {
                            "w0": {
                                "1": "17888888"
                            }
                        },
                        "reassembly": {},
                        "state": {
                            "LAST_ACK": "038dcff200000000",
                            "LAST_FRAGMENT": "15888888",
                            "bitmaps": {
                                "w0": '1111111',
                                "w1": '1110010'
                            },
                            "requested": {
                                "w1": [3, 4, 6]
                            }
                        }
                    }
                }
            }
        }
        with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as fil:
            fil.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()
        rule = Rule('000')
        storage.change_ref("simulator/1a2b3c")
        receiver = SCHCReceiver(rule, storage)

        receiver.start_new_session(retain_previous_data=True)
        self.assertTrue(receiver.STORAGE.exists("fragments"))
        self.assertTrue(receiver.STORAGE.is_empty("fragments"))
        self.assertTrue(receiver.STORAGE.exists("reassembly"))
        self.assertTrue(receiver.STORAGE.is_empty("reassembly"))
        self.assertTrue(receiver.STORAGE.exists("state"))
        self.assertTrue(receiver.STORAGE.exists("state/requested"))
        self.assertTrue(receiver.STORAGE.exists("state/LAST_FRAGMENT"))
        self.assertTrue(receiver.STORAGE.exists("state/LAST_ACK"))
        self.assertTrue(receiver.STORAGE.exists("state/bitmaps"))
        self.assertTrue(receiver.STORAGE.is_empty("state/bitmaps"))

        receiver.start_new_session(retain_previous_data=False)
        self.assertTrue(receiver.STORAGE.exists("fragments"))
        self.assertTrue(receiver.STORAGE.is_empty("fragments"))
        self.assertTrue(receiver.STORAGE.exists("reassembly"))
        self.assertTrue(receiver.STORAGE.is_empty("reassembly"))
        self.assertTrue(receiver.STORAGE.exists("state"))
        self.assertTrue(receiver.STORAGE.exists("state/requested"))
        self.assertTrue(receiver.STORAGE.exists("state/bitmaps"))

    def test_get_pending_ack(self):
        j = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {}
                    }
                }
            }
        }
        with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as fil:
            fil.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()
        rule = Rule('000')
        storage.change_ref("simulator/1a2b3c")
        receiver = SCHCReceiver(rule, storage)

        all_1 = Fragment(FragmentHeader(rule, '', '11', '111', '001'),
                         b'\x1a\x2b\x3c\x4d')
        fragment = Fragment(FragmentHeader(rule, '', '01', '101'),
                            b'\x1a\x2b\x3c\x4d')
        complete_ack = CompoundACK(rule, '', ['11'], '1', ['0000000'])
        incomplete_ack = CompoundACK(rule, '', ['11'], '0', ['1111001'])

        self.assertIsNone(receiver.get_pending_ack(all_1))
        self.assertIsNone(receiver.get_pending_ack(fragment))

        receiver.STORAGE.JSON = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "LAST_ACK": complete_ack.to_hex(),
                        }
                    }
                }
            }
        }

        self.assertIsNone(receiver.get_pending_ack(all_1))

        receiver.STORAGE.JSON = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "LAST_ACK": complete_ack.to_hex(),
                            "LAST_FRAGMENT": all_1.to_hex()
                        }
                    }
                }
            }
        }

        p_ack = receiver.get_pending_ack(all_1)
        self.assertIsNotNone(p_ack)
        self.assertEqual(complete_ack.to_hex(), p_ack.to_hex())

        self.assertIsNone(receiver.get_pending_ack(fragment))
        self.assertFalse(receiver.STORAGE.exists("state/LAST_ACK"))
        self.assertFalse(receiver.STORAGE.exists("state/LAST_FRAGMENT"))

        receiver.STORAGE.JSON = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "LAST_ACK": incomplete_ack.to_hex(),
                            "LAST_FRAGMENT": all_1.to_hex()
                        }
                    }
                }
            }
        }

        self.assertIsNone(receiver.get_pending_ack(all_1))
        self.assertIsNone(receiver.get_pending_ack(fragment))

    def test_update_bitmap(self):
        j = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "bitmaps": {
                                "w0": '1111111',
                                "w1": '1100011'
                            }
                        }
                    }
                }
            }
        }
        with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as fil:
            fil.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()
        rule = Rule('000')
        storage.change_ref("simulator/1a2b3c")
        receiver = SCHCReceiver(rule, storage)

        fragment = Fragment(FragmentHeader(rule, '', '01', '100'),
                            b'\x1a\x2b\x3c\x4d')
        receiver.update_bitmap(fragment)

        self.assertEqual('1110011', receiver.STORAGE.read(
            f"state/bitmaps/w{fragment.WINDOW}"
        ))

    def test_fragment_was_already_received(self):
        j = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "bitmaps": {
                                "w0": '1111111',
                                "w1": '1110010'
                            },
                            "LAST_RESPONSE": {}
                        }
                    }
                }
            }
        }
        with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as fil:
            fil.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()
        rule = Rule('000')
        storage.change_ref("simulator/1a2b3c")
        receiver = SCHCReceiver(rule, storage)

        fragment = Fragment(FragmentHeader(rule, '', '01', '100'),
                            b'\x1a\x2b\x3c\x4d')
        self.assertTrue(receiver.fragment_was_already_received(fragment))
        all_0 = Fragment(FragmentHeader(rule, '', '01', '000'),
                         b'\x1a\x2b\x3c\x4d')
        self.assertFalse(receiver.fragment_was_already_received(all_0))
        all_1 = Fragment(FragmentHeader(rule, '', '10', '111', '111'),
                         b'\x1a\x2b\x3c\x4d')
        self.assertFalse(receiver.fragment_was_already_received(all_1))

        complete_ack = CompoundACK(rule, '', ['11'], '1', ['0000000'])
        incomplete_ack = CompoundACK(rule, '', ['11'], '0', ['1111001'])

        receiver.STORAGE.JSON = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "LAST_ACK": incomplete_ack.to_hex(),
                            "bitmaps": {
                                "w0": '1111111',
                                "w1": '1110011'
                            }
                        }
                    }
                }
            }
        }
        self.assertFalse(receiver.fragment_was_already_received(all_1))

        receiver.STORAGE.JSON = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "LAST_ACK": complete_ack.to_hex(),
                            "LAST_FRAGMENT": all_1.to_hex(),
                            "bitmaps": {
                                "w0": '1111111',
                                "w1": '1110011'
                            }
                        }
                    }
                }
            }
        }
        self.assertTrue(receiver.fragment_was_already_received(all_1))

    def test_generate_compound_ack(self):
        j = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {
                        "fragments": {},
                        "reassembly": {},
                        "state": {
                            "bitmaps": {
                                "w0": '1111111',
                                "w1": '1110010'
                            }
                        }
                    }
                }
            }
        }
        with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as fil:
            fil.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()
        rule = Rule('000')
        storage.change_ref("simulator/1a2b3c")
        receiver = SCHCReceiver(rule, storage)

        fragment = Fragment(FragmentHeader(rule, '', '01', '000'),
                            b'\x1a\x2b\x3c\x4d')
        ack = receiver.generate_compound_ack(fragment)
        self.assertEqual([('01', '1110010')], ack.TUPLES)

        receiver.STORAGE.write({
            "w0": '1111111',
            "w1": '1111111'
        }, "state/bitmaps")

        self.assertIsNone(receiver.generate_compound_ack(fragment))

        receiver.STORAGE.write({
            "w0": '1111111',
            "w1": '1111111',
            "w2": '1100001'
        }, "state/bitmaps")

        all_1 = Fragment(FragmentHeader(rule, '', '10', '111', '111'),
                         b'\x1a\x2b\x3c\x4d')
        ack = receiver.generate_compound_ack(all_1)
        self.assertEqual([('10', '1100001')], ack.TUPLES)

        all_1 = Fragment(FragmentHeader(rule, '', '10', '111', '011'),
                         b'\x1a\x2b\x3c\x4d')
        ack = receiver.generate_compound_ack(all_1)
        self.assertEqual([('10', '0000000')], ack.TUPLES)
        self.assertTrue(ack.is_complete())

    def test_schc_recv(self):
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
        with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as fil:
            fil.write(json.dumps(j))

        storage = LocalStorage()
        storage.PATH = self.PATH
        storage.load()
        rule = Rule('000')
        storage.change_ref("simulator/1a2b3c")
        receiver = SCHCReceiver(rule, storage)

        fragment = Fragment(FragmentHeader(rule, '', '01', '100'),
                            b'\x1a\x2b\x3c\x4d')

        with self.assertRaises(ReceiverAbortError):
            receiver.schc_recv(fragment, int(time.time()))

        receiver.STORAGE.JSON = {
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

        if not DISABLE_INACTIVITY_TIMEOUT:
            receiver.RULE.INACTIVITY_TIMEOUT = 10
            ack = receiver.schc_recv(fragment, int(time.time()))
            self.assertTrue(ack.is_receiver_abort())

        receiver.STORAGE.delete("state/ABORT")

        with self.assertRaises(LengthMismatchError):
            ack = receiver.schc_recv(
                Fragment(
                    FragmentHeader(rule, '', '01', '110'),
                    b'\x1a\x2b' * UPLINK_MTU
                ), int(time.time())
            )

        receiver.STORAGE.JSON = {
            "simulator": {
                "1a2b3c": {
                    "rule_0": {}
                }
            }
        }

        sender_abort = SenderAbort(fragment.HEADER)

        with self.assertRaises(SenderAbortError):
            ack = receiver.schc_recv(sender_abort, int(time.time()))

        ack = receiver.schc_recv(fragment, int(time.time()))
        self.assertIsNone(ack)
        self.assertTrue(receiver.STORAGE.exists("fragments/w1/f2"))
        self.assertTrue(receiver.STORAGE.exists("state/bitmaps/w0"))
        self.assertTrue(receiver.STORAGE.exists("state/bitmaps/w1"))

        complete_ack = CompoundACK(rule, '', ['11'], '1', ['0000000'])
        all_1 = Fragment(FragmentHeader(rule, '', '01', '111', '001'),
                         b'\x1a\x2b')
        receiver.STORAGE.JSON = {
            'simulator': {
                '1a2b3c': {
                    'rule_0': {
                        'fragments': {
                            'w1': {
                                'f2': '0c1a2b3c4d'}
                        },
                        'reassembly': {},
                        'state': {
                            'requested': {},
                            'bitmaps': {
                                'w1': '0000001'
                            },
                            'TIMESTAMP': int(time.time()) - 5,
                            'LAST_ACK': complete_ack.to_hex(),
                            'LAST_FRAGMENT': all_1.to_hex()
                        }
                    }
                }
            }
        }
        ack = receiver.schc_recv(all_1, int(time.time()))
        self.assertTrue(ack.is_complete())
