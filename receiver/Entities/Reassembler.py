from Messages.Fragment import Fragment


class Reassembler:
	PROFILE = None
	SCHC_FRAGMENTS = []
	rule_set = set()
	dtag_set = set()
	window_set = set()
	fcn_set = set()

	def __init__(self, profile, schc_fragments):
		self.PROFILE = profile

		self.SCHC_FRAGMENTS = [Fragment(self.PROFILE, fragment) for fragment in schc_fragments]

		# for fragment in self.SCHC_FRAGMENTS:
		# 	 self.rule_set.add(fragment.HEADER.RULE_ID)
		# 	 self.dtag_set.add(fragment.HEADER.DTAG)
		#  	 self.window_set.add(fragment.HEADER.W)
		# 	 self.fcn_set.add(fragment.HEADER.FCN)

	def reassemble(self):
		payload_list = [fragment.PAYLOAD for fragment in self.SCHC_FRAGMENTS]
		return b"".join(payload_list)
