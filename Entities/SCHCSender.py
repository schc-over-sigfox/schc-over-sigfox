import json
import random

import config.schc as config
from Entities.Fragmenter import Fragmenter
from Entities.Rule import Rule
from Entities.SigfoxProfile import SigfoxProfile
from Entities.SigfoxSocket import SigfoxSocket
from Entities.exceptions import SCHCTimeoutError, SenderAbortError, ReceiverAbortError, BadProfileError, \
    NetworkDownError, SCHCError
from Logger import Logger, log
from Messages.CompoundACK import CompoundACK
from Messages.Fragment import Fragment
from Messages.SenderAbort import SenderAbort
from utils.casting import bytes_to_hex, bin_to_int
from utils.misc import replace_char, is_monochar, zfill


class SCHCSender:

    def __init__(self, profile: SigfoxProfile):
        self.PROFILE = profile
        self.FRAGMENTER = Fragmenter(self.PROFILE)
        self.STORAGE = self.FRAGMENTER.STORAGE
        self.FRAGMENT_LIST = []
        self.ATTEMPTS = 0
        self.CURRENT_FRAGMENT_INDEX = 0
        self.CURRENT_WINDOW_INDEX = 0
        self.LAST_WINDOW = 0
        self.DELAY: float = config.DELAY_BETWEEN_FRAGMENTS
        self.SEQNUM = 0
        self.SENT = 0
        self.RECEIVED = 0
        self.FINISHED = False

        self.LOGGER = Logger('', Logger.DEBUG)
        self.SOCKET = SigfoxSocket()

        self.LOSS_MASK = {}
        self.LOSS_RATE = 0

    def send(self, fragment: Fragment) -> None:
        """Send a fragment towards the receiver end."""

        as_bytes = fragment.to_bytes()

        if not fragment.is_sender_abort():
            w_index, f_index = fragment.get_indices()
            path = f"fragments/fragment_w{w_index}f{f_index}"
            f_json = json.loads(self.STORAGE.read(path))
            f_json["sent"] = True
            self.STORAGE.write(json.dumps(f_json), path)

        if self.LOSS_RATE > 0:
            if random.random() * 100 <= self.LOSS_RATE:
                self.SOCKET.SEQNUM += 1
                log.debug("Fragment lost (rate)")
                return

        elif self.LOSS_MASK != {}:
            window_mask = self.LOSS_MASK["fragment"][str(fragment.HEADER.WINDOW_NUMBER)]
            if window_mask[fragment.INDEX] != '0':
                log.debug("Fragment lost (mask)")
                self.LOSS_MASK["fragment"][str(fragment.HEADER.WINDOW_NUMBER)] = replace_char(
                    window_mask,
                    fragment.INDEX,
                    str(int(window_mask[fragment.INDEX]) - 1)
                )
                self.SEQNUM += 1
                return

        self.LOGGER.BEHAVIOR += f'W{fragment.HEADER.WINDOW_NUMBER}F{fragment.INDEX}'
        self.SENT += 1

        return self.SOCKET.send(as_bytes)

    def recv(self, bufsize: int) -> CompoundACK:
        """Receives a message from the socket and parses it as a Compound ACK."""

        received = self.SOCKET.recv(bufsize)
        ack = CompoundACK.from_hex(bytes_to_hex(received))

        if self.LOSS_RATE > 0:
            if random.random() * 100 <= self.LOSS_RATE:
                print("ACK lost (rate)")
                raise SCHCTimeoutError
        elif self.LOSS_MASK != {}:
            attempt = 1 if self.ATTEMPTS == 0 else self.ATTEMPTS
            window_mask = self.LOSS_MASK["ack"][str(ack.HEADER.WINDOW_NUMBER)]
            if window_mask[attempt - 1] != '0':
                log.debug("ACK lost (mask)")
                self.LOSS_MASK["ack"][str(ack.HEADER.WINDOW_NUMBER)] = replace_char(
                    window_mask,
                    attempt - 1,
                    window_mask[attempt - 1]
                )
                raise SCHCTimeoutError

        self.RECEIVED += 1
        return ack

    def schc_send(self, fragment: Fragment, retransmit: bool = False):
        """Uses the SCHC Sender behavior to send a SCHC Fragment."""
        if fragment.is_all_0() and not retransmit:
            log.debug("[SEND] [All-0] Using All-0 SIGFOX_DL_TIMEOUT as timeout.")
            self.SOCKET.set_timeout(self.PROFILE.SIGFOX_DL_TIMEOUT)
        elif fragment.is_all_1():
            log.debug("[SEND] [All-1] Using RETRANSMISSION_TIMER_VALUE as timeout. Increasing ACK attempts.")
            self.ATTEMPTS += 1
            self.SOCKET.set_timeout(self.PROFILE.RETRANSMISSION_TIMEOUT)
        else:
            self.SOCKET.set_timeout(60)

        log.info(f"[SEND] Sending fragment: "
                 f"Rule {fragment.PROFILE.RULE.ID} ({str(fragment.PROFILE.RULE)}), "
                 f"W{fragment.HEADER.WINDOW_NUMBER}"
                 f"F{fragment.NUMBER}")

        try:
            enable_reception = fragment.expects_ack() and not retransmit
            self.SOCKET.set_recv(enable_reception)
            self.send(fragment)

            if enable_reception:
                ack = self.recv(self.PROFILE.DOWNLINK_MTU // 8)
            else:
                ack = None

            if fragment.is_sender_abort():
                log.error("[SENDER-ABORT]")
                self.LOGGER.SENDER_ABORTED = True
                raise SenderAbortError

            if not fragment.expects_ack():
                if not retransmit:
                    self.CURRENT_FRAGMENT_INDEX += 1
                return

            if ack is not None:
                log.info(f"[ACK] Received ACK {ack.to_hex()} (hex). Ressetting attempts counter to 0.")
                self.ATTEMPTS = 0

                if ack.is_receiver_abort():
                    self.LOGGER.error("[RECEIVER-ABORT]")
                    self.LOGGER.RECEIVER_ABORTED = True
                    raise ReceiverAbortError

                if not fragment.expects_ack():
                    self.LOGGER.error(f"ACK received but not requested.")
                    raise BadProfileError

                for tup in ack.TUPLES:
                    ack_window_number = bin_to_int(tup[0])
                    bitmap = tup[1]
                    bitmap_to_retransmit = ''

                    if ack_window_number == self.LAST_WINDOW:

                        if ack.HEADER.C == '1':
                            self.LOGGER.info("ACK received with C = 1. End of transmission.")
                            self.LOGGER.FINISHED = True
                            self.CURRENT_FRAGMENT_INDEX += 1
                            self.FRAGMENTER.clear_fragment_directory()
                            return

                        else:
                            if fragment.is_all_1():
                                last_bitmap = bitmap[:(len(self.FRAGMENT_LIST) - 1) % self.PROFILE.WINDOW_SIZE]

                                bitmap_has_only_all1 = last_bitmap == '' and bitmap[-1] == '1'
                                bitmap_is_all_1s = is_monochar(last_bitmap, '1')
                                fragments_arent_missing = bitmap_has_only_all1 or bitmap_is_all_1s

                                if fragments_arent_missing:
                                    self.LOGGER.error("SCHC ACK shows no missing tile at the receiver.")
                                    self.schc_send(SenderAbort(fragment.HEADER))

                                else:
                                    bitmap_to_retransmit = last_bitmap
                            else:
                                raise BadProfileError("The last ACK-REQ was not an All-1.")

                    else:
                        bitmap_to_retransmit = bitmap

                    for j in range(len(bitmap_to_retransmit)):
                        if bitmap_to_retransmit[j] == '0':
                            fragment_id = self.PROFILE.WINDOW_SIZE * ack_window_number + j
                            w_index = zfill(
                                str(fragment_id // self.PROFILE.WINDOW_SIZE),
                                (2 ** self.PROFILE.M - 1) // 10 + 1
                            )
                            f_index = zfill(
                                str(fragment_id % self.PROFILE.WINDOW_SIZE),
                                self.PROFILE.WINDOW_SIZE // 10 + 1
                            )
                            path = f"{self.STORAGE.ROOT}fragments/fragment_w{w_index}f{f_index}"
                            self.schc_send(Fragment.from_file(path), retransmit=True)

                if fragment.is_all_1():
                    self.schc_send(fragment)
                elif fragment.is_all_0():
                    self.CURRENT_FRAGMENT_INDEX += 1
                    self.CURRENT_WINDOW_INDEX += 1

        except SCHCTimeoutError:
            if fragment.is_all_1():
                log.debug(f"ACK-REQ Attempts: {self.ATTEMPTS}")
                if self.ATTEMPTS < self.PROFILE.MAX_ACK_REQUESTS:
                    self.LOGGER.info("SCHC Timeout reached while waiting for an ACK. Sending the ACK Request again...")
                    self.schc_send(fragment)
                else:
                    self.LOGGER.error("MAX_ACK_REQUESTS reached.")
                    self.schc_send(SenderAbort(fragment.HEADER))

            if fragment.is_all_0():
                self.LOGGER.info("All-0 timeout reached. Proceeding to next window.")
                self.CURRENT_FRAGMENT_INDEX += 1
                self.CURRENT_WINDOW_INDEX += 1

            else:
                self.LOGGER.error("ERROR: Timeout reached.")
                raise NetworkDownError

    def start_session(self, schc_packet: bytes, rule: Rule):
        profile = SigfoxProfile(direction="UPLINK", mode=config.FR_MODE, rule=rule)
        fragmenter = Fragmenter(profile)
        self.FRAGMENT_LIST = fragmenter.fragment(schc_packet)

        while self.CURRENT_FRAGMENT_INDEX < len(self.FRAGMENT_LIST):
            fragment = self.FRAGMENT_LIST[self.CURRENT_FRAGMENT_INDEX]

            try:
                self.schc_send(fragment)
            except SCHCError:
                break
