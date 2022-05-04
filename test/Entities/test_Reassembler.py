from unittest import TestCase

from Entities.Fragmenter import Fragmenter
from Entities.Reassembler import Reassembler
from Entities.Rule import Rule
from Entities.SigfoxProfile import SigfoxProfile


class TestReassembler(TestCase):

    def test_reassemble(self):
        randbytes = b'\xf8\xdb\x80\x1b~!\x11?\x87<\xb1\xe3/I\xe2\xf5\x13\xcd\xdb\xdc`4\xe85MU\xbb!FC\xb96\xee:gH:' \
                    b'\t\xbc\xbde\xc2\x18\xce\xe5:"J\x140\xd8=\xc1@S8\x9aJ\xf1\xa1E2\x9d&\xaf\xd8\xc0\\\xc3\xd8T ' \
                    b'\xcaK\x07\xa5\xd9\xab\xfa>\x01e\xbb\xa1v\x9a\xa1\xbe\xfav\xbe\x04T\xee\xae\xa4\xd1|\xd7\x8b' \
                    b'Z;U\xa8LM\x10zY\x04W$}\xf4\xe940\xff\x02\x11\x9a\x89y>\xbe\xea\x83\x190\x1bm\x8d\xae\xcaeV' \
                    b'\x9b\xd9\x1b\xf9*\x03C;NR\x8c\x12\xc6\x87\xb2i~`<uw}\x14\xd9qj\xe7Gx\xee\x80L}\t\x8d\x0cxZt' \
                    b'\xe1e\xb4\xf6\xf3\x85\xa6}\x8eJ\x90\x1c4/\xff\xd5\x18$\x81}\xae\xae{\x1b\xcd#\x18r\n\xf9\x14#_' \
                    b'\x87/.\xa2^\x06\xce\xbf_\x84\x13P\xb8i\xe7\x82KK\x0e\x8eH\xdf\x90\xa5i\xf0\x97w\x87>\xf8\xa1Sj' \
                    b'\x88\xe1\xaa\x07\x87\xf1X\xdak\x85\x1fMw&\x84\x08q(Q\xf3\xa1\xfe\n\xb6e\xdc\xf9\x9e\xebq}|\x9e' \
                    b'\x0e\x98\x81\xca\xaf\xf1\x07B\x83\x85\x8d4@v\x84\x87VV\x11\xb2\xb5\xc9p\xc9\xe5'

        rule_0 = Rule(0, 0)
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", rule_0)
        fragmenter = Fragmenter(profile, "debug/unittest/sd")
        fragments = fragmenter.fragment(randbytes)

        reassembler = Reassembler(profile, fragments, fragmenter.STORAGE)
        schc_packet = reassembler.reassemble()

        self.assertEqual(randbytes, schc_packet)

        multiple_eleven = b'-\xf2}\x1d\x01\xefg\xe7+\xb3\x16\x12\xedf\xdf^\xe65\xcd\x144f'
        fragmenter = Fragmenter(profile, "debug/unittest/sd")
        fragments = fragmenter.fragment(multiple_eleven)
        reassembler = Reassembler(profile, fragments, fragmenter.STORAGE)
        schc_packet = reassembler.reassemble()

        self.assertEqual(schc_packet, multiple_eleven)
