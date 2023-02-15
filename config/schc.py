"""Contains global variables that control SCHC transmissions."""

UPLINK_MTU = 96
DOWNLINK_MTU = 64
FR_MODE = "ACK ON ERROR"
RETRANSMISSION_TIMEOUT = 43200  # in seconds
SIGFOX_DL_TIMEOUT = 43200  # in seconds
INACTIVITY_TIMEOUT = 43200  # in seconds
MAX_ACK_REQUESTS = 5
L2_WORD_SIZE = 8
DELAY_BETWEEN_FRAGMENTS = 0  # in seconds

# Sender config

# Disables the MAX_ACK_REQUESTS limit.
# Default: False
DISABLE_MAX_ACK_REQUESTS = True
