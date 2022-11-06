"""Executes the sender-side of the project."""

from Entities.Rule import Rule
from Entities.SCHCSender import SCHCSender
from Entities.SigfoxProfile import SigfoxProfile
from utils.misc import generate_packet, zfill

sizes = [1, 45, 88, 132, 176, 220, 263, 307]
loss_rates = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]

for repetition in range(10000):
    for size in sizes:

        PACKET = generate_packet(size)

        for lr in loss_rates:
            print("PACKET SIZE = {}".format(size))
            print("LOSS RATE = {}".format(size))
            print("(Repetition {})".format(repetition))
            profile = SigfoxProfile("UPLINK", "ACK ON ERROR", Rule('000'))
            sender = SCHCSender(profile)

            sender.UPLINK_LOSS_RATE = lr
            sender.PROFILE.SIGFOX_DL_TIMEOUT = 0.1
            sender.PROFILE.RETRANSMISSION_TIMEOUT = 0.1

            sender.start_session(PACKET)
            if sender.LOGGER.SENT < sender.NB_FRAGMENTS:
                exit(1)

            sender.LOGGER.export(
                "s{}_"
                "lr{}_"
                "rep{}".format(
                    size,
                    zfill(str(lr), 2),
                    str(repetition).zfill(9)
                )
            )

print("All experiments complete")
