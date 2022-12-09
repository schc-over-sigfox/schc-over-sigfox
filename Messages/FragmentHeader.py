from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import LengthMismatchError, BadProfileError
from Messages.Header import Header
from config.schc import L2_WORD_SIZE
from utils.casting import bin_to_bytes
from utils.misc import is_monochar


class FragmentHeader(Header):

    def __init__(
            self,
            profile: SigfoxProfile,
            dtag: str,
            w: str,
            fcn: str,
            rcs: str = None
    ) -> None:
        """Subclass of Header, used exclusively in Fragments."""
        super().__init__(profile, dtag, w)

        if len(fcn) != profile.N:
            raise LengthMismatchError("FCN must be of length N")
        self.FCN: str = fcn

        if rcs is None:
            self.RCS: str = ''
        else:
            if profile.U != 0 and len(rcs) != profile.U:
                raise LengthMismatchError("RCS must be of length U")
            if not is_monochar(self.FCN, '1'):
                raise BadProfileError(
                    "RCS was not None in a regular fragment (not All-1)")
            self.RCS: str = rcs

        self.PADDING: str = ''
        header_length = len(
            self.RULE_ID + self.DTAG + self.W + self.FCN + self.RCS) % L2_WORD_SIZE

        if header_length % L2_WORD_SIZE != 0:
            self.PADDING = '0' * (L2_WORD_SIZE - (header_length % L2_WORD_SIZE))

    def to_binary(self) -> str:
        """Generate the binary string representation of the Header"""

        fields_in_order = [self.RULE_ID, self.DTAG, self.W, self.FCN, self.RCS, self.PADDING]
        return ''.join(fields_in_order)

    def to_bytes(self) -> bytes:
        """Generate the byte representation of the Header,"""

        return bin_to_bytes(self.to_binary())
