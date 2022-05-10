import time
from queue import Queue, Empty

import requests.exceptions

from Entities.exceptions import SCHCTimeoutError, LengthMismatchError
from config import schc as config
from utils.casting import bytes_to_hex, hex_to_bytes


class SigfoxSocket:
    def __init__(self):
        self.BUFFER = Queue()
        self.ENDPOINT = config.RECEIVER_URL
        self.DEVICE = "1a2b3c"
        self.EXPECTS_ACK = False
        self.SEQNUM = 0
        self.TIMEOUT = 0

    def send(self, message: bytes) -> None:
        """Sends a message towards the received end."""
        self.SEQNUM += 1

        http_body = {
            'deviceTypeId': "Simulator",
            'device': self.DEVICE,
            'data': bytes_to_hex(message),
            'time': str(int(time.time())),
            'seqNumber': str(self.SEQNUM),
            'ack': "true" if self.EXPECTS_ACK else "false"
        }

        try:
            response = requests.post(
                url=self.ENDPOINT,
                json=http_body,
                headers={},
                timeout=self.TIMEOUT
            )
            if response.status_code == 200:
                self.BUFFER.put(response.json()[self.DEVICE]["downlinkData"])
        except requests.exceptions.ReadTimeout:
            raise SCHCTimeoutError

    def recv(self, bufsize: int) -> bytes:
        """Gets a message from the reception buffer."""
        try:
            msg = self.BUFFER.get(timeout=self.TIMEOUT)
            if len(msg) / 2 > bufsize:
                raise LengthMismatchError("Received data is larger than buffer size.")
            return hex_to_bytes(msg)

        except Empty:
            raise SCHCTimeoutError

    def set_recv(self, flag: bool) -> None:
        """Make the socket able to receive replies after sending a message."""
        self.EXPECTS_ACK = flag

    def set_timeout(self, timeout: int) -> None:
        """Configures the timeout for the socket, in seconds."""
        self.TIMEOUT = timeout
