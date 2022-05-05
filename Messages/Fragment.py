import json

import config.schc as config
from Entities.Rule import Rule
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import LengthMismatchError, BadProfileError
from Messages.FragmentHeader import FragmentHeader
from utils.casting import bytes_to_hex, hex_to_bin, bin_to_int, hex_to_bytes
from utils.misc import round_to_next_multiple
from utils.schc_utils import is_monochar


class Fragment:

    def __init__(
            self,
            profile: SigfoxProfile,
            header: FragmentHeader,
            payload: bytes
    ) -> None:
        """
        Create a SCHC Fragment.

        Args:
            profile: (SigfoxProfile) The Profile object used for the fragment.
            header: (FragmentHeader) The header of the fragment.
            payload: (bytes) The payload of the fragment.
        """

        self.PROFILE = profile
        self.HEADER = header
        self.PAYLOAD = payload
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

    def expects_ack(self) -> bool:
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
        profile = SigfoxProfile("UPLINK", config.FR_MODE, rule)

        rule_idx = 0
        dtag_idx = profile.RULE_ID_SIZE
        w_idx = profile.RULE_ID_SIZE + profile.T
        fcn_idx = profile.RULE_ID_SIZE + profile.T + profile.M
        rcs_idx = profile.RULE_ID_SIZE + profile.T + profile.M + profile.N

        fcn = as_bin[fcn_idx:rcs_idx]

        if is_monochar(fcn, '1'):
            header_length = profile.RULE.ALL1_HEADER_LENGTH
            header_padding_index = rcs_idx + profile.U
            rcs = as_bin[rcs_idx:header_padding_index]

            if rcs == '':
                rcs = None

            if round_to_next_multiple(rcs_idx + profile.U, config.L2_WORD_SIZE) != header_length:
                raise LengthMismatchError(f"All-1 Header length mismatch: "
                                          f"Expected {header_length}, actual {rcs_idx + profile.U}")

            header_padding = as_bin[header_padding_index:header_length]
            if not is_monochar(header_padding, '0') and header_padding != '':
                raise BadProfileError(f"Padding was not all zeroes nor empty ({header_padding})")
        else:
            header_length = profile.RULE.HEADER_LENGTH
            rcs = None

            if round_to_next_multiple(rcs_idx, config.L2_WORD_SIZE) != header_length:
                raise LengthMismatchError(f"Header length mismatch: "
                                          f"Expected {header_length}, actual {rcs_idx}")

        dtag = as_bin[dtag_idx:w_idx]
        w = as_bin[w_idx:fcn_idx]

        header = FragmentHeader(profile, dtag, w, fcn, rcs)
        header_nibs = header_length // 4
        payload = hex_to_bytes(hex_string[header_nibs:])

        return Fragment(profile, header, payload)

    @staticmethod
    def from_file(path) -> 'Fragment':
        """Loads a stored fragment and parses it into a Fragment."""
        with open(path, 'r') as f:
            fragment_data = json.load(f)
        fragment = fragment_data["hex"]
        return Fragment.from_hex(fragment)
