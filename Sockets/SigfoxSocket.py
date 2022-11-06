import socket

from network import Sigfox

import config.sigfox as config
from Sockets.Socket import Socket


class SigfoxSocket(Socket):

    def __init__(self) -> None:
        super().__init__()
        _ = Sigfox(mode=Sigfox.SIGFOX, rcz=config.RC_ZONES[4])
        self.SOCKET = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
        self.SOCKET.setblocking(True)

    def send(self, message: bytes) -> None:
        self.SOCKET.send(message)

    def recv(self, bufsize: int) -> bytes:
        return self.SOCKET.recv(bufsize)

    def set_reception(self, flag: bool) -> None:
        self.SOCKET.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, flag)

    def set_timeout(self, timeout: float) -> None:
        self.SOCKET.settimeout(timeout)
