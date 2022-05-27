import json

from flask import Flask, request

from Entities.Logger import log
from Entities.Reassembler import Reassembler
from Entities.Rule import Rule
from Entities.SCHCReceiver import SCHCReceiver
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import SenderAbortError, ReceiverAbortError
from Messages.Fragment import Fragment
from db.LocalStorage import LocalStorage as Storage

app = Flask(__name__)


@app.post('/receive')
def receive():
    """
    Parses a SCHC Fragment and saves it into the storage of the SCHC Receiver according to the SCHC receiving behavior.
    """
    request_dict = request.get_json()

    device_type_id = request_dict["deviceTypeId"]
    device = request_dict["device"]
    data = request_dict["data"]
    net_time = int(request_dict["time"])
    ack = request_dict["ack"] == "true"

    storage = Storage()
    storage.change_root(f"{device_type_id}/{device}")
    profile = SigfoxProfile("UPLINK", "ACK ON ERROR", Rule.from_hex(data))
    receiver = SCHCReceiver(profile, storage)
    fragment = Fragment.from_hex(data)
    log.debug(f"Received {data}. Rule {receiver.PROFILE.RULE.ID}")

    last_request = storage.read("state/LAST_REQUEST")
    if last_request is not None and last_request == request_dict:
        log.warning("Sigfox Callback has retried. Replying with previous response.")
        previous_response = storage.read("state/LAST_RESPONSE")
        return previous_response["body"], previous_response["status_code"]

    storage.write(request_dict, "state/LAST_REQUEST")

    response = {
        "body": '',
        "status_code": 204
    }

    try:
        comp_ack = receiver.schc_recv(fragment, net_time)

        if comp_ack is not None:
            response = {
                "body": json.dumps({device: {"downlinkData": comp_ack.to_hex()}}),
                "status_code": 200
            }

        if fragment.is_all_1() and comp_ack.is_complete():
            fragments = []

            for w in storage.list_nodes("fragments"):
                for f in storage.list_nodes(f"fragments/{w}"):
                    fragments.append(Fragment.from_hex(storage.read(f"fragments/{w}/{f}")))

            reassembler = Reassembler(profile, fragments)
            schc_packet = reassembler.reassemble()

            storage.write(schc_packet, "reassembly/SCHC_PACKET")
            receiver.start_new_session(retain_state=True)

    except SenderAbortError:
        log.info("Sender-Abort received")
        receiver.start_new_session(retain_state=True)
        storage.write(response, "state/LAST_RESPONSE")
        return response["body"], response["status_code"]

    except ReceiverAbortError:
        if ack:
            abort = receiver.get_receiver_abort()
            receiver.start_new_session(retain_state=True)
            response = {
                "body": json.dumps({device: {"downlinkData": abort.to_hex()}}),
                "status_code": 200
            }

    finally:
        storage.write(response, "state/LAST_RESPONSE")
        storage.save()
        return response["body"], response["status_code"]


if __name__ == "__main__":
    app.run(host='0.0.0.0')
