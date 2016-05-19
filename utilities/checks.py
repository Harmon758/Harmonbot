
from discord.ext import commands
from discord.ext.commands.errors import CommandError

import keys
from client import client

class NotServerOwner(CommandError):
	pass

class VoiceNotConnected(CommandError):
	pass

class SO_VoiceNotConnected(VoiceNotConnected):
	pass

class NSO_VoiceNotConnected(VoiceNotConnected):
	pass

def is_owner_check(message):
    return message.author.id == keys.myid

def is_owner():
    return commands.check(lambda ctx: is_owner_check(ctx.message))

def is_server_owner_check(message):
	return message.author == message.server.owner or is_owner_check(message)

def is_server_owner():
	
	def predicate(ctx):
		if not is_server_owner_check(ctx.message):
			raise NotServerOwner
		else:
			return True
	
	return commands.check(predicate)

def is_voice_connected_check(message):
	return client.is_voice_connected(message.server)

def is_voice_connected():
	
	def predicate(ctx):
		if not is_voice_connected_check(ctx.message):
			if is_server_owner_check(ctx.message):
				raise SO_VoiceNotConnected
			else:
				raise NSO_VoiceNotConnected
		return True
	
	return commands.check(predicate)
