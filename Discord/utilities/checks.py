
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
		if guild:
			author_permissions = ctx.author.guild_permissions
		else:
			author_permissions = (channel or ctx.channel).permissions_for(ctx.author)
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

def has_capability(*permissions, channel = None, guild = False):
	
	def predicate(ctx):
		if guild:
			bot_permissions = ctx.me.guild_permissions
		else:
			bot_permissions = (channel or ctx.channel).permissions_for(ctx.me)
		if all(getattr(bot_permissions, permission, None) for permission in permissions):
			return True
		else:
			raise errors.MissingCapability(permissions)
	
	return commands.check(predicate)

def dm_or_has_capability(*permissions, guild = False):
	
	def predicate(ctx):
		if ctx.channel.type is discord.ChannelType.private:
			return True
		return has_capability(*permissions, guild = guild).predicate(ctx)
	
	return commands.check(predicate)

def has_permissions_and_capability(*, guild = False, **permissions):
	
	async def predicate(ctx):
		if ctx.channel.type is discord.ChannelType.private:
			return False
		await has_permissions(guild = guild, **permissions).predicate(ctx)
		return has_capability(*permissions.keys(), guild = guild).predicate(ctx)
	
	return commands.check(predicate)

# Necessary?
def dm_or_has_permissions_and_capability(*, guild = False, **permissions):
	
	async def predicate(ctx):
		if ctx.channel.type is discord.ChannelType.private:
			return True
		await has_permissions(guild = guild, **permissions).predicate(ctx)
		return has_capability(*permissions.keys(), guild = guild).predicate(ctx)
	
	return commands.check(predicate)

def not_forbidden():
	
	async def predicate(ctx):
		if ctx.channel.type is discord.ChannelType.private:
			return True
		permitted = await ctx.get_permission(ctx.command.name, id = ctx.author.id)
		if permitted or permitted is None:
			return True
		try:
			return await is_server_owner().predicate(ctx)
		except errors.NotServerOwner:
			raise errors.NotPermitted
		# TODO: Include subcommands?
	
	return commands.check(predicate)

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
	has_capability(*permissions.keys(), channel = channel, guild = guild).predicate(ctx)

