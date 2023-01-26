from Entities.exceptions import LengthMismatchError
from config.schc import L2_WORD_SIZE
from utils.casting import bin_to_int, hex_to_bin
from utils.misc import round_to_next_multiple, is_monochar


class Rule:

    def __init__(self, rule_id: str) -> None:

        self.STR: str = rule_id
        self.ID: int = bin_to_int(rule_id)

        if rule_id[:3] != '111':
            self.RULE_ID_SIZE = 3
            self.T = 0
            self.M = 2
            self.N = 3
            self.WINDOW_SIZE = 7
            self.U = 3

        elif rule_id[:6] != '111111':
            self.RULE_ID_SIZE = 6
            self.T = 0
            self.M = 2
            self.N = 4
            self.WINDOW_SIZE = 12
            self.U = 4

        else:
            self.RULE_ID_SIZE = 8
            self.T = 0
            self.M = 3
            self.N = 5
            self.WINDOW_SIZE = 31
            self.U = 5

        if len(rule_id) > self.RULE_ID_SIZE:
            raise LengthMismatchError("Rule ID is larger than RULE_ID_SIZE")

        self.HEADER_LENGTH: int = round_to_next_multiple(
            self.RULE_ID_SIZE + self.T + self.M + self.N, L2_WORD_SIZE
        )

        self.ALL1_HEADER_LENGTH: int = round_to_next_multiple(
            self.RULE_ID_SIZE + self.T + self.M + self.N + self.U, L2_WORD_SIZE
        )

        self.ACK_HEADER_LENGTH: int = self.RULE_ID_SIZE + self.M + 1

    @staticmethod
    def from_hex(hexa: str) -> 'Rule':
        """Parses the Rule ID of the given hex string,
         assuming that it is located in the leftmost bits."""
        as_bin = hex_to_bin(hexa)
        first_byte = as_bin[:8]
        rule_id = first_byte[:3]
        if is_monochar(rule_id, '1'):
            rule_id = first_byte[:6]
            if is_monochar(rule_id, '1'):
                rule_id = first_byte[:8]
        return Rule(rule_id)
