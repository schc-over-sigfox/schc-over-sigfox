from Entities.Rule import Rule
from Entities.exceptions import LengthMismatchError, BadProfileError
from Messages.FragmentHeader import FragmentHeader
from test.Messages.test_Header import TestHeader


class TestFragmentHeader(TestHeader):

    def test_init(self):
        rule_0 = Rule('000')
        dtag = ''
        w = '10'
        fcn = '101'
        rcs = None
        header = FragmentHeader(rule_0, dtag, w, fcn, rcs)

        self.assertEqual(fcn, header.FCN)
        self.assertEqual('', header.RCS)
        self.assertEqual('', header.PADDING)

        rule_0.N = 7

        with self.assertRaises(LengthMismatchError):
            _ = FragmentHeader(rule_0, dtag, w, fcn, rcs)

        rule_0 = Rule('000')
        rcs = '110'

        with self.assertRaises(BadProfileError):
            _ = FragmentHeader(rule_0, dtag, w, fcn, rcs)

        fcn = '111'
        header = FragmentHeader(rule_0, dtag, w, fcn, rcs)
        self.assertEqual('110', header.RCS)
        self.assertEqual('00000', header.PADDING)

    def test_to_binary(self):
        rule_0 = Rule('000')
        dtag = ''
        w = '10'
        fcn = '111'
        rcs = '110'
        header = FragmentHeader(rule_0, dtag, w, fcn, rcs)
        self.assertEqual("0001011111000000", header.to_binary())

        fcn = '101'
        rcs = None
        header = FragmentHeader(rule_0, dtag, w, fcn, rcs)
        self.assertEqual("00010101", header.to_binary())

    def test_to_bytes(self):
        rule_0 = Rule('000')
        dtag = ''
        w = '10'
        fcn = '111'
        rcs = '110'
        header = FragmentHeader(rule_0, dtag, w, fcn, rcs)
        self.assertEqual(b"\x17\xc0", header.to_bytes())

        fcn = '101'
        rcs = None
        header = FragmentHeader(rule_0, dtag, w, fcn, rcs)
        self.assertEqual(b"\x15", header.to_bytes())
