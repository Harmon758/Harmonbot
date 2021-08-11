
import discord
from discord.ext import commands

from utilities import errors

# TODO: Check necessity of all checks
# TODO: Use native discord.py check predicates?

def is_guild_owner():
	
	async def predicate(ctx):
		if ctx.channel.type is discord.ChannelType.private:
			return True
		if ctx.author.id == ctx.guild.owner_id:
			return True
		try:
			return await commands.is_owner().predicate(ctx)
		except commands.NotOwner:
			raise errors.NotGuildOwner
	
	return commands.check(predicate)

def is_voice_connected():
	
	async def predicate(ctx):
		if ctx.guild and ctx.guild.voice_client:
			return True
		permitted = await ctx.get_permission("join", user = ctx.author)
		if permitted:
			raise errors.PermittedVoiceNotConnected
		try:
			await is_guild_owner().predicate(ctx)
			raise errors.PermittedVoiceNotConnected
		except errors.NotGuildOwner:
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
		while ((permitted := await ctx.get_permission(command.name, user = ctx.author)) is None
				and command.parent is not None):
			command = command.parent
		try:
			return permitted is not False or await is_guild_owner().predicate(ctx)
		except errors.NotGuildOwner:
			raise errors.NotPermitted
	
	return commands.check(predicate)

def is_permitted():
	
	async def predicate(ctx):
		command = ctx.command
		while ((permitted := await ctx.get_permission(command.name, user = ctx.author)) is None
				and command.parent is not None):
			command = command.parent
		if permitted:
			return True
		raise errors.NotPermitted
	
	return commands.check(predicate)

