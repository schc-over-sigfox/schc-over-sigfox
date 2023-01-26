from typing import Optional

import config.schc as config
from Entities.Rule import Rule
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import LengthMismatchError, BadProfileError
from Messages.ACK import ACK
from utils.casting import hex_to_bin
from utils.misc import is_monochar


class CompoundACK(ACK):

    def __init__(
            self,
            profile: SigfoxProfile,
            dtag: str,
            windows: list[str],
            c: str,
            bitmaps: list[str],
            padding: str = ''
    ) -> None:
        self.TUPLES: list[tuple[str, str]] = []

        if len(windows) != len(bitmaps):
            raise BadProfileError(
                "Window and bitmap arrays must be of same length. "
                f"(Window array has length {len(windows)}, "
                f"bitmap array has length {len(bitmaps)})"
            )

        first_window = windows[0]
        first_bitmap = bitmaps[0]
        self.TUPLES.append((first_window, first_bitmap))

        for i in range(len(windows[:-1])):
            self.TUPLES.append((windows[i + 1], bitmaps[i + 1]))

        payload = ''.join(f"{t[0]}{t[1]}" for t in self.TUPLES[1:]) + padding

        super().__init__(
            profile,
            dtag,
            first_window,
            c,
            first_bitmap,
            padding=payload
        )

    @staticmethod
    def from_hex(hex_string: str) -> Optional['CompoundACK']:
        """Creates a CompoundACK from a hexadecimal string."""

        if hex_string is None:
            return None

        as_bin = hex_to_bin(hex_string)

        if len(as_bin) != SigfoxProfile.DOWNLINK_MTU:
            raise LengthMismatchError(
                "Compound ACK was not of length DOWNLINK_MTU."
            )

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
        bitmap = payload[:profile.WDW_SIZE]
        padding = payload[profile.WDW_SIZE:]

        windows = [w]
        bitmaps = [bitmap]

        while len(padding) >= profile.M + profile.WDW_SIZE:
            if is_monochar(padding, '0'):
                break
            windows.append(padding[:profile.M])
            bitmaps.append(padding[profile.M:profile.M + profile.WDW_SIZE])
            padding = padding[profile.M + profile.WDW_SIZE:]

        return CompoundACK(
            profile,
            dtag,
            windows,
            c,
            bitmaps,
            padding
        )
