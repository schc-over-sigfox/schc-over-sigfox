from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import LengthMismatchError
from Messages.Header import Header


class ACKHeader(Header):

    def __init__(
            self,
            profile: SigfoxProfile,
            dtag: str,
            w: str,
            c: str
    ) -> None:
        super().__init__(profile, dtag, w)

        if len(c) != 1:
            raise LengthMismatchError("C bit must be of length 1")

        self.C = c

    def to_binary(self) -> str:
        fields_in_order = [self.RULE_ID, self.DTAG, self.W, self.C]
        return ''.join(fields_in_order)
