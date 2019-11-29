
from discord.ext.commands.errors import CommandError

class NotServerOwner(CommandError):
	'''Not Server Owner'''
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

class MissingPermissions(CommandError):
	'''Missing Permissions'''
	pass

class MissingCapability(CommandError):
	'''Missing Capability'''
	def __init__(self, permissions):
		self.permissions = permissions

class NotPermitted(CommandError):
	'''Not Permitted'''
	pass

class AudioError(CommandError):
	'''Audio Error'''
	pass

class AudioNotPlaying(AudioError):
	'''Audio Not Playing'''
	pass

