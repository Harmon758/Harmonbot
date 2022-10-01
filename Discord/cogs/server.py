
from discord.ext import commands

from utilities import checks

async def setup(bot):
	await bot.add_cog(Server(bot))

class Server(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	async def cog_check(self, ctx):
		guild_only = await commands.guild_only().predicate(ctx)
		not_forbidden = await checks.not_forbidden().predicate(ctx)
		return guild_only and not_forbidden
	
	# TODO: Add subcommands:
	#         for info in info command: emojis, afk timeout, afk channel, mfa level, verification level, 
	#                                   explicit content filter, default notifications, premium tier, 
	#                                   premium subscription count, emoji limit, bitrate limit, filesize limit, 
	#                                   member count, created at, system channel, system channel flags, 
	#                                   features: vanity url, invite splash, banner
	#         features: vip, verified, partnered, more emoji?, discoverable, commerce, lurkable, news, animated icon
	#                   (add verified, partner to info command, via emoji?, also emoji for owner, boost?)
	#                   (add discoverable, commerce, lurkable, news to info command?)
	#         audit logs (disabled by default) (integration with?), bans (disabled by default), create custom emoji, 
	#         estimate pruned members, invites (disabled by default), kick, leave?, prune?, unban, webhooks?, widget?, 
	#         channels?, channels voice?, channels text?, channels category?, members?, roles?, large?, premium subscribers?
	#         max_presences?, max_members?, description? (also add to info command?)
	#       Integrate with channel + role cogs?
	#       Add option to set/edit: icon, name, region
	# TODO: Server settings
	
	@commands.hybrid_group(aliases = ["guild"], case_insensitive = True)
	async def server(self, ctx):
		"""Server"""
		await ctx.send_help(ctx.command)
	
	@server.command(with_app_command = False)
	async def icon(self, ctx):
		'''See a bigger version of the server icon'''
		if not ctx.guild.icon:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} This server doesn't have an icon")
		else:
			await ctx.embed_reply("This server's icon:", image_url = ctx.guild.icon.url)
	
	@server.command()
	async def id(self, ctx):
		"""Show the ID of the server"""
		await ctx.embed_reply(ctx.guild.id)
	
	@server.command(aliases = ["info"], with_app_command = False)
	async def information(self, ctx):
		"""Information about the server"""
		if command := ctx.bot.get_command("information server"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"information server command not found "
				"when server information command invoked"
			)
	
	@server.command(with_app_command = False)
	async def name(self, ctx):
		'''The server's name'''
		await ctx.embed_reply(ctx.guild.name)
	
	@server.command(with_app_command = False)
	async def owner(self, ctx):
		'''The owner of the server'''
		if not (guild_owner := ctx.guild.owner):
			guild_owner = await ctx.guild.fetch_member(ctx.guild.owner_id)
		await ctx.embed_reply(
			f"The owner of this server is {guild_owner.mention}",
			footer_text = str(guild_owner),
			footer_icon_url = guild_owner.display_avatar.url
		)
	
	@server.command(hidden = True, with_app_command = False)
	async def region(self, ctx):
		"""
		This command is deprecated, as server regions have been deprecated by Discord
		https://github.com/discord/discord-api-docs/pull/3001
		"""
		await ctx.send_help(ctx.command)
	
	@server.group(aliases = ["setting"], case_insensitive = True, with_app_command = False)
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settings(self, ctx, setting : str, on_off : bool):
		'''WIP'''
		await ctx.bot.set_guild_setting(ctx.guild.id, setting, on_off)
		# TODO: Check valid setting
		# await ctx.embed_reply("Setting not found")
		await ctx.embed_reply(f"{setting} set to {on_off}")
	
	@settings.command(
		name = "logs", aliases = ["log"], with_app_command = False
	)
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settings_logs(self, ctx):
		'''WIP'''
		# TODO:
		# Choose channel
		# Ability to log: typing?, message send?, message edit, message delete,
		# reaction add?, reaction remove?

