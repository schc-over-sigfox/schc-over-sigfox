import threading
import time

from Entities.exceptions import SCHCTimeoutError


class Timer:

    def __init__(self):
        self.THREAD = threading.Thread()
        self.STOPPED = False

    def sleep(self, timeout: int, raise_exception: bool = False) -> None:
        """Freezes code execution for the specified amount of time."""
        t_i = time.perf_counter()
        while abs(time.perf_counter() - t_i) < timeout and not self.STOPPED:
            continue
        if not self.STOPPED:
            if raise_exception:
                raise SCHCTimeoutError
            return

    def start(self, timeout: int, raise_exception: bool = False) -> None:
        """Starts an asynchronous timer which will expire after the specified amount of time."""
        self.THREAD = threading.Thread(target=self.sleep, args=(timeout, raise_exception))
        self.THREAD.start()

    def stop(self) -> None:
        """Stops the timer if it has not already expired."""
        self.STOPPED = True
        self.THREAD.join()

    @staticmethod
    def time(resolution: int = 1) -> int:
        """Returns the current Unix timestamp in the given resolution (in seconds)."""
        return int(time.time()) // resolution


timer = Timer()
