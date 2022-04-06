import queue
import random
import time

import requests

from Entities.Fragmenter import Fragmenter
from Entities.SCHCLogger import SCHCLogger
from Entities.SCHCTimer import SCHCTimer
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import *
from Messages.ACK import ACK
from Messages.CompoundACK import CompoundACK
from Messages.SenderAbort import SenderAbort
from utils.schc_utils import is_monochar, replace_bit, ordinal


class SCHCSender:
    PROTOCOL = None
    PROFILE = None
    MESSAGE = ''
    FRAGMENTS = []
    ATTEMPTS = None
    FRAGMENT_INDEX = None
    CURRENT_WINDOW = None
    LAST_WINDOW = None
    TIMER = None
    HEADER_BYTES = None
    DELAY = None
    ENDPOINT = None

    LOGGER = None
    DEVICE = None
    TIMEOUT = None
    BUFFER = None
    SEQNUM = None

    LOSS_RATE = None
    LOSS_MASK = None

    def __init__(self, endpoint):
        # self.PROTOCOL = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ4)
        # self.SOCKET = s.socket(s.AF_SIGFOX, s.SOCK_RAW)
        # self.SOCKET.setblocking(True)
        self.MESSAGE = ''
        self.FRAGMENTS = []
        self.ATTEMPTS = None
        self.FRAGMENT_INDEX = 0
        self.CURRENT_WINDOW = None
        self.LAST_WINDOW = None
        self.TIMER = SCHCTimer(0)
        self.HEADER_BYTES = None
        self.DELAY = .0
        self.TIMEOUT = 0
        self.SEQNUM = 0
        self.BUFFER = queue.Queue()
        self.LOSS_RATE = 0
        self.LOSS_MASK = {}
        self.SENT = 0
        self.RECEIVED = 0

        self.ENDPOINT = endpoint

    def set_logging(self, filename, json_file, severity):
        self.LOGGER = SCHCLogger(filename, json_file)
        self.LOGGER.set_severity(severity)

    def set_delay(self, delay):
        self.DELAY = delay

    def set_device(self, device):
        self.DEVICE = device

    def set_timeout(self, timeout):
        self.TIMEOUT = timeout

    def set_loss_rate(self, loss_rate):
        self.LOSS_RATE = loss_rate

    def set_loss_mask(self, loss_mask):
        self.LOSS_MASK = loss_mask

    def send(self, fragment, loss=False):

        # LoPy should use to_bytes()
        message = fragment.to_hex().decode()

        http_body = {
            'device': self.DEVICE,
            'data': message,
            'time': int(time.time()),
            'seqNumber': self.SEQNUM
        }

        print(f"[SEND] sending {message}; time {int(time.time())}; seqnum {self.SEQNUM}; timeout {self.TIMEOUT}")

        self.SEQNUM += 1

        if loss and random.random() * 100 <= self.LOSS_RATE:
            print("[SEND] Fragment lost")
        else:
            self.LOGGER.BEHAVIOR += f'W{fragment.HEADER.WINDOW_NUMBER}F{fragment.NUMBER}'
            self.SENT += 1
            try:
                response = requests.post(url=self.ENDPOINT, json=http_body, timeout=self.TIMEOUT)
                if response.status_code == 200 and self.DEVICE in response.json():
                    self.BUFFER.put(response.json()[self.DEVICE]["downlinkData"])
            except requests.exceptions.ReadTimeout:
                raise SCHCTimeoutError

    def send_mask(self, fragment):
        print("Sending with loss mask")
        window_mask = self.LOSS_MASK["fragment"][str(fragment.HEADER.WINDOW_NUMBER)]
        if window_mask[fragment.NUMBER] != '0':
            print("[SEND] Fragment lost")
            self.LOSS_MASK["fragment"][str(fragment.HEADER.WINDOW_NUMBER)] = replace_bit(window_mask,
                                                                                         fragment.NUMBER,
                                                                                         str(int(window_mask[fragment.NUMBER]) - 1))
            print(f"loss_mask is now {self.LOSS_MASK}")
            self.SEQNUM += 1
        else:
            self.SENT += 1
            self.send(fragment)

    def recv(self, bufsize, loss=False):
        try:
            print("[RECV] Receiving")
            received = self.BUFFER.get(timeout=self.TIMEOUT)

            if len(received) / 2 > bufsize:
                raise LengthMismatchError

            if loss and random.random() * 100 <= self.LOSS_RATE:
                print("[RECV] Fragment lost")
                raise SCHCTimeoutError
            else:
                self.RECEIVED += 1
                return received

        except queue.Empty:
            raise SCHCTimeoutError

    def recv_mask(self):
        received = self.recv(self.PROFILE.DOWNLINK_MTU // 8)
        ack = ACK.parse_from_hex(self.PROFILE, received)

        attempts = 1 if self.ATTEMPTS == 0 else self.ATTEMPTS

        window_mask = self.LOSS_MASK["ack"][str(ack.HEADER.WINDOW_NUMBER)]
        if window_mask[attempts - 1] != '0':
            print("[RECV] Fragment lost")
            self.LOSS_MASK["ack"][str(ack.HEADER.WINDOW_NUMBER)] = replace_bit(window_mask,
                                                                               attempts - 1,
                                                                               str(int(window_mask[attempts - 1]) - 1))
            raise SCHCTimeoutError
        else:
            self.RECEIVED += 1
            return received

    def set_session(self, mode, message):
        self.HEADER_BYTES = 1 if len(message) <= 300 else 2
        self.PROFILE = SigfoxProfile("UPLINK", mode, self.HEADER_BYTES)
        self.MESSAGE = message
        fragmenter = Fragmenter(self.PROFILE, message)
        self.FRAGMENTS = fragmenter.fragment()

        if self.LOGGER is not None:
            self.LOGGER.FRAGMENTATION_TIME = self.LOGGER.CHRONO.read()
            self.LOGGER.debug("fragmentation time -> {}".format(self.LOGGER.FRAGMENTATION_TIME))

        if len(self.FRAGMENTS) > (2 ** self.PROFILE.M) * self.PROFILE.WINDOW_SIZE:
            raise RuleSelectionError

        self.LAST_WINDOW = (len(self.FRAGMENTS) - 1) // self.PROFILE.WINDOW_SIZE
        self.ATTEMPTS = 0

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

    def schc_send(self, fragment_sent, retransmit=False):
        print(f"Fragment index: {self.FRAGMENT_INDEX}")
        ack = None
        current_fragment = {}
        logging = self.LOGGER is not None and self.LOGGER.JSON_FILE is not None
        self.TIMER.wait(timeout=self.DELAY, raise_exception=False)

        if logging:
            self.LOGGER.LOGGING_TIME += self.DELAY
            current_fragment = {'RULE_ID': fragment_sent.HEADER.RULE_ID,
                                'W': fragment_sent.HEADER.W,
                                'FCN': fragment_sent.HEADER.FCN,
                                'data': fragment_sent.to_bytes(),
                                'fragment_size': len(fragment_sent.to_bytes()),
                                'abort': False,
                                'sending_start': 0,
                                'sending_end': 0,
                                'send_time': 0,
                                'downlink_enable': False,
                                'timeout': 0,
                                'ack_received': False,
                                'ack': "",
                                'rssi': 0,
                                'receiver_abort_received': False,
                                'receiver_abort_message': ""}

        if fragment_sent.is_all_0() and not retransmit:
            self.LOGGER.debug("[POST] This is an All-0. Using All-0 SIGFOX_DL_TIMEOUT.")
            self.set_timeout(self.PROFILE.SIGFOX_DL_TIMEOUT)
            if logging:
                current_fragment["timeout"] = self.PROFILE.SIGFOX_DL_TIMEOUT
        elif fragment_sent.is_all_1():
            self.LOGGER.debug("[POST] This is an All-1. Using RETRANSMISSION_TIMER_VALUE. Increasing ACK attempts.")
            self.ATTEMPTS += 1
            self.set_timeout(self.PROFILE.RETRANSMISSION_TIMER_VALUE)
            if logging:
                current_fragment["timeout"] = self.PROFILE.RETRANSMISSION_TIMER_VALUE
        else:
            self.set_timeout(60)
            if logging:
                current_fragment["timeout"] = 60

        self.LOGGER.info(f"[POST] Sending fragment {fragment_sent.HEADER.to_string()} (W{fragment_sent.HEADER.WINDOW_NUMBER}F{fragment_sent.NUMBER})")

        if fragment_sent.expects_ack() and not retransmit:
            current_fragment['downlink_enable'] = True
        else:
            current_fragment['downlink_enable'] = False

        try:
            if logging:
                current_fragment['sending_start'] = self.LOGGER.CHRONO.read()

            if self.LOSS_MASK != {}:
                self.send_mask(fragment_sent)
            else:
                self.send(fragment_sent, loss=True)

            if fragment_sent.expects_ack() and not retransmit:
                if logging:
                    current_fragment['ack_received'] = False

                ack = self.recv(self.PROFILE.DOWNLINK_MTU // 8, loss=True)
                # ack = self.recv_mask()

            if logging:
                current_fragment['sending_end'] = self.LOGGER.CHRONO.read()
                current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
                if ack is not None:
                    current_fragment['rssi'] = self.PROTOCOL.rssi()
                    self.LOGGER.debug("Response received at: {}: ".format(self.LOGGER.CHRONO.read()))
                    self.LOGGER.debug('ack -> {}'.format(ack))
                    self.LOGGER.debug('message RSSI: {}'.format(self.PROTOCOL.rssi()))

            if fragment_sent.is_sender_abort():
                self.LOGGER.debug("--- senderAbort:{}".format(fragment_sent.to_string()))
                self.LOGGER.debug("--- senderAbort:{}".format(fragment_sent.to_bytes()))
                if logging:
                    current_fragment['abort'] = True
                    self.LOGGER.FRAGMENTS_INFO_ARRAY.append(current_fragment)
                self.LOGGER.error("Sent Sender-Abort. Goodbye")
                self.LOGGER.SENDER_ABORTED = True
                raise SenderAbortError

            if not fragment_sent.expects_ack():
                if not retransmit:
                    self.FRAGMENT_INDEX += 1
                if logging:
                    self.LOGGER.FRAGMENTS_INFO_ARRAY.append(current_fragment)
                return

            if ack is not None:
                if logging:
                    current_fragment['ack'] = ack
                    current_fragment['ack_received'] = True
                self.LOGGER.info("[ACK] Bytes: {}. Ressetting attempts counter to 0.".format(ack))
                self.ATTEMPTS = 0

                # Parse ACK
                ack_object = CompoundACK.parse_from_hex(self.PROFILE, ack)
                print("Received Compound ACK")
                print(ack_object.TUPLES)

                if ack_object.is_receiver_abort():
                    if logging:
                        current_fragment['receiver_abort_message'] = ack
                        current_fragment['receiver_abort_received'] = True
                        self.LOGGER.FRAGMENTS_INFO_ARRAY.append(current_fragment)
                    self.LOGGER.error("ERROR: Receiver Abort received. Aborting communication.")
                    self.LOGGER.RECEIVER_ABORTED = True
                    raise ReceiverAbortError

                if not fragment_sent.expects_ack():
                    self.LOGGER.error("ERROR: ACK received but not requested ({}).".format(ack))
                    self.LOGGER.FRAGMENTS_INFO_ARRAY.append(current_fragment)
                    raise UnrequestedACKError

                # Extract data from ACK
                ack_window = ack_object.HEADER.W
                c = ack_object.HEADER.C
                bitmap = ack_object.BITMAP
                self.LOGGER.debug("ACK: {}".format(ack))
                self.LOGGER.debug("ACK window: {}".format(ack_window))
                self.LOGGER.debug("ACK bitmap: {}".format(bitmap))
                self.LOGGER.debug("ACK C bit: {}".format(c))
                self.LOGGER.debug("last window: {}".format(self.LAST_WINDOW))

                # Save ACKREQ data
                self.LOGGER.FRAGMENTS_INFO_ARRAY.append(current_fragment)

                for tup in ack_object.TUPLES:
                    ack_window_number = int(tup[0], 2)
                    bitmap = tup[1]

                    # If the SCHC Compound ACK reports the last window of the SCHC Packet:
                    if ack_window_number == self.LAST_WINDOW:
                        # If the C bit is set, the sender MAY exit successfully.
                        if c == '1':
                            print(f"here because fragment {fragment_sent.HEADER.to_string()} sn {self.SEQNUM}")
                            self.LOGGER.info("Last ACK received, fragments reassembled successfully. End of transmission.")
                            self.LOGGER.FINISHED = True
                            self.FRAGMENT_INDEX += 1
                            return
                        # Otherwise,
                        else:
                            # If the Profile mandates that the last tile be sent in an All-1 SCHC Fragment
                            # (we are in the last window), .is_all_1() should be true:
                            if fragment_sent.is_all_1():
                                # This is the last bitmap, it contains the data before the All-1 fragment.
                                # The leftmost bit of this bitmap should always be 1, as the All-1 gets to the network
                                # to request the ACK.
                                last_bitmap = bitmap[:(len(self.FRAGMENTS) - 1) % self.PROFILE.WINDOW_SIZE]
                                self.LOGGER.debug("last bitmap {}".format(last_bitmap))
                                # If the SCHC ACK shows no missing tile at the receiver, abort.
                                # (C = 0 but transmission complete)
                                if last_bitmap == '' or (last_bitmap[0] == '1' and is_monochar(last_bitmap)):
                                    self.LOGGER.error("ERROR: SCHC ACK shows no missing tile at the receiver.")
                                    self.schc_send(SenderAbort(fragment_sent.PROFILE, fragment_sent.HEADER))

                                # Otherwise (fragments are lost),
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
                                            fragment_to_be_resent = self.FRAGMENTS[self.PROFILE.WINDOW_SIZE * ack_window_number + j]
                                            self.LOGGER.debug("Lost fragment: {}".format(fragment_to_be_resent.to_string()))
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
