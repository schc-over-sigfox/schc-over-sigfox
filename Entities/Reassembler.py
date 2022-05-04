from Entities.SigfoxProfile import SigfoxProfile
from Messages.Fragment import Fragment
from db.JSONStorage import JSONStorage


class Reassembler:

	def __init__(self, profile: SigfoxProfile, fragments: list[Fragment], storage: JSONStorage):
		self.PROFILE = profile
		self.FRAGMENTS = fragments
		# TODO: self.STORAGE = storage
		self.SCHC_PACKET = b''
		self.COMPLETE = False

	def reassemble(self):
		"""Merges all the SCHC Fragments into the original SCHC Packet."""

		self.SCHC_PACKET = b''.join([fragment.PAYLOAD for fragment in self.FRAGMENTS])
		self.COMPLETE = True

		return self.SCHC_PACKET
