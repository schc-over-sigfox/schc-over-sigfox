"""
Module that contains functions used to transform between different data types.
"""
import binascii
from math import log


def bin_to_int(b: str) -> int:
    return int(b, 2)


def bin_to_hex(b: str) -> str:
    hex_string = hex(int(b, 2))[2:]
    return zfill(hex_string, len(b) // 4)


def bin_to_bytes(b: str) -> bytes:
    return bytes(int(b[i:i + 8], 2) for i in range(0, len(s), 8))


def bin_to_string(bits: str, encoding: str = 'utf-8') -> str:
    as_int = int(bits, 2)
    return as_int.to_bytes((as_int.bit_length() + 7) // 8, byteorder='big').decode(encoding)


def hex_to_bin(h: str, length: int = None) -> str:
    if length is None:
        length = len(h) * 4

    as_int = int(h, 16)
    as_bin = bin(as_int)

    return zfill(as_bin[2:], length)


def hex_to_bytes(h: str) -> bytes:
    return binascii.unhexlify(h)


def bytes_to_hex(b: bytes) -> str:
    return str(binascii.hexlify(b))[2:-1]


def bytes_to_bin(b: bytes, length: int = None) -> str:
    if length is None:
        length = len(b) * 8

    as_int = int.from_bytes(b, byteorder='big')
    as_bin = bin(as_int)[2:]

    return zfill(as_bin[2:], length)


def int_to_bin(n: int, length: int = 0) -> str:
    return zfill(bin(n)[2:], length)


def int_to_hex(n: int) -> str:
    return hex(n)


def int_to_bytes(n: int, length: int = None) -> bytes:
    if length is None:
        length = int(log(n, 256)) + 1 if n != 0 else 1
    return n.to_bytes(length, byteorder='big')


def string_to_bin(s: str, encoding: str = 'utf-8') -> str:
    as_int = int.from_bytes(s.encode(encoding), byteorder='big')
    as_bin = bin(as_int)[2:]
    return zfill(as_bin, 8 * ((len(as_bin) + 7) // 8))
