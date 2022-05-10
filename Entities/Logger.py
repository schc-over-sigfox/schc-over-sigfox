from Entities.Timer import Timer


class Logger:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3

    def __init__(self, filename, json_file):

        self.FILENAME = filename
        self.JSON_FILE = json_file
        self.TOTAL_SIZE = 0
        self.CHRONO = Timer()
        self.LOGGING_TIME = 0
        self.LAPS = []
        self.FRAGMENTS_INFO_ARRAY = []
        self.FRAGMENTATION_TIME = 0
        self.START_SENDING_TIME = 0
        self.END_SENDING_TIME = 0
        self.LOGGING_TIME = 0
        self.FINISHED = False
        self.SENDER_ABORTED = False
        self.RECEIVER_ABORTED = False
        self.SEVERITY = Logger.DEBUG
        self.BEHAVIOR = ''

    def set_severity(self, severity):
        self.SEVERITY = severity

    def debug(self, text):
        if self.SEVERITY <= self.DEBUG:
            print(self, "[DEBUG] {}".format(text))

    def info(self, text):
        if self.SEVERITY <= self.INFO:
            print(self, "[INFO] {}".format(text))

    def warning(self, text):
        if self.SEVERITY <= self.WARNING:
            print(self, "[WARNING] {}".format(text))

    def error(self, text):
        if self.SEVERITY <= self.ERROR:
            print(self, "[ERROR] {}".format(text))

    def save(self):
        """TODO: Implement how should the data of the logger attributes be written."""
        raise NotImplementedError


log = Logger('', Logger.DEBUG)
