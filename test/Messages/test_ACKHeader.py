from Entities.Rule import Rule
from Entities.exceptions import LengthMismatchError
from Messages.ACKHeader import ACKHeader
from test.Messages.test_Header import TestHeader


class TestACKHeader(TestHeader):
    def test_init(self):
        rule_0 = Rule('000')
        dtag = ''
        w = '10'
        c = '0'
        header = ACKHeader(rule_0, dtag, w, c)

        self.assertEqual(c, header.C)

        with self.assertRaises(LengthMismatchError):
            c = '11'
            _ = ACKHeader(rule_0, dtag, w, c)

    def test_to_binary(self):
        rule_0 = Rule('000')
        dtag = ''
        w = '10'
        c = '0'
        header = ACKHeader(rule_0, dtag, w, c)

        self.assertEqual('000100', header.to_binary())
