"""
Loss masks control deterministic combinations of losses.
0 -> Don't lose the message
1 -> Lose the message, accept its retransmission
2 -> Lose the message and its first retransmission, accept the following
i -> Lose the message i times
"""

loss_masks = [
    # Loss mask 0
    {
        "fragment": {
            "0": "0000000"
        },
        "ack": {
            "0": "0",
        },
        "expected": "W0F0W0F6A0"
    },
    # Loss mask 1
    # This loss mask, when executed after loss mask 0, requires
    # RESET_DATA_AFTER_REASSEMBLY set to False
    {
        "fragment": {
            "0": "1000000"
        },
        "ack": {
            "0": "0",
        },
        "expected": "W0F6A0"
                    "W0F0W0F6A0"
    },
    # Loss mask 2
    {
        "fragment": {
            "0": "0000001"
        },
        "ack": {
            "0": "0",
        },
        "expected": "W0F0W0F6A0"
    },
]
