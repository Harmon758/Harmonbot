
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

def is_voice_connected():
	
	async def predicate(ctx):
		if ctx.guild and ctx.guild.voice_client:
			return True
		permitted = await ctx.get_permission("join", id = ctx.author.id)
		if permitted:
			raise errors.PermittedVoiceNotConnected
		try:
			await is_server_owner().predicate(ctx)
			raise errors.PermittedVoiceNotConnected
		except errors.NotServerOwner:
			raise errors.NotPermittedVoiceNotConnected
	
	return commands.check(predicate)

def has_permissions(*, channel = None, guild = False, **permissions):
	
	async def predicate(ctx):
		author_permissions = ctx.author.guild_permissions if guild else (channel or ctx.channel).permissions_for(ctx.author)
		if all(getattr(author_permissions, permission, None) == setting for permission, setting in permissions.items()):
			return True
		try:
			return await commands.is_owner().predicate(ctx)
		except commands.NotOwner:
			raise errors.MissingPermissions
	
	return commands.check(predicate)

def dm_or_has_permissions(*, guild = False, **permissions):
	
	async def predicate(ctx):
		if ctx.channel.type is discord.ChannelType.private:
			return True
		return await has_permissions(guild = guild, **permissions).predicate(ctx)
	
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
		await has_permissions(guild = guild, **permissions).predicate(ctx)
		if not has_capability_check(ctx, permissions.keys(), guild = guild):
			raise errors.MissingCapability(permissions.keys())
		else:
			return True
	
	return commands.check(predicate)

# Necessary?
def dm_or_has_permissions_and_capability(*, guild = False, **permissions):
	
	async def predicate(ctx):
		if ctx.channel.type is discord.ChannelType.private:
			return True
		await has_permissions(guild = guild, **permissions).predicate(ctx)
		if not has_capability_check(ctx, permissions.keys(), guild = guild):
			raise errors.MissingCapability(permissions.keys())
		else:
			return True
	
	return commands.check(predicate)

async def not_forbidden_check(ctx):
	if ctx.channel.type is discord.ChannelType.private:
		return True
	permitted = await ctx.get_permission(ctx.command.name, id = ctx.author.id)
	if permitted or permitted is None:
		return True
	try:
		return await is_server_owner().predicate(ctx)
	except errors.NotServerOwner:
		return False
	# TODO: Include subcommands?

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
		command = command.parent
		permitted = await ctx.get_permission(command.name, id = ctx.author.id)
		if permitted:
			return True
		if permitted is not None:
			break
	try:
		return await is_server_owner().predicate(ctx)
	except errors.NotServerOwner:
		return False

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
	await has_permissions(channel = channel, guild = guild, **permissions).predicate(ctx)
	if not has_capability_check(ctx, permissions.keys(), channel = channel, guild = guild):
		raise errors.MissingCapability(permissions.keys())

