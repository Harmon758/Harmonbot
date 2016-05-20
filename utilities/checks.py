
from discord.ext import commands

from utilities import errors

import keys
from client import client

def is_owner_check(message):
    return message.author.id == keys.myid

def is_owner():
    return commands.check(lambda ctx: is_owner_check(ctx.message))

def is_server_owner_check(message):
	return (message.server and message.author == message.server.owner) or is_owner_check(message)

def is_server_owner():
	
	def predicate(ctx):
		if not is_server_owner_check(ctx.message):
			raise errors.NotServerOwner
		else:
			return True
	
	return commands.check(predicate)

def is_voice_connected_check(message):
	return message.server and client.is_voice_connected(message.server)

def is_voice_connected():
	
	def predicate(ctx):
		if not is_voice_connected_check(ctx.message):
			if is_server_owner_check(ctx.message):
				raise errors.SO_VoiceNotConnected
			else:
				raise errors.NSO_VoiceNotConnected
		return True
	
	return commands.check(predicate)
