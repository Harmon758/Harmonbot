
from discord.ext import commands

from utilities import errors
from modules import utilities

import credentials
from clients import client

def is_owner_check(ctx):
	return ctx.message.author.id == credentials.myid

def is_owner():
	
	def predicate(ctx):
		if is_owner_check(ctx):
			return True
		else:
			raise errors.NotOwner
	
	return commands.check(predicate)

def is_server_owner_check(ctx):
	return ctx.message.channel.is_private or ctx.message.author == ctx.message.server.owner or is_owner_check(ctx)

def is_server_owner():
	
	def predicate(ctx):
		if is_server_owner_check(ctx):
			return True
		else:
			raise errors.NotServerOwner
	
	return commands.check(predicate)

def is_voice_connected_check(ctx):
	return ctx.message.server and client.is_voice_connected(ctx.message.server)

def is_voice_connected():
	
	def predicate(ctx):
		if not is_voice_connected_check(ctx):
			if is_server_owner_check(ctx):
				raise errors.SO_VoiceNotConnected
			else:
				raise errors.NSO_VoiceNotConnected
		return True
	
	return commands.check(predicate)

def has_permissions_check(ctx, permissions):
	_permissions = ctx.message.channel.permissions_for(ctx.message.author)
	return all(getattr(_permissions, permission, None) == setting for permission, setting in permissions.items()) or is_owner_check(ctx)

def has_permissions(**permissions):
	
	def predicate(ctx):
		if has_permissions_check(ctx, permissions):
			return True
		else:
			raise errors.MissingPermissions
	
	return commands.check(predicate)

def dm_or_has_permissions(**permissions):
	
	def predicate(ctx):
		if ctx.message.channel.is_private or has_permissions_check(ctx, permissions):
			return True
		else:
			raise errors.MissingPermissions
	
	return commands.check(predicate)

def has_capability_check(ctx, permissions):
	_permissions = ctx.message.channel.permissions_for(ctx.message.server.me)
	return all(getattr(_permissions, permission, None) == True for permission in permissions)

def has_capability(*permissions):
	
	def predicate(ctx):
		if has_capability_check(ctx, permissions):
			return True
		else:
			raise errors.MissingCapability(permissions)
	
	return commands.check(predicate)

def dm_or_has_capability(*permissions):
	
	def predicate(ctx):
		if ctx.message.channel.is_private or has_capability_check(ctx, permissions):
			return True
		else:
			raise errors.MissingCapability(permissions)
	
	return commands.check(predicate)

def has_permissions_and_capability(**permissions):
	
	def predicate(ctx):
		if ctx.message.channel.is_private:
			return False
		elif not has_permissions_check(ctx, permissions):
			raise errors.MissingPermissions
		elif not has_capability_check(ctx, permissions.keys()):
			raise errors.MissingCapability(permissions.keys())
		else:
			return True
	
	return commands.check(predicate)

def dm_or_has_permissions_and_capability(**permissions):
	
	def predicate(ctx):
		if ctx.message.channel.is_private:
			return True
		elif not has_permissions_check(ctx, permissions):
			raise errors.MissingPermissions
		elif not has_capability_check(ctx, permissions.keys()):
			raise errors.MissingCapability(permissions.keys())
		else:
			return True
	
	return commands.check(predicate)

def not_forbidden_check(ctx):
	if ctx.message.channel.is_private:
		return True
	permitted = utilities.get_permission(ctx, ctx.command.name, id = ctx.message.author.id)
	return permitted or permitted is None or is_server_owner_check(ctx)

def not_forbidden():
	
	def predicate(ctx):
		if not_forbidden_check(ctx):
			return True
		else:
			raise errors.NotPermitted
	
	return commands.check(predicate)

def is_permitted_check(ctx):
	if ctx.message.channel.is_private:
		return True
	permitted = utilities.get_permission(ctx, ctx.command.name, id = ctx.message.author.id)
	return permitted or is_server_owner_check(ctx)

def is_permitted():
	
	def predicate(ctx):
		if is_permitted_check(ctx):
			return True
		else:
			raise errors.NotPermitted
	
	return commands.check(predicate)

