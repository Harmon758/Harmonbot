
from discord.ext.commands.errors import CheckFailure

class NotGuildOwner(CheckFailure):
	'''Not Guild Owner'''
	pass

class VoiceNotConnected(CheckFailure):
	'''Voice Not Connected'''
	pass

class PermittedVoiceNotConnected(VoiceNotConnected):
	'''Permitted, but Voice Not Connected'''
	pass

class NotPermittedVoiceNotConnected(VoiceNotConnected):
	'''Voice Not Connected, and Not Permitted'''
	pass

class NotPermitted(CheckFailure):
	'''Not Permitted'''
	pass

class AudioError(CheckFailure):
	'''Audio Error'''
	pass

