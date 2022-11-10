import json
import os

from Entities.Timer import Timer


class Logger:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3

    def __init__(self, severity):

        self.SEVERITY = severity
        self.CHRONO = Timer()
        self.PACKET_SIZE = 0
        self.NB_FRAGMENTS = 0
        self.UPLINK_LOSS_RATE = 0
        self.DOWNLINK_LOSS_RATE = 0
        self.REGULAR_COUNT = 0
        self.ALL_0_COUNT = 0
        self.ALL_1_COUNT = 0
        self.ABORT_COUNT = 0
        self.SENT = 0
        self.RECEIVED = 0
        self.LOGGING_TIME = 0
        self.FRAGMENTS_INFO = {}

        self.LAPS = []
        self.FRAGMENTATION_TIME = 0
        self.START_SENDING_TIME = 0
        self.END_SENDING_TIME = 0
        self.LOGGING_TIME = 0
        self.FINISHED = False
        self.SENDER_ABORTED = False
        self.RECEIVER_ABORTED = False
        self.SEQUENCE = ''

    def set_severity(self, severity) -> None:
        """Configure the minimum severity of the messages displayed
        by the Logger."""
        self.SEVERITY = severity

    def debug(self, text) -> None:
        """Display a debug-level message."""
        if self.SEVERITY <= self.DEBUG:
            print(self, f"[DEBUG] {text}")

    def info(self, text) -> None:
        """Display an info-level message."""
        if self.SEVERITY <= self.INFO:
            print(self, f"[INFO] {text}")

    def warning(self, text) -> None:
        """Display a warning-level message."""
        if self.SEVERITY <= self.WARNING:
            print(self, f"[WARNING] {text}")

    def error(self, text) -> None:
        """Display an error-level message"""
        if self.SEVERITY <= self.ERROR:
            print(self, f"[ERROR] {text}")

    def export(self, filename) -> None:
        """Exports the data recorded in the Logger into a JSON file."""

        j = {
            "packet_size": self.PACKET_SIZE,
            "nb_fragments": self.NB_FRAGMENTS,
            "sent": {
                "regular": self.REGULAR_COUNT,
                "all-0": self.ALL_0_COUNT,
                "all-1": self.ALL_1_COUNT,
                "abort": self.ABORT_COUNT,
                "total": self.SENT
            },
            "received": self.RECEIVED,
            "sender-aborted": self.SENDER_ABORTED,
            "receiver-aborted": self.RECEIVER_ABORTED,
            "finished": self.FINISHED,
            "uplink-loss-rate": self.UPLINK_LOSS_RATE,
            "downlink-loss-rate": self.DOWNLINK_LOSS_RATE,
            "sequence": self.SEQUENCE,
            "fragments": self.FRAGMENTS_INFO
        }

        if not os.path.isdir("export"):
            os.mkdir("export")

        with open(f"export/{filename}", 'w') as fi:
            fi.write(json.dumps(j, indent=2))


log = Logger(Logger.WARNING)
