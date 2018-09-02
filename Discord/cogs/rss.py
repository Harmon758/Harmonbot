
import discord
from discord.ext import commands

import asyncio
import datetime
import functools
import html
import io
import json
import re
import sys
import time
import textwrap
import traceback
import urllib

import aiohttp
from bs4 import BeautifulSoup
import dateutil.parser
import dateutil.tz
import feedparser
import pytz

import clients
from utilities import checks
from modules import logging

def setup(bot):
	bot.add_cog(RSS(bot))

class RSS:
	
	def __init__(self, bot):
		self.bot = bot
		self.feeds_ids = {}
		clients.create_file("rss_feeds", content = {})
		with open(clients.data_path + "/rss_feeds.json", 'r') as feeds_file:
			self.feeds_following = json.load(feeds_file)
		self.unique_feeds_following = set(feed for feeds in self.feeds_following.values() for feed in feeds)
		self.new_unique_feeds_following = self.unique_feeds_following.copy()
		
		# Generate tzinfos
		self.tzinfos = {}
		for timezone_abbreviation in ("EDT",):
			matching_timezones = list(filter(lambda t: datetime.datetime.now(pytz.timezone(t)).strftime("%Z") == timezone_abbreviation, pytz.common_timezones))
			matching_utc_offsets = set(datetime.datetime.now(pytz.timezone(t)).strftime("%z") for t in matching_timezones)
			if len(matching_utc_offsets) == 1:
				self.tzinfos[timezone_abbreviation] = dateutil.tz.gettz(matching_timezones[0])
		
		self.task = self.bot.loop.create_task(self.check_rss_feeds())
	
	def __unload(self):
		self.task.cancel()
	
	@commands.group(aliases = ["feed"], invoke_without_command = True)
	@checks.is_permitted()
	async def rss(self, ctx):
		'''RSS'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@rss.command(name = "add")
	@checks.is_permitted()
	async def rss_add(self, ctx, url : str):
		'''Add a feed to a channel'''
		# TODO: check if already following
		self.feeds_following[str(ctx.channel.id)] = self.feeds_following.get(str(ctx.channel.id), []) + [url]
		self.new_unique_feeds_following.add(url)
		with open(clients.data_path + "/rss_feeds.json", 'w') as feeds_file:
			json.dump(self.feeds_following, feeds_file, indent = 4)
		# Add entry IDs
		if url not in self.feeds_ids: self.feeds_ids[url] = set()
		async with clients.aiohttp_session.get(url) as resp:
			feed_text = await resp.text()
		feed_info = await self.bot.loop.run_in_executor(None, functools.partial(feedparser.parse, io.BytesIO(feed_text.encode("UTF-8")), response_headers = {"Content-Location": url}))
		# Still necessary to run in executor?
		for entry in feed_info.entries:
			self.feeds_ids[url].add(entry.id)
		await ctx.embed_reply("The feed, {}, has been added to this channel".format(url))

	@rss.command(name = "remove", aliases = ["delete"])
	@checks.is_permitted()
	async def rss_remove(self, ctx, url : str):
		'''Remove a feed from a channel'''
		if url not in self.feeds_following.get(str(ctx.channel.id), []):
			await ctx.embed_reply(":no_entry: This channel isn't following that feed")
			return
		self.feeds_following[str(ctx.channel.id)].remove(url)
		self.new_unique_feeds_following = set(feed for feeds in self.feeds_following.values() for feed in feeds)
		with open(clients.data_path + "/rss_feeds.json", 'w') as feeds_file:
			json.dump(self.feeds_following, feeds_file, indent = 4)
		await ctx.embed_reply("The feed, {}, has been removed from this channel".format(url))

	@rss.command(aliases = ["feed"])
	@checks.not_forbidden()
	async def feeds(self, ctx):
		'''Show feeds being followed in this channel'''
		await ctx.embed_reply('\n'.join(self.feeds_following[str(ctx.channel.id)]))
	
	async def check_rss_feeds(self):
		# TODO: embed limit constants/Bot variables
		await self.bot.wait_until_ready()
		offset_aware_task_start_time = datetime.datetime.now(datetime.timezone.utc)
		## offset_naive_task_start_time = datetime.datetime.utcnow()
		for feed in self.unique_feeds_following:
			try:
				self.feeds_ids[feed] = set()
				async with clients.aiohttp_session.get(feed) as resp:
					feed_text = await resp.text()
				feed_info = await self.bot.loop.run_in_executor(None, functools.partial(feedparser.parse, io.BytesIO(feed_text.encode("UTF-8")), response_headers = {"Content-Location": feed}))
				# Still necessary to run in executor?
				for entry in feed_info.entries:
					self.feeds_ids[feed].add(entry.id)
			except Exception as e:
				print("Exception in RSS Task", file = sys.stderr)
				traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
				logging.errors_logger.error("Uncaught RSS Task exception\n", exc_info = (type(e), e, e.__traceback__))
				print(" (feed: {})".format(feed))
				return
				# TODO: Handle error better
		while not self.bot.is_closed():
			if not self.unique_feeds_following:
				await asyncio.sleep(60)
			for feed in self.unique_feeds_following:
				try:
					async with clients.aiohttp_session.get(feed) as resp:
						feed_text = await resp.text()
					feed_info = await self.bot.loop.run_in_executor(None, functools.partial(feedparser.parse, io.BytesIO(feed_text.encode("UTF-8")), response_headers = {"Content-Location": feed}))
					# Still necessary to run in executor?
					for entry in feed_info.entries:
						if entry.id in self.feeds_ids[feed]:
							continue
						self.feeds_ids[feed].add(entry.id)
						# Get timestamp
						## if "published_parsed" in entry:
						##  timestamp = datetime.datetime.fromtimestamp(time.mktime(entry.published_parsed))
						### inaccurate
						if "published" in entry and entry.published:
							timestamp = dateutil.parser.parse(entry.published, tzinfos = self.tzinfos)
						elif "updated" in entry:  # and entry.updated necessary?; check updated first?
							timestamp = dateutil.parser.parse(entry.updated)
						else:
							timestamp = discord.Embed.Empty
						# TODO: Better method?
						if timestamp and timestamp.tzinfo and timestamp < offset_aware_task_start_time:
							continue
						## elif timestamp < offset_naive_task_start_time: continue
						# Get and set description, title, url + set timestamp
						description = entry.get("summary")
						if not description and "content" in entry:
							description = entry["content"][0].get("value")
						if description:
							description = BeautifulSoup(description, "lxml").get_text(separator = '\n')
							description = re.sub("\n\s*\n", '\n', description)
							if len(description) > 2048:
								space_index = description.rfind(' ', 0, 2045)
								description = description[:space_index] + "..."
						title = textwrap.shorten(entry.get("title"), width = 256, placeholder = "...")
						embed = discord.Embed(title = html.unescape(title), 
												url = entry.link, 
												description = description, 
												timestamp = timestamp, 
												color = self.bot.rss_color)
						# Get and set thumbnail url
						thumbnail_url = None
						if "media_thumbnail" in entry:
							thumbnail_url = entry["media_thumbnail"][0].get("url")
						if not thumbnail_url and "media_content" in entry:
							media_image = discord.utils.find(lambda c: "image" in c.get("medium", ""), entry["media_content"])
							if media_image:
								thumbnail_url = media_image.get("url")
						if not thumbnail_url and "links" in entry:
							image_link = discord.utils.find(lambda l: "image" in l["type"], entry["links"])
							if image_link:
								thumbnail_url = image_link.get("href")
						if not thumbnail_url and "content" in entry:
							content_value = entry["content"][0].get("value")
							if content_value:
								parsed_content_value = BeautifulSoup(content_value, "lxml")
								content_img = getattr(parsed_content_value, "img")
								if content_img:
									thumbnail_url = content_img.get("src")
						if not thumbnail_url and "media_content" in entry:
							media_content = discord.utils.find(lambda c: "url" in c, entry["media_content"])
							if media_content:
								thumbnail_url = media_content["url"]
						if not thumbnail_url and "description" in entry:
							parsed_description = BeautifulSoup(entry.description, "lxml")
							description_img = getattr(parsed_description, "img")
							if description_img:
								thumbnail_url = description_img.get("src")
						if thumbnail_url:
							if not urllib.parse.urlparse(thumbnail_url).netloc:
								thumbnail_url = feed_info.feed.link + thumbnail_url
							embed.set_thumbnail(url = thumbnail_url)
						# Get and set footer icon url
						feed_channel_info = feed_info.feed
						footer_icon_url = discord.Embed.Empty
						if "icon" in feed_channel_info:
							footer_icon_url = feed_channel_info["icon"]
						if not footer_icon_url and "logo" in feed_channel_info:
							footer_icon_url = feed_channel_info["logo"]
						if not footer_icon_url and "image" in feed_channel_info:
							feed_image = feed_channel_info["image"]
							if "href" in feed_image:
								footer_icon_url = feed_image["href"]
						if not footer_icon_url:
							parsed_text = BeautifulSoup(feed_text, "lxml")
							image_parsed = getattr(parsed_text, "image")
							if image_parsed:
								image_parsed_values = list(image_parsed.attrs.values())
								if image_parsed_values:
									footer_icon_url = image_parsed_values[0]
						embed.set_footer(text = feed_info.feed.title, icon_url = footer_icon_url)
						for text_channel_id, feeds in self.feeds_following.items():
							if feed in feeds:
								text_channel = self.bot.get_channel(int(text_channel_id))
								if text_channel:
									try:
										await text_channel.send(embed = embed)
									except discord.Forbidden:
										pass
								# TODO: Remove text channel data if now non-existent
				except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as e:
					error_message = "{}RSS Task Connection Error @ ".format(self.bot.console_message_prefix)
					error_message += "{}: ".format(datetime.datetime.now().time().isoformat())
					error_message += "{}: {}".format(type(e).__name__, e)
					if len(error_message) > self.bot.console_line_limit - len(feed) - 9:
						# 9 = length of " (feed: )"
						error_message += '\n'
					print(error_message + " (feed: {})".format(feed))
					await asyncio.sleep(10)
					# TODO: Add variable for sleep time
					'''
					except asyncio.CancelledError:
						print("{}RSS Task Cancelled @ {}".format(self.bot.console_message_prefix, datetime.datetime.now().time().isoformat()))
						return
					'''
					# TODO: Handle canceled error/task cleanup
				except Exception as e:
					print("Exception in RSS Task", file = sys.stderr)
					traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
					logging.errors_logger.error("Uncaught RSS Task exception\n", exc_info = (type(e), e, e.__traceback__))
					print(" (feed: {})".format(feed))
					await asyncio.sleep(60)
			self.unique_feeds_following = self.new_unique_feeds_following.copy()

