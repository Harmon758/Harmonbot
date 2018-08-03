
import discord
from discord.ext import commands

import textwrap
import unicodedata
import urllib

import dateutil
import isodate
# import unicodedata2 as unicodedata

import clients
import credentials
from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Info(bot))

class Info:
	
	def __init__(self, bot):
		self.bot = bot
		# Add info subcommands as subcommands of corresponding commands
		self.info_subcommands = ((self.role, "Role.role"), (self.server, "Server.server"), (self.user, "Discord.user"))
		for command, parent_name in self.info_subcommands:
			utilities.add_as_subcommand(self, command, parent_name, "info", aliases = ["information"])
	
	def __unload(self):
		for command, parent_name in self.info_subcommands:
			utilities.remove_as_subcommand(self, parent_name, "info")
	
	@commands.group(aliases = ["information"], invoke_without_command = True)
	@checks.not_forbidden()
	async def info(self, ctx):
		'''Info'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	# TODO: Add about command
	# TODO: Add soundcloud info
	# TODO: Add member info
	
	@info.command(aliases = ["char"])
	@checks.not_forbidden()
	async def character(self, ctx, character : str):
		'''Information about unicode characters'''
		character = character[0]
		# TODO: Return info on each character in the input string; use paste tool api?
		try:
			name = unicodedata.name(character)
		except ValueError:
			name = "UNKNOWN"
		hex_char = hex(ord(character))
		url = "http://www.fileformat.info/info/unicode/char/{}/index.htm".format(hex_char[2:])
		await ctx.embed_reply("`{} ({})`".format(character, hex_char), title = name, title_url = url)
	
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
		server = ctx.guild
		embed = discord.Embed(title = server.name, url = server.icon_url, timestamp = server.created_at, color = ctx.bot.bot_color)
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
		embed.set_thumbnail(url = server.icon_url)
		embed.add_field(name = "Owner", value = server.owner.mention)
		embed.add_field(name = "ID", value = server.id)
		embed.add_field(name = "Region", value = str(server.region))
		embed.add_field(name = "Roles", value = len(server.roles))
		text_count = sum(isinstance(channel, discord.TextChannel) for channel in server.channels)
		voice_count = sum(isinstance(channel, discord.VoiceChannel) for channel in server.channels)
		embed.add_field(name = "Channels", value = "{} text\n{} voice".format(text_count, voice_count))
		embed.add_field(name = "Members", value = "{}\n({} bots)".format(server.member_count, sum(m.bot for m in server.members)))
		embed.add_field(name = "AFK Timeout", value = "{:g} min.".format(server.afk_timeout / 60))
		embed.add_field(name = "AFK Channel", value = str(server.afk_channel))
		embed.add_field(name = "Verification Level", value = str(server.verification_level).capitalize())
		embed.add_field(name = "2FA Requirement", value = bool(server.mfa_level))
		embed.add_field(name = "Explicit Content Filter", value = server.explicit_content_filter)
		# TODO: Add system channel
		emojis = {"standard": [], "animated": [], "managed": []}
		for emoji in server.emojis:
			if emoji.managed:
				emojis["managed"].append(str(emoji))
			elif emoji.animated:
				emojis["animated"].append(str(emoji))
			else:
				emojis["standard"].append(str(emoji))
		for emoji_type in ("standard", "animated", "managed"):
			specific_emojis = emojis[emoji_type]
			if specific_emojis:
				specific_emojis = textwrap.wrap(' '.join(specific_emojis), width = ctx.bot.EFVCL)
				# EFVCL = Embed Field Value Character Limit
				embed.add_field(name = f"{emoji_type.replace('standard', '').capitalize()} Emojis", 
								value = specific_emojis[0], inline = False)
				for emoji in specific_emojis[1:]:
					embed.add_field(name = ctx.bot.ZERO_WIDTH_SPACE, value = emoji, inline = False)
		embed.set_footer(text = "Created")
		await ctx.send(embed = embed)
	
	@info.command()
	@checks.not_forbidden()
	async def spotify(self, ctx, url : str):
		'''Information about a Spotify track'''
		path = urllib.parse.urlparse(url).path
		if path[:7] != "/track/":
			await ctx.embed_reply(":no_entry: Syntax error")
			return
		spotify_access_token = await self.bot.cogs["Audio"].get_spotify_access_token()
		async with clients.aiohttp_session.get("https://api.spotify.com/v1/tracks/" + path[7:], headers = {"Authorization": "Bearer {}".format(spotify_access_token)}) as resp:
			data = await resp.json()
		# tracknumber = str(data["track_number"])
		# TODO: handle track not found
		description = "Artist: [{}]({})\n".format(data["artists"][0]["name"], data["artists"][0]["external_urls"]["spotify"])
		description += "Album: [{}]({})\n".format(data["album"]["name"], data["album"]["external_urls"]["spotify"])
		description += "Duration: {}\n".format(utilities.secs_to_colon_format(data["duration_ms"] / 1000))
		# TODO: handle no preview
		description += "[Preview]({})".format(data["preview_url"])
		await ctx.embed_reply(description, title = data["name"], title_url = url, thumbnail_url = data["album"]["images"][0]["url"])
		# TODO: keep spotify embed?
	
	@info.command(aliases = ["member"])
	@checks.not_forbidden()
	async def user(self, ctx, *, user : discord.Member = None):
		'''Information about a user'''
		if not user: user = ctx.author
		await ctx.embed_reply(title = str(user), title_url = user.avatar_url, thumbnail_url = user.avatar_url, footer_text = "Created", timestamp = user.created_at, fields = [("User", user.mention), ("ID", user.id), ("Bot", user.bot)])
		# member info, status, game, roles, color, etc.
	
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
		api_url = "https://www.googleapis.com/youtube/v3/videos?id={}&key={}&part=snippet,contentDetails,statistics".format(query['v'][0], credentials.google_apikey)
		async with clients.aiohttp_session.get(api_url) as resp:
			data = await resp.json()
		if not data:
			await ctx.embed_reply(":no_entry: Error")
			return
		data = data["items"][0]
		# TODO: Handle no items
		info = "Length: {}".format(utilities.secs_to_letter_format(isodate.parse_duration(data["contentDetails"]["duration"]).total_seconds()))
		if "likeCount" in data["statistics"]:
			likes, dislikes = int(data["statistics"]["likeCount"]), int(data["statistics"]["dislikeCount"])
			info += "\nLikes: {:,}, Dislikes: {:,}".format(likes, dislikes)
			if likes + dislikes != 0: info += " ({:.2f}%)".format(likes / (likes + dislikes) * 100)
		info += "\nViews: {:,}".format(int(data["statistics"]["viewCount"]))
		if "commentCount" in data["statistics"]: info += ", Comments: {:,}".format(int(data["statistics"]["commentCount"]))
		info += "\nChannel: [{0[channelTitle]}](https://www.youtube.com/channel/{0[channelId]})".format(data["snippet"])
		# data["snippet"]["description"]
		await ctx.embed_reply(info, title = data["snippet"]["title"], title_url = url, thumbnail_url = data["snippet"]["thumbnails"]["high"]["url"], footer_text = "Published on", timestamp = dateutil.parser.parse(data["snippet"]["publishedAt"]).replace(tzinfo = None))
		# TODO: Handle invalid url

