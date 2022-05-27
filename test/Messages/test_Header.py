from unittest import TestCase

from Entities.Rule import Rule
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import LengthMismatchError
from Messages.Header import Header


class TestHeader(TestCase):

    def test_init(self):
        rule_0 = Rule('000')
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule_0)
        dtag = ''
        w = '10'
        header = Header(profile, dtag, w)

        self.assertEqual(rule_0.STR, header.RULE_ID)
        self.assertEqual('', header.DTAG)
        self.assertEqual('10', header.W)
        self.assertEqual(2, header.WINDOW_NUMBER)

        profile.RULE_ID_SIZE = 1

        with self.assertRaises(LengthMismatchError):
            _ = Header(profile, dtag, w)

        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule_0)
        profile.T = 2

        with self.assertRaises(LengthMismatchError):
            _ = Header(profile, dtag, w)

        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule_0)
        profile.M = 5

        with self.assertRaises(LengthMismatchError):
            _ = Header(profile, dtag, w)
