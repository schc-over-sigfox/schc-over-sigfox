from Entities.Rule import Rule
from config import schc as cfg
from utils.casting import int_to_bin


class SigfoxProfile:
    """
    Class that defines the parameters for the Sigfox SCHC Profile, defined in
    https://datatracker.ietf.org/doc/html/draft-ietf-lpwan-schc-over-sigfox-09.
    """

    UPLINK_MTU = 96
    DOWNLINK_MTU = 64

    def __init__(self, direction: str, mode: str, rule: Rule) -> None:
        self.DIRECTION: str = direction
        self.MODE: str = mode
        self.RULE: Rule = rule

        self.MAX_ACK_REQUESTS = cfg.MAX_ACK_REQUESTS
        self.RETRANSMISSION_TIMEOUT = cfg.RETRANSMISSION_TIMEOUT
        self.INACTIVITY_TIMEOUT = cfg.INACTIVITY_TIMEOUT
        self.SIGFOX_DL_TIMEOUT = cfg.SIGFOX_DL_TIMEOUT

        if direction == "UPLINK":
            if mode == "ACK ON ERROR":
                self.RULE_ID_SIZE = rule.RULE_ID_SIZE
                self.T = rule.T
                self.N = rule.N
                self.M = rule.M
                self.U = rule.U
                self.WDW_SIZE = rule.WINDOW_SIZE
                self.MAX_WINDOW_NUMBER = 2 ** self.M
                self.MAX_FRAGMENT_NUMBER = self.MAX_WINDOW_NUMBER\
                                           * self.WDW_SIZE

                self.FCN_DICT = {
                    int_to_bin(
                        self.WDW_SIZE - (j % self.WDW_SIZE) - 1, self.N
                    ): j
                    for j in range(self.WDW_SIZE)
                }
