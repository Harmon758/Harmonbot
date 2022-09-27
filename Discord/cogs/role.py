
import discord
from discord.ext import commands

from operator import attrgetter

from utilities import checks

async def setup(bot):
	await bot.add_cog(Role(bot))

class Role(commands.Cog):
	"""Role"""
	
	def __init__(self, bot):
		self.bot = bot
	
	async def cog_check(self, ctx):
		guild_only = await commands.guild_only().predicate(ctx)
		not_forbidden = await checks.not_forbidden().predicate(ctx)
		return guild_only and not_forbidden
	
	@commands.hybrid_group(aliases = ["roles"], case_insensitive = True)
	async def role(self, ctx):
		"""Role"""
		await ctx.send_help(ctx.command)
	
	# TODO: check role hierarchy
	# TODO: reason options?
	
	@role.command(aliases = ["colour"], with_app_command = False)
	async def color(self, ctx, role: discord.Role, *, color: discord.Color = None):
		'''The color of a role'''
		if color:
			await commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner()).predicate(ctx)
			await commands.bot_has_guild_permissions(manage_roles = True).predicate(ctx)
			await role.edit(color = color)
			await ctx.embed_reply(role.mention + " has been recolored")
		else:
			await ctx.embed_reply(role.mention + "'s color is {}".format(role.color))
	
	@role.command(aliases = ["make", "new"], with_app_command = False)
	@commands.bot_has_guild_permissions(manage_roles = True)
	@commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner())
	async def create(self, ctx, *, name: str = ""):
		'''Creates a role'''
		# TODO: Add more options
		role = await ctx.guild.create_role(name = name)
		await ctx.embed_reply(role.mention + " created")
	
	@role.command(with_app_command = False)
	async def default(self, ctx, *, role: discord.Role):
		'''Whether a role is the default role or not'''
		await ctx.embed_reply(role.mention + " is {}the default role".format("" if role.is_default() else "not "))
	
	@role.command(aliases = ["hoist"], with_app_command = False)
	async def hoisted(self, ctx, role: discord.Role, hoist: bool = None):
		'''Whether a role is displayed separately from other members or not'''
		if hoist is not None:
			await commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner()).predicate(ctx)
			await commands.bot_has_guild_permissions(manage_roles = True).predicate(ctx)
			await role.edit(hoist = hoist)
			await ctx.embed_reply(role.mention + " has been {}hoisted".format("" if hoist else "un"))
		else:
			await ctx.embed_reply(role.mention + " is {}hoisted".format("" if role.hoist else "not "))
	
	@role.command(with_app_command = False)
	async def id(self, ctx, *, role: discord.Role):
		'''The ID of a role'''
		await ctx.embed_reply(role.id)
	
	@role.command(aliases = ["info"], with_app_command = False)
	async def information(self, ctx, *, role: discord.Role):
		"""Information about a role"""
		if command := ctx.bot.get_command("information role"):
			await command(ctx, role = role)
		else:
			raise RuntimeError(
				"information role command not found "
				"when role information command invoked"
			)
	
	@role.command(with_app_command = False)
	async def managed(self, ctx, *, role: discord.Role):
		'''Indicates if the role is managed by the guild through some form of integrations such as Twitch'''
		await ctx.embed_reply(role.mention + " is {}managed".format("" if role.managed else "not "))
	
	@role.command(with_app_command = False)
	async def mentionable(self, ctx, role: discord.Role, mentionable: bool = None):
		'''Whether a role is mentionable or not'''
		if mentionable is not None:
			await commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner()).predicate(ctx)
			await commands.bot_has_guild_permissions(manage_roles = True).predicate(ctx)
			await role.edit(mentionable = mentionable)
			await ctx.embed_reply(role.mention + " is now {}mentionable".format("" if mentionable else "not "))
		else:
			await ctx.embed_reply(role.mention + " is {}mentionable".format("" if role.mentionable else "not "))
	
	@role.command(with_app_command = False)
	async def name(self, ctx, role: discord.Role, *, name: str = ""):
		'''The name of a role'''
		if name:
			await commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner()).predicate(ctx)
			await commands.bot_has_guild_permissions(manage_roles = True).predicate(ctx)
			await role.edit(name = name)
			await ctx.embed_reply(role.mention + " has been renamed")
		else:
			await ctx.embed_reply(role.name)
	
	@role.command(with_app_command = False)
	async def position(self, ctx, role: discord.Role, position: int = None):
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
	@role.command(with_app_command = False)
	async def positions(self, ctx):
		'''
		WIP
		Positions of roles in the server
		'''
		await ctx.embed_reply(', '.join("{}: {}".format(role.mention, role.position) for role in sorted(ctx.guild.roles[1:], key = attrgetter("position"), reverse = True)))

