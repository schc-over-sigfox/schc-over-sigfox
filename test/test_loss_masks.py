from Entities.Rule import Rule
from Entities.SCHCSender import SCHCSender
from test.loss_masks_28f import loss_masks
from utils.misc import generate_packet

print("Start the server and press any key afterwards.")

for loss_mask in loss_masks:

    packet = generate_packet(307)
    rule = Rule('000')
    sender = SCHCSender(rule)
    sender.RULE.SIGFOX_DL_TIMEOUT = 2
    sender.RULE.RETRANSMISSION_TIMEOUT = 5
    sender.LOSS_MASK = loss_mask
    sender.start_session(packet)

    print("Actual: " + sender.LOGGER.SEQUENCE)
    print("Expect: " + sender.LOSS_MASK["expected"])
    success = sender.LOGGER.SEQUENCE == sender.LOSS_MASK["expected"]

    if success:
        print("Success!")
        # input("Press Enter to continue.")
    else:
        print("Failure in loss mask {}".format(loss_masks.index(loss_mask)))
        break
