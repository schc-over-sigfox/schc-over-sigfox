from Entities.exceptions import LengthMismatchError
from config.schc import L2_WORD_SIZE
from utils.casting import int_to_bin
from utils.misc import round_to_next_multiple


class Rule:

    def __init__(self, rule_id: int, option: int):

        self.ID = rule_id

        if option == 0:
            self.RULE_ID_SIZE = 3
            self.T = 0
            self.M = 2
            self.N = 3
            self.WINDOW_SIZE = 7
            self.U = 3

        elif option == 1:
            self.RULE_ID_SIZE = 6
            self.T = 0
            self.M = 2
            self.N = 4
            self.WINDOW_SIZE = 12
            self.U = 4

        elif option == 2:
            self.RULE_ID_SIZE = 8
            self.T = 0
            self.M = 3
            self.N = 5
            self.WINDOW_SIZE = 31
            self.U = 5

        if len(int_to_bin(rule_id)) > self.RULE_ID_SIZE:
            raise LengthMismatchError("Rule ID is larger than RULE_ID_SIZE")

        self.HEADER_LENGTH = round_to_next_multiple(
            self.RULE_ID_SIZE + self.T + self.M + self.N, L2_WORD_SIZE
        )

        self.ALL1_HEADER_LENGTH = round_to_next_multiple(
            self.RULE_ID_SIZE + self.T + self.M + self.N + self.U, L2_WORD_SIZE
        )

        self.ACK_HEADER_LENGTH = self.RULE_ID_SIZE + self.M + 1

    def __str__(self):
        return int_to_bin(self.ID, length=self.RULE_ID_SIZE)
