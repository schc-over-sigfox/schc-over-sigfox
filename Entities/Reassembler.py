from Entities.SigfoxProfile import SigfoxProfile
from Messages.Fragment import Fragment


class Reassembler:

	def __init__(
			self,
			profile: SigfoxProfile,
			fragments: list[Fragment],
	) -> None:
		self.PROFILE = profile
		self.FRAGMENTS = fragments
		self.SCHC_PACKET = b''
		self.COMPLETE = False

	def reassemble(self) -> bytes:
		"""Merges all the SCHC Fragments into the original SCHC Packet."""

		self.FRAGMENTS = sorted(self.FRAGMENTS, key=(lambda f: (f.WINDOW, f.INDEX)))
		self.SCHC_PACKET = b''.join([fragment.PAYLOAD for fragment in self.FRAGMENTS])
		self.COMPLETE = True

		return self.SCHC_PACKET
