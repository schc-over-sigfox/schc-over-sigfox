from typing import Optional

from Entities.Logger import Logger
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import ReceiverAbortError, LengthMismatchError, \
    SenderAbortError
from Messages.ACK import ACK
from Messages.CompoundACK import CompoundACK
from Messages.Fragment import Fragment
from Messages.Header import Header
from Messages.ReceiverAbort import ReceiverAbort
from config import schc as config
from db.JSONStorage import JSONStorage
from utils.casting import int_to_bin, bin_to_int
from utils.misc import replace_char


class SCHCReceiver:

    def __init__(self, profile: SigfoxProfile, storage: JSONStorage):
        self.PROFILE: SigfoxProfile = profile
        self.STORAGE: JSONStorage = storage
        self.STORAGE.change_ref(f"rule_{self.PROFILE.RULE.ID}")
        self.LOGGER: Logger = Logger(Logger.DEBUG)

        if self.STORAGE.is_empty():
            self.start_new_session(retain_previous_data=False)

    def session_was_aborted(self) -> bool:
        """Checks if an "ABORT" node exists in the Storage."""
        return self.STORAGE.exists("state/ABORT")

    def inactivity_timer_expired(self, current_timestamp: int) -> bool:
        """Checks if the difference between the current timestamp and the
        previous one exceeds the timeout value."""
        if config.DISABLE_INACTIVITY_TIMEOUT:
            return False
        if self.STORAGE.exists("state/TIMESTAMP"):
            previous_timestamp = int(self.STORAGE.read("state/TIMESTAMP"))
            if abs(
                    current_timestamp - previous_timestamp
            ) > self.PROFILE.INACTIVITY_TIMEOUT:
                return True
        return False

    def generate_receiver_abort(self, header: Header) -> ReceiverAbort:
        """Creates a Receiver-Abort, stores it in the Storage
        and returns it."""
        abort = ReceiverAbort(header)
        self.STORAGE.write(abort.to_hex(), "state/ABORT")
        return abort

    def fragment_is_requested(self, fragment: Fragment) -> bool:
        """Checks if the fragment was requested for retransmission."""
        requested_fragments = self.STORAGE.read("state/requested")
        if requested_fragments is None:
            return False
        window = f"w{fragment.WINDOW}"
        index = fragment.INDEX

        return window in requested_fragments.keys() \
               and index in requested_fragments[window]

    def fragment_is_receivable(self, fragment: Fragment) -> bool:
        """
        Checks if a fragment is expected according to the SCHC state machine.
        The checks to decide this are:

        * If the fragment is an All-1, and if it was already received, it can
        be processed again
         (The only fragment that can be received more than once is the All-1)
         -> Receivable
        * If there is no previous fragment, then there is no active SCHC
        session -> Receivable
        * If the last fragment was a Sender-Abort, the previous SCHC session
        was terminated -> Receivable
        * If the last fragment was an All-1 and the ACK it generated was
        complete,
         the previous SCHC session was completed -> Receivable
        * If the new fragment was requested to be retransmitted, it is
        expected to arrive -> Receivable
        * If the new fragment is of a higher window than the last one,
        accept it -> Receivable
        * If both fragments are part of the same window, but the new one
        has a fragment index greater than the last one,
         accept it -> Receivable
        * If both fragments have the same window and index, but they are
        an All-0 or an All-1, accept it since
         ACK-REQs can be sent multiple times -> Receivable
        * Otherwise -> Not receivable.
        """

        if not fragment.is_all_1() and self.fragment_was_already_received(
                fragment):
            return False

        if not self.STORAGE.exists("state/LAST_FRAGMENT"):
            return True

        last_fragment = Fragment.from_hex(
            self.STORAGE.read("state/LAST_FRAGMENT")
        )

        if last_fragment is not None and last_fragment.is_sender_abort():
            return True

        if last_fragment.is_all_1():
            last_ack = CompoundACK.from_hex(
                self.STORAGE.read("state/LAST_ACK"))
            if last_ack is not None and last_ack.is_complete():
                return True

        if self.fragment_is_requested(fragment):
            return True

        if fragment.WINDOW > last_fragment.WINDOW:
            return True
        if fragment.WINDOW == last_fragment.WINDOW:
            if fragment.INDEX > last_fragment.INDEX:
                return True
            if fragment.INDEX == last_fragment.INDEX and fragment.is_all_1():
                return True

        return False

    def start_new_session(self, retain_previous_data: bool) -> None:
        """Deletes data of the SCHC session for the current Rule ID
        of the Receiver."""

        if retain_previous_data:
            state = self.STORAGE.read("state")
            try:
                state["bitmaps"] = {}
                state["requested"] = {}
            except KeyError:
                pass
        else:
            state = {
                "requested": {},
                "bitmaps": {}
            }

        root = {
            "fragments": {},
            "reassembly": {},
            "state": state
        }

        self.STORAGE.write(root)
        self.STORAGE.save()

    def get_pending_ack(self, fragment: Fragment) -> Optional[CompoundACK]:
        """Checks if there exists an ACK to be retransmitted in the Storage."""

        last_ack = CompoundACK.from_hex(self.STORAGE.read("state/LAST_ACK"))

        if last_ack is not None:
            if last_ack.is_complete():
                if fragment.is_all_1():
                    last_fragment = Fragment.from_hex(
                        self.STORAGE.read("state/LAST_FRAGMENT")
                    )
                    if last_fragment is not None and last_fragment.is_all_1():
                        return last_ack
                else:
                    self.STORAGE.delete("state/LAST_ACK")
                    self.STORAGE.delete("state/LAST_FRAGMENT")
            else:
                self.LOGGER.warning(
                    "LAST_ACK was not complete. "
                    "Maybe the previous session was terminated abruptly?"
                )

        return None

    def get_receiver_abort(self) -> CompoundACK:
        """Obtains a receiver abort from the state/ABORT node
        in the Storage."""
        abort = CompoundACK.from_hex(self.STORAGE.read("state/ABORT"))
        self.STORAGE.delete("state/ABORT")
        return abort

    def update_bitmap(self, fragment: Fragment) -> None:
        """Updates a stored bitmap according to the window
        and FCN of the fragment."""

        for i in range(fragment.WINDOW):
            if not self.STORAGE.exists(f"state/bitmaps/w{i}"):
                self.STORAGE.write('0' * self.PROFILE.WDW_SIZE,
                                   f"state/bitmaps/w{i}")

        bitmap = self.STORAGE.read(f"state/bitmaps/w{fragment.WINDOW}")
        if bitmap is None:
            bitmap = '0' * self.PROFILE.WDW_SIZE
        updated_bitmap = replace_char(bitmap, fragment.INDEX, '1')
        self.STORAGE.write(updated_bitmap, f"state/bitmaps/w{fragment.WINDOW}")

    def fragment_was_already_received(self, fragment: Fragment) -> bool:
        """Checks if the fragment was already processed by the receiver."""

        bitmap = self.STORAGE.read(f"state/bitmaps/w{fragment.WINDOW}")

        if bitmap is not None and bitmap[fragment.INDEX] == '1':
            return True

        if fragment.is_all_1():
            last_ack = CompoundACK.from_hex(
                self.STORAGE.read("state/LAST_ACK"))
            if last_ack is not None and last_ack.is_complete():
                last_fragment = Fragment.from_hex(
                    self.STORAGE.read("state/LAST_FRAGMENT")
                )
                if fragment.to_hex() == last_fragment.to_hex():
                    return True
        return False

    def update_requested(self, ack: CompoundACK) -> None:
        """Updates the dictionary of requested fragments,
        using the tuples of a Compound ACK."""
        if not ack.is_complete():
            requested = self.STORAGE.read("state/requested")

            if requested is None:
                requested = {}

            for tup in ack.TUPLES:
                window = tup[0]
                bitmap = tup[1]
                lost_fragments = [idx for (idx, bit) in enumerate(bitmap) if
                                  bit != '1']
                requested.update({f"w{bin_to_int(window)}": lost_fragments})

            self.STORAGE.write(requested, "state/requested")

    def generate_compound_ack(self, fragment: Fragment) -> Optional[
        CompoundACK]:
        """Reads data from the stored bitmaps and generates (or not)
        an ACK accordingly."""
        current_window = fragment.WINDOW
        windows = []
        bitmaps = []

        for i in range(current_window + 1):
            bitmap = self.STORAGE.read(f"state/bitmaps/w{i}")
            lost = False

            if fragment.is_all_1() and i == current_window:
                expected_fragments = bin_to_int(fragment.HEADER.RCS)
                expected_bitmap = \
                    f"{'1' * (expected_fragments - 1)}" \
                    f"{'0' * (self.PROFILE.WDW_SIZE - expected_fragments)}" \
                    f"1"
                if bitmap != expected_bitmap:
                    lost = True
            elif '0' in bitmap:
                lost = True

            if lost:
                windows.append(int_to_bin(i, self.PROFILE.M))
                bitmaps.append(bitmap)

        losses_were_found = bitmaps and windows
        ack = None

        if losses_were_found:
            ack = CompoundACK(
                profile=self.PROFILE,
                dtag=fragment.HEADER.DTAG,
                windows=windows,
                c='0',
                bitmaps=bitmaps,
            )
        else:
            if fragment.is_all_1():
                ack = CompoundACK(
                    profile=self.PROFILE,
                    dtag=fragment.HEADER.DTAG,
                    windows=[fragment.HEADER.W],
                    c='1',
                    bitmaps=['0' * self.PROFILE.WDW_SIZE],
                )
                self.STORAGE.write(ack.to_hex(), "state/LAST_ACK")

        if ack is not None:
            self.update_requested(ack)
            return ack

        return None

    def upload_fragment(self, fragment: Fragment) -> None:
        """Uploads the hex representation of a fragment into the Storage."""

        if self.fragment_was_already_received(fragment):
            self.LOGGER.info(
                f"Fragment W{fragment.WINDOW}F{fragment.INDEX} "
                f"was already received"
            )
            return

        self.STORAGE.write(
            fragment.to_hex(),
            f"fragments/w{fragment.get_indices()[0]}/"
            f"f{fragment.get_indices()[1]}"
        )

    def schc_recv(self, fragment: Fragment, timestamp: int) -> Optional[ACK]:
        """Receives a SCHC Fragment and processes it accordingly."""

        if self.STORAGE.is_empty():
            self.start_new_session(retain_previous_data=False)

        if self.session_was_aborted():
            self.LOGGER.error("Session aborted.")
            raise ReceiverAbortError

        if self.inactivity_timer_expired(timestamp):
            self.STORAGE.delete("state/TIMESTAMP")
            self.LOGGER.error("Inactivity Timer expired.")
            return self.generate_receiver_abort(fragment.HEADER)

        if len(fragment.to_bin()) > self.PROFILE.UPLINK_MTU:
            raise LengthMismatchError("Fragment is larger than uplink MTU.")

        self.STORAGE.write(timestamp, "state/TIMESTAMP")

        if fragment.is_sender_abort():
            self.LOGGER.error(
                f"[Sender-Abort] Aborting session for rule "
                f"{self.PROFILE.RULE.ID}")
            raise SenderAbortError

        self.LOGGER.info(
            f"Received fragment W{fragment.WINDOW}F{fragment.INDEX}")

        if not self.fragment_is_receivable(fragment):
            self.start_new_session(retain_previous_data=False)

        self.upload_fragment(fragment)
        self.update_bitmap(fragment)
        pending_ack = self.get_pending_ack(fragment)
        if pending_ack is not None:
            self.LOGGER.info("Pending ACK retrieved.")
            return pending_ack

        if not fragment.expects_ack() or self.fragment_is_requested(fragment):
            return None
        return self.generate_compound_ack(fragment)
