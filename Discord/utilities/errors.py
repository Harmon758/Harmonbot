
from discord.ext.commands.errors import CommandError

class NotGuildOwner(CommandError):
	'''Not Guild Owner'''
	pass

class VoiceNotConnected(CommandError):
	'''Voice Not Connected'''
	pass

class PermittedVoiceNotConnected(VoiceNotConnected):
	'''Permitted, but Voice Not Connected'''
	pass

class NotPermittedVoiceNotConnected(VoiceNotConnected):
	'''Voice Not Connected, and Not Permitted'''
	pass

class NotPermitted(CommandError):
	'''Not Permitted'''
	pass

class AudioError(CommandError):
	'''Audio Error'''
	pass

