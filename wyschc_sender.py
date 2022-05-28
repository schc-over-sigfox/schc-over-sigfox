from Entities.Rule import Rule
from Entities.SCHCSender import SCHCSender
from Entities.SigfoxProfile import SigfoxProfile
from utils.misc import generate_packet

packet = generate_packet(100)

profile = SigfoxProfile("UPLINK", "ACK ON ERROR", Rule('000'))
sender = SCHCSender(profile)

sender.start_session(packet)

input("Press Enter to exit.")
