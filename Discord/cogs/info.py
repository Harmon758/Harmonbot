
import discord
from discord import app_commands
from discord.ext import commands

import contextlib
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

BADGE_EMOJI_IDS = {
	discord.PublicUserFlags.staff: 773894866656034816, 
	discord.PublicUserFlags.partner: 773895031882121218, 
	discord.PublicUserFlags.hypesquad: 773895189311914064, 
	discord.PublicUserFlags.bug_hunter: 773895334123798528, 
	discord.PublicUserFlags.hypesquad_bravery: 773895517478322187, 
	discord.PublicUserFlags.hypesquad_brilliance: 773895531281252353, 
	discord.PublicUserFlags.hypesquad_balance: 773895543494672415, 
	discord.PublicUserFlags.early_supporter: 773895694552662046, 
	discord.PublicUserFlags.bug_hunter_level_2: 773895708839116840, 
	discord.PublicUserFlags.early_verified_bot_developer: 773895804015869953
}

async def setup(bot):
	await bot.add_cog(Info(bot))

class Info(commands.GroupCog, group_name = "information"):
	"""Information"""
	
	def __init__(self, bot):
		self.bot = bot
		super().__init__()
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(aliases = ["info"], invoke_without_command = True, case_insensitive = True)
	async def information(self, ctx):
		'''Information'''
		if cog := self.bot.get_cog("Meta"):
			await ctx.invoke(cog.about)
		else:
			await ctx.send_help(ctx.command)
	
	# TODO: Add about command
	# TODO: Add soundcloud info
	# TODO: Add member info
	
	@information.command(aliases = ["char"])
	async def character(self, ctx, character: str):
		'''Information about a Unicode character'''
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
	
	@information.command()
	@commands.guild_only()
	async def role(self, ctx, *, role: discord.Role):
		"""Information about a role"""
		# Note: role information command invokes this command
		await ctx.embed_reply(
			title = role.name,
			description = role.mention,
			fields = (
				("ID", role.id), ("Members", len(role.members)),
				("Color", role.color), ("Mentionable", role.mentionable),
				("Displayed Separately", role.hoist),
				("Default", role.is_default()), ("Managed", role.managed),
				("Position", role.position)
			),
			footer_text = "Created", timestamp = role.created_at
		)
	
	@information.command(aliases = ["guild"])
	@commands.guild_only()
	async def server(self, ctx):
		'''Information about the server'''
		# Note: server information command invokes this command
		text_count = sum(isinstance(channel, discord.TextChannel) for channel in ctx.guild.channels)
		voice_count = sum(channel.type is discord.ChannelType.voice for channel in ctx.guild.channels)
		bot_count = sum(m.bot for m in ctx.guild.members)
		if system_messages := ctx.guild.system_channel:
			system_messages = system_messages.mention
			if ctx.guild.system_channel_flags.join_notifications:
				system_messages += "\nRandom welcome messages"
			if ctx.guild.system_channel_flags.premium_subscriptions:
				system_messages += "\nBoosts"
		if not (guild_owner := ctx.guild.owner):
			guild_owner = await ctx.guild.fetch_member(ctx.guild.owner_id)
		fields = [("Owner", guild_owner.mention), ("ID", ctx.guild.id), 
					("Channels", f"{text_count} text\n{voice_count} voice"), 
					("Members", f"{ctx.guild.member_count}\n({bot_count} bots)"), 
					("Roles", len(ctx.guild.roles)), 
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
			with contextlib.suppress(discord.Forbidden):
				invite = await ctx.guild.vanity_invite()
				fields.append(("Vanity Invite URL", invite))
		if "INVITE_SPLASH" in ctx.guild.features and ctx.guild.splash:
			fields.append(("Invite Splash", f"[URL]({ctx.guild.splash.url})"))
		if "BANNER" in ctx.guild.features:
			fields.append(("Banner", f"[URL]({ctx.guild.banner.url})"))
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
		await ctx.embed_reply(title = ctx.guild.name, title_url = str(ctx.guild.icon.url), 
								thumbnail_url = ctx.guild.icon.url, fields = fields, 
								footer_text = "Created", timestamp = ctx.guild.created_at)
	
	@information.command()
	async def spotify(self, ctx, url: str):
		'''Information about a Spotify track'''
		path = urllib.parse.urlparse(url).path
		if path[:7] != "/track/":
			return await ctx.embed_reply(":no_entry: Syntax error")
		spotify_access_token = await self.bot.cogs["Audio"].get_spotify_access_token()
		url = "https://api.spotify.com/v1/tracks/" + path[7:]
		headers = {"Authorization": f"Bearer {spotify_access_token}"}
		async with ctx.bot.aiohttp_session.get(url, headers = headers) as resp:
			data = await resp.json()
		# tracknumber = str(data["track_number"])
		# TODO: handle track not found
		description = (f"Artist: [{data['artists'][0]['name']}]({data['artists'][0]['external_urls']['spotify']})\n"
						f"Album: [{data['album']['name']}]({data['album']['external_urls']['spotify']})\n"
						f"Duration: {utilities.secs_to_colon_format(data['duration_ms'] / 1000)}")
		if preview_url := data["preview_url"]:
			description += f"\n[Preview]({preview_url})"
		await ctx.embed_reply(description, title = data["name"], title_url = url, 
								thumbnail_url = data["album"]["images"][0]["url"])
		# TODO: keep spotify embed?
	
	@information.command(aliases = ["member"])
	async def user(self, ctx, *, user: discord.Member = commands.Author):
		'''Information about a user'''
		# Note: user information command invokes this command
		title = str(user)
		if user.public_flags.verified_bot:
			title += " [Verified Bot]"
		elif user.bot:
			title += " [Bot]"
		
		description = "".join(
			str(badge_emoji) for flag_name, flag_value in user.public_flags
			if flag_value and (
				badge_emoji := ctx.bot.get_emoji(
					BADGE_EMOJI_IDS.get(
						getattr(discord.PublicUserFlags, flag_name), None
					)
				)
			)
		)
		
		statuses = user.status.name.capitalize().replace("Dnd", "Do Not Disturb")
		for status_type in ("desktop", "web", "mobile"):
			if (status := getattr(user, f"{status_type}_status")) is not discord.Status.offline:
				statuses += f"\n{status_type.capitalize()}: {status.name.capitalize().replace('Dnd', 'Do Not Disturb')}"
		fields = [
			("User", user.mention), ("ID", user.id), ("Status", statuses),
			(
				ctx.bot.inflect_engine.plural("activity", len(user.activities)).capitalize(), 
				# inflect_engine.plural("Activity") returns "Activitys"
				'\n'.join(
					f"{activity.type.name.capitalize().replace('Listening', 'Listening to').replace('Custom', 'Custom status:')} "
					+ (activity.name if isinstance(activity, discord.Activity) else str(activity))
					for activity in user.activities
				) or None
			), 
			(
				"Color",
				f"#{user.color.value:0>6X}\n{user.color.to_rgb()}"
				if user.color.value else None
			),
			(
				"Roles",
				", ".join(role.mention for role in user.roles[1:]) or None
			),
			(
				"Joined",
				f"{discord.utils.format_dt(user.joined_at)} ({user.joined_at.isoformat(timespec = 'milliseconds')})"
			)
		]
		if user.premium_since:
			fields.append((
				"Boosting Since",
				f"{discord.utils.format_dt(user.premium_since)} ({user.premium_since.isoformat(timespec = 'milliseconds')})"
			))
		
		fetched_user = await ctx.bot.fetch_user(user.id)
		
		await ctx.embed_reply(
			title = title, title_url = user.display_avatar.url,
			thumbnail_url = user.display_avatar.url,
			description = description,
			fields = fields,
			image_url = fetched_user.banner.url if fetched_user.banner else None,
			footer_text = "Created", timestamp = user.created_at,
			color = fetched_user.accent_color
		)
		
		# TODO: Add voice state?
		# TODO: Accept User input?
		# TODO: More detailed activities?
		# TODO: Guild permissions?, separate command?
	
	@information.command(aliases = ["yt"])
	async def youtube(self, ctx, url: str):
		"""Information about a YouTube video"""
		# TODO: Automatic on YouTube links, server specific toggleable option
		# TODO: Handle playlists
		url_data = urllib.parse.urlparse(url)
		query = urllib.parse.parse_qs(url_data.query)
		if 'v' not in query:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Invalid input")
			return
		
		async with ctx.bot.aiohttp_session.get(
			"https://www.googleapis.com/youtube/v3/videos",
			params = {
				"id": query['v'][0],
				"part": "snippet,contentDetails,statistics",
				"key": ctx.bot.GOOGLE_API_KEY
			}
		) as resp:
			data = await resp.json()
		
		if not data or not data["items"]:
			await ctx.embed_reply(
				f"{ctx.bot.error_emoji} Error: Unable to retrieve video information"
			)
			return
		
		data = data["items"][0]
		snippet = data["snippet"]
		statistics = data["statistics"]
		
		fields = []
		if length := duration_to_string(
			isodate.parse_duration(data["contentDetails"]["duration"]),
			abbreviate = True
		):
			fields.append(("Length", length))
		if (like_count := statistics.get("likeCount")) is not None:
			fields.append(("Likes", f"{int(like_count):,}"))
		if (view_count := statistics.get("viewCount")) is not None:
			fields.append(("Views", f"{int(view_count):,}"))
		if (comment_count := statistics.get("commentCount")) is not None:
			fields.append(("Comments", f"{int(comment_count):,}"))
		fields.append(
			(
				"Channel",
				f"[{snippet['channelTitle']}]"
				f"(https://www.youtube.com/channel/{snippet['channelId']})"
			)
		)
		# TODO: Use snippet["description"]
		await ctx.embed_reply(
			title = snippet["title"],
			title_url = url,
			thumbnail_url = snippet["thumbnails"]["high"]["url"],
			fields = fields,
			footer_text = "Published",
			timestamp = dateutil.parser.parse(snippet["publishedAt"])
		)
		# TODO: Handle invalid url
	
	@app_commands.command(name = "youtube")
	async def slash_youtube(self, interaction, link: str):
		"""
		Information about a YouTube video
		
		Parameters
		----------
		link
			YouTube video URL
		"""
		ctx = await interaction.client.get_context(interaction)
		await self.youtube(ctx, url = link)

