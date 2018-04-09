
import discord
from discord.ext import commands

import asyncio
import datetime
import dateutil.parser
import feedparser
import isodate
import itertools
import json
import os
import sys
import traceback

import clients
import credentials
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

class YouTube:
	
	def __init__(self, bot):
		self.bot = bot
		self.streams_announced = {}
		self.old_streams_announced = {}
		self.uploads_processed = []
		
		utilities.add_as_subcommand(self, self.youtube_streams, "Audio.audio", "streams", aliases = ["stream"])
		utilities.add_as_subcommand(self, self.youtube_uploads, "Audio.audio", "uploads", aliases = ["videos"])
		
		clients.create_file("youtube_streams", content = {"channels" : {}})
		with open(clients.data_path + "/youtube_streams.json", 'r') as streams_file:
			self.streams_info = json.load(streams_file)
		self.streams_task = self.bot.loop.create_task(self.check_youtube_streams())
		
		clients.create_file("youtube_uploads", content = {"channels" : {}})
		with open(clients.data_path + "/youtube_uploads.json", 'r') as uploads_file:
			self.uploads_info = json.load(uploads_file)
		self.youtube_uploads_following = set([channel_id for channels in self.uploads_info["channels"].values() for channel_id in channels["yt_channel_ids"]])
		self.renew_uploads_task = self.bot.loop.create_task(self.renew_upload_supscriptions())
	
	def __unload(self):
		utilities.remove_as_subcommand(self, "Audio.audio", "streams")
		utilities.remove_as_subcommand(self, "Audio.audio", "uploads")
		
		self.youtube_streams.recursively_remove_all_commands() # Necessary?
		# youtube.remove_command("streams") # Handle when audio cog not loaded first
		self.streams_task.cancel()
		self.renew_uploads_task.cancel()
	
	# TODO: use on_ready instead?
	# TODO: renew after hub.lease_seconds?
	async def renew_upload_supscriptions(self):
		for channel_id in self.youtube_uploads_following:
			async with clients.aiohttp_session.post("https://pubsubhubbub.appspot.com/", headers = {"content-type": "application/x-www-form-urlencoded"}, data = {"hub.callback": credentials.callback_url, "hub.mode": "subscribe", "hub.topic": "https://www.youtube.com/xml/feeds/videos.xml?channel_id=" + channel_id}) as resp:
				if resp.status not in (202, 204):
					error_description = await resp.text()
					print("{}Google PubSubHubbub Error {} re-subscribing to {}: {}".format(clients.console_message_prefix, resp.status, channel_id, error_description))
			await asyncio.sleep(5)  # Google PubSubHubbub rate limit?
	
	@commands.group(name = "streams", invoke_without_command = True)
	# Handle stream alias when audio cog not loaded first | aliases = ["stream"]
	@checks.is_permitted()
	async def youtube_streams(self, ctx):
		'''Youtube Streams'''
		await ctx.invoke(self.bot.get_command("help"), "youtube", ctx.invoked_with)
	
	@youtube_streams.command(name = "add", invoke_without_command = True)
	@checks.is_permitted()
	async def youtube_streams_add(self, ctx, channel_id : str):
		'''Add Youtube channel to follow'''
		# TODO: Check channel ID validity
		# TODO: Add by username option
		channel = self.streams_info["channels"].get(ctx.channel.id)
		if channel:
			if channel_id in channel["channel_ids"]:
				await ctx.embed_reply(":no_entry: This text channel is already following that Youtube channel")
				return
			channel["channel_ids"].append(channel_id)
		else:
			self.streams_info["channels"][ctx.channel.id] = {"name": ctx.channel.name, "channel_ids": [channel_id]}
		with open(clients.data_path + "/youtube_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await ctx.embed_reply("Added the Youtube channel, [`{0}`](https://www.youtube.com/channel/{0}), to this text channel\n"
		"I will now announce here when this Youtube channel goes live".format(channel_id))
	
	@youtube_streams.command(name = "remove", aliases = ["delete"], invoke_without_command = True)
	@checks.is_permitted()
	async def youtube_streams_remove(self, ctx, channel_id : str):
		'''Remove Youtube channel being followed'''
		channel = self.streams_info["channels"].get(ctx.channel.id)
		if not channel or channel_id not in channel["channel_ids"]:
			await ctx.embed_reply(":no_entry: This text channel isn't following that Youtube channel")
			return
		channel["channel_ids"].remove(channel_id)
		with open(clients.data_path + "/youtube_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await ctx.embed_reply("Removed the Youtube channel, [`{0}`](https://www.youtube.com/channel/{0}), from this text channel".format(channel_id))
	
	@youtube_streams.command(name = "channels", aliases = ["streams"])
	@checks.not_forbidden()
	async def youtube_streams_channels(self, ctx):
		'''Show Youtube channels being followed in this text channel'''
		await ctx.embed_reply(clients.code_block.format('\n'.join(self.streams_info["channels"].get(ctx.channel.id, {}).get("channel_ids", []))))
	
	async def check_youtube_streams(self):
		await self.bot.wait_until_ready()
		if os.path.isfile(clients.data_path + "/temp/youtube_streams_announced.json"):
			with open(clients.data_path + "/temp/youtube_streams_announced.json", 'r') as streams_file:
				self.streams_announced = json.load(streams_file)
			for announced_video_id, announcements in self.streams_announced.items():
				for announcement in announcements:
					text_channel = self.bot.get_channel(announcement[2])
					# TODO: Handle text channel not existing anymore
					announcement[0] = await self.bot.get_message(text_channel, announcement[0])
					# TODO: Handle message deleted
					announcement[1] = discord.Embed(title = announcement[1]["title"], description = announcement[1].get("description"), url = announcement[1]["url"], timestamp = dateutil.parser.parse(announcement[1]["timestamp"]), color = announcement[1]["color"]).set_thumbnail(url = announcement[1]["thumbnail"]["url"]).set_author(name = announcement[1]["author"]["name"], url = announcement[1]["author"]["url"], icon_url = announcement[1]["author"]["icon_url"])
					del announcement[2]
		## os.remove(clients.data_path + "/temp/youtube_streams_announced.json")
		while not self.bot.is_closed():
			try:
				channel_ids = set(itertools.chain(*[channel["channel_ids"] for channel in self.streams_info["channels"].values()]))
				video_ids = []
				for channel_id in channel_ids:
					url = "https://www.googleapis.com/youtube/v3/search?part=snippet&eventType=live&type=video&channelId={}&key={}"
					async with clients.aiohttp_session.get(url.format(channel_id, credentials.google_apikey)) as resp:
						stream_data = await resp.json()
					# Multiple streams from one channel possible
					for item in stream_data.get("items", []):
						video_id = item["id"]["videoId"]
						item_data = item["snippet"]
						if video_id in self.old_streams_announced:
							for announcement in self.old_streams_announced[video_id]:
								embed = announcement[1]
								embed.set_author(name = embed.author.name.replace("was live", "is live now"), url = embed.author.url, icon_url = embed.author.icon_url)
								await self.bot.edit_message(announcement[0], embed = embed)
							self.streams_announced[video_id] = self.old_streams_announced[video_id]
							del self.old_streams_announced[video_id]
						elif video_id not in self.streams_announced:
							for text_channel_id, channel_info in self.streams_info["channels"].items():
								if channel_id in channel_info["channel_ids"]:
									text_channel = self.bot.get_channel(text_channel_id)
									if not text_channel:
										# TODO: Remove text channel data if now non-existent
										continue
									embed = discord.Embed(title = item_data["title"], description = item_data["description"], url = "https://www.youtube.com/watch?v=" + video_id, timestamp = dateutil.parser.parse(item_data["publishedAt"]).replace(tzinfo = None), color = self.bot.youtube_color)
									embed.set_author(name = "{} is live now on Youtube".format(item_data["channelTitle"]), url = "https://www.youtube.com/channel/" + item_data["channelId"], icon_url = self.bot.youtube_icon_url)
									# TODO: Add channel icon as author icon?
									embed.set_thumbnail(url = item_data["thumbnails"]["high"]["url"])
									message = await self.bot.send_message(text_channel, embed = embed)
									self.streams_announced[video_id] = self.streams_announced.get(video_id, []) + [[message, embed]]
						video_ids.append(video_id)
					await asyncio.sleep(1)
				for announced_video_id, announcements in self.streams_announced.copy().items():
					if announced_video_id not in video_ids:
						for announcement in announcements:
							embed = announcement[1]
							embed.set_author(name = embed.author.name.replace("is live now", "was live"), url = embed.author.url, icon_url = embed.author.icon_url)
							await self.bot.edit_message(announcement[0], embed = embed)
							# TODO: Handle message deleted
							self.old_streams_announced[announced_video_id] = self.streams_announced[announced_video_id]
							del self.streams_announced[announced_video_id]
					# TODO: Handle no longer being followed?
				await asyncio.sleep(20)
			except asyncio.CancelledError:
				for announced_video_id, announcements in self.streams_announced.items():
					for announcement in announcements:
						announcement.append(announcement[0].channel.id)
						announcement[0] = announcement[0].id
						announcement[1] = announcement[1].to_dict()
				with open(clients.data_path + "/temp/youtube_streams_announced.json", 'w') as streams_file:
					json.dump(self.streams_announced, streams_file, indent = 4)
				return
			except Exception as e:
				print("Exception in Youtube Task", file = sys.stderr)
				traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
				logging.errors_logger.error("Uncaught Youtube Task exception\n", exc_info = (type(e), e, e.__traceback__))
				await asyncio.sleep(60)
	
	# TODO: Follow channels/new video uploads
	
	@commands.group(name = "uploads", aliases = ["videos"], invoke_without_command = True)
	@checks.is_permitted()
	async def youtube_uploads(self, ctx):
		'''Youtube Uploads/Videos'''
		await ctx.invoke(self.bot.get_command("help"), "youtube", ctx.invoked_with)
	
	@youtube_uploads.command(name = "add", aliases = ["subscribe"], invoke_without_command = True)
	@checks.is_permitted()
	async def youtube_uploads_add(self, ctx, channel : str):
		'''Add Youtube channel to follow'''
		channel_id = await self.get_youtube_channel_id(channel)
		if not channel_id:
			await ctx.embed_reply(":no_entry: Error: Youtube channel not found")
			return
		text_channel = self.uploads_info["channels"].get(str(ctx.channel.id))
		if text_channel:
			if channel_id in text_channel["yt_channel_ids"]:
				await ctx.embed_reply(":no_entry: This text channel is already following that Youtube channel")
				return
			text_channel["yt_channel_ids"].append(channel_id)
		else:
			self.uploads_info["channels"][str(ctx.channel.id)] = {"yt_channel_ids": [channel_id]}
		self.youtube_uploads_following.add(channel_id)
		async with clients.aiohttp_session.post("https://pubsubhubbub.appspot.com/", headers = {"content-type": "application/x-www-form-urlencoded"}, data = {"hub.callback": credentials.callback_url, "hub.mode": "subscribe", "hub.topic": "https://www.youtube.com/xml/feeds/videos.xml?channel_id=" + channel_id}) as resp:
		# TODO: unique callback url for each subscription?
			if resp.status not in (202, 204):
				error_description = await resp.text()
				await ctx.embed_reply(":no_entry: Error {}: {}".format(resp.status, error_description))
				self.uploads_info["channels"][str(ctx.channel.id)]["yt_channel_ids"].remove(channel_id)
				self.youtube_uploads_following.discard(channel_id)
				return
		with open(clients.data_path + "/youtube_uploads.json", 'w') as uploads_file:
			json.dump(self.uploads_info, uploads_file, indent = 4)
		await ctx.embed_reply("Added the Youtube channel, [`{0}`](https://www.youtube.com/channel/{0}), to this text channel\n"
		"I will now announce here when this Youtube channel uploads videos".format(channel_id))
	
	@youtube_uploads.command(name = "remove", aliases = ["delete", "unsubscribe"], invoke_without_command = True)
	@checks.is_permitted()
	async def youtube_uploads_remove(self, ctx, channel_id : str):
		'''Remove Youtube channel being followed'''
		channel = self.uploads_info["channels"].get(str(ctx.channel.id))
		if not channel or channel_id not in channel["yt_channel_ids"]:
			await ctx.embed_reply(":no_entry: This text channel isn't following that Youtube channel")
			return
		channel["yt_channel_ids"].remove(channel_id)
		self.youtube_uploads_following.discard(channel_id)
		async with clients.aiohttp_session.post("https://pubsubhubbub.appspot.com/", headers = {"content-type": "application/x-www-form-urlencoded"}, data = {"hub.callback": credentials.callback_url, "hub.mode": "unsubscribe", "hub.topic": "https://www.youtube.com/xml/feeds/videos.xml?channel_id=" + channel_id}) as resp:
			if resp.status not in (202, 204):
				error_description = await resp.text()
				await ctx.embed_reply(":no_entry: Error {}: {}".format(resp.status, error_description))
				self.uploads_info["channels"][str(ctx.channel.id)]["yt_channel_ids"].append(channel_id)
				self.youtube_uploads_following.add(channel_id)
				return
		with open(clients.data_path + "/youtube_uploads.json", 'w') as uploads_file:
			json.dump(self.uploads_info, uploads_file, indent = 4)
		await ctx.embed_reply("Removed the Youtube channel, [`{0}`](https://www.youtube.com/channel/{0}), from this text channel".format(channel_id))
	
	@youtube_uploads.command(name = "channels", aliases = ["uploads", "videos"])
	@checks.not_forbidden()
	async def youtube_uploads_channels(self, ctx):
		'''Show Youtube channels being followed in this text channel'''
		await ctx.embed_reply(clients.code_block.format('\n'.join(self.uploads_info["channels"].get(str(ctx.channel.id), {}).get("yt_channel_ids", []))))
	
	async def process_youtube_upload(self, channel_id, request_content):
		request_info = await self.bot.loop.run_in_executor(None, feedparser.parse, request_content) # Necessary to run in executor?
		if request_info.entries and not request_info.entries[0].yt_videoid in self.uploads_processed:
			video_data = request_info.entries[0]
			self.uploads_processed.append(video_data.yt_videoid)
			time_published = dateutil.parser.parse(video_data.published)
			# Don't process videos published more than an hour ago
			if time_published < datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours = 1): return
			embed = discord.Embed(title = video_data.title, url = video_data.link, timestamp = time_published, color = self.bot.youtube_color)
			embed.set_author(name = "{} just uploaded a video on Youtube".format(video_data.author), url = video_data.author_detail.href, icon_url = self.bot.youtube_icon_url)
			# TODO: Add channel icon as author icon?
			# Add description + thumbnail + length
			async with clients.aiohttp_session.get("https://www.googleapis.com/youtube/v3/videos", params = {"id": video_data.yt_videoid, "key": credentials.google_apikey, "part": "snippet,contentDetails"}) as resp:
				data = await resp.json()
			data = next(iter(data.get("items", [])), {})
			if data.get("snippet", {}).get("liveBroadcastContent") in ("live", "upcoming"): return
			description = data.get("snippet", {}).get("description", "")
			if len(description) > 200: description = description[:200].rsplit(' ', 1)[0] + "..."
			embed.description = description or ""
			thumbnail_url = data.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url", None)
			if thumbnail_url: embed.set_thumbnail(url = thumbnail_url)
			duration = data.get("contentDetails", {}).get("duration")
			if duration: embed.description += "\nLength: {}".format(utilities.secs_to_letter_format(isodate.parse_duration(duration).total_seconds()))
			for text_channel_id, channel_info in self.uploads_info["channels"].items():
				if channel_id in channel_info["yt_channel_ids"]:
					text_channel = self.bot.get_channel(int(text_channel_id))
					if not text_channel:
						# TODO: Remove text channel data if now non-existent
						continue
					message = await text_channel.send(embed = embed)
	
	# TODO: get to remove as well
	async def get_youtube_channel_id(self, id_or_username):
		async with clients.aiohttp_session.get("https://www.googleapis.com/youtube/v3/channels", params = {"part": "id", "id": id_or_username, "key": credentials.google_apikey}) as resp:
			data = await resp.json()
		if data["pageInfo"]["totalResults"]: return data["items"][0]["id"]
		async with clients.aiohttp_session.get("https://www.googleapis.com/youtube/v3/channels", params = {"part": "id", "forUsername": id_or_username, "key": credentials.google_apikey}) as resp:
			data = await resp.json()
		if data["pageInfo"]["totalResults"]: return data["items"][0]["id"]
		return ""

