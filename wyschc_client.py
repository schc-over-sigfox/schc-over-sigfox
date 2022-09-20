"""Executes the sender-side of the project."""

from Entities.Rule import Rule
from Entities.SCHCSender import SCHCSender
from Entities.SigfoxProfile import SigfoxProfile
from utils.misc import generate_packet

PACKET = generate_packet(256)

loss_rates = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]

for lr in loss_rates:
    print(f"LOSS RATE = {lr}")
    for repetition in range(1):
        print(f"(Repetition {repetition})")
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", Rule('000'))
        sender = SCHCSender(profile)

        sender.UPLINK_LOSS_RATE = lr
        sender.PROFILE.SIGFOX_DL_TIMEOUT = 2
        sender.PROFILE.RETRANSMISSION_TIMEOUT = 5
        sender.ENABLE_MAX_ACK_REQUESTS = False

        sender.start_session(PACKET)

        sender.LOGGER.export(f"{str(lr).zfill(2)}_"
                             f"rep{str(repetition).zfill(2)}")

print("All experiments complete")
