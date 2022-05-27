class Socket:
    def __init__(self) -> None:
        self.EXPECTS_ACK = False
        self.SEQNUM = 0
        self.TIMEOUT = 60

    def send(self, message: bytes) -> None:
        """Sends data towards the receiver end."""
        raise NotImplementedError

    def recv(self, bufsize: int) -> bytes:
        """Receives data from the socket buffer."""
        raise NotImplementedError

    def set_reception(self, flag: bool) -> None:
        """Configures the socket to be able to receive a message after sending one."""
        raise NotImplementedError

    def set_timeout(self, timeout: float) -> None:
        """Configures the timeout value of the socket, in seconds."""
        raise NotImplementedError
