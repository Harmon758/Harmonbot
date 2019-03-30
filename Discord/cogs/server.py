
import discord
from discord.ext import commands

from utilities import checks

def setup(bot):
	bot.add_cog(Server(bot))

class Server(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	# TODO: add commands
	
	@commands.group(aliases = ["guild"], invoke_without_command = True)
	@checks.not_forbidden()
	async def server(self, ctx):
		'''Server'''
		await ctx.send_help(ctx.command)
	
	@server.command()
	@commands.guild_only()
	@checks.not_forbidden()
	async def icon(self, ctx):
		'''See a bigger version of the server icon'''
		if not ctx.guild.icon:
			await ctx.embed_reply(":no_entry: This server doesn't have an icon")
		else:
			await ctx.embed_reply("This server's icon:", image_url = ctx.guild.icon_url)
	
	@server.command()
	@commands.guild_only()
	@checks.not_forbidden()
	async def id(self, ctx):
		'''The server's ID'''
		await ctx.embed_reply(ctx.guild.id)
	
	@server.command()
	@commands.guild_only()
	@checks.not_forbidden()
	async def name(self, ctx):
		'''The server's name'''
		await ctx.embed_reply(ctx.guild.name)
	
	@server.command()
	@commands.guild_only()
	@checks.not_forbidden()
	async def owner(self, ctx):
		'''The owner of the server'''
		await ctx.embed_reply("The owner of this server is {}".format(ctx.guild.owner.mention), footer_text = str(ctx.guild.owner), footer_icon_url = ctx.guild.owner.avatar_url)
	
	@server.command()
	@commands.guild_only()
	@checks.not_forbidden()
	async def region(self, ctx):
		'''The server region'''
		await ctx.embed_reply(ctx.guild.region)
	
	@server.group(aliases = ["setting"], invoke_without_command = True)
	@commands.guild_only()
	@checks.is_permitted()
	async def settings(self, ctx, setting : str, on_off : bool):
		'''WIP'''
		await ctx.bot.set_guild_setting(ctx.guild.id, setting, on_off)
		# TODO: Check valid setting
		# await ctx.embed_reply("Setting not found")
		await ctx.embed_reply(f"{setting} set to {on_off}")
	
	@settings.group(name = "logs", aliases = ["log"])
	@commands.guild_only()
	@checks.is_permitted()
	async def settings_logs(self, ctx):
		'''WIP'''
		...
	
	@settings_logs.command(name = "channel")
	@commands.guild_only()
	@checks.is_permitted()
	async def settings_logs_channel(self, ctx):
		'''WIP'''
		...
	
	@settings_logs.command(name = "typing", aliases = ["type"])
	@commands.guild_only()
	@checks.is_permitted()
	async def settings_logs_typing(self, ctx):
		'''WIP'''
		...
	
	@settings_logs.group(name = "message", aliases = ["messages"])
	@commands.guild_only()
	@checks.is_permitted()
	async def settings_logs_message(self, ctx):
		'''WIP'''
		...
	
	@settings_logs_message.command(name = "send")
	@commands.guild_only()
	@checks.is_permitted()
	async def settings_logs_message_send(self, ctx):
		'''WIP'''
		...
	
	@settings_logs_message.command(name = "delete")
	@commands.guild_only()
	@checks.is_permitted()
	async def settings_logs_message_delete(self, ctx):
		'''WIP'''
		...
	
	@settings_logs_message.command(name = "edit")
	@commands.guild_only()
	@checks.is_permitted()
	async def settings_logs_message_edit(self, ctx):
		'''WIP'''
		...
	
	@settings_logs.group(name = "reaction", aliases = ["reactions"])
	@commands.guild_only()
	@checks.is_permitted()
	async def settings_logs_reaction(self, ctx):
		'''WIP'''
		...
	
	@settings_logs_reaction.command(name = "add")
	@commands.guild_only()
	@checks.is_permitted()
	async def settings_logs_reaction_add(self, ctx):
		'''WIP'''
		...
	
	@settings_logs_reaction.command(name = "remove")
	@commands.guild_only()
	@checks.is_permitted()
	async def settings_logs_reaction_remove(self, ctx):
		'''WIP'''
		...

