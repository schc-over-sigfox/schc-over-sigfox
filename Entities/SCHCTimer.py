import threading
import time

from Entities.exceptions import SCHCTimeoutError


class SCHCTimer:

    def __init__(self, timeout):
        self.timeout = timeout

    @staticmethod
    def wait(timeout, raise_exception=False):
        t_i = time.perf_counter()
        while True:
            t_f = time.perf_counter()
            if t_f - t_i >= timeout:
                if raise_exception:
                    raise SCHCTimeoutError
                return

    def start(self):
        thread = threading.Thread(target=self.wait, args=(True,))
        thread.start()

    @staticmethod
    def read():
        return time.perf_counter()
