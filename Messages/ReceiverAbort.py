from Messages.ACK import ACK
from Messages.ACKHeader import ACKHeader
from config.schc import L2_WORD_SIZE


class ReceiverAbort(ACK):

    def __init__(self, header: ACKHeader):
        profile = header.PROFILE
        dtag = header.DTAG
        w = '1' * profile.M
        c = '1'

        header_length = len(str(profile.RULE) + dtag + w + c)

        if header_length % L2_WORD_SIZE != 0:
            padding = '1' * (L2_WORD_SIZE - header_length % L2_WORD_SIZE)
        else:
            padding = ''

        padding += '1' * L2_WORD_SIZE

        super().__init__(profile, dtag, w, c, bitmap='', padding=padding)
