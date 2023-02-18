from Entities.Rule import Rule
from Entities.exceptions import LengthMismatchError


class Header:

    def __init__(
            self,
            rule: Rule,
            dtag: str,
            w: str
    ) -> None:
        """Class to encapsulate SCHC Header fields
        present in Fragments and ACKs."""

        self.RULE: Rule = rule

        if len(rule.STR) != rule.RULE_ID_SIZE:
            raise LengthMismatchError(
                f"RULE must be of length RULE_ID_SIZE "
                f"({rule.RULE_ID_SIZE}). "
                f"Rule was {rule.STR}, "
                f"length = {len(rule.STR)}.")
        self.RULE_ID: str = rule.STR

        if rule.T == 0:
            self.DTAG: str = ""
        elif len(dtag) != rule.T:
            raise LengthMismatchError("DTAG must be of length T")
        else:
            self.DTAG: str = dtag

        if len(w) != rule.M:
            raise LengthMismatchError("W must be of length M")
        self.W: str = w
        self.WINDOW_NUMBER: int = int(self.W, 2)

    def to_binary(self) -> str:
        """Method to be implemented in child classes."""
        raise NotImplementedError
