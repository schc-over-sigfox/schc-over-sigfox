from typing import Optional

from Entities.Logger import Logger
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import ReceiverAbortError, LengthMismatchError, SenderAbortError
from Messages.ACK import ACK
from Messages.CompoundACK import CompoundACK
from Messages.Fragment import Fragment
from Messages.Header import Header
from Messages.ReceiverAbort import ReceiverAbort
from db.JSONStorage import JSONStorage
from utils.casting import int_to_bin, bin_to_int
from utils.misc import replace_char


class SCHCReceiver:

    def __init__(self, profile: SigfoxProfile, storage: JSONStorage):
        self.PROFILE = profile
        self.STORAGE = storage
        self.LOGGER = Logger('', Logger.DEBUG)

    def session_was_aborted(self) -> bool:
        """Checks if an "ABORT" node exists in the Storage."""
        return self.STORAGE.exists(f"state/ABORT")

    def inactivity_timer_expired(self, current_timestamp) -> bool:
        """Checks if the difference between the current timestamp and the previous one exceeds the timeout value."""
        if self.STORAGE.exists(f"state/TIMESTAMP"):
            previous_timestamp = self.STORAGE.read(f"state/TIMESTAMP")
            if abs(current_timestamp - previous_timestamp) > self.PROFILE.INACTIVITY_TIMEOUT:
                return True
        return False

    def generate_receiver_abort(self, header: Header) -> ReceiverAbort:
        """Creates a Receiver-Abort, stores it in the Storage and returns it."""
        abort = ReceiverAbort(header)
        self.STORAGE.write(abort.to_hex(), "state/ABORT")
        return abort

    def fragment_is_requested(self, fragment: Fragment) -> bool:
        """Checks if the fragment was requested for retransmission."""
        requested_fragments = self.STORAGE.read("state/REQUESTED")
        window = f"W{fragment.WINDOW}"
        index = fragment.INDEX
        return window in requested_fragments.keys() and index in requested_fragments[window]

    def fragment_is_receivable(self, fragment: Fragment) -> bool:
        """
        Checks if a fragment is expected according to the SCHC state machine. The checks to decide this are:

        * If the fragment is an All-1, and if it was already received, it can be processed again
         (The only fragment that can be received more than once is the All-1) -> Receivable
        * If there is no previous fragment, then there is no active SCHC session -> Receivable
        * If the last fragment was a Sender-Abort, the previous SCHC session was terminated -> Receivable
        * If the last fragment was an All-1 and the ACK it generated was complete,
         the previous SCHC session was completed -> Receivable
        * If the new fragment was requested to be retransmitted, it is expected to arrive -> Receivable
        * If the new fragment is of a higher window than the last one, accept it -> Receivable
        * If both fragments are part of the same window, but the new one has a fragment index greater than the last one,
         accept it -> Receivable
        * If both fragments have the same window and index, but they are an All-0 or an All-1, accept it since
         ACK-REQs can be sent multiple times -> Receivable
        * Otherwise -> Not receivable.
        """

        if not fragment.is_all_1() and self.fragment_was_already_received(fragment):
            return False

        if not self.STORAGE.exists("state/LAST_FRAGMENT"):
            return True

        last_fragment = Fragment.from_hex(self.STORAGE.read("state/LAST_FRAGMENT"))

        if last_fragment is not None and last_fragment.is_sender_abort():
            return True

        elif last_fragment.is_all_1():
            last_ack = CompoundACK.from_hex(self.STORAGE.read("state/LAST_ACK"))
            if last_ack is not None and last_ack.is_complete():
                return True

        if self.fragment_is_requested(fragment):
            return True

        if fragment.WINDOW > last_fragment.WINDOW:
            return True
        elif fragment.WINDOW == last_fragment.WINDOW:
            if fragment.INDEX > last_fragment.INDEX:
                return True
            elif fragment.INDEX == last_fragment.INDEX and fragment.is_all_1():
                return True

        return False

    def start_new_session(self, retain_state: bool) -> None:
        """Deletes data of the SCHC session for the current Rule ID of the Receiver."""

        if retain_state:
            state = self.STORAGE.read("state")
            try:
                _ = state.pop("REQUESTED")
            except KeyError:
                pass
        else:
            state = {}

        root = {
            "fragments": {},
            "reassembly": {},
            "state": state
        }

        bitmaps = {f"w{i}": '0' * self.PROFILE.WINDOW_SIZE for i in range(self.PROFILE.MAX_WINDOW_NUMBER)}
        root["state"]["bitmaps"] = bitmaps

        self.STORAGE.write(root)
        self.STORAGE.save()

    def get_pending_ack(self, fragment: Fragment) -> Optional[CompoundACK]:
        """Checks if there exists an ACK to be retransmitted in the Storage."""

        last_ack = CompoundACK.from_hex(self.STORAGE.read("state/LAST_ACK"))

        if last_ack is not None:
            if last_ack.is_complete():
                if fragment.is_all_1():
                    last_fragment = Fragment.from_hex(self.STORAGE.read("state/LAST_FRAGMENT"))
                    if last_fragment is not None and last_fragment.is_all_1():
                        return last_ack
                else:
                    self.STORAGE.delete("state/LAST_ACK")
                    self.STORAGE.delete("state/LAST_FRAGMENT")
            else:
                self.LOGGER.warning("LAST_ACK was not complete. "
                                    "Maybe the previous session was terminated abruptly?")

        return None

    def update_bitmap(self, fragment: Fragment) -> None:
        """Updates a stored bitmap according to the window and FCN of the fragment."""
        bitmap = self.STORAGE.read(f"state/bitmaps/w{fragment.WINDOW}")
        if bitmap is None:
            bitmap = '0' * self.PROFILE.WINDOW_SIZE
        updated_bitmap = replace_char(bitmap, fragment.INDEX, '1')
        self.STORAGE.write(updated_bitmap, f"state/bitmaps/w{fragment.WINDOW}")

    def fragment_was_already_received(self, fragment: Fragment):
        """Checks if the fragment was already processed by the receiver."""

        bitmap = self.STORAGE.read(f"state/bitmaps/w{fragment.WINDOW}")

        if bitmap is not None and bitmap[fragment.INDEX] == '1':
            return True

        if fragment.is_all_1():
            last_ack = CompoundACK.from_hex(self.STORAGE.read("state/LAST_ACK"))
            if last_ack is not None and last_ack.is_complete():
                last_fragment = Fragment.from_hex(self.STORAGE.read("state/LAST_FRAGMENT"))
                if fragment.to_hex() == last_fragment.to_hex():
                    return True

        return False

    def generate_compound_ack(self, fragment: Fragment) -> Optional[CompoundACK]:
        """Reads data from the stored bitmaps and generates (or not) an ACK accordingly."""

        current_window = fragment.WINDOW
        windows = []
        bitmaps = []

        for i in range(current_window + 1):
            bitmap = self.STORAGE.read(f"state/bitmaps/w{current_window}")
            lost = False

            if fragment.is_all_1() and i == current_window:
                expected_fragments = bin_to_int(fragment.HEADER.RCS)
                expected_bitmap = f"{'1' * (expected_fragments - 1)}" \
                                  f"{'0' * (self.PROFILE.WINDOW_SIZE - expected_fragments)}" \
                                  f"1"
                if bitmap != expected_bitmap:
                    lost = True
            elif '0' in bitmap:
                lost = True

            if lost:
                windows.append(int_to_bin(i, self.PROFILE.M))
                bitmaps.append(bitmap)

        losses_were_found = bitmaps != [] and windows != []

        if losses_were_found:
            return CompoundACK(
                profile=self.PROFILE,
                dtag=fragment.HEADER.DTAG,
                windows=windows,
                c='0',
                bitmaps=bitmaps,
            )

        else:
            if fragment.is_all_1():
                return CompoundACK(
                    profile=self.PROFILE,
                    dtag=fragment.HEADER.DTAG,
                    windows=[fragment.HEADER.W],
                    c='0',
                    bitmaps=['0' * self.PROFILE.WINDOW_SIZE],
                )

        return None

    def schc_recv(self, fragment: Fragment, timestamp: int) -> Optional[ACK]:
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

        if not self.fragment_is_receivable(fragment):
            self.start_new_session(retain_state=False)

        if not self.fragment_was_already_received(fragment):
            self.STORAGE.write(fragment.to_hex(), f"fragments/w{current_window}/f{fragment_index}")
        else:
            self.LOGGER.info(f"Fragment W{current_window}F{fragment_index} was already received")

        pending_ack = self.get_pending_ack(fragment)
        if pending_ack is not None:
            self.LOGGER.info(f"Pending ACK retrieved.")
            return pending_ack

        self.update_bitmap(fragment)

        if not fragment.expects_ack():
            return None

        return self.generate_compound_ack(fragment)
