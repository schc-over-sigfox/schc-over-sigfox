from Entities.Rule import Rule
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import LengthMismatchError
from Messages.ACKHeader import ACKHeader
from config import schc as config
from utils.casting import bin_to_hex, hex_to_bin
from utils.misc import is_monochar


class ACK:
    def __init__(
            self,
            profile: SigfoxProfile,
            dtag: str,
            w: str,
            c: str,
            bitmap: str,
            padding: str = ''
    ) -> None:
        self.PROFILE = profile
        self.BITMAP = bitmap

        self.HEADER = ACKHeader(profile, dtag, w, c)
        self.PADDING = padding + '0' * (profile.DOWNLINK_MTU - len(self.HEADER.to_binary() + self.BITMAP + padding))

    def to_hex(self) -> str:
        """Obtains the hex representationi of the ACK."""
        return bin_to_hex(self.HEADER.to_binary() + self.BITMAP + self.PADDING)

    def is_receiver_abort(self) -> bool:
        """Checks whether the ACK is a SCHC Receiver Abort."""

        as_bin = hex_to_bin(self.to_hex())
        header_length = len(self.HEADER.RULE_ID + self.HEADER.DTAG + self.HEADER.W + self.HEADER.C)
        header = as_bin[:header_length]
        padding = as_bin[header_length:as_bin.rfind('1') + 1]
        padding_start = padding[:-config.L2_WORD_SIZE]
        padding_end = padding[-config.L2_WORD_SIZE:]

        if is_monochar(self.HEADER.W, '1') and self.HEADER.C == '1':
            if padding_end == "1" * config.L2_WORD_SIZE:
                if padding_start != '' and len(header) % config.L2_WORD_SIZE != 0:
                    return is_monochar(padding_start, '1') \
                           and (len(header) + len(padding_start)) % config.L2_WORD_SIZE == 0
                return len(header) % config.L2_WORD_SIZE == 0
        return False

    def is_compound_ack(self) -> bool:
        """Checks if the ACK can be parsed as a Compound ACK."""
        return not self.is_receiver_abort() and not is_monochar(self.PADDING, '0')

    def is_complete(self) -> bool:
        """Checks if the ACK reports the end of a SCHC session."""
        return self.HEADER.C == '1' and not self.is_receiver_abort()

    @staticmethod
    def from_hex(hex_string: str) -> 'ACK':
        """Creates an ACK from a hexadecimal string."""
        as_bin = hex_to_bin(hex_string)

        if len(as_bin) != SigfoxProfile.DOWNLINK_MTU:
            raise LengthMismatchError("ACK was not of length DOWNLINK_MTU.")

        rule = Rule.from_hex(hex_string)
        profile = SigfoxProfile("UPLINK", config.FR_MODE, rule)

        dtag_idx = profile.RULE_ID_SIZE
        w_idx = profile.RULE_ID_SIZE + profile.T
        c_idx = profile.RULE_ID_SIZE + profile.T + profile.M

        header = as_bin[:rule.ACK_HEADER_LENGTH]

        dtag = header[dtag_idx:dtag_idx + profile.T]
        w = header[w_idx:w_idx + profile.M]
        c = header[c_idx:c_idx + 1]

        payload = as_bin[rule.ACK_HEADER_LENGTH:]
        bitmap = payload[:profile.WINDOW_SIZE]
        padding = payload[profile.WINDOW_SIZE:]

        return ACK(
            profile,
            dtag,
            w,
            c,
            bitmap,
            padding
        )
