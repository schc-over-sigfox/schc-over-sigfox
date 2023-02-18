"""Executes the receiver side of the SCHC/Sigfox simulation.
It is a Flask server that receives HTTP messages,
emulating Sigfox Callbacks"""

import json

from flask import Flask, request

from Entities.Logger import log
from Entities.Reassembler import Reassembler
from Entities.Rule import Rule
from Entities.SCHCReceiver import SCHCReceiver
from Entities.exceptions import SenderAbortError, ReceiverAbortError
from Messages.Fragment import Fragment
from config import schc as config
from db.LocalStorage import LocalStorage as Storage

app = Flask(__name__)


@app.post('/receive')
def receive():
    """
    Parses a SCHC Fragment and saves it into the storage of the SCHC Receiver
    according to the SCHC receiving behavior.
    """

    request_dict = request.get_json()
    device_type_id = request_dict["deviceType"]
    device = request_dict["device"]
    data = request_dict["data"]
    net_time = int(request_dict["time"])
    ack = request_dict["ack"] == "true"

    storage = Storage()
    storage.load()
    storage.change_ref(f"{device_type_id}/{device}")
    rule = Rule.from_hex(data)
    receiver = SCHCReceiver(rule, storage)
    fragment = Fragment.from_hex(data)
    log.debug(f"Received {data}. Rule {receiver.RULE.ID}")

    last_request = storage.read("state/LAST_REQUEST")
    if config.CHECK_FOR_CALLBACK_RETRIES and last_request is not None \
            and last_request == request_dict:
        log.warning("Sigfox Callback has retried. "
                    "Replying with previous response.")
        previous_response = storage.read("state/LAST_RESPONSE")
        return previous_response["body"], previous_response["status_code"]

    storage.write(request_dict, "state/LAST_REQUEST")

    response = {
        "body": '',
        "status_code": 204
    }
    schc_packet = None

    try:
        comp_ack = receiver.schc_recv(fragment, net_time)

        if comp_ack is not None:
            response = {
                "body": json.dumps(
                    {device: {"downlinkData": comp_ack.to_hex()}}),
                "status_code": 200
            }

        if fragment.is_all_1() and comp_ack.is_complete():
            fragments = []

            for wdw in storage.list_nodes("fragments"):
                for frg in storage.list_nodes(f"fragments/{wdw}"):
                    fragments.append(
                        Fragment.from_hex(storage.read(
                            f"fragments/{wdw}/{frg}"
                        ))
                    )

            reassembler = Reassembler(fragments)
            schc_packet = reassembler.reassemble()
            log.info(f"Reassembled SCHC Packet: {schc_packet}")
            storage.write(schc_packet, "reassembly/SCHC_PACKET")
            receiver.start_new_session(retain_previous_data=True)

    except SenderAbortError:
        log.info("Sender-Abort received")
        receiver.start_new_session(retain_previous_data=True)
        storage.write(response, "state/LAST_RESPONSE")
        return response["body"], response["status_code"]

    except ReceiverAbortError:
        if ack:
            abort = receiver.get_receiver_abort()
            receiver.start_new_session(retain_previous_data=True)
            response = {
                "body": json.dumps({device: {"downlinkData": abort.to_hex()}}),
                "status_code": 200
            }

    finally:
        storage.write(response, "state/LAST_RESPONSE")
        storage.write(fragment.to_hex(), "state/LAST_FRAGMENT")
        storage.save()
        log.info(f"Replying with {response}")

        if schc_packet is not None and config.RESET_DATA_AFTER_REASSEMBLY:
            receiver.start_new_session(retain_previous_data=False)

        return response["body"], response["status_code"]


if __name__ == "__main__":
    app.run(host='0.0.0.0')
