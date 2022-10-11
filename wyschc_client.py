"""Executes the sender-side of the project."""

from Entities.Rule import Rule
from Entities.SCHCSender import SCHCSender
from Entities.SigfoxProfile import SigfoxProfile
from utils.misc import generate_packet

sizes = [11, 54, 96, 139, 181, 224, 266, 307]
loss_rates = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

for repetition in range(10000):
    for size in sizes:

        PACKET = generate_packet(size)

        for lr in loss_rates:
            print(f"PACKET SIZE = {size}")
            print(f"LOSS RATE = {lr}")
            print(f"(Repetition {repetition})")
            profile = SigfoxProfile("UPLINK", "ACK ON ERROR", Rule('000'))
            sender = SCHCSender(profile)

            sender.UPLINK_LOSS_RATE = lr
            sender.PROFILE.SIGFOX_DL_TIMEOUT = 5
            sender.PROFILE.RETRANSMISSION_TIMEOUT = 5

            sender.start_session(PACKET)

            print(f"total sent: {sender.LOGGER.SENT}")
            if sender.LOGGER.SENT < sender.NB_FRAGMENTS:
                exit(1)

            sender.LOGGER.export(
                f"s{size}_"
                f"lr{str(lr).zfill(2)}_"
                f"rep{str(repetition).zfill(9)}"
            )

print("All experiments complete")
