"""
Module that contains functions used to transform between different data types.
"""
import binascii
from math import log

from utils.misc import zfill


def bin_to_int(bi: str) -> int:
    """Transforms a binary string into its integer representation."""
    return int(bi, 2)


def bin_to_hex(bits: str) -> str:
    """Transforms a binary string into its hexadecimal representation."""
    hex_string = hex(int(bits, 2))[2:]
    return zfill(hex_string, len(bits) // 4)


def bin_to_bytes(bits: str) -> bytes:
    """Transforms a binary string into its byte representation."""
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def bin_to_string(bits: str, encoding: str = 'utf-8') -> str:
    """Transforms a binary string into its encoded string representation."""
    as_int = int(bits, 2)
    return as_int.to_bytes((as_int.bit_length() + 7) // 8, byteorder='big').decode(encoding)


def hex_to_bin(hexa: str, length: int = None) -> str:
    """Transforms a hexadecimal string into its binary representation."""
    if length is None:
        length = len(hexa) * 4

    as_int = int(hexa, 16)
    as_bin = bin(as_int)

    return zfill(as_bin[2:], length)


def hex_to_bytes(hexa: str) -> bytes:
    """Transforms a hexadecimal string into its byte representation."""
    return binascii.unhexlify(hexa)


def bytes_to_bin(byt: bytes, length: int = None) -> str:
    """Transforms a byte string into its binary representation."""
    if byt == b'':
        return ''

    if length is None:
        length = len(byt) * 8

    as_int = int.from_bytes(byt, byteorder='big')
    as_bin = bin(as_int)[2:]

    return zfill(as_bin, length)


def bytes_to_hex(byt: bytes) -> str:
    """Transforms a byte string into its hexadecimal representation."""
    return str(binascii.hexlify(byt))[2:-1]


def int_to_bin(num: int, length: int = 0) -> str:
    """Transforms an integer into its binary representation."""
    return zfill(bin(num)[2:], length)


def int_to_hex(num: int) -> str:
    """Transforms an integer into its hexadecimal representation."""
    return hex(num)[2:]


def int_to_bytes(num: int, length: int = None) -> bytes:
    """Transforms an integer into its byte representation."""
    if length is None:
        length = int(log(num, 256)) + 1 if num != 0 else 1
    return num.to_bytes(length, byteorder='big')


def string_to_bin(string: str, encoding: str = 'utf-8') -> str:
    """Transforms an encoded string into its binary representation."""
    as_int = int.from_bytes(string.encode(encoding), byteorder='big')
    as_bin = bin(as_int)[2:]
    return zfill(as_bin, 8 * ((len(as_bin) + 7) // 8))
