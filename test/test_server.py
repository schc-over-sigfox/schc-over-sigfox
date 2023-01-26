import time

from flask import Flask, request

from Messages.Fragment import Fragment

APP = Flask(__name__)
PORT = 5000


@APP.route('/test', methods=['POST'])
def test() -> tuple[object, int]:
    if request.method != 'POST':
        return '', 403
    request_dict = request.get_json()

    device = request_dict["device"]
    data = request_dict["data"]

    fragment = Fragment.from_hex(data)

    if fragment.is_all_1():
        return {device: {'downlinkData': '1c00000000000000'}}, 200
    elif fragment.to_hex()[-1] == 'f':
        time.sleep(2)
    return '', 204


if __name__ == '__main__':
    APP.run('127.0.0.1', 1313)
