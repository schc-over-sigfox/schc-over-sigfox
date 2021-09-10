# Controlling deterministic losses. This file states when should a fragment be
# lost, separated by windows:
# 0 -> don't lose the fragment/ACK
# 1 -> lose the fragment/ACK but accepts retransmissions
# 2 -> lose the fragment/ACK, lose its first retransmission
# i > 0 -> lose the fragment/ACK i times

loss_mask_0 = {"fragment": {"0": "0000000",
                            "1": "0000000",
                            "2": "0000000",
                            "3": "0000000"},
               "ack": {"0": "0",
                       "1": "0",
                       "2": "0",
                       "3": "000"},
               "expected": "W0F0W0F1W0F2W0F3W0F4W0F5W0F6"
                           "W1F0W1F1W1F2W1F3W1F4W1F5W1F6"
                           "W2F0W2F1W2F2W2F3W2F4W2F5W2F6"
                           "W3F0W3F1W3F2W3F3W3F4W3F5W3F6"}

loss_mask_1 = {"fragment": {"0": "0010000",
                            "1": "0000000",
                            "2": "0000000",
                            "3": "0000000"},
               "ack": {"0": "0",
                       "1": "0",
                       "2": "0",
                       "3": "000"},
               "expected": "W0F0W0F1W0F3W0F4W0F5W0F6W0F2"
                           "W1F0W1F1W1F2W1F3W1F4W1F5W1F6"
                           "W2F0W2F1W2F2W2F3W2F4W2F5W2F6"
                           "W3F0W3F1W3F2W3F3W3F4W3F5W3F6"}

loss_mask_2 = {"fragment": {"0": "0010000",
                            "1": "0000001",
                            "2": "0100000",
                            "3": "0000010"},
               "ack": {"0": "0",
                       "1": "0",
                       "2": "0",
                       "3": "000"},
               "expected": "W0F0W0F1W0F3W0F4W0F5W0F6W0F2"
                           "W1F0W1F1W1F2W1F3W1F4W1F5"
                           "W2F0W2F2W2F3W2F4W2F5W2F6W1F6W2F1"
                           "W3F0W3F1W3F2W3F3W3F4W3F6W3F5W3F6"}

loss_mask_3 = {"fragment": {"0": "0010000",
                            "1": "0000000",
                            "2": "0000002",
                            "3": "0000000"},
               "ack": {"0": "0",
                       "1": "0",
                       "2": "0",
                       "3": "000"},
               "expected": "W0F0W0F1W0F3W0F4W0F5W0F6W0F2"
                           "W1F0W1F1W1F2W1F3W1F4W1F5W1F6"
                           "W2F0W2F1W2F2W2F3W2F4W2F5"
                           "W3F0W3F1W3F2W3F3W3F4W3F5W3F6W3F6W2F6W3F6"}

loss_mask_4 = {"fragment": {"0": "0000002",
                            "1": "0010000",
                            "2": "0000000",
                            "3": "0000000"},
               "ack": {"0": "0",
                       "1": "0",
                       "2": "0",
                       "3": "000"},
               "expected": "W0F0W0F1W0F2W0F3W0F4W0F5"
                           "W1F0W1F1W1F3W1F4W1F5W1F6W1F2"
                           "W2F0W2F1W2F2W2F3W2F4W2F5W2F6W0F6"
                           "W3F0W3F1W3F2W3F3W3F4W3F5W3F6"}

loss_mask_5 = {"fragment": {"0": "0000002",
                            "1": "0030000",
                            "2": "0000010",
                            "3": "0000000"},
               "ack": {"0": "0",
                       "1": "0",
                       "2": "0",
                       "3": "000"},
               "expected": "W0F0W0F1W0F2W0F3W0F4W0F5"
                           "W1F0W1F1W1F3W1F4W1F5W1F6"
                           "W2F0W2F1W2F2W2F3W2F4W2F6W0F6W2F5"
                           "W3F0W3F1W3F2W3F3W3F4W3F5W3F6W1F2W3F6"}

loss_mask_6 = {"fragment": {"0": "0000000",
                            "1": "0000000",
                            "2": "0000000",
                            "3": "0000001"},
               "ack": {"0": "0",
                       "1": "0",
                       "2": "0",
                       "3": "000"},
               "expected": "W0F0W0F1W0F2W0F3W0F4W0F5W0F6"
                           "W1F0W1F1W1F2W1F3W1F4W1F5W1F6"
                           "W2F0W2F1W2F2W2F3W2F4W2F5W2F6"
                           "W3F0W3F1W3F2W3F3W3F4W3F5W3F6"}

loss_mask_7 = {"fragment": {"0": "0000000",
                            "1": "0000000",
                            "2": "0000000",
                            "3": "0010000"},
               "ack": {"0": "0",
                       "1": "0",
                       "2": "0",
                       "3": "000"},
               "expected": "W0F0W0F1W0F2W0F3W0F4W0F5W0F6"
                           "W1F0W1F1W1F2W1F3W1F4W1F5W1F6"
                           "W2F0W2F1W2F2W2F3W2F4W2F5W2F6"
                           "W3F0W3F1W3F3W3F4W3F5W3F6W3F2W3F6"}
