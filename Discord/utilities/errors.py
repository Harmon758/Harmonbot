
from discord.ext.commands.errors import CommandError

class NotOwner(CommandError):
	pass

class NotServerOwner(CommandError):
	pass

class VoiceNotConnected(CommandError):
	pass

class PermittedVoiceNotConnected(VoiceNotConnected):
	pass

class NotPermittedVoiceNotConnected(VoiceNotConnected):
	pass

class MissingPermissions(CommandError):
	pass

class MissingCapability(CommandError):
	def __init__(self, permissions):
		self.permissions = permissions

class NotPermitted(CommandError):
	pass

class LichessUserNotFound(CommandError):
	pass

