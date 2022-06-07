"""
Loss masks control deterministic combinations of losses.
0 -> Don't lose the message
1 -> Lose the message, accept its retransmission
2 -> Lose the message and its first retransmission, accept the following
i -> Lose the message i times
"""

loss_mask_0 = {
    "fragment": {
        "0": "0000000",
        "1": "0000000",
        "2": "0000000",
        "3": "0000000"
    },
    "ack": {
        "0": "0",
        "1": "0",
        "2": "0",
        "3": "0"
    },
    "expected": "W0F0W0F1W0F2W0F3W0F4W0F5W0F6"
                "W1F0W1F1W1F2W1F3W1F4W1F5W1F6"
                "W2F0W2F1W2F2W2F3W2F4W2F5W2F6"
                "W3F0W3F1W3F2W3F3W3F4W3F5W3F6"
}

loss_mask_1 = {
    "fragment": {
        "0": "0001000",
        "1": "0000000",
        "2": "0000000",
        "3": "0000000"
    },
    "ack": {
        "0": "0",
        "1": "0",
        "2": "0",
        "3": "0"
    },
    "expected": "W0F0W0F1W0F2W0F4W0F5W0F6W0F3"
                "W1F0W1F1W1F2W1F3W1F4W1F5W1F6"
                "W2F0W2F1W2F2W2F3W2F4W2F5W2F6"
                "W3F0W3F1W3F2W3F3W3F4W3F5W3F6"
}

loss_mask_2 = {
    "fragment": {
        "0": "0000000",
        "1": "0000000",
        "2": "0011000",
        "3": "0000000"
    },
    "ack": {
        "0": "0",
        "1": "0",
        "2": "0",
        "3": "0"
    },
    "expected": "W0F0W0F1W0F2W0F3W0F4W0F5W0F6"
                "W1F0W1F1W1F2W1F3W1F4W1F5W1F6"
                "W2F0W2F1W2F4W2F5W2F6W2F2W2F3"
                "W3F0W3F1W3F2W3F3W3F4W3F5W3F6"
}

loss_mask_3 = {
    "fragment": {
        "0": "0000001",
        "1": "0000000",
        "2": "0011000",
        "3": "0000000"
    },
    "ack": {
        "0": "0",
        "1": "0",
        "2": "0",
        "3": "0"
    },
    "expected": "W0F0W0F1W0F2W0F3W0F4W0F5"
                "W1F0W1F1W1F2W1F3W1F4W1F5W1F6W0F6"
                "W2F0W2F1W2F4W2F5W2F6W2F2W2F3"
                "W3F0W3F1W3F2W3F3W3F4W3F5W3F6"
}

loss_mask_4 = {
    "fragment": {
        "0": "0000001",
        "1": "0000000",
        "2": "0011001",
        "3": "0000000"
    },
    "ack": {
        "0": "0",
        "1": "0",
        "2": "0",
        "3": "0"
    },
    "expected": "W0F0W0F1W0F2W0F3W0F4W0F5"
                "W1F0W1F1W1F2W1F3W1F4W1F5W1F6W0F6"
                "W2F0W2F1W2F4W2F5"
                "W3F0W3F1W3F2W3F3W3F4W3F5W3F6W2F2W2F3W2F6W3F6"
}

loss_mask_5 = {
    "fragment": {
        "0": "0010000",
        "1": "0000001",
        "2": "0100000",
        "3": "0000010"
    },
    "ack": {
        "0": "0",
        "1": "0",
        "2": "0",
        "3": "0"
    },
    "expected": "W0F0W0F1W0F3W0F4W0F5W0F6W0F2"
                "W1F0W1F1W1F2W1F3W1F4W1F5"
                "W2F0W2F2W2F3W2F4W2F5W2F6W1F6W2F1"
                "W3F0W3F1W3F2W3F3W3F4W3F6W3F5W3F6"
}

loss_mask_6 = {
    "fragment": {
        "0": "0010002",
        "1": "0000001",
        "2": "0100000",
        "3": "0000010"
    },
    "ack": {
        "0": "0",
        "1": "0",
        "2": "0",
        "3": "0"
    },
    "expected": "W0F0W0F1W0F3W0F4W0F5"
                "W1F0W1F1W1F2W1F3W1F4W1F5"
                "W2F0W2F2W2F3W2F4W2F5W2F6W0F2W1F6W2F1"
                "W3F0W3F1W3F2W3F3W3F4W3F6W0F6W3F5W3F6"
}
