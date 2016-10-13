
from discord.ext.commands.errors import CommandError

class NotOwner(CommandError):
	pass

class NotServerOwner(CommandError):
	pass

class VoiceNotConnected(CommandError):
	pass

class SO_VoiceNotConnected(VoiceNotConnected):
	pass

class NSO_VoiceNotConnected(VoiceNotConnected):
	pass

class TagError(CommandError):
	pass

class NoTags(TagError):
	pass

class NoTag(TagError):
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
