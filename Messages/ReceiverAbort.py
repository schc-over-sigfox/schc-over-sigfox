from Messages.ACK import ACK
from Messages.Header import Header
from config.schc import L2_WORD_SIZE


class ReceiverAbort(ACK):

    def __init__(self, header: Header) -> None:
        rule = header.RULE
        dtag = header.DTAG
        w = '1' * rule.M
        c = '1'

        header_length = len(rule.STR + dtag + w + c)

        if header_length % L2_WORD_SIZE != 0:
            padding = '1' * (L2_WORD_SIZE - header_length % L2_WORD_SIZE)
        else:
            padding = ''

        padding += '1' * L2_WORD_SIZE

        super().__init__(rule, dtag, w, c, bitmap='', padding=padding)
