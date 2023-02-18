from typing import Optional

from Entities.Rule import Rule
from Entities.exceptions import LengthMismatchError, BadProfileError
from Messages.ACK import ACK
from config.schc import DOWNLINK_MTU
from utils.casting import hex_to_bin
from utils.misc import is_monochar


class CompoundACK(ACK):

    def __init__(
            self,
            rule: Rule,
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

        super().__init__(rule, dtag, first_window, c, first_bitmap,
                         padding=payload)

    @staticmethod
    def from_hex(hex_string: str) -> Optional['CompoundACK']:
        """Creates a CompoundACK from a hexadecimal string."""

        if hex_string is None:
            return None

        as_bin = hex_to_bin(hex_string)

        if len(as_bin) != DOWNLINK_MTU:
            raise LengthMismatchError(
                "Compound ACK was not of length DOWNLINK_MTU."
            )

        rule = Rule.from_hex(hex_string)

        dtag_idx = rule.RULE_ID_SIZE
        w_idx = rule.RULE_ID_SIZE + rule.T
        c_idx = rule.RULE_ID_SIZE + rule.T + rule.M

        header = as_bin[:rule.ACK_HEADER_LENGTH]

        dtag = header[dtag_idx:dtag_idx + rule.T]
        w = header[w_idx:w_idx + rule.M]
        c = header[c_idx:c_idx + 1]

        payload = as_bin[rule.ACK_HEADER_LENGTH:]
        bitmap = payload[:rule.WINDOW_SIZE]
        padding = payload[rule.WINDOW_SIZE:]

        windows = [w]
        bitmaps = [bitmap]

        while len(padding) >= rule.M + rule.WINDOW_SIZE:
            if is_monochar(padding, '0'):
                break
            windows.append(padding[:rule.M])
            bitmaps.append(padding[rule.M:rule.M + rule.WINDOW_SIZE])
            padding = padding[rule.M + rule.WINDOW_SIZE:]

        return CompoundACK(rule, dtag, windows, c, bitmaps, padding)
