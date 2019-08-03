
import discord
from discord.ext import commands

import sys
import textwrap
# import unicodedata
import urllib

import dateutil
import isodate
import unicodedata2 as unicodedata

from modules import utilities
from utilities import checks

sys.path.insert(0, "..")
from units.time import duration_to_string
sys.path.pop(0)

def setup(bot):
	bot.add_cog(Info(bot))

class Info(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		# Add info subcommands as subcommands of corresponding commands
		self.info_subcommands = ((self.role, "Role.role"), (self.server, "Server.server"), (self.user, "Discord.user"))
		for command, parent_name in self.info_subcommands:
			utilities.add_as_subcommand(self, command, parent_name, "info", aliases = ["information"])
	
	def cog_unload(self):
		for command, parent_name in self.info_subcommands:
			utilities.remove_as_subcommand(self, parent_name, "info")
	
	@commands.group(aliases = ["information"], invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def info(self, ctx):
		'''Info'''
		await ctx.send_help(ctx.command)
	
	# TODO: Add about command
	# TODO: Add soundcloud info
	# TODO: Add member info
	
	@info.command(aliases = ["char"])
	@checks.not_forbidden()
	async def character(self, ctx, character: str):
		'''Information about unicode characters'''
		output = []
		for char in character:
			output.append({"char": char})
			try:
				output[-1]["name"] = unicodedata.name(char)
			except ValueError:
				output[-1]["name"] = "UNKNOWN"
			output[-1]["hex"] = hex(ord(char))
			output[-1]["url"] = f"http://www.fileformat.info/info/unicode/char/{output[-1]['hex'][2:]}/index.htm"
		if len(output) == 1:
			await ctx.embed_reply(f"`{output[0]['char']}` ({output[0]['hex']})", 
									title = output[0]["name"], title_url = output[0]["url"])
		else:
			output = '\n'.join(f"[{char['name']}]({char['url']}): `{char['char']}` ({char['hex']})" 
								for char in output)
			if len(output) > ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
				output = output[:ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT]
				output = output[:output.rfind('\n')]
			await ctx.embed_reply(output)
	
	@info.command()
	@commands.guild_only()
	@checks.not_forbidden()
	async def role(self, ctx, *, role : discord.Role):
		'''Information about a role'''
		embed = discord.Embed(description = role.mention, title = role.name, timestamp = role.created_at, color = ctx.bot.bot_color)
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
		embed.add_field(name = "ID", value = role.id)
		embed.add_field(name = "Members", value = len(role.members))
		embed.add_field(name = "Color", value = role.color)
		embed.add_field(name = "Mentionable", value = role.mentionable)
		embed.add_field(name = "Displayed Separately", value = role.hoist)
		embed.add_field(name = "Default", value = role.is_default())
		embed.add_field(name = "Managed", value = role.managed)
		embed.add_field(name = "Position", value = role.position)
		embed.set_footer(text = "Created")
		await ctx.send(embed = embed)
	
	@info.command(aliases = ["guild"])
	@commands.guild_only()
	@checks.not_forbidden()
	async def server(self, ctx):
		'''Information about the server'''
		region = str(ctx.guild.region).replace('-', ' ').title()
		region = region.replace("Vip", "VIP").replace("Us", "US").replace("Eu", "EU")
		text_count = sum(isinstance(channel, discord.TextChannel) for channel in ctx.guild.channels)
		voice_count = sum(channel.type is discord.ChannelType.voice for channel in ctx.guild.channels)
		bot_count = sum(m.bot for m in ctx.guild.members)
		if ctx.guild.system_channel:  # Use := in Python 3.8
			system_messages = ctx.guild.system_channel.mention
			if ctx.guild.system_channel_flags.join_notifications:
				system_messages += "\nRandom welcome messages"
			if ctx.guild.system_channel_flags.premium_subscriptions:
				system_messages += "\nBoosts"
		else:
			system_messages = ctx.guild.system_channel
		fields = [("Owner", ctx.guild.owner.mention), ("ID", ctx.guild.id), 
					("Channels", f"{text_count} text\n{voice_count} voice"), 
					("Members", f"{ctx.guild.member_count}\n({bot_count} bots)"), 
					("Roles", len(ctx.guild.roles)), ("Region", region), 
					("AFK Channel", getattr(ctx.guild.afk_channel, "mention", ctx.guild.afk_channel)), 
					("AFK Timeout", f"{ctx.guild.afk_timeout / 60:g} min."), 
					("System Messages", system_messages), 
					# ZWS = Zero Width Space
					("Default Notification Settings", ctx.guild.default_notifications.name.replace('_', ' ').title().replace("Mentions", f"@{ctx.bot.ZWS}mentions")), 
					("Verification Level", str(ctx.guild.verification_level).capitalize()), 
					("Explicit Content Filter", str(ctx.guild.explicit_content_filter).replace('_', ' ').title()), 
					("2FA Requirement", bool(ctx.guild.mfa_level)), 
					("Boost Status", f"Level {ctx.guild.premium_tier}\n"
										f"{ctx.guild.premium_subscription_count} {ctx.bot.inflect_engine.plural('Boost', ctx.guild.premium_subscription_count)}"), 
					("Limits", f"Emoji: {ctx.guild.emoji_limit}\n"
								f"Bitrate: {ctx.guild.bitrate_limit // 1000:g} kbps\n"
								f"Filesize: {ctx.guild.filesize_limit // 1024 ** 2} MB")]
		if "VANITY_URL" in ctx.guild.features:
			try:
				invite = await ctx.guild.vanity_invite()
				fields.append(("Vanity Invite URL", invite))
			except discord.Forbidden:
				pass
		if "INVITE_SPLASH" in ctx.guild.features:
			fields.append(("Invite Splash", f"[URL]({ctx.guild.splash_url})"))
		if "BANNER" in ctx.guild.features:
			fields.append(("Banner", f"[URL]({ctx.guild.banner_url})"))
		emojis = {"standard": [], "animated": [], "managed": [], "unavailable": []}
		for emoji in ctx.guild.emojis:
			if not emoji.available:
				emojis["unavailable"].append(str(emoji))
			elif emoji.managed:
				emojis["managed"].append(str(emoji))
			elif emoji.animated:
				emojis["animated"].append(str(emoji))
			else:
				emojis["standard"].append(str(emoji))
		for emoji_type in ("standard", "animated", "managed", "unavailable"):
			specific_emojis = emojis[emoji_type]
			if specific_emojis:
				specific_emojis = textwrap.wrap(' '.join(specific_emojis), width = ctx.bot.EFVCL)
				# EFVCL = Embed Field Value Character Limit
				fields.append((f"{emoji_type.replace('standard', '').capitalize()} Emojis", specific_emojis[0]))
				for emoji in specific_emojis[1:]:
					fields.append((ctx.bot.ZERO_WIDTH_SPACE, emoji))
		await ctx.embed_reply(title = ctx.guild.name, title_url = str(ctx.guild.icon_url), 
								thumbnail_url = ctx.guild.icon_url, fields = fields, 
								footer_text = "Created", timestamp = ctx.guild.created_at)
	
	@info.command()
	@checks.not_forbidden()
	async def spotify(self, ctx, url : str):
		'''Information about a Spotify track'''
		path = urllib.parse.urlparse(url).path
		if path[:7] != "/track/":
			await ctx.embed_reply(":no_entry: Syntax error")
			return
		spotify_access_token = await self.bot.cogs["Audio"].get_spotify_access_token()
		url = "https://api.spotify.com/v1/tracks/" + path[7:]
		headers = {"Authorization": f"Bearer {spotify_access_token}"}
		async with ctx.bot.aiohttp_session.get(url, headers = headers) as resp:
			data = await resp.json()
		# tracknumber = str(data["track_number"])
		# TODO: handle track not found
		description = f"Artist: [{data['artists'][0]['name']}]({data['artists'][0]['external_urls']['spotify']})\n"
		description += f"Album: [{data['album']['name']}]({data['album']['external_urls']['spotify']})\n"
		description += f"Duration: {utilities.secs_to_colon_format(data['duration_ms'] / 1000)}\n"
		# TODO: handle no preview
		description += f"[Preview]({data['preview_url']})"
		await ctx.embed_reply(description, title = data["name"], title_url = url, 
								thumbnail_url = data["album"]["images"][0]["url"])
		# TODO: keep spotify embed?
	
	@info.command(aliases = ["member"])
	@checks.not_forbidden()
	async def user(self, ctx, *, user : discord.Member = None):
		'''Information about a user'''
		if not user:
			user = ctx.author
		fields = [("User", user.mention), ("ID", user.id), 
					("Status", user.status.name.capitalize().replace('Dnd', 'Do Not Disturb'))]
		for status_type in ("desktop_status", "web_status", "mobile_status"):
			status = getattr(user, status_type)
			if status is not discord.Status.offline:
				fields.append((status_type.replace('_', ' ').title(), 
								status.name.capitalize().replace('Dnd', 'Do Not Disturb')))
		activities = '\n'.join(f"{activity.type.name.capitalize()} {activity.name}" for activity in user.activities)
		if activities:
			fields.append((ctx.bot.inflect_engine.plural("activity", len(user.activities)).capitalize(), 
							activities.replace("Listening", "Listening to")))
			# inflect_engine.plural("Activity") returns "Activitys"
		fields.append(("Bot", user.bot))
		await ctx.embed_reply(title = str(user), title_url = str(user.avatar_url), 
								thumbnail_url = user.avatar_url, fields = fields, 
								footer_text = "Created", timestamp = user.created_at)
		# member info, roles, color, joined at, boosting since, etc.
		# TODO: more detailed activities
	
	@info.command(aliases = ["yt"])
	@checks.not_forbidden()
	async def youtube(self, ctx, url : str):
		'''Information about YouTube videos'''
		# TODO: Automatic on YouTube links, server specific toggleable option
		# TODO: Handle playlists
		url_data = urllib.parse.urlparse(url)
		query = urllib.parse.parse_qs(url_data.query)
		if 'v' not in query:
			await ctx.embed_reply(":no_entry: Invalid input")
			return
		api_url = "https://www.googleapis.com/youtube/v3/videos"
		params = {"id": query['v'][0], "key": ctx.bot.GOOGLE_API_KEY,
					"part": "snippet,contentDetails,statistics"}
		async with ctx.bot.aiohttp_session.get(api_url, params = params) as resp:
			data = await resp.json()
		if not data:
			await ctx.embed_reply(":no_entry: Error")
			return
		data = data["items"][0]
		# TODO: Handle no items
		duration = isodate.parse_duration(data["contentDetails"]["duration"])
		info = f"Length: {duration_to_string(duration, abbreviate = True)}"
		if "likeCount" in data["statistics"]:
			likes = int(data["statistics"]["likeCount"])
			dislikes = int(data["statistics"]["dislikeCount"])
			info += f"\nLikes: {likes:,}, Dislikes: {dislikes:,}"
			if likes + dislikes != 0:
				info += f" ({likes / (likes + dislikes) * 100:.2f}%)"
		if "viewCount" in data["statistics"]:
			info += f"\nViews: {int(data['statistics']['viewCount']):,}"
		if "commentCount" in data["statistics"]:
			info += f", Comments: {int(data['statistics']['commentCount']):,}"
		info += f"\nChannel: [{data['snippet']['channelTitle']}]"
		info += f"(https://www.youtube.com/channel/{data['snippet']['channelId']})"
		# data["snippet"]["description"]
		timestamp = dateutil.parser.parse(data["snippet"]["publishedAt"]).replace(tzinfo = None)
		await ctx.embed_reply(info, title = data["snippet"]["title"], title_url = url, 
								thumbnail_url = data["snippet"]["thumbnails"]["high"]["url"], 
								footer_text = "Published", timestamp = timestamp)
		# TODO: Handle invalid url

