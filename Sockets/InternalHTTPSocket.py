import requests

import config.schc
from Sockets.Socket import Socket


class InternalHTTPSocket(Socket):

    def __init__(self):
        super().__init__()
        self.ENDPOINT = config.schc.REASSEMBLER_URL
        self.TIMEOUT = 60

    def send(self, message: dict) -> None:

        if not self.EXPECTS_ACK:
            self.set_timeout(.1)

        try:
            response = requests.post(
                url=self.ENDPOINT,
                json=message,
                headers={},
                timeout=self.TIMEOUT
            )
        except requests.exceptions.ReadTimeout:
            raise SCHCTimeoutError

    def recv(self, bufsize: int) -> bytes:
        try:
            msg = self.BUFFER.get(timeout=self.TIMEOUT)
            if len(msg) / 2 > bufsize:
                raise LengthMismatchError("Received data is larger than buffer size.")
            return hex_to_bytes(msg)

        except Empty:
            raise SCHCTimeoutError

    def set_reception(self, flag: bool) -> None:
        self.EXPECTS_ACK = flag

    def set_timeout(self, timeout: float) -> None:
        self.TIMEOUT = timeout
