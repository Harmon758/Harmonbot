
import discord
from discord.ext import commands

from utilities import errors

# TODO: Check necessity of all checks
# TODO: Use native discord.py check predicates?

def is_guild_owner():
	
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
			await is_guild_owner().predicate(ctx)
			raise errors.PermittedVoiceNotConnected
		except errors.NotServerOwner:
			raise errors.NotPermittedVoiceNotConnected
	
	return commands.check(predicate)

def has_permissions_for(channel, **permissions):
	
	async def predicate(ctx):
		if not (missing := [permission for permission, setting in permissions.items()
							if getattr(channel.permissions_for(ctx.author), permission, None) != setting]):
			return True
		raise commands.MissingPermissions(missing)
	
	return commands.check(predicate)

def bot_has_permissions_for(channel, **permissions):
	
	def predicate(ctx):
		if not (missing := [permission for permission, setting in permissions.items()
							if getattr(channel.permissions_for(ctx.me), permission, None) != setting]):
			return True
		raise commands.BotMissingPermissions(missing)
	
	return commands.check(predicate)

def not_forbidden():
	
	async def predicate(ctx):
		if ctx.channel.type is discord.ChannelType.private:
			return True
		command = ctx.command
		while ((permitted := await ctx.get_permission(command.name, id = ctx.author.id)) is None
				and command.parent is not None):
			command = command.parent
		try:
			return permitted is not False or await is_guild_owner().predicate(ctx)
		except errors.NotServerOwner:
			raise errors.NotPermitted
	
	return commands.check(predicate)

def is_permitted():
	
	async def predicate(ctx):
		if ctx.channel.type is discord.ChannelType.private:
			return True
		command = ctx.command
		while ((permitted := await ctx.get_permission(command.name, id = ctx.author.id)) is None
				and command.parent is not None):
			command = command.parent
		try:
			return permitted or await is_guild_owner().predicate(ctx)
		except errors.NotServerOwner:
			raise errors.NotPermitted
	
	return commands.check(predicate)

