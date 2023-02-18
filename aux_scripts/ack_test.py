"""Sends a Sigfox message and waits for a downlink response."""

import socket

from network import Sigfox

sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ4)
s = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
s.setblocking(True)
s.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, True)

s.send(bytes([0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]))
print("Sent.")

ack = s.recv(64)
print(ack)
print(type(ack))
