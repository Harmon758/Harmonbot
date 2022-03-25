
import discord
from discord.ext import commands

from operator import attrgetter

from utilities import checks

async def setup(bot):
	await bot.add_cog(Role(bot))

class Role(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	# Role
	
	@commands.group(aliases = ["roles"], invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def role(self, ctx):
		'''Role'''
		await ctx.send_help(ctx.command)
	
	# TODO: check role hierarchy
	# TODO: reason options?
	
	@role.command(name = "color", aliases = ["colour"])
	@commands.guild_only()
	@checks.not_forbidden()
	async def role_color(self, ctx, role: discord.Role, *, color: discord.Color = None):
		'''The color of a role'''
		if color:
			await commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner()).predicate(ctx)
			await commands.bot_has_guild_permissions(manage_roles = True).predicate(ctx)
			await role.edit(color = color)
			await ctx.embed_reply(role.mention + " has been recolored")
		else:
			await ctx.embed_reply(role.mention + "'s color is {}".format(role.color))
	
	@role.command(name = "create", aliases = ["make", "new"])
	@commands.bot_has_guild_permissions(manage_roles = True)
	@commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner())
	async def role_create(self, ctx, *, name: str = ""):
		'''Creates a role'''
		# TODO: Add more options
		role = await ctx.guild.create_role(name = name)
		await ctx.embed_reply(role.mention + " created")
	
	@role.command(name = "default")
	@commands.guild_only()
	@checks.not_forbidden()
	async def role_default(self, ctx, *, role: discord.Role):
		'''Whether a role is the default role or not'''
		await ctx.embed_reply(role.mention + " is {}the default role".format("" if role.is_default() else "not "))
	
	@role.command(name = "hoisted", aliases = ["hoist"])
	@commands.guild_only()
	@checks.not_forbidden()
	async def role_hoisted(self, ctx, role: discord.Role, hoist: bool = None):
		'''Whether a role is displayed separately from other members or not'''
		if hoist is not None:
			await commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner()).predicate(ctx)
			await commands.bot_has_guild_permissions(manage_roles = True).predicate(ctx)
			await role.edit(hoist = hoist)
			await ctx.embed_reply(role.mention + " has been {}hoisted".format("" if hoist else "un"))
		else:
			await ctx.embed_reply(role.mention + " is {}hoisted".format("" if role.hoist else "not "))
	
	@role.command(name = "id")
	@commands.guild_only()
	@checks.not_forbidden()
	async def role_id(self, ctx, *, role: discord.Role):
		'''The ID of a role'''
		await ctx.embed_reply(role.id)
	
	@role.command(name = "managed")
	@commands.guild_only()
	@checks.not_forbidden()
	async def role_managed(self, ctx, *, role: discord.Role):
		'''Indicates if the role is managed by the guild through some form of integrations such as Twitch'''
		await ctx.embed_reply(role.mention + " is {}managed".format("" if role.managed else "not "))
	
	@role.command(name = "mentionable")
	@commands.guild_only()
	@checks.not_forbidden()
	async def role_mentionable(self, ctx, role: discord.Role, mentionable: bool = None):
		'''Whether a role is mentionable or not'''
		if mentionable is not None:
			await commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner()).predicate(ctx)
			await commands.bot_has_guild_permissions(manage_roles = True).predicate(ctx)
			await role.edit(mentionable = mentionable)
			await ctx.embed_reply(role.mention + " is now {}mentionable".format("" if mentionable else "not "))
		else:
			await ctx.embed_reply(role.mention + " is {}mentionable".format("" if role.mentionable else "not "))
	
	@role.command(name = "name")
	@commands.guild_only()
	@checks.not_forbidden()
	async def role_name(self, ctx, role: discord.Role, *, name: str = ""):
		'''The name of a role'''
		if name:
			await commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner()).predicate(ctx)
			await commands.bot_has_guild_permissions(manage_roles = True).predicate(ctx)
			await role.edit(name = name)
			await ctx.embed_reply(role.mention + " has been renamed")
		else:
			await ctx.embed_reply(role.name)
	
	@role.command(name = "position")
	@commands.guild_only()
	@checks.not_forbidden()
	async def role_position(self, ctx, role: discord.Role, position: int = None):
		'''
		The position of a role
		This number is usually positive
		The bottom role has a position of 0
		'''
		if position is not None:
			await commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner()).predicate(ctx)
			await commands.bot_has_guild_permissions(manage_roles = True).predicate(ctx)
			await role.edit(position = position)
			await ctx.embed_reply(role.mention + "'s position has been set to {}".format(position))
		else:
			await ctx.embed_reply(role.mention + "'s position is {}".format(role.position))
	
	# TODO: move to server cog
	@role.command(name = "positions")
	@commands.guild_only()
	@checks.not_forbidden()
	async def role_positions(self, ctx):
		'''
		WIP
		Positions of roles in the server
		'''
		await ctx.embed_reply(', '.join("{}: {}".format(role.mention, role.position) for role in sorted(ctx.guild.roles[1:], key = attrgetter("position"), reverse = True)))

