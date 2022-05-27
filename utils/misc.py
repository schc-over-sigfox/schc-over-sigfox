"""Module of miscellaneous functions used in the project."""
import os
from typing import Optional

import requests


def zfill(s: str, length: int) -> str:
    """Adds zeroes at the begginning of a string until it completes the desired length."""
    return '0' * (length - len(s)) + s


def zpad(s: str, length: int) -> str:
    """Adds zeroes at the end of a string until it completes the desired length."""
    return s + '0' * (length - len(s))


def replace_char(s: str, position: int, new_char: str) -> str:
    """Replaces a single character in the specified position of a string."""
    return "{p}{n}{s}".format(
        p=s[:position],
        n=new_char,
        s=s[position + 1:]
    )


def find(s: str, char: str) -> 'list[int]':
    """Lists all the occurrences of a character in a string."""
    return [i for i, c in enumerate(s) if char == c]


def is_monochar(s: str, char: str = None) -> bool:
    """Checks if a string contains only repetitions of one character."""
    monochar = len(set(s)) == 1

    if char is not None:
        return monochar and s[0] == char

    return monochar


def section_string(s: str, indices: list[int]) -> list[str]:
    """Sections a string in the specified indices and returns a list of its sections."""
    indices.append(len(s))

    return [s[i:j] for i, j in zip(indices, indices[1:])]


def generate_packet(byte_size: int, path: str = None) -> str:
    """Generates a string of the specified byte size and optionally saves it into a file."""

    s = '0'
    i = 0
    while len(s) < byte_size:
        i = (i + 1) % 10
        s += str(i)

    if path is not None and not os.path.isfile(path):
        with open(path, 'w') as f:
            f.write(s)

    return s


def invert_dict(d: dict) -> dict:
    """Inverts {key: value} pairs of a dictionary into {value: kay} pairs, only if no values are repeated."""
    values = list(d.values())

    if len(values) != len(set(values)):
        raise ValueError("Dictionary cannot be inverted")

    return {v: k for k, v in d.items()}


def round_to_next_multiple(n, factor):
    """Rounds a number to the next greater multiple of a specified factor."""

    return -(n // (-factor)) * factor


def http_post(body: dict, endpoint: str, asynchronous: bool = False) -> Optional[requests.Response]:
    """Makes a HTTP POST request, which wait for its response or not."""

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
            return
