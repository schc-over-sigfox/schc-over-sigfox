import time
from queue import Queue, Empty

import requests.exceptions

from Entities.exceptions import SCHCTimeoutError, LengthMismatchError
from Sockets.Socket import Socket
from config import schc as config
from utils.casting import bytes_to_hex, hex_to_bytes


class SigfoxHTTPSocket(Socket):

    def __init__(self):
        super().__init__()
        self.DEVICE = "1a2b3c"
        self.BUFFER = Queue()
        self.ENDPOINT = config.RECEIVER_URL
        self.TIMEOUT = 60

    def send(self, message: bytes) -> None:
        self.SEQNUM += 1

        http_body = {
            'deviceTypeId': "simulator",
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
                if self.EXPECTS_ACK:
                    self.BUFFER.put(
                        response.json()[self.DEVICE]["downlinkData"]
                    )
        except requests.exceptions.ReadTimeout as exc:
            raise SCHCTimeoutError from exc

    def recv(self, bufsize: int) -> bytes:
        try:
            msg = self.BUFFER.get(timeout=self.TIMEOUT)
            if len(msg) / 2 > bufsize:
                raise LengthMismatchError(
                    "Received data is larger than buffer size."
                )
            return hex_to_bytes(msg)

        except Empty as exc:
            raise SCHCTimeoutError from exc

    def set_reception(self, flag: bool) -> None:
        self.EXPECTS_ACK = flag

    def set_timeout(self, timeout: int) -> None:
        self.TIMEOUT = timeout
