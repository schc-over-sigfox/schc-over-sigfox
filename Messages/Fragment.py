import json

import config.schc as config
from Entities.Rule import Rule
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import LengthMismatchError, BadProfileError
from Messages.FragmentHeader import FragmentHeader
from utils.casting import bytes_to_hex, hex_to_bin, hex_to_bytes, bytes_to_bin
from utils.misc import is_monochar, round_to_next_multiple, zfill


class Fragment:

    def __init__(
            self,
            header: FragmentHeader,
            payload: bytes
    ) -> None:
        """
        Create a SCHC Fragment.

        Args:
            header: (FragmentHeader) The header of the fragment.
            payload: (bytes) The payload of the fragment.
        """

        self.PROFILE = header.PROFILE
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

    def to_bin(self) -> str:
        """Returns the binary representation of the Fragment."""
        return ''.join([self.HEADER.to_binary(), bytes_to_bin(self.PAYLOAD)])

    def is_all_1(self) -> bool:
        """Checks if the fragment is an All-1"""

        if not is_monochar(self.HEADER.FCN, '1'):
            return False

        if self.PAYLOAD == b'':
            return len(self.to_bin()) == self.PROFILE.RULE.ALL1_HEADER_LENGTH

        return True

    def is_all_0(self) -> bool:
        """Checks if the fragment is an All-0"""
        return is_monochar(self.HEADER.FCN, '0')

    def expects_ack(self) -> bool:
        """Checks if the fragment can request an ACK."""
        return self.is_all_0() or self.is_all_1()

    def is_sender_abort(self) -> bool:
        """Checks if the fragment is a SCHC Sender-Abort."""

        if not is_monochar(self.HEADER.FCN, '1') or not is_monochar(
                self.HEADER.W, '1'):
            return False

        if self.PAYLOAD == b'':
            return len(self.to_bin()) < self.PROFILE.RULE.ALL1_HEADER_LENGTH

        return False

    @staticmethod
    def from_hex(hex_string: str) -> 'Fragment':
        """Parses a hex string into a Fragment, using the specified Profile"""

        if hex_string is None or hex_string == '':
            return None

        as_bin = hex_to_bin(hex_string)
        rule = Rule.from_hex(as_bin)
        profile = SigfoxProfile("UPLINK", config.FR_MODE, rule)

        dtag_idx = profile.RULE_ID_SIZE
        w_idx = profile.RULE_ID_SIZE + profile.T
        fcn_idx = profile.RULE_ID_SIZE + profile.T + profile.M
        rcs_idx = profile.RULE_ID_SIZE + profile.T + profile.M + profile.N

        fcn = as_bin[fcn_idx:fcn_idx + profile.N]

        if is_monochar(fcn, '1'):
            header_length = profile.RULE.ALL1_HEADER_LENGTH
            header_padding_index = rcs_idx + profile.U
            rcs = as_bin[rcs_idx:rcs_idx + profile.U]

            if rcs == '':
                rcs = None

            if round_to_next_multiple(rcs_idx + profile.U,
                                      config.L2_WORD_SIZE) != header_length:
                raise LengthMismatchError(
                    "All-1 Header length mismatch: "
                    "Expected {}, actual {}".format(
                        header_length, rcs_idx + profile.U
                    )
                )

            header_padding = as_bin[header_padding_index:header_length]
            if not is_monochar(header_padding, '0') and header_padding != '':
                raise BadProfileError(
                    "Padding was not all zeroes nor empty ({})"
                        .format(header_padding)
                )
        else:
            header_length = profile.RULE.HEADER_LENGTH
            rcs = None

            if round_to_next_multiple(rcs_idx,
                                      config.L2_WORD_SIZE) != header_length:
                raise LengthMismatchError(
                    "Header length mismatch: "
                    "Expected {}, actual {}"
                        .format(header_length, rcs_idx)
                )

        dtag = as_bin[dtag_idx:dtag_idx + profile.T]
        w = as_bin[w_idx:w_idx + profile.M]

        header = FragmentHeader(profile, dtag, w, fcn, rcs)
        header_nibs = header_length // 4
        payload = hex_to_bytes(hex_string[header_nibs:])

        return Fragment(header, payload)

    def get_indices(self) -> tuple[str, str]:
        """Returns a tuple of the indices (window, fragment) of the fragment,
        formatted to be used as filenames."""
        w_index = zfill(
            str(self.HEADER.WINDOW_NUMBER), (2 ** self.PROFILE.M - 1) // 10 + 1
        )
        f_index = zfill(str(self.INDEX), self.PROFILE.WINDOW_SIZE // 10 + 1)

        return w_index, f_index

    @staticmethod
    def from_file(path) -> 'Fragment':
        """Loads a stored fragment and parses it into a Fragment."""
        with open(path, 'r', encoding="utf-8") as f:
            fragment_data = json.load(f)
        fragment = fragment_data["hex"]
        return Fragment.from_hex(fragment)
