import socket

from network import Sigfox

import config.sigfox as config
from Entities.exceptions import SCHCTimeoutError
from Sockets.Socket import Socket


class SigfoxSocket(Socket):

    def __init__(self) -> None:
        super().__init__()
        _ = Sigfox(mode=Sigfox.SIGFOX, rcz=config.RC_ZONES[4])
        self.SOCKET = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
        self.SOCKET.setblocking(True)

    def send(self, message: bytes) -> None:
        """Sends a message over the Sigfox network."""
        try:
            self.SOCKET.send(message)
        except OSError:
            raise SCHCTimeoutError

    def recv(self, bufsize: int) -> bytes:
        """Receives a downlink message from the Sigfox network."""
        return self.SOCKET.recv(bufsize)

    def set_reception(self, flag: bool) -> None:
        """Configures the reception flag of the Sigfox Socket."""
        self.SOCKET.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, flag)
        self.EXPECTS_ACK = flag

    def set_timeout(self, timeout: float) -> None:
        """Configures the timeout value of the Sigfox socket."""
        self.SOCKET.settimeout(timeout)
