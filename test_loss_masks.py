from Entities.Rule import Rule
from Entities.SCHCSender import SCHCSender
from Entities.SigfoxProfile import SigfoxProfile
from test.loss_masks import *
from utils.misc import generate_packet

print("Start the server and press any key afterwards.")

loss_mask = loss_mask_6

packet = generate_packet(300)
profile = SigfoxProfile("UPLINK", "ACK ON ERROR", Rule('000'))
sender = SCHCSender(profile)
sender.PROFILE.SIGFOX_DL_TIMEOUT = 2
sender.PROFILE.RETRANSMISSION_TIMEOUT = 5
sender.LOSS_MASK = loss_mask
sender.start_session(packet)

print("Actual: " + sender.LOGGER.BEHAVIOR)
print("Expect: " + sender.LOSS_MASK["expected"])
print(sender.LOGGER.BEHAVIOR == sender.LOSS_MASK["expected"])

input("Press Enter to exit.")
