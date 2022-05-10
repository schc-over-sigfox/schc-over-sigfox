import json
import random

import config.schc as config
from Entities.Fragmenter import Fragmenter
from Entities.SigfoxProfile import SigfoxProfile
from Entities.SigfoxSocket import SigfoxSocket
from Entities.exceptions import SCHCTimeoutError, SenderAbortError, ReceiverAbortError, BadProfileError
from Logger import Logger, log
from Messages.CompoundACK import CompoundACK
from Messages.Fragment import Fragment
from Messages.SenderAbort import SenderAbort
from utils.casting import bytes_to_hex, bin_to_int
from utils.misc import replace_char, is_monochar


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
        ack = None

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
                                log.debug("last bitmap {}".format(last_bitmap))
                                # If the SCHC ACK shows no missing tile at the receiver, abort.
                                # (C = 0 but transmission complete)
                                fragments_arent_missing = (last_bitmap == '' and bitmap[-1] == '1') or (
                                    is_monochar(last_bitmap, '1'))

                                # Aquí llegué :)

                                if fragments_arent_missing:
                                    self.LOGGER.error("ERROR: SCHC ACK shows no missing tile at the receiver.")
                                    self.schc_send(SenderAbort(fragment.HEADER))

                                else:
                                    # Check for lost fragments.
                                    for j in range(len(last_bitmap)):
                                        # If the j-th bit of the bitmap is 0, then the j-th fragment was lost.
                                        if last_bitmap[j] == '0':
                                            self.LOGGER.info("The {} ({} / {}) fragment was lost! "
                                                             "Sending again...".format(ordinal(j),
                                                                                       self.PROFILE.WINDOW_SIZE * ack_window_number + j,
                                                                                       len(self.FRAGMENTS)))
                                            # Try sending again the lost fragment.
                                            fragment_to_be_resent = self.FRAGMENTS[
                                                self.PROFILE.WINDOW_SIZE * ack_window_number + j]
                                            self.LOGGER.debug(
                                                "Lost fragment: {}".format(fragment_to_be_resent.to_string()))
                                            self.schc_send(fragment_to_be_resent, retransmit=True)

                                    # Send All-1 again to end communication or check again for lost data.
                                    # print("Send All-1 again to end communication or check again for lost data.")
                                    # self.schc_send(fragment_sent)

                            else:
                                self.LOGGER.error("ERROR: While being at the last window, "
                                                  "the ACK-REQ was not an All-1."
                                                  "This is outside of the Sigfox scope.")
                                raise BadProfileError

                    # Otherwise, there are lost fragments in a non-final window.
                    else:

                        # Check for lost fragments.
                        for j in range(len(bitmap)):
                            # If the j-th bit of the bitmap is 0, then the j-th fragment was lost.
                            if bitmap[j] == '0':
                                self.LOGGER.info("The {} ({} / {}) fragment was lost! "
                                                 "Sending again...".format(ordinal(j),
                                                                           self.PROFILE.WINDOW_SIZE * ack_window_number + j,
                                                                           len(self.FRAGMENTS)))
                                # Try sending again the lost fragment.
                                fragment_to_be_resent = self.FRAGMENTS[self.PROFILE.WINDOW_SIZE * ack_window_number + j]
                                self.LOGGER.debug("Lost fragment: {}".format(fragment_to_be_resent.to_string()))
                                self.schc_send(fragment_to_be_resent, retransmit=True)

                # After retransmission, send All-1 again (last window) or proceed to the next window
                if fragment_sent.is_all_1():
                    # Send All-1 again to end communication.
                    self.schc_send(fragment_sent)
                elif fragment_sent.is_all_0():
                    # Continue with next window
                    self.FRAGMENT_INDEX += 1
                    self.CURRENT_WINDOW += 1

        except SCHCTimeoutError as e:
            if logging:
                current_fragment['sending_end'] = self.LOGGER.CHRONO.read()
                current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
                current_fragment['rssi'] = self.PROTOCOL.rssi()
                current_fragment['ack'] = ""
                current_fragment['ack_received'] = False
                self.LOGGER.info("OSError at: {}: ".format(self.LOGGER.CHRONO.read()))
                self.LOGGER.info('OSError number {}, {}'.format(e.args[0], e))

            # Save ACKREQ data
            if logging:
                self.LOGGER.FRAGMENTS_INFO_ARRAY.append(current_fragment)

            # If an ACK was expected
            if fragment_sent.is_all_1():
                # If the attempts counter is strictly less than MAX_ACK_REQUESTS, try again
                self.LOGGER.debug("attempts:{}".format(self.ATTEMPTS))
                if self.ATTEMPTS < self.PROFILE.MAX_ACK_REQUESTS:
                    self.LOGGER.info("SCHC Timeout reached while waiting for an ACK. Sending the ACK Request again...")
                    self.schc_send(fragment_sent, retransmit=False)
                # Else, exit with an error.
                else:
                    self.LOGGER.error("ERROR: MAX_ACK_REQUESTS reached. Sending Sender-Abort.")
                    abort = SenderAbort(self.PROFILE, fragment_sent.HEADER)
                    self.schc_send(abort)

            # If the ACK can be not sent (Sigfox only)
            if fragment_sent.is_all_0():
                self.LOGGER.info("All-0 timeout reached. Proceeding to next window.")
                self.FRAGMENT_INDEX += 1
                self.CURRENT_WINDOW += 1

            # Else, Sigfox communication failed.
            else:
                self.LOGGER.error("ERROR: Timeout reached.")
                raise NetworkDownError

    def start_session(self):
        self.CURRENT_WINDOW = 0

        total_size = len(self.MESSAGE)
        current_size = 0

        logging = self.LOGGER is not None and self.LOGGER.JSON_FILE is not None

        if logging:
            self.LOGGER.START_SENDING_TIME = self.LOGGER.CHRONO.read()
            self.LOGGER.TOTAL_SIZE = total_size
            self.LOGGER.FINISHED = False

        while self.FRAGMENT_INDEX < len(self.FRAGMENTS):
            fragment = self.FRAGMENTS[self.FRAGMENT_INDEX]
            current_size += len(self.FRAGMENTS[self.FRAGMENT_INDEX])
            percent = round(float(current_size) / float(total_size) * 100, 2)

            if logging:
                self.LOGGER.info("Sending...")
                self.LOGGER.LAPS.append(self.LOGGER.CHRONO.read())
                self.LOGGER.debug("laps - > {}".format(self.LOGGER.LAPS))

                self.LOGGER.debug("--------------------------")
                self.LOGGER.debug("{} fragment:".format(ordinal(self.FRAGMENT_INDEX)))
                self.LOGGER.debug("RuleID:{}, DTAG:{}, WINDOW:{}, FCN:{}".format(fragment.HEADER.RULE_ID,
                                                                                 fragment.HEADER.DTAG,
                                                                                 fragment.HEADER.W,
                                                                                 fragment.HEADER.FCN))
                self.LOGGER.debug("SCHC Fragment: {}".format(fragment.to_string()))
                self.LOGGER.debug("SCHC Fragment Payload: {}".format(fragment.PAYLOAD))
                self.LOGGER.debug("{} / {}, {}%".format(current_size,
                                                        total_size,
                                                        percent))

            try:
                self.schc_send(fragment)
            except SCHCError:
                if logging:
                    self.LOGGER.FINISHED = False
                break

        if logging:
            self.LOGGER.END_SENDING_TIME = self.LOGGER.CHRONO.read()
            self.LOGGER.save()
