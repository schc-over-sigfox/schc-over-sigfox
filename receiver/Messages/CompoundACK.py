from Entities.exceptions import LengthMismatchError
from Messages.ACK import ACK
from utils.schc_utils import is_monochar, zfill

# This class extend the regular ACK into the SCHC Compound ACK defined in
# https://datatracker.ietf.org/doc/html/draft-ietf-lpwan-schc-compound-ack-00


class CompoundACK(ACK):
    TUPLES = None

    def __init__(self, profile, rule_id, dtag, windows, c, bitmaps, padding=''):
        self.TUPLES = []

        if len(windows) != len(bitmaps):
            print("ERROR: Window array and bitmap array must be of same length.")
            raise LengthMismatchError

        first_window = windows[0]
        first_bitmap = bitmaps[0]
        self.TUPLES.append((first_window, first_bitmap))

        payload_arr = []
        for i in range(len(windows[:-1])):
            payload_arr.extend([windows[i + 1], bitmaps[i + 1]])
            self.TUPLES.append((windows[i + 1], bitmaps[i + 1]))

        payload = ''.join(payload_arr) + padding

        super().__init__(profile, rule_id, dtag, first_window, c, first_bitmap, padding=payload)

    @staticmethod
    def parse_from_string(profile, s):
        ack = s
        index_dtag = profile.RULE_ID_SIZE
        index_first_window = index_dtag + profile.T
        index_c = index_first_window + profile.M
        index_first_bitmap = index_c + 1
        index_padding = index_first_bitmap + profile.BITMAP_SIZE

        windows = [ack[index_first_window:index_c]]
        bitmaps = [ack[index_first_bitmap:index_padding]]
        padding = ack[index_padding:]

        while len(padding) >= profile.M + profile.BITMAP_SIZE:
            if is_monochar(padding, "0"):
                break
            next_window = padding[:profile.M]
            windows.append(padding[:profile.M])
            bitmaps.append(padding[profile.M:profile.M + profile.BITMAP_SIZE])
            padding = padding[profile.M + profile.BITMAP_SIZE:]

        return CompoundACK(profile,
                           ack[:index_dtag],
                           ack[index_dtag:index_first_window],
                           windows,
                           ack[index_c],
                           bitmaps,
                           padding)

    @staticmethod
    def parse_from_hex(profile, h):
        ack = zfill(bin(int(h, 16))[2:], profile.DOWNLINK_MTU)
        return CompoundACK.parse_from_string(profile, ack)

    @staticmethod
    def parse_from_bytes(profile, b):
        ack = ''.join("{:08b}".format(int(byte)) for byte in b)
        return CompoundACK.parse_from_string(profile, ack)
