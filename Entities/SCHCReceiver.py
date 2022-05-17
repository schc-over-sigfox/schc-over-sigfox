from Entities.Logger import Logger
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import ReceiverAbortError, LengthMismatchError, SenderAbortError
from Messages import CompoundACK
from Messages.Fragment import Fragment
from Messages.Header import Header
from Messages.ReceiverAbort import ReceiverAbort
from db.JSONStorage import JSONStorage


class SCHCReceiver:

    def __init__(self, profile: SigfoxProfile, storage: JSONStorage):
        self.PROFILE = profile
        storage.ROOT += f"rule_{self.PROFILE.RULE.ID}/"
        self.STORAGE = storage
        self.LOGGER = Logger('', Logger.DEBUG)

    def schc_recv(self, fragment: Fragment, timestamp: int) -> CompoundACK:
        """Receives a SCHC Fragment and processes it accordingly."""

        if self.session_was_aborted():
            self.LOGGER.error("Session aborted.")
            raise ReceiverAbortError

        if self.inactivity_timer_expired(timestamp):
            self.STORAGE.delete("state/TIMESTAMP")
            self.LOGGER.error("Inactivity Timer expired.")
            return self.generate_receiver_abort(fragment.HEADER)

        self.STORAGE.write(str(timestamp), "state/TIMESTAMP")

        if len(fragment.to_bin()) > self.PROFILE.UPLINK_MTU:
            raise LengthMismatchError("Fragment is larger than uplink MTU.")

        if fragment.is_sender_abort():
            self.LOGGER.error(f"[Sender-Abort] Aborting session for rule {self.PROFILE.RULE.ID}")
            raise SenderAbortError

        current_window = fragment.WINDOW
        fragment_index = fragment.INDEX

        self.LOGGER.info(f"Received fragment W{current_window}F{fragment_index}")

        if not self.fragment_is_expected(fragment):
            self.reset()

    def session_was_aborted(self) -> bool:
        """Checks if an "ABORT" node exists in the Storage."""
        return self.STORAGE.exists(f"rule_{self.PROFILE.RULE.ID}/state/ABORT")

    def inactivity_timer_expired(self, current_timestamp) -> bool:
        """Checks if the difference between the current timestamp and the previous one exceeds the timeout value."""
        if self.STORAGE.exists(f"rule_{self.PROFILE.RULE.ID}/TIMESTAMP"):
            previous_timestamp = self.STORAGE.read(f"rule_{self.PROFILE.RULE.ID}/TIMESTAMP")
            if abs(current_timestamp - previous_timestamp) > self.PROFILE.INACTIVITY_TIMEOUT:
                return True
        return False

    def generate_receiver_abort(self, header: Header) -> ReceiverAbort:
        """Creates a Receiver-Abort, stores it in the Storage and returns it."""
        abort = ReceiverAbort(header)
        self.STORAGE.write(abort.to_hex(), "state/ABORT")
        return abort

    def fragment_is_expected(self, fragment: Fragment) -> bool:
        """Checks if a fragment is expected according to the SCHC state machine."""
        ...

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