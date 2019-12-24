
import discord
from discord.ext import commands

from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(User(bot))

class User(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	# TODO: add commands
	# TODO: role removal
	
	@commands.group(aliases = ["member"], invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def user(self, ctx):
		'''User'''
		await ctx.send_help(ctx.command)
	
	@user.command(aliases = ["addrole"])
	@commands.guild_only()
	@checks.has_permissions_and_capability(manage_roles = True)
	async def add_role(self, ctx, member : discord.Member, *, role : discord.Role):
		'''Gives a user a role'''
		await member.add_roles(role)
		await ctx.embed_reply("I gave the role, {}, to {}".format(role, member))
	
	@commands.command()
	@checks.not_forbidden()
	async def avatar(self, ctx, *, name : str = ""):
		'''
		See a bigger version of an avatar
		Your own or someone else's avatar
		'''
		if not name:
			await ctx.embed_reply(title = "Your avatar", image_url = ctx.author.avatar_url)
		elif not ctx.guild:
			await ctx.embed_reply(":no_entry: Error: Please use that command in a server")
		else:
			user = await utilities.get_user(ctx, name)
			if not user:
				await ctx.embed_reply(":no_entry: Error: {} was not found on this server".format(name))
			else:
				await ctx.embed_reply(title = "{}'s avatar".format(user), image_url = user.avatar_url)
	
	@commands.command()
	@checks.not_forbidden()
	async def discriminator(self, ctx, *, name : str = ""):
		'''
		Get a discriminator
		Your own or someone else's discriminator
		'''
		if not name:
			return await ctx.embed_reply("Your discriminator: #" + ctx.author.discriminator)
		if not ctx.guild:
			return await ctx.embed_reply(":no_entry: Please use that command in a server")
		found = False
		for member in ctx.guild.members:
			if member.name == name:
				await ctx.embed_reply(name + "'s discriminator: #" + member.discriminator, footer_text = str(member), footer_icon_url = member.avatar_url)
				found = True
		if not found:
			await ctx.embed_reply(name + " was not found on this server")
	
	@user.command()
	@checks.not_forbidden()
	async def name(self, ctx, *, user : discord.Member):
		'''The name of a user'''
		# Include mention?
		await ctx.embed_reply(user.mention, footer_text = str(user), footer_icon_url = user.avatar_url)
	
	@commands.command(aliases = ["usertoid", "usernametoid", "name_to_id", "user_to_id", "username_to_id"])
	@commands.guild_only()
	@checks.not_forbidden()
	async def nametoid(self, ctx, *, name : str):
		'''Convert username to id'''
		user = await utilities.get_user(ctx, name)
		if not user:
			await ctx.embed_reply(":no_entry: Error: {} was not found on this server".format(name))
		else:
			# Include mention?
			await ctx.embed_reply(user.id, footer_text = str(user), footer_icon_url = user.avatar_url)

