"""Contains global variables that control SCHC transmissions."""

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

# ========= Receiver config

# Makes SCHCReceiver delete all data from a SCHC session after reassembly.
# Default: False
RESET_DATA_AFTER_REASSEMBLY = False

# Enables SCHCReceiver to check for Sigfox callback retries.
# Default: True
CHECK_FOR_CALLBACK_RETRIES = True

# Disables SCHCReceiver to perform inactivity timer validation.
# Default: False
DISABLE_INACTIVITY_TIMEOUT = False

RECEIVER_URL = "http://localhost:5000/receive"
REASSEMBLER_URL = "http://localhost:5000/reassemble"
