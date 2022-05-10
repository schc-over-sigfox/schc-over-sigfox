import requests

import config_testing as config
from Entities.Logger import Logger
from Entities.SCHCSender import SCHCSender
from testing.loss_masks import *

with open(config.PAYLOAD, "rb") as data:
    f = data.read()
    payload = bytearray(f)

sender = SCHCSender(config.LOCAL_RECEIVER_URL)
sender.set_session("ACK ON ERROR", payload)

sender.PROFILE.RETRANSMISSION_TIMER_VALUE = 5
sender.PROFILE.SIGFOX_DL_TIMEOUT = 5

sender.set_logging(None, None, severity=Logger.INFO)
loss_mask = loss_mask_2
sender.set_loss_mask(loss_mask)
sender.set_device("4d5a87")

print("This is the SENDER script for a SCHC transmission experiment")
input("Press enter to continue...")

_ = requests.post(url=config.LOCAL_CLEAN_URL, json={'header_bytes': sender.HEADER_BYTES,
                                                    'not_delete_dl_losses': "False",
                                                    'clear': 'True'})

sender.start_session()

if sender.LOGGER.BEHAVIOR == loss_mask["expected"]:
    print(f"Expected behavior!!\nExpected:\n{loss_mask['expected']}\nActual:\n{sender.LOGGER.BEHAVIOR}")
else:
    print(f"Wrong behavior.\nExpected:\n{loss_mask['expected']}\nActual:\n{sender.LOGGER.BEHAVIOR}")

sender.TIMER.wait(1, raise_exception=False)

del sender

input("Press Enter to exit.")
