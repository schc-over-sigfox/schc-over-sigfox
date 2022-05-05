from unittest import TestCase

from Entities.Rule import Rule
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import LengthMismatchError
from Messages.ACKHeader import ACKHeader


class TestACKHeader(TestCase):
    def test_init(self):
        rule_0 = Rule(0, 0)
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule_0)
        dtag = ''
        w = '10'
        c = '0'
        header = ACKHeader(profile, dtag, w, c)

        self.assertEqual(c, header.C)

        with self.assertRaises(LengthMismatchError):
            c = '11'
            _ = ACKHeader(profile, dtag, w, c)

    def test_to_binary(self):
        rule_0 = Rule(0, 0)
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule_0)
        dtag = ''
        w = '10'
        c = '0'
        header = ACKHeader(profile, dtag, w, c)

        self.assertEqual('000100', header.to_binary())
