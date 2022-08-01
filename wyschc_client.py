"""Executes the sender-side of the project."""

from Entities.Rule import Rule
from Entities.SCHCSender import SCHCSender
from Entities.SigfoxProfile import SigfoxProfile
from utils.misc import generate_packet

PACKET = generate_packet(100)

profile = SigfoxProfile("UPLINK", "ACK ON ERROR", Rule('000'))
sender = SCHCSender(profile)

sender.start_session(PACKET)

input("Press Enter to exit.")
