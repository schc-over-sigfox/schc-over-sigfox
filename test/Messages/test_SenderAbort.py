from Messages.Fragment import Fragment
from Messages.SenderAbort import SenderAbort
from test.Messages.test_Fragment import TestFragment
from utils.casting import bin_to_hex


class TestSenderAbort(TestFragment):
    def test_init(self):
        b = '00010101100010001000100010001000'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)

        abort = SenderAbort(fragment.HEADER)

        self.assertEqual(fragment.HEADER.RULE_ID, abort.HEADER.RULE_ID)
        self.assertEqual(fragment.HEADER.DTAG, abort.HEADER.DTAG)
        self.assertEqual('11', abort.HEADER.W)
        self.assertEqual('111', abort.HEADER.FCN)
        self.assertEqual('', abort.HEADER.RCS)

        self.assertFalse(fragment.is_sender_abort())
        self.assertTrue(abort.is_sender_abort())

        b = '00011111100000000100010001000100'
        h = bin_to_hex(b)
        fragment = Fragment.from_hex(h)

        abort = SenderAbort(fragment.HEADER)

        self.assertEqual(fragment.HEADER.RULE_ID, abort.HEADER.RULE_ID)
        self.assertEqual(fragment.HEADER.DTAG, abort.HEADER.DTAG)
        self.assertEqual('11', abort.HEADER.W)
        self.assertEqual('111', abort.HEADER.FCN)
        self.assertEqual('', abort.HEADER.RCS)

        self.assertFalse(fragment.is_sender_abort())
        self.assertTrue(abort.is_sender_abort())
