import filecmp
import re

from flask import Flask, request, abort

import config_testing as config
from Entities.Reassembler import Reassembler
from Entities.SigfoxProfile import SigfoxProfile
from Messages.CompoundACK import CompoundACK
from Messages.Fragment import Fragment
from Messages.ReceiverAbort import ReceiverAbort
from utils.schc_utils import *

mode = 'filedir'

if mode == 'firebase':
    from utils.firebase_utils import *
elif mode == 'filedir':
    from utils.filedir_utils import *

app = Flask(__name__)


@app.route('/receiver', methods=['GET', 'POST'])
def receiver():

    # Wait for an HTTP POST request.
    if request.method == 'POST':

        # Get request JSON.
        print("POST RECEIVED")
        request_dict = request.get_json()
        print('Received Sigfox message: {}'.format(request_dict))

        # Get data and Sigfox Sequence Number.
        fragment = request_dict["data"]
        sigfox_sequence_number = request_dict["seqNumber"]

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
            return 'wrong header', 204

        data = [header, payload]

        # Initialize SCHC variables.
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", header_bytes)
        buffer_size = profile.UPLINK_MTU
        n = profile.N
        m = profile.M

        # If fragment size is greater than buffer size, ignore it and end function.
        if len(fragment) / 2 * 8 > buffer_size:  # Fragment is hex, 1 hex = 1/2 byte
            return json.dumps({"message": "Fragment size is greater than buffer size D:"}), 200

        # Initialize empty window
        window = []
        for i in range(2 ** n - 1):
            window.append([b"", b""])

        # Compute the fragment compressed number (FCN) from the Profile
        fcn_dict = {}
        for j in range(2 ** n - 1):
            fcn_dict[zfill(bin((2 ** n - 2) - (j % (2 ** n - 1)))[2:], n)] = j

        # Convert to a Fragment class for easier manipulation.
        fragment_message = Fragment(profile, data)

        # Get current window for this fragment.
        current_window = int(fragment_message.HEADER.W, 2)

        # Get the current bitmap.
        bitmap = read_blob("all_windows/window_%d/bitmap_%d" % (current_window, current_window))

        if fragment_message.is_sender_abort():
            print("Sender-Abort received")
            return 'Sender-Abort received', 204

        try:
            fragment_number = fcn_dict[fragment_message.HEADER.FCN]
            upload_blob(fragment_number, "fragment_number")

            time_received = int(request_dict["time"])
            if exists_blob("timestamp"):
                # Check time validation.
                last_time_received = int(read_blob("timestamp"))

                # If this is not the very first fragment and the inactivity timer has been reached, ignore the message.
                if str(fragment_number) != "0" and str(
                        current_window) != "0" and time_received - last_time_received > profile.INACTIVITY_TIMER_VALUE:
                    print("[RECV] Inactivity timer reached. Ending session.")
                    receiver_abort = ReceiverAbort(profile, fragment_message.HEADER)
                    print("Sending Receiver Abort")
                    response_json = send_ack(request_dict, receiver_abort)
                    print(f"Response content -> {response_json}")
                    return response_json, 200

            # Upload current timestamp.
            upload_blob(time_received, "timestamp")

            # Print some data for the user.
            print(f"[RECV] This corresponds to the {ordinal(fragment_number)} fragment "
                  f"of the {ordinal(current_window)} window).")
            print(f"[RECV] Sigfox sequence number: {sigfox_sequence_number}")

            # Update bitmap and upload it.
            bitmap = replace_bit(bitmap, fragment_number, '1')

        # If the FCN could not been found, it almost certainly is the final fragment.
        except KeyError:
            print("[RECV] This seems to be the final fragment.")
            fragment_number = profile.WINDOW_SIZE - 1
            # Upload current timestamp.
            time_received = int(request_dict["time"])
            upload_blob(time_received, "timestamp")
            print(f"is All-1:{fragment_message.is_all_1()}, is All-0:{fragment_message.is_all_0()}")
            # Update bitmap and upload it.
            bitmap = replace_bit(bitmap, len(bitmap) - 1, '1')

        # Upload the fragment data.
        upload_blob(bitmap, f"all_windows/window_{current_window}/bitmap_{current_window}")
        upload_blob(data[0].decode("ISO-8859-1") + data[1].decode("utf-8"),
                    f"all_windows/window_{current_window}/fragment_{current_window}_{fragment_number}")

        # Get some SCHC values from the fragment.
        rule_id = fragment_message.HEADER.RULE_ID
        dtag = fragment_message.HEADER.DTAG

        # Get last and current Sigfox sequence number (SSN)
        last_sequence_number = 0
        if exists_blob("SSN"):
            last_sequence_number = read_blob("SSN")
        upload_blob(sigfox_sequence_number, "SSN")

        # If the fragment is at the end of a window (ALL-0 or ALL-1)
        if fragment_message.is_all_0() or fragment_message.is_all_1():

            # Prepare the compound ACK bitmaps. Find all bitmaps with a 0 in it.
            bitmaps = []
            windows = []
            lost = False
            for i in range(current_window + 1):
                bitmap_ack = read_blob("all_windows/window_%d/bitmap_%d" % (i, i))
                print(bitmap_ack)
                if '0' in bitmap_ack:
                    lost = True
                    windows.append(zfill(format(i, 'b'), m))
                    bitmaps.append(bitmap_ack)

            # If the ACK bitmap has a 0 at the end of a non-final window, a fragment has been lost.
            if fragment_message.is_all_0():
                # "is_all_0 and lost" doesn't consider the final window. In this case "lost" only reports
                # non-final windows
                if lost:
                    print("[ALL0] Sending Compound ACK for lost fragments...")
                    print("windows with errors -> {}".format(windows))
                    print("bitmaps with errors -> {}".format(bitmaps))
                    # Create a Compound ACK message and send it.
                    ack = CompoundACK(profile=profile,
                                      rule_id=rule_id,
                                      dtag=dtag,
                                      windows=windows,
                                      c='0',
                                      bitmaps=bitmaps)
                    response_json = send_ack(request_dict, ack)
                    print("Response content -> {}".format(response_json))
                    return response_json, 200

                # If the ACK bitmap is complete and the fragment is an ALL-0, don't send an ACK
                else:
                    print("[ALL0] All Fragments up to this point received")
                    print("[ALL0] No need to send an ACK")
                    return '', 204

            # If the fragment is an ALL-1
            if fragment_message.is_all_1():

                # If there is another window (non-final) in the windows array, send ACK
                if contains_different_from(windows, zfill(format(current_window, 'b'), m)):
                    print("[ALL1] Sending Compound ACK for lost fragments in previous windows...")
                    print("windows with errors -> {}".format(windows))
                    print("bitmaps with errors -> {}".format(bitmaps))
                    # Create a Compound ACK message and send it.
                    ack = CompoundACK(profile=profile,
                                      rule_id=rule_id,
                                      dtag=dtag,
                                      windows=windows,
                                      c='0',
                                      bitmaps=bitmaps)
                    response_json = send_ack(request_dict, ack)
                    print("Response content -> {}".format(response_json))
                    return response_json, 200

                # Else, the only other possible case is when the last bitmap has 0s or is full.
                # We should only look at the last bitmap, saved in the "bitmap_ack" variable
                else:
                    # The bitmap in the last window follows the following regular expression: "1*0*1*"
                    # Since the ALL-1, if received, changes the least significant bit of the bitmap.
                    # For a "complete" bitmap in the last window, there shouldn't be non-consecutive zeroes:
                    # 1110001 is a valid bitmap, 1101001 is not.

                    pattern = re.compile("1*0*1")
                    # If the final bitmap matches the regex, check if the last two received fragments are consecutive.
                    if pattern.fullmatch(bitmap_ack):
                        print("SSN is {} and last SSN is {}".format(sigfox_sequence_number, last_sequence_number))
                        # If the last two received fragments are consecutive, accept the ALL-1 and start reassembling
                        if int(sigfox_sequence_number) - int(last_sequence_number) == 1:
                            last_index = profile.WINDOW_SIZE - 1
                            print("Info for reassemble: last_index:{}, current_window:{}".format(last_index,
                                                                                                 current_window))
                            print('Activating reassembly process...')
                            start_request(url=config.LOCAL_REASSEMBLE_URL,
                                          body={"current_window": current_window,
                                                "header_bytes": header_bytes})

                            # Send last ACK to end communication.
                            print("[ALL1] Reassembled: Sending last ACK")
                            bitmap = ''
                            for k in range(profile.BITMAP_SIZE):
                                bitmap += '0'
                            last_ack = CompoundACK(profile=profile,
                                                   rule_id=rule_id,
                                                   dtag=dtag,
                                                   windows=[zfill(format(current_window, 'b'), m)],
                                                   c='1',
                                                   bitmaps=[bitmap])
                            response_json = send_ack(request_dict, last_ack)
                            # return response_json, 200
                            # response_json = send_ack(request_dict, last_ack)
                            print("200, Response content -> {}".format(response_json))
                            return response_json, 200
                        else:
                            # Send Compound ACK at the end of the window.
                            print("[ALL1] Sending NACK for lost fragments because of SSN...")
                            print("windows with errors -> {}".format(windows))
                            print("bitmaps with errors -> {}".format(bitmaps))
                            # Create a Compound ACK message and send it.
                            ack = CompoundACK(profile=profile,
                                              rule_id=rule_id,
                                              dtag=dtag,
                                              windows=windows,
                                              c='0',
                                              bitmaps=bitmaps)
                            response_json = send_ack(request_dict, ack)
                            print("Response content -> {}".format(response_json))
                            return response_json, 200

                        # If they are not, there is a gap between two fragments: a fragment has been lost.
                    # The same happens if the bitmap doesn't match the regex.
                    else:
                        # Send Compound ACK at the end of the window.
                        print("[ALL1] Sending Compound ACK for lost fragments...")
                        print("windows with errors -> {}".format(windows))
                        print("bitmaps with errors -> {}".format(bitmaps))
                        # Create a Compound ACK message and send it.
                        ack = CompoundACK(profile=profile,
                                          rule_id=rule_id,
                                          dtag=dtag,
                                          windows=windows,
                                          c='0',
                                          bitmaps=bitmaps)
                        response_json = send_ack(request_dict, ack)
                        print("Response content -> {}".format(response_json))
                        return response_json, 200
        return '', 204
    else:
        print('Invalid HTTP Method to invoke Cloud Function. Only POST supported')
        return abort(405)


@app.route('/reassemble', methods=['GET', 'POST'])
def reassemble():
    if request.method == "POST":
        # Get request JSON.
        print("[RSMB] POST RECEIVED")
        request_dict = request.get_json()
        print('Received HTTP message: {}'.format(request_dict))

        current_window = int(request_dict["current_window"])
        # last_index = int(request_dict["last_index"])
        header_bytes = int(request_dict["header_bytes"])

        # Initialize SCHC variables.
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", header_bytes)

        print("[RSMB] Loading fragments")

        # Get all the fragments into an array in the format "fragment = [header, payload]"
        fragments = []

        # For each window, load every fragment into the fragments array
        # Note: This assumes all fragments are ordered
        for i in range(current_window + 1):
            for j in range(profile.WINDOW_SIZE):
                if not exists_blob(f"all_windows/window_{i}/fragment_{i}_{j}"):
                    continue
                fragment_file = read_blob(f"all_windows/window_{i}/fragment_{i}_{j}")
                header = fragment_file[:header_bytes].encode()
                payload = fragment_file[header_bytes:].encode()
                fragment = [header, payload]
                fragments.append(fragment)

        print(len(fragments))
        # Instantiate a Reassembler and start reassembling.
        reassembler = Reassembler(profile, fragments)
        payload = bytearray(reassembler.reassemble())
        # Upload the full message.
        upload_blob(payload.decode("utf-8"), "SCHC_PACKET")
        with open(config.REASSEMBLED, "w") as f:
            f.write(payload.decode())

        if filecmp.cmp(config.PAYLOAD, config.REASSEMBLED):
            print("The reassembled file is equal to the original message.")
        else:
            print("The reassembled file is corrupt.")

        # start_request(url=config.LOCAL_CLEAN_URL,
        #               body={"header_bytes": header_bytes})

        return '', 204


@app.route('/clean', methods=['GET', 'POST'])
def clean():
    # Wait for an HTTP POST request.
    if request.method == 'POST':

        # Get request JSON.
        print("POST RECEIVED")
        request_dict = request.get_json()
        print(request_dict)
        print('Received Sigfox message: {}'.format(request_dict))

        # Get data and Sigfox Sequence Number.
        header_bytes = int(request_dict["header_bytes"])
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", header_bytes)
        bitmap = '0' * (2 ** profile.N - 1)

        if not exists_folder("all_windows"):
            create_folder("all_windows")
            for i in range(2 ** profile.M):
                create_folder(f"all_windows/window_{i}")

        for i in range(2 ** profile.M):
            upload_blob(bitmap, f"all_windows/window_{i}/bitmap_{i}")
            upload_blob(bitmap, f"all_windows/window_{i}/losses_mask_{i}")
            # For each fragment in the SCHC Profile, create its blob.

            start_request(url=config.LOCAL_CLEAN_WINDOW_URL,
                          body={"header_bytes": header_bytes,
                                "window_number": i,
                                "clear": request_dict["clear"] if "clear" in request_dict else "False"})

        if exists_blob("SCHC_PACKET"):
            delete_blob("SCHC_PACKET")

        upload_blob("", "SSN")

        print(f"not_delete_dl_losses? {request_dict['not_delete_dl_losses']}")
        if request_dict["not_delete_dl_losses"] == "False":
            for blob in blob_list():
                if blob.startswith("DL_LOSSES_"):
                    delete_blob(blob)
        else:
            current_experiment = 1
            for blob in blob_list():
                if blob.startswith("DL_LOSSES_"):
                    current_experiment += 1
            print(f"Preparing for the {current_experiment}th experiment")
            upload_blob("", f"DL_LOSSES_{current_experiment}")

        return '', 204


@app.route('/clean_window', methods=['GET', 'POST'])
def clean_window():
    request_dict = request.get_json()
    header_bytes = int(request_dict["header_bytes"])
    window_number = int(request_dict["window_number"])
    profile = SigfoxProfile("UPLINK", "ACK ON ERROR", header_bytes)

    print(f"header_bytes: {header_bytes}, window_number: {window_number}")

    for j in range(2 ** profile.N - 1):
        if request_dict["clear"] == "False":
            upload_blob("", f"all_windows/window_{window_number}/fragment_{window_number}_{j}")
        else:
            delete_blob(f"all_windows/window_{window_number}/fragment_{window_number}_{j}")

    return '', 204


if __name__ == "__main__":
    app.run(host='0.0.0.0')
