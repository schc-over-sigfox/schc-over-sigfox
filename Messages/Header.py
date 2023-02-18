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
                "RULE must be of length RULE_ID_SIZE ({}). "
                "Rule was {}, length = {}. ".format(
                    rule.RULE_ID_SIZE,
                    rule.STR,
                    len(rule.STR)
                )
            )
        self.RULE_ID = rule.STR

        if rule.T == 0:
            self.DTAG = ""
        elif len(dtag) != rule.T:
            raise LengthMismatchError("DTAG must be of length T")
        else:
            self.DTAG = dtag

        if len(w) != rule.M:
            raise LengthMismatchError("W must be of length M")
        self.W = w
        self.WINDOW_NUMBER = int(self.W, 2)

    def to_binary(self) -> str:
        """Method to be implemented in child classes."""
        raise NotImplementedError
