
import discord
from discord.ext import commands

from utilities import errors

# Decorators & Predicates

def is_server_owner():
	
	async def predicate(ctx):
		if ctx.channel.type is discord.ChannelType.private:
			return True
		if ctx.author == ctx.guild.owner:
			return True
		try:
			return await commands.is_owner().predicate(ctx)
		except commands.NotOwner:
			raise errors.NotServerOwner
	
	return commands.check(predicate)

def is_voice_connected_check(ctx):
	return ctx.guild and ctx.guild.voice_client

def is_voice_connected():
	
	async def predicate(ctx):
		if not is_voice_connected_check(ctx):
			permitted = await ctx.get_permission("join", id = ctx.author.id)
			if permitted:
				raise errors.PermittedVoiceNotConnected
			try:
				await is_server_owner().predicate(ctx)
				raise errors.PermittedVoiceNotConnected
			except errors.NotServerOwner:
				raise errors.NotPermittedVoiceNotConnected
		return True
	
	return commands.check(predicate)

async def has_permissions_check(ctx, permissions, *, channel = None, guild = False):
	channel = channel or ctx.channel
	author_permissions = ctx.author.guild_permissions if guild else channel.permissions_for(ctx.author)
	try:
		is_owner = await commands.is_owner().predicate(ctx)
	except commands.NotOwner:
		is_owner = False
	return all(getattr(author_permissions, permission, None) == setting for permission, setting in permissions.items()) or is_owner

def has_permissions(*, guild = False, **permissions):
	
	async def predicate(ctx):
		has_permissions = await has_permissions_check(ctx, permissions, guild = guild)
		if has_permissions:
			return True
		else:
			raise errors.MissingPermissions
	
	return commands.check(predicate)

def dm_or_has_permissions(*, guild = False, **permissions):
	
	async def predicate(ctx):
		has_permissions = await has_permissions_check(ctx, permissions, guild = guild)
		if ctx.channel.type is discord.ChannelType.private or has_permissions:
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
		if ctx.channel.type is discord.ChannelType.private or has_capability_check(ctx, permissions, guild = guild):
			return True
		else:
			raise errors.MissingCapability(permissions)
	
	return commands.check(predicate)

def has_permissions_and_capability(*, guild = False, **permissions):
	
	async def predicate(ctx):
		if ctx.channel.type is discord.ChannelType.private:
			return False
		has_permissions = await has_permissions_check(ctx, permissions, guild = guild)
		if not has_permissions:
			raise errors.MissingPermissions
		elif not has_capability_check(ctx, permissions.keys(), guild = guild):
			raise errors.MissingCapability(permissions.keys())
		else:
			return True
	
	return commands.check(predicate)

# Necessary?
def dm_or_has_permissions_and_capability(*, guild = False, **permissions):
	
	async def predicate(ctx):
		if ctx.channel.type is discord.ChannelType.private:
			return True
		has_permissions = await has_permissions_check(ctx, permissions, guild = guild)
		if not has_permissions:
			raise errors.MissingPermissions
		elif not has_capability_check(ctx, permissions.keys(), guild = guild):
			raise errors.MissingCapability(permissions.keys())
		else:
			return True
	
	return commands.check(predicate)

async def not_forbidden_check(ctx):
	if ctx.channel.type is discord.ChannelType.private:
		return True
	permitted = await ctx.get_permission(ctx.command.name, id = ctx.author.id)
	try:
		is_server_owner = await is_server_owner().predicate(ctx)
	except errors.NotServerOwner:
		is_server_owner = False
	# TODO: Include subcommands?
	return permitted or permitted is None or is_server_owner

async def not_forbidden_predicate(ctx):
	not_forbidden = await not_forbidden_check(ctx)
	if not_forbidden:
		return True
	else:
		raise errors.NotPermitted

def not_forbidden():
	return commands.check(not_forbidden_predicate)

async def is_permitted_check(ctx):
	'''Check if permitted'''
	if ctx.channel.type is discord.ChannelType.private:
		return True
	command = ctx.command
	permitted = await ctx.get_permission(command.name, id = ctx.author.id)
	while command.parent is not None and not permitted:
		# permitted is None instead?
		command = command.parent
		permitted = await ctx.get_permission(command.name, id = ctx.author.id)
		# include non-final parent commands?
	try:
		is_server_owner = await is_server_owner().predicate(ctx)
	except errors.NotServerOwner:
		is_server_owner = False
	return permitted or is_server_owner

def is_permitted():
	
	async def predicate(ctx):
		permitted = await is_permitted_check(ctx)
		if permitted:
			return True
		else:
			raise errors.NotPermitted
	
	return commands.check(predicate)

# Functions

async def has_permissions_and_capability_check(ctx, channel = None, guild = False, **permissions):
	channel = channel or ctx.channel
	# TODO: if owner?
	has_permissions = await has_permissions_check(ctx, permissions, channel = channel, guild = guild)
	if not has_permissions:
		raise errors.MissingPermissions
	elif not has_capability_check(ctx, permissions.keys(), channel = channel, guild = guild):
		raise errors.MissingCapability(permissions.keys())

