from unittest import TestCase

from Entities.Rule import Rule
from Entities.exceptions import LengthMismatchError
from Messages.Header import Header


class TestHeader(TestCase):

    def test_init(self):
        rule_0 = Rule('000')
        dtag = ''
        w = '10'
        header = Header(rule_0, dtag, w)

        self.assertEqual(rule_0.STR, header.RULE_ID)
        self.assertEqual('', header.DTAG)
        self.assertEqual('10', header.W)
        self.assertEqual(2, header.WINDOW_NUMBER)

        rule_0.RULE_ID_SIZE = 1

        with self.assertRaises(LengthMismatchError):
            _ = Header(rule_0, dtag, w)

        rule_0 = Rule('000')
        rule_0.T = 2

        with self.assertRaises(LengthMismatchError):
            _ = Header(rule_0, dtag, w)

        rule_0 = Rule('000')
        rule_0.M = 5

        with self.assertRaises(LengthMismatchError):
            _ = Header(rule_0, dtag, w)
