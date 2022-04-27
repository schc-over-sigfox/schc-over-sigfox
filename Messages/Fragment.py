import json

import config.schc
from Entities.Rule import Rule
from Entities.SigfoxProfile import SigfoxProfile
from Messages.FragmentHeader import FragmentHeader
from utils.casting import bytes_to_bin, bytes_to_hex, hex_to_bin, bin_to_int, hex_to_bytes
from utils.schc_utils import is_monochar


class Fragment:

    def __init__(
            self,
            profile: SigfoxProfile,
            fragment: tuple[bytes, bytes]
    ):
        """
        Create a SCHC Fragment.

        Args:
            profile: (SigfoxProfile) The Profile object used for the fragment.
            fragment: (tuple[bytes, bytes]) The header and payload of the fragment.
        """

        self.PROFILE = profile
        header = bytes_to_bin(fragment[0])

        self.HEADER = FragmentHeader(self.PROFILE, header)
        self.PAYLOAD = fragment[1]
        self.WINDOW = self.HEADER.WINDOW_NUMBER
        self.INDEX = self.PROFILE.FCN_DICT.get(self.HEADER.FCN, self.PROFILE.WINDOW_SIZE - 1)
        self.NUMBER = self.WINDOW * self.PROFILE.WINDOW_SIZE + self.INDEX

    def to_bytes(self) -> bytes:
        """Returns the byte representation of the Fragment."""
        return b''.join([self.HEADER.to_bytes(), self.PAYLOAD])

    def to_hex(self) -> str:
        """Returns the hex representation of the Fragment."""
        return ''.join(map(bytes_to_hex, [self.HEADER.to_bytes(), self.PAYLOAD]))

    def is_all_1(self) -> bool:
        """Checks if the fragment is an All-1"""
        return is_monochar(self.HEADER.FCN, '1') and not self.PAYLOAD == b''

    def is_all_0(self) -> bool:
        """Checks if the fragment is an All-0"""
        return is_monochar(self.HEADER.FCN, '0')

    def expect_ack(self) -> bool:
        """Checks if the fragment can request an ACK."""
        return self.is_all_0() or self.is_all_1()

    def is_sender_abort(self) -> bool:
        """Checks if the fragment is a SCHC Sender-Abort."""
        return is_monochar(self.HEADER.FCN, '1') and is_monochar(self.HEADER.W, '1') and self.PAYLOAD == b''

    @staticmethod
    def from_hex(hex_string: str) -> 'Fragment':
        """Parses a hex string into a Fragment, using the specified Profile"""

        as_bin = hex_to_bin(hex_string)
        first_byte = as_bin[:8]
        rule_id = first_byte[:3]
        option = 0
        if is_monochar(rule_id, '1'):
            rule_id = first_byte[:6]
            option = 1
            if is_monochar(rule_id, '1'):
                option = 2
                rule_id = first_byte[:8]

        rule = Rule(bin_to_int(rule_id), option)
        profile = SigfoxProfile("UPLINK", config.schc.FR_MODE, rule)
        fcn_index = profile.RULE_ID_SIZE + profile.M
        fcn = as_bin[fcn_index:fcn_index + profile.N]

        if is_monochar(fcn, '1'):
            header_length = profile.RULE.ALL1_HEADER_LENGTH
        else:
            header_length = profile.RULE.HEADER_LENGTH

        header_nibs = header_length // 4
        header = hex_to_bytes(hex_string[:header_nibs])
        payload = hex_to_bytes(hex_string[header_nibs:])

        return Fragment(profile, (header, payload))

    @staticmethod
    def from_file(path) -> 'Fragment':
        """Loads a stored fragment and parses it into a Fragment."""
        with open(path, 'r') as f:
            fragment_data = json.load(f)
        fragment = fragment_data["hex"]
        return Fragment.from_hex(fragment)
