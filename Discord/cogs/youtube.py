
import discord
from discord.ext import commands, tasks

import asyncio
import datetime
import json
import logging
import sys
import traceback

import aiohttp
import dateutil.parser
import feedparser
import isodate

import clients
from utilities import checks

sys.path.insert(0, "..")
from units.time import duration_to_string
sys.path.pop(0)

errors_logger = logging.getLogger("errors")

def setup(bot):
	bot.add_cog(YouTube(bot))

class YouTube(commands.Cog):
	
	'''
	YouTube streams and uploads notification system
	See also documentation for youtube command
	Uploads system relevant documentation:
	https://developers.google.com/youtube/v3/guides/push_notifications
	https://pubsubhubbub.appspot.com/
	https://pubsubhubbub.github.io/PubSubHubbub/pubsubhubbub-core-0.4.html
	'''
	
	def __init__(self, bot):
		self.bot = bot
		self.uploads_processed = []
		# Add youtube (audio) streams and uploads subcommands and their corresponding subcommands
		streams_command = commands.Group(streams, aliases = ["stream"], 
											invoke_without_command = True, case_insensitive = True, 
											checks = [commands.check_any(checks.is_permitted(), checks.is_guild_owner()).predicate])
		streams_command.add_command(commands.Command(streams_add, name = "add", 
														checks = [commands.check_any(checks.is_permitted(), checks.is_guild_owner()).predicate]))
		streams_command.add_command(commands.Command(streams_remove, name = "remove", aliases = ["delete"], 
														checks = [commands.check_any(checks.is_permitted(), checks.is_guild_owner()).predicate]))
		streams_command.add_command(commands.Command(streams_channels, name = "channels", aliases = ["streams"], 
														checks = [checks.not_forbidden().predicate]))
		"""
		uploads_command = commands.Group(self.uploads, aliases = ["videos"], 
											invoke_without_command = True, case_insensitive = True, 
											checks = [commands.check_any(checks.is_permitted(), checks.is_guild_owner()).predicate])
		uploads_command.add_command(commands.Command(self.uploads_add, name = "add", aliases = ["subscribe"], 
														checks = [commands.check_any(checks.is_permitted(), checks.is_guild_owner()).predicate]))
		uploads_command.add_command(commands.Command(self.uploads_remove, name = "remove", aliases = ["delete", "unsubscribe"], 
														checks = [commands.check_any(checks.is_permitted(), checks.is_guild_owner()).predicate]))
		uploads_command.add_command(commands.Command(self.uploads_channels, name = "channels", aliases = ["uploads", "videos"], 
														checks = [checks.not_forbidden().predicate]))
		"""
		if (cog := self.bot.get_cog("Audio")) and (parent := getattr(cog, "audio")):
			parent.add_command(streams_command)
			# parent.add_command(uploads_command)
		else:
			command = commands.Group(youtube, aliases = ["yt"], 
										invoke_without_command = True, case_insensitive = True, 
										checks = [checks.not_forbidden().predicate])
			command.add_command(streams_command)
			# command.add_command(uploads_command)
			self.bot.add_command(command)
		
		self.streams_task = self.check_streams.start()
		self.streams_task.set_name("YouTube streams")
		
		clients.create_file("youtube_uploads", content = {})
		with open(self.bot.data_path + "/youtube_uploads.json", 'r') as uploads_file:
			self.uploads_info = json.load(uploads_file)
		self.uploads_following = set(channel_id for channels in self.uploads_info.values() for channel_id in channels)
	
	async def cog_load(self):
		self.renew_uploads_task = self.bot.loop.create_task(self.renew_upload_supscriptions(), name = "Renew YouTube upload subscriptions")
	
	def cog_unload(self):
		if (cog := self.bot.get_cog("Audio")) and (parent := getattr(cog, "audio")):
			parent.remove_command("streams")
			parent.remove_command("uploads")
		self.check_streams.cancel()
		self.renew_uploads_task.cancel()
	
	async def initialize_database(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS youtube")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS youtube.streams (
				discord_channel_id	BIGINT, 
				youtube_channel_id	TEXT, 
				PRIMARY KEY			(discord_channel_id, youtube_channel_id)
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS youtube.stream_announcements (
				video_id		TEXT, 
				channel_id		BIGINT, 
				message_id		BIGINT, 
				live			BOOL, 
				PRIMARY KEY		(video_id, channel_id)
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS youtube.stream_errors (
				timestamp	TIMESTAMPTZ PRIMARY KEY DEFAULT NOW(), 
				channel_id	TEXT, 
				type		TEXT, 
				message		TEXT
			)
			"""
		)
	
	# TODO: renew after hub.lease_seconds?
	async def renew_upload_supscriptions(self):
		for channel_id in self.uploads_following:
			url = "https://pubsubhubbub.appspot.com/"
			headers = {"content-type": "application/x-www-form-urlencoded"}
			data = {"hub.callback": self.bot.HTTP_SERVER_CALLBACK_URL, "hub.mode": "subscribe", 
					"hub.topic": "https://www.youtube.com/xml/feeds/videos.xml?channel_id=" + channel_id}
			async with self.bot.aiohttp_session.post(url, headers = headers, data = data) as resp:
				if resp.status not in (202, 204):
					error_description = await resp.text()
					self.bot.print(f"Google PubSubHubbub Error {resp.status} re-subscribing to {channel_id}: {error_description}")
			await asyncio.sleep(5)  # Google PubSubHubbub rate limit?
	
	# R/PT60S
	@tasks.loop(seconds = 60)
	async def check_streams(self):
		try:
			records = await self.bot.db.fetch("SELECT DISTINCT youtube_channel_id FROM youtube.streams")
			video_ids = []
			for record in records:
				channel_id = record["youtube_channel_id"]
				try:
					url = "https://www.googleapis.com/youtube/v3/search"
					params = {"part": "snippet", "eventType": "live", "type": "video", 
								"channelId": channel_id, "key": self.bot.GOOGLE_API_KEY}
					async with self.bot.aiohttp_session.get(url, params = params) as resp:
						if resp.status == 502:
							await self.bot.db.execute(
								"""
								INSERT INTO youtube.stream_errors (channel_id, type, message)
								VALUES ($1, $2, $3)
								""", 
								channel_id, str(resp.status), resp.reason
							)
							await asyncio.sleep(10)
							continue
						stream_data = await resp.json()
					# Multiple streams from one channel possible
					for item in stream_data.get("items", []):
						video_id = item["id"]["videoId"]
						item_data = item["snippet"]
						channel_records = await self.bot.db.fetch(
							"""
							SELECT discord_channel_id
							FROM youtube.streams
							WHERE youtube_channel_id = $1
							""", 
							channel_id
						)
						for channel_record in channel_records:
							record = await self.bot.db.fetchrow(
								"""
								SELECT message_id, live
								FROM youtube.stream_announcements
								WHERE video_id = $1 AND channel_id = $2
								""", 
								video_id, channel_record["discord_channel_id"]
							)
							if not record:
								text_channel = self.bot.get_channel(channel_record["discord_channel_id"])
								if text_channel:
									embed = discord.Embed(title = item_data["title"], description = item_data["description"], url = "https://www.youtube.com/watch?v=" + video_id, timestamp = dateutil.parser.parse(item_data["publishedAt"]).replace(tzinfo = None), color = self.bot.youtube_color)
									embed.set_author(name = f"{item_data['channelTitle']} is live now on YouTube", url = "https://www.youtube.com/channel/" + item_data["channelId"], icon_url = self.bot.youtube_icon_url)
									# TODO: Add channel icon as author icon?
									embed.set_thumbnail(url = item_data["thumbnails"]["high"]["url"])
									message = await text_channel.send(embed = embed)
									await self.bot.db.execute(
										"""
										INSERT INTO youtube.stream_announcements (video_id, channel_id, message_id, live)
										VALUES ($1, $2, $3, TRUE)
										""", 
										video_id, text_channel.id, message.id
									)
								# TODO: Remove text channel data if now non-existent
							elif not record["live"]:
								text_channel = self.bot.get_channel(channel_record["discord_channel_id"])
								if text_channel:
									message = await text_channel.fetch_message(record["message_id"])
									# TODO: Handle message deleted
									embed = message.embeds[0]
									embed.set_author(name = embed.author.name.replace("was live", "is live now"), url = embed.author.url, icon_url = embed.author.icon_url)
									await message.edit(embed = embed)
									await self.bot.db.execute(
										"""
										UPDATE youtube.stream_announcements
										SET live = TRUE
										WHERE video_id = $1 AND channel_id = $2
										""", 
										video_id, channel_record["discord_channel_id"]
									)
						video_ids.append(video_id)
					await asyncio.sleep(1)
				except (aiohttp.ClientOSError, asyncio.TimeoutError) as e:
					await self.bot.db.execute(
						"""
						INSERT INTO youtube.stream_errors (channel_id, type, message)
						VALUES ($1, $2, $3)
						""", 
						channel_id, type(e).__name__, str(e)
					)
					# Print error?
					await asyncio.sleep(10)
			records = await self.bot.db.fetch(
				"""
				SELECT video_id, channel_id, message_id
				FROM youtube.stream_announcements
				WHERE live = TRUE
				"""
			)
			for record in records:
				if record["video_id"] not in video_ids:
					text_channel = self.bot.get_channel(record["channel_id"])
					if text_channel:
						message = await text_channel.fetch_message(record["message_id"])
						# TODO: Handle message deleted
						embed = message.embeds[0]
						embed.set_author(name = embed.author.name.replace("is live now", "was live"), url = embed.author.url, icon_url = embed.author.icon_url)
						await message.edit(embed = embed)
						await self.bot.db.execute(
							"""
							UPDATE youtube.stream_announcements
							SET live = FALSE
							WHERE video_id = $1 AND channel_id = $2
							""", 
							record["video_id"], record["channel_id"]
						)
				# TODO: Handle no longer being followed?
		except Exception as e:
			print("Exception in YouTube Task", file = sys.stderr)
			traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
			errors_logger.error("Uncaught YouTube Task exception\n", exc_info = (type(e), e, e.__traceback__))
			await asyncio.sleep(60)
	
	@check_streams.before_loop
	async def before_check_streams(self):
		await self.initialize_database()
		await self.bot.wait_until_ready()
	
	@check_streams.after_loop
	async def after_check_streams(self):
		self.bot.print("YouTube streams task cancelled")
	
	# TODO: Follow channels/new video uploads
	
	async def uploads(self, ctx):
		'''YouTube Uploads/Videos'''
		await ctx.send_help(ctx.command)
	
	async def uploads_add(self, ctx, channel : str):
		'''Add YouTube channel to follow'''
		channel_id = await get_channel_id(ctx, channel)
		if not channel_id:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: YouTube channel not found")
		channels = self.uploads_info.get(str(ctx.channel.id))
		if channels:
			if channel_id in channels:
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} This text channel is already following that YouTube channel")
			channels.append(channel_id)
		else:
			self.uploads_info[str(ctx.channel.id)] = [channel_id]
		url = "https://pubsubhubbub.appspot.com/"
		headers = {"content-type": "application/x-www-form-urlencoded"}
		data = {"hub.callback": ctx.bot.HTTP_SERVER_CALLBACK_URL, "hub.mode": "subscribe", 
				"hub.topic": "https://www.youtube.com/xml/feeds/videos.xml?channel_id=" + channel_id}
		async with ctx.bot.aiohttp_session.post(url, headers = headers, data = data) as resp:
			# TODO: unique callback url for each subscription?
			if resp.status not in (202, 204):
				error_description = await resp.text()
				await ctx.embed_reply(f"{ctx.bot.error_emoji} Error {resp.status}: {error_description}")
				self.uploads_info[str(ctx.channel.id)].remove(channel_id)
				return
		self.uploads_following.add(channel_id)
		with open(ctx.bot.data_path + "/youtube_uploads.json", 'w') as uploads_file:
			json.dump(self.uploads_info, uploads_file, indent = 4)
		await ctx.embed_reply(f"Added the YouTube channel, "
								f"[`{channel_id}`](https://www.youtube.com/channel/{channel_id}), "
								"to this text channel\n"
								"I will now announce here when this YouTube channel uploads videos")
	
	async def uploads_remove(self, ctx, channel_id : str):
		'''Remove YouTube channel being followed'''
		channels = self.uploads_info.get(str(ctx.channel.id))
		if not channels or channel_id not in channels:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} This text channel isn't following that YouTube channel")
		channels.remove(channel_id)
		self.uploads_following = set(channel_id for channels in self.uploads_info.values() for channel_id in channels)
		url = "https://pubsubhubbub.appspot.com/"
		headers = {"content-type": "application/x-www-form-urlencoded"}
		data = {"hub.callback": ctx.bot.HTTP_SERVER_CALLBACK_URL, "hub.mode": "unsubscribe", 
				"hub.topic": "https://www.youtube.com/xml/feeds/videos.xml?channel_id=" + channel_id}
		async with ctx.bot.aiohttp_session.post(url, headers = headers, data = data) as resp:
			if resp.status not in (202, 204):
				error_description = await resp.text()
				await ctx.embed_reply(f"{ctx.bot.error_emoji} Error {resp.status}: {error_description}")
				self.uploads_info[str(ctx.channel.id)].append(channel_id)
				self.uploads_following.add(channel_id)
				return
		with open(ctx.bot.data_path + "/youtube_uploads.json", 'w') as uploads_file:
			json.dump(self.uploads_info, uploads_file, indent = 4)
		await ctx.embed_reply("Removed the YouTube channel, "
								f"[`{channel_id}`](https://www.youtube.com/channel/{channel_id}), "
								"from this text channel")
	
	async def uploads_channels(self, ctx):
		'''Show YouTube channels being followed in this text channel'''
		await ctx.embed_reply(ctx.bot.CODE_BLOCK.format('\n'.join(self.uploads_info.get(str(ctx.channel.id), []))))
	
	async def process_upload(self, channel_id, request_content):
		request_info = await self.bot.loop.run_in_executor(None, feedparser.parse, request_content) # Necessary to run in executor?
		if request_info.entries and not request_info.entries[0].yt_videoid in self.uploads_processed:
			video_data = request_info.entries[0]
			self.uploads_processed.append(video_data.yt_videoid)
			time_published = dateutil.parser.parse(video_data.published)
			# Don't process videos published more than an hour ago
			if time_published < datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours = 1): return
			embed = discord.Embed(title = video_data.title, url = video_data.link, timestamp = time_published, color = self.bot.youtube_color)
			embed.set_author(name = f"{video_data.author} just uploaded a video on YouTube", url = video_data.author_detail.href, icon_url = self.bot.youtube_icon_url)
			# TODO: Add channel icon as author icon?
			# Add description + thumbnail + length
			async with self.bot.aiohttp_session.get("https://www.googleapis.com/youtube/v3/videos", params = {"id": video_data.yt_videoid, "key": self.bot.GOOGLE_API_KEY, "part": "snippet,contentDetails"}) as resp:
				data = await resp.json()
			data = next(iter(data.get("items", [])), {})
			if data.get("snippet", {}).get("liveBroadcastContent") in ("live", "upcoming"): return
			description = data.get("snippet", {}).get("description", "")
			if len(description) > 200: description = description[:200].rsplit(' ', 1)[0] + "..."
			embed.description = description or ""
			thumbnail_url = data.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url", None)
			if thumbnail_url: embed.set_thumbnail(url = thumbnail_url)
			duration = data.get("contentDetails", {}).get("duration")
			if duration: embed.description += f"\nLength: {duration_to_string(isodate.parse_duration(duration), abbreviate = True)}"
			for text_channel_id, yt_channels in self.uploads_info.items():
				if channel_id in yt_channels:
					text_channel = self.bot.get_channel(int(text_channel_id))
					if text_channel:
						await text_channel.send(embed = embed)
					# TODO: Remove text channel data if now non-existent


async def youtube(ctx):
	'''YouTube'''
	await ctx.send_help(ctx.command)

async def streams(ctx):
	'''YouTube Streams'''
	await ctx.send_help(ctx.command)

async def streams_add(ctx, channel : str):
	'''Add YouTube channel to follow'''
	channel_id = await get_channel_id(ctx, channel)
	if not channel_id:
		return await ctx.embed_reply(
			f"{ctx.bot.error_emoji} Error: YouTube channel not found"
		)
	inserted = await ctx.bot.db.fetchrow(
		"""
		INSERT INTO youtube.streams (discord_channel_id, youtube_channel_id)
		VALUES ($1, $2)
		ON CONFLICT DO NOTHING
		RETURNING *
		""", 
		ctx.channel.id, channel_id
	)
	if not inserted:
		return await ctx.embed_reply(
			f"{ctx.bot.error_emoji} This text channel is already following that YouTube channel"
		)
	await ctx.embed_reply(
		f"Added the YouTube channel, [`{channel}`](https://www.youtube.com/channel/{channel_id}), to this text channel\n"
		"I will now announce here when this YouTube channel goes live"
	)

async def streams_remove(ctx, channel : str):
	'''Remove YouTube channel being followed'''
	channel_id = await get_channel_id(ctx, channel)
	if not channel_id:
		return await ctx.embed_reply(
			f"{ctx.bot.error_emoji} Error: YouTube channel not found"
		)
	deleted = await ctx.bot.db.fetchval(
		"""
		DELETE FROM youtube.streams
		WHERE discord_channel_id = $1 AND youtube_channel_id = $2
		RETURNING *
		""", 
		ctx.channel.id, channel_id
	)
	if not deleted:
		return await ctx.embed_reply(
			f"{ctx.bot.error_emoji} This text channel isn't following that YouTube channel"
		)
	await ctx.embed_reply(
		f"Removed the YouTube channel, [`{channel}`](https://www.youtube.com/channel/{channel_id}), from this text channel"
	)

async def streams_channels(ctx):
	'''Show YouTube channels being followed in this text channel'''
	records = await ctx.bot.db.fetch(
		"""
		SELECT youtube_channel_id
		FROM youtube.streams
		WHERE discord_channel_id = $1
		""", 
		ctx.channel.id
	)
	await ctx.embed_reply(ctx.bot.CODE_BLOCK.format('\n'.join(record["youtube_channel_id"] for record in records)))

async def get_channel_id(ctx, id_or_username):
	url = "https://www.googleapis.com/youtube/v3/channels"
	for key in ("id", "forUsername"):
		params = {"part": "id", key: id_or_username, "key": ctx.bot.GOOGLE_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data["pageInfo"]["totalResults"]:
			return data["items"][0]["id"]
	return ""

