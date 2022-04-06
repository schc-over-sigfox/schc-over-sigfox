from math import ceil, floor

from Messages.Fragment import Fragment
from utils.schc_utils import zfill


class Fragmenter:

    def __init__(self, profile, schc_packet):
        self.PROFILE = profile
        self.SCHC_PACKET = schc_packet
        self.CURRENT_FRAGMENT_NUMBER = 0
        self.FRAGMENT_LIST = []

    def fragment(self):
        payload_max_length = int((self.PROFILE.UPLINK_MTU - self.PROFILE.HEADER_LENGTH) / 8)
        message = self.SCHC_PACKET
        n = self.PROFILE.N
        m = self.PROFILE.M
        number_of_fragments = int(ceil(float(len(message)) / payload_max_length))

        print("[FRGM] Fragmenting message into " + str(number_of_fragments) + " pieces...")

        for i in range(number_of_fragments):
            self.CURRENT_FRAGMENT_NUMBER = i
            payload = message[i * payload_max_length:(i + 1) * payload_max_length]
            f = self.generate_fragment(payload, number_of_fragments)
            self.FRAGMENT_LIST.append(f)

        self.CURRENT_FRAGMENT_NUMBER = 0

        return self.FRAGMENT_LIST

    def generate_fragment(self, payload, number_of_fragments=None):
        if number_of_fragments is None:
            number_of_fragments = self.PROFILE.MAX_FRAGMENT_NUMBER

        payload_max_length = int((self.PROFILE.UPLINK_MTU - self.PROFILE.HEADER_LENGTH) / 8)
        n = self.PROFILE.N
        m = self.PROFILE.M
        w = zfill(bin(int(floor((self.CURRENT_FRAGMENT_NUMBER / (2 ** n - 1) % (2 ** m)))))[2:], m)
        fcn = zfill(bin((2 ** n - 2) - (self.CURRENT_FRAGMENT_NUMBER % (2 ** n - 1)))[2:], n)

        if self.SCHC_PACKET is None or len(self.SCHC_PACKET) <= 300:
            rule_id = "000"
            dtag = ""
            if len(payload) < payload_max_length or self.CURRENT_FRAGMENT_NUMBER == number_of_fragments - 1:
                fcn = "111"
            else:
                fcn = zfill(bin((2 ** n - 2) - (self.CURRENT_FRAGMENT_NUMBER % (2 ** n - 1)))[2:], n)
        else:
            rule_id = "11110000"
            dtag = ""
            if len(payload) < payload_max_length or self.CURRENT_FRAGMENT_NUMBER == number_of_fragments - 1:
                fcn = "11111"
            else:
                fcn = zfill(bin((2 ** n - 2) - (self.CURRENT_FRAGMENT_NUMBER % (2 ** n - 1)))[2:], n)

        h = rule_id + dtag + w + fcn
        header = bytes(int(h[i:i + 8], 2) for i in range(0, len(h), 8))

        self.CURRENT_FRAGMENT_NUMBER += 1
        return Fragment(self.PROFILE, [header, payload])
