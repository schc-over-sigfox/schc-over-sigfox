import unittest
from unittest import TestCase

from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import SCHCTimeoutError
from Messages.CompoundACK import CompoundACK
from Messages.Fragment import Fragment
from Sockets.HTTPSocket import HTTPSocket
from utils.casting import bytes_to_hex

PORT = 1313


@unittest.skip
class TestHTTPSocket(TestCase):

    def test_send(self):
        socket = HTTPSocket()
        socket.ENDPOINT = f'http://127.0.0.1:{PORT}/test'
        socket.TIMEOUT = 1
        fragment = Fragment.from_hex('128888888888888888888888')

        try:
            socket.send(fragment.to_bytes())
            self.assertTrue(True)
        except SCHCTimeoutError:
            self.fail()

        fragment = Fragment.from_hex('12888888888888888888888f')
        with self.assertRaises(SCHCTimeoutError):
            socket.send(fragment.to_bytes())

        self.assertTrue(socket.BUFFER.empty())
        fragment = Fragment.from_hex('172088888888888888888888')
        socket.EXPECTS_ACK = True
        socket.send(fragment.to_bytes())
        self.assertFalse(socket.BUFFER.empty())

    def test_set_reception(self):
        socket = HTTPSocket()
        socket.ENDPOINT = f'http://127.0.0.1:{PORT}/test'
        socket.TIMEOUT = 1

        self.assertFalse(socket.EXPECTS_ACK)
        socket.set_reception(True)
        self.assertTrue(socket.EXPECTS_ACK)

    def test_recv(self):
        socket = HTTPSocket()
        socket.ENDPOINT = f'http://127.0.0.1:{PORT}/test'
        socket.TIMEOUT = 1
        socket.set_reception(True)

        fragment = Fragment.from_hex('172088888888888888888888')
        socket.send(fragment.to_bytes())
        res = socket.recv(SigfoxProfile.DOWNLINK_MTU)
        ack = CompoundACK.from_hex(bytes_to_hex(res))

        self.assertTrue(res, ack.to_hex())

    def test_set_timeout(self):
        socket = HTTPSocket()
        socket.ENDPOINT = f'http://127.0.0.1:{PORT}/test'
        socket.TIMEOUT = 1
        socket.set_timeout(100)
        self.assertTrue(100, socket.TIMEOUT)
