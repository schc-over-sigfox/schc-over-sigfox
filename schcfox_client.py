"""Executes the sender-side of the SCHC/Sigfox simulation.
It demonstrates the functioning of the SCHC simulator:
Sends packets of different sizes over different induced loss rates,
and stores the logging information afterwards."""
import sys

from Entities.Rule import Rule
from Entities.SCHCSender import SCHCSender
from Entities.SigfoxProfile import SigfoxProfile
from utils.misc import generate_packet

sizes = [1, 45, 88, 132, 176, 220, 263, 307]
loss_rates = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]

for repetition in range(2):
    for size in sizes:

        PACKET = generate_packet(size)

        for lr in loss_rates:
            print(f"PACKET SIZE = {size}")
            print(f"LOSS RATE = {lr}")
            print(f"(Repetition {repetition})")
            profile = SigfoxProfile("UPLINK", "ACK ON ERROR", Rule('000'))
            sender = SCHCSender(profile)

            sender.UPLINK_LOSS_RATE = lr
            sender.PROFILE.SIGFOX_DL_TIMEOUT = 1
            sender.PROFILE.RETRANSMISSION_TIMEOUT = 1

            sender.start_session(PACKET)

            print(f"Total sent: {sender.LOGGER.SENT}")
            if sender.LOGGER.SENT < sender.NB_FRAGMENTS:
                sys.exit(1)

            sender.LOGGER.export(
                f"s{size}_"
                f"lr{str(lr).zfill(2)}_"
                f"rep{str(repetition).zfill(9)}"
            )

print("All experiments complete")
