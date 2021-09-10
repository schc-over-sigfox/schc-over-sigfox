from Entities.Protocol import Protocol
from utils.schc_utils import zfill


class SigfoxProfile(Protocol):
    DIRECTION = None
    MODE = None
    FCN_DICT = None
    NUMBER_DICT = None
    MAX_FRAGMENT_NUMBER = None

    def __init__(self, direction, mode, header_bytes):

        self.NAME = "SIGFOX"
        self.DIRECTION = direction
        self.MODE = mode
        self.RETRANSMISSION_TIMER_VALUE = 45  # (45) enough to let a downlink message to be sent if needed
        self.INACTIVITY_TIMER_VALUE = 60  # (60) for demo purposes
        self.SIGFOX_DL_TIMEOUT = 20  # This is to be tested
        self.L2_WORD_SIZE = 8
        self.N = 0
        self.HEADER_LENGTH = 0
        self.MESSAGE_INTEGRITY_CHECK_SIZE = None  # TBD
        self.RCS_ALGORITHM = None  # TBD
        self.UPLINK_MTU = 12*8
        self.DOWNLINK_MTU = 8*8

        if direction == "UPLINK":

            if mode == "ACK ON ERROR":
                if header_bytes == 1:
                    self.HEADER_LENGTH = 8
                    self.RULE_ID_SIZE = 3
                    self.T = 0
                    self.N = 3
                    self.M = 2
                    self.WINDOW_SIZE = 2 ** self.N - 1
                    self.BITMAP_SIZE = 2 ** self.N - 1
                    self.MAX_ACK_REQUESTS = 5
                    self.MAX_FRAGMENT_NUMBER = (2 ** self.M) * self.WINDOW_SIZE

                elif header_bytes == 2:
                    self.HEADER_LENGTH = 16
                    self.RULE_ID_SIZE = 8
                    self.T = 0
                    self.N = 5
                    self.M = 3
                    self.WINDOW_SIZE = 2 ** self.N - 1
                    self.BITMAP_SIZE = 2 ** self.N - 1
                    self.MAX_ACK_REQUESTS = 5

        if direction == "DOWNLINK":
            if mode == "ACK ALWAYS":
                self.HEADER_LENGTH = 8
                self.RULE_ID_SIZE = 3
                self.T = 0
                self.N = 5
                self.M = 0
                self.MAX_ACK_REQUESTS = 5

            else:
                pass

        self.FCN_DICT = {zfill(bin((2 ** self.N - 2) - (j % (2 ** self.N - 1)))[2:], self.N): j
                         for j in range(2 ** self.N - 1)}

        self.NUMBER_DICT = {v: k for k, v in self.FCN_DICT.items()}
