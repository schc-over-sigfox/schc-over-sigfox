from Messages.Fragment import Fragment
from Messages.FragmentHeader import FragmentHeader


class SenderAbort(Fragment):

    def __init__(self, header: FragmentHeader) -> None:
        profile = header.RULE
        dtag = header.DTAG
        w = '1' * profile.M
        fcn = '1' * profile.N
        rcs = None

        header = FragmentHeader(profile, dtag, w, fcn, rcs)
        payload = b''

        super().__init__(header, payload)
