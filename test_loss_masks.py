from Entities.Rule import Rule
from Entities.SCHCSender import SCHCSender
from Entities.SigfoxProfile import SigfoxProfile
from test.loss_masks import loss_masks
from utils.misc import generate_packet

input("Start the server and press any key afterwards.")

for loss_mask in loss_masks:

    packet = generate_packet(300)
    profile = SigfoxProfile("UPLINK", "ACK ON ERROR", Rule('000'))
    sender = SCHCSender(profile)
    sender.PROFILE.SIGFOX_DL_TIMEOUT = 2
    sender.PROFILE.RETRANSMISSION_TIMEOUT = 5
    sender.LOSS_MASK = loss_mask
    sender.start_session(packet)

    print("Actual: " + sender.LOGGER.BEHAVIOR)
    print("Expect: " + sender.LOSS_MASK["expected"])
    success = sender.LOGGER.BEHAVIOR == sender.LOSS_MASK["expected"]

    if success:
        print("Success!")
        # input("Press Enter to continue.")
    else:
        print(f"Failure in loss mask {loss_masks.index(loss_mask)}")
        break
