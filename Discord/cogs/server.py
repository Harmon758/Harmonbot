
import discord
from discord.ext import commands

from utilities import checks

def setup(bot):
	bot.add_cog(Server(bot))

class Server(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
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
	
	@commands.group(aliases = ["guild"], invoke_without_command = True, case_insensitive = True)
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
			await ctx.embed_reply(f"{ctx.bot.error_emoji} This server doesn't have an icon")
		else:
			await ctx.embed_reply("This server's icon:", image_url = ctx.guild.icon.url)
	
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
		if not (guild_owner := ctx.guild.owner):
			guild_owner = await ctx.guild.fetch_member(ctx.guild.owner_id)
		await ctx.embed_reply(f"The owner of this server is {guild_owner.mention}", 
								footer_text = str(guild_owner), footer_icon_url = guild_owner.display_avatar.url)
	
	@server.command()
	@commands.guild_only()
	@checks.not_forbidden()
	async def region(self, ctx):
		'''The server region'''
		await ctx.embed_reply(str(ctx.guild.region).replace('-', ' ').title().replace("Vip", "VIP").replace("Us", "US").replace("Eu", "EU"))
	
	@server.group(aliases = ["setting"], invoke_without_command = True, case_insensitive = True)
	@commands.guild_only()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settings(self, ctx, setting : str, on_off : bool):
		'''WIP'''
		await ctx.bot.set_guild_setting(ctx.guild.id, setting, on_off)
		# TODO: Check valid setting
		# await ctx.embed_reply("Setting not found")
		await ctx.embed_reply(f"{setting} set to {on_off}")
	
	@settings.group(name = "logs", aliases = ["log"], case_insensitive = True)
	@commands.guild_only()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settings_logs(self, ctx):
		'''WIP'''
		...
	
	@settings_logs.command(name = "channel")
	@commands.guild_only()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settings_logs_channel(self, ctx):
		'''WIP'''
		...
	
	@settings_logs.command(name = "typing", aliases = ["type"])
	@commands.guild_only()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settings_logs_typing(self, ctx):
		'''WIP'''
		...
	
	@settings_logs.group(name = "message", aliases = ["messages"], case_insensitive = True)
	@commands.guild_only()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settings_logs_message(self, ctx):
		'''WIP'''
		...
	
	@settings_logs_message.command(name = "send")
	@commands.guild_only()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settings_logs_message_send(self, ctx):
		'''WIP'''
		...
	
	@settings_logs_message.command(name = "delete")
	@commands.guild_only()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settings_logs_message_delete(self, ctx):
		'''WIP'''
		...
	
	@settings_logs_message.command(name = "edit")
	@commands.guild_only()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settings_logs_message_edit(self, ctx):
		'''WIP'''
		...
	
	@settings_logs.group(name = "reaction", aliases = ["reactions"], case_insensitive = True)
	@commands.guild_only()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settings_logs_reaction(self, ctx):
		'''WIP'''
		...
	
	@settings_logs_reaction.command(name = "add")
	@commands.guild_only()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settings_logs_reaction_add(self, ctx):
		'''WIP'''
		...
	
	@settings_logs_reaction.command(name = "remove")
	@commands.guild_only()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settings_logs_reaction_remove(self, ctx):
		'''WIP'''
		...

