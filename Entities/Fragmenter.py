import json
from math import floor

from Entities.Rule import Rule
from Entities.exceptions import LengthMismatchError
from Messages.Fragment import Fragment
from Messages.FragmentHeader import FragmentHeader
from config.schc import UPLINK_MTU
from db.CommonFileStorage import CommonFileStorage as Storage
from utils.casting import int_to_bin, bytes_to_bin


class Fragmenter:
    """A Fragmenter object, which generates SCHC Fragments from a SCHC Packet."""

    def __init__(
            self,
            rule: Rule,
            fragment_dir: str = "debug/sd",
    ) -> None:
        """
        Instantiate a Fragmenter.

        Args:
            profile: (SCHCProfile) SCHC Profile used for the fragmentation procedure.
            fragment_dir: (str) Directory where to store the fragments,
        """
        self.RULE = rule
        self.STORAGE = Storage(
            "{}/rule_{}".format(fragment_dir, self.RULE.ID)
        )
        self.CURR_FRAG_NUMBER = 0

        if not self.STORAGE.folder_exists("fragments"):
            self.STORAGE.create_folder("fragments")

    def generate_fragment(self, payload: bytes, all_1: bool) -> Fragment:

        window_id = self.CURR_FRAG_NUMBER / self.RULE.WINDOW_SIZE
        w = int_to_bin(floor(window_id % 2 ** self.RULE.M), self.RULE.M)
        dtag = ''

        if all_1:
            fcn = '1' * self.RULE.N
            rcs = int_to_bin(
                self.CURR_FRAG_NUMBER % self.RULE.WINDOW_SIZE + 1,
                self.RULE.U
            )
            header_length = self.RULE.ALL1_HEADER_LENGTH
            payload_max_length = UPLINK_MTU - header_length
        else:
            index = self.RULE.WINDOW_SIZE \
                    - (self.CURR_FRAG_NUMBER % self.RULE.WINDOW_SIZE) - 1
            fcn = int_to_bin(index, self.RULE.N)
            rcs = None
            header_length = self.RULE.HEADER_LENGTH
            payload_max_length = UPLINK_MTU - header_length

        header = FragmentHeader(self.RULE, dtag, w, fcn, rcs)

        if len(header.to_binary()) > header_length:
            raise LengthMismatchError(
                "Header is larger than its maximum size ({} > {})."
                    .format(len(header.to_binary()), header_length)
            )
        if len(bytes_to_bin(payload)) > payload_max_length:
            raise LengthMismatchError(
                "Payload is larger than its maximum size ({} > {}).".format(
                    (len(bytes_to_bin(payload))), payload_max_length
                )
            )

        fragment = Fragment(header, payload)
        fragment_data = {
            "hex": fragment.to_hex(),
            "sent": False
        }
        w_index, f_index = fragment.get_indices()

        self.STORAGE.write(
            "fragments/fragment_w{}f{}".format(w_index, f_index),
            json.dumps(fragment_data)
        )
        self.CURR_FRAG_NUMBER = (self.CURR_FRAG_NUMBER + 1) \
                                % self.RULE.MAX_FRAGMENT_NUMBER

        return fragment

    def fragment(self, schc_packet: bytes) -> list[Fragment]:
        """
        Generates a list of SCHC Fragments.
        """
        header_len = self.RULE.HEADER_LENGTH
        all_1_header_len = self.RULE.ALL1_HEADER_LENGTH
        max_fragment_number = self.RULE.MAX_FRAGMENT_NUMBER

        payload_max_length = (UPLINK_MTU - header_len) // 8
        all_1_payload = (UPLINK_MTU - all_1_header_len) // 8

        maximum_packet_size = payload_max_length * (
                max_fragment_number - 1) + all_1_payload

        if len(schc_packet) > maximum_packet_size:
            raise LengthMismatchError(
                "SCHC Packet is larger than allowed "
                "by Rule {}".format(self.RULE.ID)
            )

        number_of_fragments = -(len(schc_packet) // -payload_max_length)
        fragments = []

        if header_len < all_1_header_len and len(
                schc_packet) % payload_max_length == 0:
            number_of_fragments += 1

        for i in range(number_of_fragments):
            payload = schc_packet[
                      i * payload_max_length:(i + 1) * payload_max_length]
            fragment = self.generate_fragment(payload, all_1=(
                        i == number_of_fragments - 1))
            fragments.append(fragment)

        self.CURR_FRAG_NUMBER = 0
        return fragments

    def clear_fragment_directory(self) -> None:
        for file in self.STORAGE.list_files("fragments"):
            self.STORAGE.delete_file("fragments/{}".format(file))
