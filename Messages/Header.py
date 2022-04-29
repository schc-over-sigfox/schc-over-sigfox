from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import LengthMismatchError


class Header:

    def __init__(
            self,
            profile: SigfoxProfile,
            dtag: str,
            w: str
    ):
        """Class to encapsulate SCHC Header fields present in Fragments and ACKs."""

        self.PROFILE = profile

        if len(str(profile.RULE)) != profile.RULE_ID_SIZE:
            raise LengthMismatchError("RULE must be of length RULE_ID_SIZE")
        else:
            self.RULE_ID = str(profile.RULE)

        if profile.T == "0":
            self.DTAG = ""
        elif len(dtag) != profile.T:
            raise LengthMismatchError("DTAG must be of length T")
        else:
            self.DTAG = dtag

        if len(w) != profile.M:
            raise LengthMismatchError("W must be of length M")
        else:
            self.W = w
            self.WINDOW_NUMBER = int(self.W, 2)

    def to_binary(self) -> str:
        """Method to be implemented in child classes."""
        raise NotImplementedError
