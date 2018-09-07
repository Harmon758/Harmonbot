
import discord
from discord.ext import commands

import clients
import credentials
from utilities import errors

# Decorators & Predicates

def is_owner_check(ctx):
	return ctx.author.id == ctx.bot.owner_id

def is_server_owner_check(ctx):
	return isinstance(ctx.channel, discord.DMChannel) or ctx.author == ctx.guild.owner or is_owner_check(ctx)

def is_server_owner():
	
	def predicate(ctx):
		if is_server_owner_check(ctx):
			return True
		else:
			raise errors.NotServerOwner
	
	return commands.check(predicate)

def is_voice_connected_check(ctx):
	return ctx.guild and ctx.guild.voice_client

def is_voice_connected():
	
	def predicate(ctx):
		if not is_voice_connected_check(ctx):
			if is_server_owner_check(ctx) or clients.get_permission(ctx, "join", id = ctx.author.id):
				raise errors.PermittedVoiceNotConnected
			else:
				raise errors.NotPermittedVoiceNotConnected
		return True
	
	return commands.check(predicate)

def has_permissions_check(ctx, permissions, *, channel = None, guild = False):
	channel = channel or ctx.channel
	author_permissions = ctx.author.guild_permissions if guild else channel.permissions_for(ctx.author)
	return all(getattr(author_permissions, permission, None) == setting for permission, setting in permissions.items()) or is_owner_check(ctx)

def has_permissions(*, guild = False, **permissions):
	
	def predicate(ctx):
		if has_permissions_check(ctx, permissions, guild = guild):
			return True
		else:
			raise errors.MissingPermissions
	
	return commands.check(predicate)

def dm_or_has_permissions(*, guild = False, **permissions):
	
	def predicate(ctx):
		if isinstance(ctx.channel, discord.DMChannel) or has_permissions_check(ctx, permissions, guild = guild):
			return True
		else:
			raise errors.MissingPermissions
	
	return commands.check(predicate)

def has_capability_check(ctx, permissions, *, channel = None, guild = False):
	channel = channel or ctx.channel
	bot_permissions = ctx.me.guild_permissions if guild else channel.permissions_for(ctx.me)
	return all(getattr(bot_permissions, permission, None) == True for permission in permissions)

def has_capability(*permissions, guild = False):
	
	def predicate(ctx):
		if has_capability_check(ctx, permissions, guild = guild):
			return True
		else:
			raise errors.MissingCapability(permissions)
	
	return commands.check(predicate)

def dm_or_has_capability(*permissions, guild = False):
	
	def predicate(ctx):
		if isinstance(ctx.channel, discord.DMChannel) or has_capability_check(ctx, permissions, guild = guild):
			return True
		else:
			raise errors.MissingCapability(permissions)
	
	return commands.check(predicate)

def has_permissions_and_capability(*, guild = False, **permissions):
	
	def predicate(ctx):
		if isinstance(ctx.channel, discord.DMChannel):
			return False
		elif not has_permissions_check(ctx, permissions, guild = guild):
			raise errors.MissingPermissions
		elif not has_capability_check(ctx, permissions.keys(), guild = guild):
			raise errors.MissingCapability(permissions.keys())
		else:
			return True
	
	return commands.check(predicate)

def dm_or_has_permissions_and_capability(*, guild = False, **permissions):
	
	def predicate(ctx):
		if isinstance(ctx.channel, discord.DMChannel):
			return True
		elif not has_permissions_check(ctx, permissions, guild = guild):
			raise errors.MissingPermissions
		elif not has_capability_check(ctx, permissions.keys(), guild = guild):
			raise errors.MissingCapability(permissions.keys())
		else:
			return True
	
	return commands.check(predicate)

def not_forbidden_check(ctx):
	if isinstance(ctx.channel, discord.DMChannel):
		return True
	permitted = clients.get_permission(ctx, ctx.command.name, id = ctx.author.id)
	# TODO: Include subcommands?
	return permitted or permitted is None or is_server_owner_check(ctx)

def not_forbidden():
	
	def predicate(ctx):
		if not_forbidden_check(ctx):
			return True
		else:
			raise errors.NotPermitted
	
	return commands.check(predicate)

def is_permitted_check(ctx):
	'''Check if permitted'''
	if isinstance(ctx.channel, discord.DMChannel):
		return True
	command = ctx.command
	permitted = clients.get_permission(ctx, command.name, id = ctx.author.id)
	while command.parent is not None and not permitted:
		# permitted is None instead?
		command = command.parent
		permitted = clients.get_permission(ctx, command.name, id = ctx.author.id)
		# include non-final parent commands?
	return permitted or is_server_owner_check(ctx)

def is_permitted():
	
	def predicate(ctx):
		if is_permitted_check(ctx):
			return True
		else:
			raise errors.NotPermitted
	
	return commands.check(predicate)

# Functions

def has_permissions_and_capability_check(ctx, channel = None, guild = False, **permissions):
	channel = channel or ctx.channel
	if not has_permissions_check(ctx, permissions, channel = channel, guild = guild):
		raise errors.MissingPermissions
	elif not has_capability_check(ctx, permissions.keys(), channel = channel, guild = guild):
		raise errors.MissingCapability(permissions.keys())

