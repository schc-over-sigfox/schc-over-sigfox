from Messages.Fragment import Fragment
from Messages.FragmentHeader import FragmentHeader


class SenderAbort(Fragment):

    def __init__(self, header: FragmentHeader) -> None:
        rule = header.RULE
        dtag = header.DTAG
        w = '1' * rule.M
        fcn = '1' * rule.N
        rcs = None

        header = FragmentHeader(rule, dtag, w, fcn, rcs)
        payload = b''

        super().__init__(header, payload)
