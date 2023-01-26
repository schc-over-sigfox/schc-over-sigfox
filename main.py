"""Executes the sender-side of the project."""
import time

import pycom

from Entities.Rule import Rule
from Entities.SCHCSender import SCHCSender
from Entities.SigfoxProfile import SigfoxProfile
from db.CommonFileStorage import CommonFileStorage
from utils.casting import int_to_bin
from utils.misc import generate_packet, zfill, set_led


sizes = [1, 45, 88, 132, 176, 220, 263, 307]
loss_rates = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]

fs = CommonFileStorage("debug")

try:
    fs.read("completed")
    print("Experiments were already completed")
    set_led("yellow")
except OSError:
    pass

    pycom.heartbeat(True)

    for repetition in range(2):

        for size in sizes:

            PACKET = generate_packet(size)

            for lr in loss_rates:
                print("PACKET SIZE = {}".format(size))
                print("LOSS RATE = {}".format(lr))
                print("(Repetition {})".format(repetition))
                profile = SigfoxProfile("UPLINK", "ACK ON ERROR", Rule('000'))
                sender = SCHCSender(profile)

                sender.UPLINK_LOSS_RATE = lr
                sender.PROFILE.SIGFOX_DL_TIMEOUT = 60
                sender.PROFILE.RETRANSMISSION_TIMEOUT = 60

                sender.start_session(PACKET)
                if sender.LOGGER.SENT < sender.NB_FRAGMENTS:
                    set_led("red")
                    exit(1)

                sender.LOGGER.export(
                    "s{}_"
                    "lr{}_"
                    "rep{}".format(
                        size,
                        zfill(str(lr), 2),
                        zfill(str(repetition), 9)
                    )
                )

    print("All experiments complete")

    set_led("green")

    fs.write("completed", "1")
