import json

import config.schc as config
from Entities.Fragmenter import Fragmenter
from Entities.Logger import Logger, log
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import SCHCTimeoutError, SenderAbortError, \
    ReceiverAbortError, BadProfileError, \
    NetworkDownError, SCHCError
from Messages.CompoundACK import CompoundACK
from Messages.Fragment import Fragment
from Messages.SenderAbort import SenderAbort
from Sockets.SigfoxSocket import SigfoxSocket as Socket
from utils.casting import bytes_to_hex, bin_to_int
from utils.misc import replace_char, is_monochar, zfill, urand, blink


class SCHCSender:

    def __init__(self, profile: SigfoxProfile):
        self.PROFILE = profile
        self.FRAGMENTER = Fragmenter(self.PROFILE)
        self.STORAGE = self.FRAGMENTER.STORAGE
        self.ATTEMPTS = 0
        self.NB_FRAGMENTS = 0
        self.LAST_WINDOW = 0
        self.DELAY = config.DELAY_BETWEEN_FRAGMENTS
        self.LOGGER = Logger(Logger.INFO)
        self.SOCKET = Socket()

        self.TRANSMISSION_QUEUE = []
        self.RETRANSMISSION_QUEUE = []
        self.RT = False

        self.LOSS_MASK = {}
        self.UPLINK_LOSS_RATE = 0
        self.DOWNLINK_LOSS_RATE = 0
        self.ENABLE_MAX_ACK_REQUESTS = True

    def send(self, fragment: Fragment) -> None:
        """Send a fragment towards the receiver end."""

        as_bytes = fragment.to_bytes()
        w_index, f_index = fragment.get_indices()
        fragment_info, fragment_pk = self.load_fragment_info(fragment)

        self.LOGGER.SENT += 1

        if fragment.is_all_0():
            self.LOGGER.ALL_0_COUNT += 1
        elif fragment.is_all_1():
            self.LOGGER.ALL_1_COUNT += 1
        elif fragment.is_sender_abort():
            self.LOGGER.ABORT_COUNT += 1
        else:
            self.LOGGER.REGULAR_COUNT += 1

        if not fragment.is_sender_abort():
            path = "fragments/fragment_w{}f{}".format(w_index, f_index)
            f_json = json.loads(self.STORAGE.read(path))
            f_json["sent"] = True
            self.STORAGE.write(path, json.dumps(f_json))

        if self.UPLINK_LOSS_RATE > 0 and not fragment.is_sender_abort():
            if urand() <= self.UPLINK_LOSS_RATE:
                self.SOCKET.SEQNUM += 1
                log.debug("Fragment lost (rate)")
                fragment_info[fragment_pk]["losses"] += 1
                self.LOGGER.FRAGMENTS_INFO.update(fragment_info)
                if fragment.expects_ack():
                    raise SCHCTimeoutError
                return

        elif self.LOSS_MASK != {}:
            window_mask = self.LOSS_MASK["fragment"][str(
                fragment.HEADER.WINDOW_NUMBER
            )]
            if window_mask[fragment.INDEX] != '0':
                log.debug("Fragment lost (mask)")
                self.LOSS_MASK["fragment"][
                    str(fragment.HEADER.WINDOW_NUMBER)
                ] = replace_char(
                    window_mask,
                    fragment.INDEX,
                    str(int(window_mask[fragment.INDEX]) - 1)
                )
                self.SOCKET.SEQNUM += 1
                fragment_info[fragment_pk]["losses"] += 1
                self.LOGGER.FRAGMENTS_INFO.update(fragment_info)
                if fragment.expects_ack():
                    raise SCHCTimeoutError
                return

        if fragment.is_sender_abort():
            self.LOGGER.SEQUENCE += 'SABORT'
            fragment_info[fragment_pk]["abort"] = True
        else:
            self.LOGGER.SEQUENCE += 'W{}' \
                                    'F{}'.format(
                fragment.HEADER.WINDOW_NUMBER, fragment.INDEX
            )

        self.LOGGER.FRAGMENTS_INFO.update(fragment_info)
        return self.SOCKET.send(as_bytes)

    def recv(self, bufsize: int) -> CompoundACK:
        """Receives a message from the socket and parses it
        as a Compound ACK."""

        if not self.SOCKET.EXPECTS_ACK:
            return None

        received = self.SOCKET.recv(bufsize)
        ack = CompoundACK.from_hex(bytes_to_hex(received))

        if self.DOWNLINK_LOSS_RATE > 0:
            if urand() <= self.DOWNLINK_LOSS_RATE:
                log.debug("ACK lost (rate)")
                raise SCHCTimeoutError
        elif self.LOSS_MASK != {}:
            ack_mask = self.LOSS_MASK["ack"][str(ack.HEADER.WINDOW_NUMBER)]
            loss = ack_mask != '0'

            if loss:
                self.LOSS_MASK["ack"][str(ack.HEADER.WINDOW_NUMBER)] = str(
                    int(ack_mask) - 1
                )
                log.debug("ACK lost (mask)")
                raise SCHCTimeoutError

        if ack.is_receiver_abort():
            self.LOGGER.SEQUENCE += "RABORT"
        else:
            self.LOGGER.SEQUENCE += "A{}".format(ack.HEADER.WINDOW_NUMBER)

        self.LOGGER.RECEIVED += 1
        return ack

    def schc_send(self, fragment: Fragment) -> None:
        """Uses the SCHC Sender behavior to send a SCHC Fragment."""
        self.update_timeout(fragment)

        log.info(
            "[SEND] Sending fragment: "
            "Rule {} "
            "({}), "
            "W{}"
            "F{}".format(
                fragment.PROFILE.RULE.ID,
                fragment.PROFILE.RULE.STR,
                fragment.HEADER.WINDOW_NUMBER,
                fragment.INDEX
            )
        )

        try:
            enable_reception = fragment.expects_ack() and not self.RT
            self.SOCKET.set_reception(enable_reception)
            blink("blue", 1, 0.1)
            self.send(fragment)

            if enable_reception:
                ack = self.recv(self.PROFILE.DOWNLINK_MTU // 8)
            else:
                ack = None

            self.update_rt()

            if fragment.is_sender_abort():
                log.error("[SENDER-ABORT]")
                self.LOGGER.SENDER_ABORTED = True
                raise SenderAbortError

            if not fragment.expects_ack():
                return

            if ack is not None:
                log.info(
                    "[ACK] ACK received {} (hex). "
                    "Tuples: {} "
                    "Resetting attempts counter to 0.".format(
                        ack.to_hex(),
                        ack.TUPLES
                    )
                )
                self.ATTEMPTS = 0

                if ack.is_receiver_abort():
                    log.error("[RECEIVER-ABORT]")
                    self.LOGGER.RECEIVER_ABORTED = True
                    raise ReceiverAbortError

                if not fragment.expects_ack():
                    log.error("ACK received but not requested.")
                    raise BadProfileError

                if ack.HEADER.WINDOW_NUMBER == self.LAST_WINDOW:
                    if ack.HEADER.C == '1':
                        log.info("ACK received with C = 1. "
                                 "End of transmission.")
                        self.LOGGER.FINISHED = True
                        self.FRAGMENTER.clear_fragment_directory()
                        return

                self.update_queues(fragment, ack)

            self.update_rt()
            return

        except SCHCTimeoutError as exc:
            blink("red", 1, 0.1)
            if fragment.is_all_1():
                log.debug("ACK-REQ Attempts: {}".format(self.ATTEMPTS))
                if self.ATTEMPTS >= self.PROFILE.MAX_ACK_REQUESTS and \
                        config.ENABLE_MAX_ACK_REQUESTS:
                    log.error("MAX_ACK_REQUESTS reached.")
                    self.TRANSMISSION_QUEUE.insert(
                        0, SenderAbort(fragment.HEADER)
                    )
                else:
                    log.info(
                        "All-1 timeout reached. "
                        "Sending the ACK Request again..."
                    )
                    self.TRANSMISSION_QUEUE.append(fragment)

            elif fragment.is_all_0():
                log.info("All-0 timeout reached. "
                         "Proceeding to next window.")

            else:
                log.error(
                    "ERROR: Timeout reached at fragment "
                    "W{}"
                    "F{}".format(
                        fragment.HEADER.WINDOW_NUMBER,
                        fragment.INDEX
                    )
                )
                raise NetworkDownError from exc

    def load_fragment_info(self, fragment: Fragment) -> tuple[dict, str]:
        """
        Loads the information of the fragment depending on if the Logger
        has registered something previously.
        """

        w_index, f_index = fragment.get_indices()
        fragment_pk = "W{}F{}".format(w_index, f_index)

        if fragment_pk in self.LOGGER.FRAGMENTS_INFO.keys():
            fragment_info = {
                fragment_pk: self.LOGGER.FRAGMENTS_INFO[fragment_pk]
            }
        else:
            fragment_info = {
                fragment_pk: {
                    "data": fragment.to_hex(),
                    "losses": 0,
                    "abort": False
                }
            }

        return fragment_info, fragment_pk

    def update_rt(self) -> None:
        """Updates the RT flag. This method should be called before and
        after processing an ACK."""
        self.RT = self.RETRANSMISSION_QUEUE != []

    def update_queues(self, fragment: Fragment, ack: CompoundACK) -> None:
        """Updates the transmission and retransmission queues with
        information of the current state (fragment and ACK)."""
        for tup in ack.TUPLES:
            ack_window_number = bin_to_int(tup[0])
            bitmap = tup[1]
            bitmap_to_retransmit = ''

            if ack_window_number == self.LAST_WINDOW:

                if not fragment.is_all_1():
                    raise BadProfileError("The last ACK-REQ was not an All-1.")

                last_bitmap = bitmap[:(
                                                  self.NB_FRAGMENTS - 1) % self.PROFILE.WINDOW_SIZE]

                bitmap_has_only_all1 = last_bitmap == '' and bitmap[-1] == '1'
                bitmap_is_1s = is_monochar(last_bitmap, '1')
                fragments_arent_missing = bitmap_has_only_all1 or bitmap_is_1s

                if fragments_arent_missing:
                    log.error(
                        "SCHC ACK shows no missing tile "
                        "at the receiver."
                    )
                    self.TRANSMISSION_QUEUE.insert(
                        0, SenderAbort(fragment.HEADER)
                    )

                else:
                    bitmap_to_retransmit = last_bitmap

            else:
                bitmap_to_retransmit = bitmap

            for j, bit in enumerate(bitmap_to_retransmit):
                if bit == '0':
                    fragment_id = self.PROFILE.WINDOW_SIZE \
                                  * ack_window_number \
                                  + j
                    w_index = zfill(
                        str(fragment_id // self.PROFILE.WINDOW_SIZE),
                        (2 ** self.PROFILE.M - 1) // 10 + 1
                    )
                    f_index = zfill(
                        str(fragment_id % self.PROFILE.WINDOW_SIZE),
                        self.PROFILE.WINDOW_SIZE // 10 + 1
                    )
                    path = "{}/" \
                           "fragments/fragment_w{}f{}" \
                        .format(self.STORAGE.ROOT, w_index, f_index)

                    self.RETRANSMISSION_QUEUE.append(
                        fragment.from_file(path)
                    )

        if fragment.is_all_1():
            self.TRANSMISSION_QUEUE.append(fragment)

    def update_timeout(self, fragment: Fragment) -> None:
        """Updates the socket timeout according to the SCHC Fragment."""
        if fragment.is_all_0() and not self.RT:
            log.debug("[SEND] [All-0] "
                      "Using All-0 SIGFOX_DL_TIMEOUT as timeout ({}s)."
                      .format(self.PROFILE.SIGFOX_DL_TIMEOUT))
            self.SOCKET.set_timeout(self.PROFILE.SIGFOX_DL_TIMEOUT)
        elif fragment.is_all_1():
            log.debug("[SEND] [All-1] "
                      "Using RETRANSMISSION_TIMEOUT as timeout ({}s)."
                      "Increasing ACK attempts."
                      .format(self.PROFILE.RETRANSMISSION_TIMEOUT))
            self.ATTEMPTS += 1
            self.SOCKET.set_timeout(self.PROFILE.RETRANSMISSION_TIMEOUT)
        else:
            self.SOCKET.set_timeout(60)

    def start_session(self, schc_packet: bytes):
        """Performs the full SCHC Sender procedure for a given SCHC Packet."""

        log.info("SCHC Packet: {}".format(schc_packet))
        fragmenter = Fragmenter(self.PROFILE)
        self.TRANSMISSION_QUEUE = fragmenter.fragment(schc_packet)
        self.NB_FRAGMENTS = len(self.TRANSMISSION_QUEUE)
        self.LAST_WINDOW = self.TRANSMISSION_QUEUE[-1].HEADER.WINDOW_NUMBER

        self.LOGGER.PACKET_SIZE = len(schc_packet)
        self.LOGGER.NB_FRAGMENTS = self.NB_FRAGMENTS
        self.LOGGER.UPLINK_LOSS_RATE = self.UPLINK_LOSS_RATE
        self.LOGGER.DOWNLINK_LOSS_RATE = self.DOWNLINK_LOSS_RATE

        while self.TRANSMISSION_QUEUE != [] or self.RETRANSMISSION_QUEUE != []:
            if not self.RT:
                fragment = self.TRANSMISSION_QUEUE.pop(0)
            else:
                fragment = self.RETRANSMISSION_QUEUE.pop(0)
            try:
                self.schc_send(fragment)
            except SCHCError:
                blink("red", 3, 0.1)
                break
