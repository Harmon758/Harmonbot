
import discord
from discord.ext import commands

import asyncio
import datetime
import itertools
import json
import os
import sys
import traceback

import aiohttp
import asyncpg
import dateutil.parser
import feedparser
import isodate

import clients
from modules import logging
from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(YouTube(bot))
	if "Audio" in bot.cogs:
		bot.remove_command("streams")
		bot.remove_command("uploads")

# TODO: Handle audio cog not loaded
## youtube = getattr(clients.client.get_cog("Audio"), "audio", commands)

class YouTube(commands.Cog):
	'''
	YouTube streams and uploads notification system
	Uploads system relevant documentation:
	https://developers.google.com/youtube/v3/guides/push_notifications
	https://pubsubhubbub.appspot.com/
	https://pubsubhubbub.github.io/PubSubHubbub/pubsubhubbub-core-0.4.html
	'''
	
	def __init__(self, bot):
		self.bot = bot
		self.uploads_processed = []
		
		utilities.add_as_subcommand(self, self.youtube_streams, "Audio.audio", "streams", aliases = ["stream"])
		utilities.add_as_subcommand(self, self.youtube_uploads, "Audio.audio", "uploads", aliases = ["videos"])
		
		self.streams_task = self.bot.loop.create_task(self.check_youtube_streams())
		
		clients.create_file("youtube_uploads", content = {})
		with open(clients.data_path + "/youtube_uploads.json", 'r') as uploads_file:
			self.uploads_info = json.load(uploads_file)
		self.youtube_uploads_following = set(channel_id for channels in self.uploads_info.values() for channel_id in channels)
		self.renew_uploads_task = self.bot.loop.create_task(self.renew_upload_supscriptions())
	
	def __unload(self):
		utilities.remove_as_subcommand(self, "Audio.audio", "streams")
		utilities.remove_as_subcommand(self, "Audio.audio", "uploads")
		
		self.youtube_streams.recursively_remove_all_commands() # Necessary?
		# youtube.remove_command("streams") # Handle when audio cog not loaded first
		self.streams_task.cancel()
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
	
	# TODO: use on_ready instead?
	# TODO: renew after hub.lease_seconds?
	async def renew_upload_supscriptions(self):
		for channel_id in self.youtube_uploads_following:
			url = "https://pubsubhubbub.appspot.com/"
			headers = {"content-type": "application/x-www-form-urlencoded"}
			data = {"hub.callback": self.bot.HTTP_SERVER_CALLBACK_URL, "hub.mode": "subscribe", 
					"hub.topic": "https://www.youtube.com/xml/feeds/videos.xml?channel_id=" + channel_id}
			async with clients.aiohttp_session.post(url, headers = headers, data = data) as resp:
				if resp.status not in (202, 204):
					error_description = await resp.text()
					print(f"{self.bot.console_message_prefix}Google PubSubHubbub Error {resp.status} "
							f"re-subscribing to {channel_id}: {error_description}")
			await asyncio.sleep(5)  # Google PubSubHubbub rate limit?
	
	@commands.group(name = "streams", invoke_without_command = True)
	# Handle stream alias when audio cog not loaded first | aliases = ["stream"]
	@checks.is_permitted()
	async def youtube_streams(self, ctx):
		'''YouTube Streams'''
		await ctx.invoke(self.bot.get_command("help"), "youtube", ctx.invoked_with)
	
	@youtube_streams.command(name = "add", invoke_without_command = True)
	@checks.is_permitted()
	async def youtube_streams_add(self, ctx, channel : str):
		'''Add YouTube channel to follow'''
		channel_id = await self.get_youtube_channel_id(channel)
		if not channel_id:
			return await ctx.embed_reply(":no_entry: Error: YouTube channel not found")
		try:
			await ctx.bot.db.execute(
				"""
				INSERT INTO youtube.streams (discord_channel_id, youtube_channel_id)
				VALUES ($1, $2)
				""", 
				ctx.channel.id, channel_id
			)
		except asyncpg.UniqueViolationError:
			return await ctx.embed_reply(":no_entry: This text channel is already following that YouTube channel")
		await ctx.embed_reply(f"Added the YouTube channel, [`{channel}`](https://www.youtube.com/channel/{channel_id}), to this text channel\n"
		"I will now announce here when this YouTube channel goes live")
	
	@youtube_streams.command(name = "remove", aliases = ["delete"], invoke_without_command = True)
	@checks.is_permitted()
	async def youtube_streams_remove(self, ctx, channel : str):
		'''Remove YouTube channel being followed'''
		channel_id = await self.get_youtube_channel_id(channel)
		if not channel_id:
			return await ctx.embed_reply(":no_entry: Error: YouTube channel not found")
		deleted = await ctx.bot.db.fetchval(
			"""
			DELETE FROM youtube.streams
			WHERE discord_channel_id = $1 AND youtube_channel_id = $2
			RETURNING *
			""", 
			ctx.channel.id, channel_id
		)
		if not deleted:
			return await ctx.embed_reply(":no_entry: This text channel isn't following that YouTube channel")
		await ctx.embed_reply(f"Removed the YouTube channel, [`{channel}`](https://www.youtube.com/channel/{channel_id}), from this text channel")
	
	@youtube_streams.command(name = "channels", aliases = ["streams"])
	@checks.not_forbidden()
	async def youtube_streams_channels(self, ctx):
		'''Show YouTube channels being followed in this text channel'''
		records = await ctx.bot.db.fetch(
			"""
			SELECT youtube_channel_id
			FROM youtube.streams
			WHERE discord_channel_id = $1
			""", 
			ctx.channel.id
		)
		await ctx.embed_reply(clients.code_block.format('\n'.join(record["youtube_channel_id"] for record in records)))
	
	async def check_youtube_streams(self):
		await self.initialize_database()
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			try:
				records = await self.bot.db.fetch("SELECT DISTINCT youtube_channel_id FROM youtube.streams")
				video_ids = []
				for record in records:
					channel_id = record["youtube_channel_id"]
					try:
						url = "https://www.googleapis.com/youtube/v3/search"
						params = {"part": "snippet", "eventType": "live", "type": "video", 
									"channelId": channel_id, "key": self.bot.GOOGLE_API_KEY}
						async with clients.aiohttp_session.get(url, params = params) as resp:
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
										message = await text_channel.get_message(record["message_id"])
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
							message = await text_channel.get_message(record["message_id"])
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
				await asyncio.sleep(20)
			except asyncio.CancelledError:
				print(f"{self.bot.console_message_prefix}YouTube Task cancelled")
				return
			except Exception as e:
				print("Exception in YouTube Task", file = sys.stderr)
				traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
				logging.errors_logger.error("Uncaught YouTube Task exception\n", exc_info = (type(e), e, e.__traceback__))
				await asyncio.sleep(60)
	
	# TODO: Follow channels/new video uploads
	
	@commands.group(name = "uploads", aliases = ["videos"], invoke_without_command = True)
	@checks.is_permitted()
	async def youtube_uploads(self, ctx):
		'''YouTube Uploads/Videos'''
		await ctx.invoke(self.bot.get_command("help"), "youtube", ctx.invoked_with)
	
	@youtube_uploads.command(name = "add", aliases = ["subscribe"], invoke_without_command = True)
	@checks.is_permitted()
	async def youtube_uploads_add(self, ctx, channel : str):
		'''Add YouTube channel to follow'''
		channel_id = await self.get_youtube_channel_id(channel)
		if not channel_id:
			return await ctx.embed_reply(":no_entry: Error: YouTube channel not found")
		channels = self.uploads_info.get(str(ctx.channel.id))
		if channels:
			if channel_id in channels:
				return await ctx.embed_reply(":no_entry: This text channel is already following that YouTube channel")
			channels.append(channel_id)
		else:
			self.uploads_info[str(ctx.channel.id)] = [channel_id]
		url = "https://pubsubhubbub.appspot.com/"
		headers = {"content-type": "application/x-www-form-urlencoded"}
		data = {"hub.callback": ctx.bot.HTTP_SERVER_CALLBACK_URL, "hub.mode": "subscribe", 
				"hub.topic": "https://www.youtube.com/xml/feeds/videos.xml?channel_id=" + channel_id}
		async with clients.aiohttp_session.post(url, headers = headers, data = data) as resp:
			# TODO: unique callback url for each subscription?
			if resp.status not in (202, 204):
				error_description = await resp.text()
				await ctx.embed_reply(f":no_entry: Error {resp.status}: {error_description}")
				self.uploads_info[str(ctx.channel.id)].remove(channel_id)
				return
		self.youtube_uploads_following.add(channel_id)
		with open(clients.data_path + "/youtube_uploads.json", 'w') as uploads_file:
			json.dump(self.uploads_info, uploads_file, indent = 4)
		await ctx.embed_reply(f"Added the YouTube channel, "
								f"[`{channel_id}`](https://www.youtube.com/channel/{channel_id}), "
								"to this text channel\n"
								"I will now announce here when this YouTube channel uploads videos")
	
	@youtube_uploads.command(name = "remove", aliases = ["delete", "unsubscribe"], invoke_without_command = True)
	@checks.is_permitted()
	async def youtube_uploads_remove(self, ctx, channel_id : str):
		'''Remove YouTube channel being followed'''
		channels = self.uploads_info.get(str(ctx.channel.id))
		if not channels or channel_id not in channels:
			return await ctx.embed_reply(":no_entry: This text channel isn't following that YouTube channel")
		channels.remove(channel_id)
		self.youtube_uploads_following = set(channel_id for channels in self.uploads_info.values() for channel_id in channels)
		url = "https://pubsubhubbub.appspot.com/"
		headers = {"content-type": "application/x-www-form-urlencoded"}
		data = {"hub.callback": ctx.bot.HTTP_SERVER_CALLBACK_URL, "hub.mode": "unsubscribe", 
				"hub.topic": "https://www.youtube.com/xml/feeds/videos.xml?channel_id=" + channel_id}
		async with clients.aiohttp_session.post(url, headers = headers, data = data) as resp:
			if resp.status not in (202, 204):
				error_description = await resp.text()
				await ctx.embed_reply(f":no_entry: Error {resp.status}: {error_description}")
				self.uploads_info[str(ctx.channel.id)].append(channel_id)
				self.youtube_uploads_following.add(channel_id)
				return
		with open(clients.data_path + "/youtube_uploads.json", 'w') as uploads_file:
			json.dump(self.uploads_info, uploads_file, indent = 4)
		await ctx.embed_reply("Removed the YouTube channel, "
								f"[`{channel_id}`](https://www.youtube.com/channel/{channel_id}), "
								"from this text channel")
	
	@youtube_uploads.command(name = "channels", aliases = ["uploads", "videos"])
	@checks.not_forbidden()
	async def youtube_uploads_channels(self, ctx):
		'''Show YouTube channels being followed in this text channel'''
		await ctx.embed_reply(clients.code_block.format('\n'.join(self.uploads_info.get(str(ctx.channel.id), []))))
	
	async def process_youtube_upload(self, channel_id, request_content):
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
			async with clients.aiohttp_session.get("https://www.googleapis.com/youtube/v3/videos", params = {"id": video_data.yt_videoid, "key": self.bot.GOOGLE_API_KEY, "part": "snippet,contentDetails"}) as resp:
				data = await resp.json()
			data = next(iter(data.get("items", [])), {})
			if data.get("snippet", {}).get("liveBroadcastContent") in ("live", "upcoming"): return
			description = data.get("snippet", {}).get("description", "")
			if len(description) > 200: description = description[:200].rsplit(' ', 1)[0] + "..."
			embed.description = description or ""
			thumbnail_url = data.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url", None)
			if thumbnail_url: embed.set_thumbnail(url = thumbnail_url)
			duration = data.get("contentDetails", {}).get("duration")
			if duration: embed.description += f"\nLength: {utilities.secs_to_letter_format(isodate.parse_duration(duration).total_seconds())}"
			for text_channel_id, yt_channels in self.uploads_info.items():
				if channel_id in yt_channels:
					text_channel = self.bot.get_channel(int(text_channel_id))
					if text_channel:
						await text_channel.send(embed = embed)
					# TODO: Remove text channel data if now non-existent
	
	async def get_youtube_channel_id(self, id_or_username):
		url = "https://www.googleapis.com/youtube/v3/channels"
		for key in ("id", "forUsername"):
			params = {"part": "id", key: id_or_username, "key": self.bot.GOOGLE_API_KEY}
			async with clients.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if data["pageInfo"]["totalResults"]:
				return data["items"][0]["id"]
		return ""

