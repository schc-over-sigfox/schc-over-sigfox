from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import FormatError, LengthMismatchError, SenderAbortError, SCHCTimeoutError
from Messages.Fragment import Fragment
from Messages.ReceiverAbort import ReceiverAbort
from schc_utils import replace_bit, send_ack

mode = 'filedir'

if mode == 'firebase':
    from firebase_utils import *
elif mode == 'filedir':
    from filedir_utils import *


class SCHCReceiver:
    PROFILE = None
    BUFFER_SIZE = None
    N = None
    M = None
    SIGFOX_SN = None
    DATA = None
    FRAGMENT = None
    FRAGMENT_NUMBER = None
    CURRENT_WINDOW = None
    CURRENT_BITMAP = None
    TIMESTAMP = None
    DEVICE = None

    def __init__(self, request_dict):
        # Get data and Sigfox Sequence Number.
        fragment = request_dict["data"]
        self.SIGFOX_SN = request_dict["seqNumber"]
        self.TIMESTAMP = int(request_dict["time"])
        self.DEVICE = request_dict["device"]

        header_first_hex = fragment[0]

        if header_first_hex == '0' or header_first_hex == '1':
            header = bytes.fromhex(fragment[:2])
            payload = bytearray.fromhex(fragment[2:])
            header_bytes = 1
        elif header_first_hex == 'f' or header_first_hex == '2':
            header = bytearray.fromhex(fragment[:4])
            payload = bytearray.fromhex(fragment[4:])
            header_bytes = 2
        else:
            print("Wrong header in fragment")
            raise FormatError

        # Initialize SCHC variables
        self.FRAGMENT = Fragment(self.PROFILE, [header, payload])

        if self.FRAGMENT.is_sender_abort():
            self.sender_abort_procedure()
            raise SenderAbortError

        self.PROFILE = SigfoxProfile("UPLINK", "ACK ON ERROR", header_bytes)
        self.BUFFER_SIZE = self.PROFILE.UPLINK_MTU
        self.N = self.PROFILE.N
        self.M = self.PROFILE.M

        if len(fragment) / 2 * 8 > self.BUFFER_SIZE:  # Fragment is hex, 1 hex = 1/2 byte
            print("Fragment size is greater than buffer size")
            raise LengthMismatchError

        # Get current window for this fragment.
        self.CURRENT_WINDOW = int(self.FRAGMENT.HEADER.W, 2)

        # Get the current bitmap.
        self.CURRENT_BITMAP = read_blob(f"all_windows/window_{self.CURRENT_WINDOW}/bitmap_{self.CURRENT_WINDOW}")

    def check_inactivity_timer(self):
        if exists_blob("timestamp"):

            try:
                # Check time validation.
                last_time = int(read_blob("timestamp"))

                # If this is not the very first fragment and the inactivity timer has been reached, abort session.
                if self.FRAGMENT.NUMBER != 0 and self.CURRENT_WINDOW != 0 and self.TIMESTAMP - last_time > self.PROFILE.INACTIVITY_TIMER_VALUE:
                    print("[RECV] Inactivity timer reached. Ending session.")
                    raise SCHCTimeoutError

            except SCHCTimeoutError:
                return self.send_receiver_abort()

    def update_bitmap(self):
        if self.FRAGMENT.NUMBER == self.PROFILE.WINDOW_SIZE - 1:
            print("[RECV] This seems to be the final fragment.")
            self.CURRENT_BITMAP = replace_bit(self.CURRENT_BITMAP, len(self.CURRENT_BITMAP) - 1, '1')
        else:
            self.CURRENT_BITMAP = replace_bit(self.CURRENT_BITMAP, self.FRAGMENT.NUMBER, '1')

    def send_receiver_abort(self):
        receiver_abort = ReceiverAbort(self.PROFILE, self.FRAGMENT.HEADER)
        print("Sending Receiver Abort")
        response_json = send_ack(self.DEVICE, receiver_abort)
        print(f"Response content -> {response_json}")
        return response_json, 200