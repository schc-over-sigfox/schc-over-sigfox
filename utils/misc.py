"""Module of miscellaneous functions used in the project."""
import os
from typing import Optional

import requests


def zfill(string: str, length: int) -> str:
    """Adds zeroes at the begginning of a string until it completes
    the desired length."""
    return '0' * (length - len(string)) + string


def zpad(string: str, length: int) -> str:
    """Adds zeroes at the end of a string until it completes
    the desired length."""
    return string + '0' * (length - len(string))


def replace_char(string: str, position: int, new_char: str) -> str:
    """Replaces a single character in the specified position of a string."""
    return f"{string[:position]}{new_char}{string[position + 1:]}"


def find(string: str, char: str) -> 'list[int]':
    """Lists all the occurrences of a character in a string."""
    return [i for i, c in enumerate(string) if char == c]


def is_monochar(string: str, char: str = None) -> bool:
    """Checks if a string contains only repetitions of one character."""
    monochar = len(set(string)) == 1

    if char is not None:
        return monochar and string[0] == char

    return monochar


def section_string(string: str, indices: list[int]) -> list[str]:
    """Sections a string in the specified indices and
    returns a list of its sections."""
    indices.append(len(string))

    return [string[i:j] for i, j in zip(indices, indices[1:])]


def generate_packet(byte_size: int, path: str = None) -> bytes:
    """Generates a string of the specified byte size and
    optionally saves it into a file."""

    string = '0'
    i = 0
    while len(string) < byte_size:
        i = (i + 1) % 10
        string += str(i)

    string = string.encode('utf-8')

    if path is not None and not os.path.isfile(path):
        with open(path, 'wb') as fil:
            fil.write(string)

    return string


def invert_dict(dic: dict) -> dict:
    """Inverts {key: value} pairs of a dictionary into {value: kay} pairs,
    only if no values are repeated."""
    values = list(dic.values())

    if len(values) != len(set(values)):
        raise ValueError("Dictionary cannot be inverted")

    return {v: k for k, v in dic.items()}


def round_to_next_multiple(num, factor):
    """Rounds a number to the next greater multiple of a specified factor."""
    return -(num // (-factor)) * factor


def http_post(
        body: dict, endpoint: str, asynchronous: bool = False
) -> Optional[requests.Response]:
    """Makes an HTTP POST request, waiting or not for its response."""

    timeout = .1 if asynchronous else 60

    try:
        return requests.post(
            url=endpoint,
            json=body,
            headers={},
            timeout=timeout
        )
    except requests.exceptions.ReadTimeout:
        if asynchronous:
            return None
