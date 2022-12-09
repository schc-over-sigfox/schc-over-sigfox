from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import LengthMismatchError


class Header:

    def __init__(
            self,
            profile: SigfoxProfile,
            dtag: str,
            w: str
    ) -> None:
        """Class to encapsulate SCHC Header fields present in Fragments and ACKs."""

        self.PROFILE: SigfoxProfile = profile

        if len(profile.RULE.STR) != profile.RULE_ID_SIZE:
            raise LengthMismatchError(f"RULE must be of length RULE_ID_SIZE ({profile.RULE_ID_SIZE}). "
                                      f"Rule was {profile.RULE.STR}, length = {len(profile.RULE.STR)}. ")
        self.RULE_ID: str = profile.RULE.STR

        if profile.T == "0":
            self.DTAG: str = ""
        elif len(dtag) != profile.T:
            raise LengthMismatchError("DTAG must be of length T")
        else:
            self.DTAG: str = dtag

        if len(w) != profile.M:
            raise LengthMismatchError("W must be of length M")
        self.W: str = w
        self.WINDOW_NUMBER: int = int(self.W, 2)

    def to_binary(self) -> str:
        """Method to be implemented in child classes."""
        raise NotImplementedError
