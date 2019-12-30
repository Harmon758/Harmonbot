
import discord
from discord.ext import commands, tasks

import asyncio
import datetime
import functools
import html
import io
import logging
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

from utilities import checks

errors_logger = logging.getLogger("errors")

def setup(bot):
	bot.add_cog(RSS(bot))

class RSS(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		
		# Generate tzinfos
		self.tzinfos = {}
		for timezone_abbreviation in ("EDT", "EST"):
			matching_timezones = list(filter(lambda t: datetime.datetime.now(pytz.timezone(t)).strftime("%Z") == timezone_abbreviation, pytz.common_timezones))
			matching_utc_offsets = set(datetime.datetime.now(pytz.timezone(t)).strftime("%z") for t in matching_timezones)
			if len(matching_utc_offsets) == 1:
				self.tzinfos[timezone_abbreviation] = dateutil.tz.gettz(matching_timezones[0])
		
		self.check_rss_feeds.start()
	
	def cog_unload(self):
		self.check_rss_feeds.cancel()
	
	async def inititalize_database(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS rss")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS rss.feeds (
				channel_id		BIGINT, 
				feed			TEXT, 
				last_checked	TIMESTAMPTZ, 
				ttl				INT, 
				PRIMARY KEY		(channel_id, feed)
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS rss.entries (
				entry			TEXT, 
				feed			TEXT, 
				PRIMARY KEY		(entry, feed)
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS rss.errors (
				timestamp		TIMESTAMPTZ PRIMARY KEY DEFAULT NOW(), 
				feed			TEXT, 
				type			TEXT, 
				message			TEXT
			)
			"""
		)
	
	@commands.group(aliases = ["feed"], invoke_without_command = True, case_insensitive = True)
	@checks.is_permitted()
	async def rss(self, ctx):
		'''RSS'''
		await ctx.send_help(ctx.command)
	
	@rss.command(name = "add")
	@checks.is_permitted()
	async def rss_add(self, ctx, url : str):
		'''Add a feed to a channel'''
		following = await ctx.bot.db.fetchval(
			"""
			SELECT EXISTS (
				SELECT FROM rss.feeds
				WHERE channel_id = $1 AND feed = $2
			)
			""", 
			ctx.channel.id, url
		)
		if following:
			return await ctx.embed_reply(":no_entry: This text channel is already following that feed")
		async with ctx.bot.aiohttp_session.get(url) as resp:
			feed_text = await resp.text()
		# TODO: Handle issues getting URL
		partial = functools.partial(feedparser.parse, io.BytesIO(feed_text.encode("UTF-8")), 
																	response_headers = {"Content-Location": url})
		feed_info = await self.bot.loop.run_in_executor(None, partial)
		# Still necessary to run in executor?
		# TODO: Handle if feed already being followed elsewhere
		ttl = None
		if "ttl" in feed_info.feed:
			ttl = int(feed_info.feed.ttl)
		for entry in feed_info.entries:
			await ctx.bot.db.execute(
				"""
				INSERT INTO rss.entries (entry, feed)
				VALUES ($1, $2)
				ON CONFLICT (entry, feed) DO NOTHING
				""", 
				entry.id, url
			)
		await ctx.bot.db.execute(
			"""
			INSERT INTO rss.feeds (channel_id, feed, last_checked, ttl)
			VALUES ($1, $2, NOW(), $3)
			""", 
			ctx.channel.id, url, ttl
		)
		await ctx.embed_reply(f"The feed, {url}, has been added to this channel")

	@rss.command(name = "remove", aliases = ["delete"])
	@checks.is_permitted()
	async def rss_remove(self, ctx, url : str):
		'''Remove a feed from a channel'''
		deleted = await ctx.bot.db.fetchval(
			"""
			DELETE FROM rss.feeds
			WHERE channel_id = $1 AND feed = $2
			RETURNING *
			""", 
			ctx.channel.id, url
		)
		if not deleted:
			return await ctx.embed_reply(":no_entry: This channel isn't following that feed")
		await ctx.embed_reply(f"The feed, {url}, has been removed from this channel")

	@rss.command(aliases = ["feed"])
	@checks.not_forbidden()
	async def feeds(self, ctx):
		'''Show feeds being followed in this channel'''
		records = await ctx.bot.db.fetch("SELECT feed FROM rss.feeds WHERE channel_id = $1", ctx.channel.id)
		await ctx.embed_reply('\n'.join(record["feed"] for record in records))
	
	# R/PT0S
	@tasks.loop()
	async def check_rss_feeds(self):
		records = await self.bot.db.fetch(
			"""
			SELECT DISTINCT ON (feed) feed, last_checked, ttl
			FROM rss.feeds
			ORDER BY feed, last_checked
			"""
		)
		if not records:
			await asyncio.sleep(60)
		for record in records:
			feed = record["feed"]
			if record["ttl"] and datetime.datetime.now(datetime.timezone.utc) < record["last_checked"] + datetime.timedelta(minutes = record["ttl"]):
				continue
			try:
				async with self.bot.aiohttp_session.get(feed) as resp:
					feed_text = await resp.text()
				try:
					feed_info = await self.bot.loop.run_in_executor(None, functools.partial(feedparser.parse, io.BytesIO(feed_text.encode("UTF-8")), response_headers = {"Content-Location": feed}))
				# Still necessary to run in executor?
				except RuntimeError as e:
					# Handle RuntimeError: generator raised StopIteration in feedparser _gen_georss_coords
					# https://github.com/kurtmckee/feedparser/issues/130
					# Wait for feedparser release with fix
					# https://github.com/kurtmckee/feedparser/pull/131
					# Update to feedparser@develop?
					if str(e) == "generator raised StopIteration":
						continue
					raise
				ttl = None
				if "ttl" in feed_info.feed:
					ttl = int(feed_info.feed.ttl)
				await self.bot.db.execute(
					"""
					UPDATE rss.feeds
					SET last_checked = NOW(), 
						ttl = $1
					WHERE feed = $2
					""", 
					ttl, feed
				)
				for entry in feed_info.entries:
					if "id" not in entry:
						continue
					inserted = await self.bot.db.fetchrow(
						"""
						INSERT INTO rss.entries (entry, feed)
						VALUES ($1, $2)
						ON CONFLICT DO NOTHING
						RETURNING *
						""", 
						entry.id, feed
					)
					if not inserted:
						continue
					# Get timestamp
					## if "published_parsed" in entry:
					##  timestamp = datetime.datetime.fromtimestamp(time.mktime(entry.published_parsed))
					### inaccurate
					if "published" in entry and entry.published:
						timestamp = dateutil.parser.parse(entry.published, tzinfos = self.tzinfos)
					elif "updated" in entry:  # and entry.updated necessary?; check updated first?
						timestamp = dateutil.parser.parse(entry.updated, tzinfos = self.tzinfos)
					else:
						timestamp = discord.Embed.Empty
					# Get and set description, title, url + set timestamp
					description = entry.get("summary")
					if not description and "content" in entry:
						description = entry["content"][0].get("value")
					if description:
						description = BeautifulSoup(description, "lxml").get_text(separator = '\n')
						description = re.sub(r"\n\s*\n", '\n', description)
						if len(description) > self.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
							space_index = description.rfind(' ', 0, self.bot.EDCL - 3)
							# EDCL: Embed Description Character Limit
							description = description[:space_index] + "..."
					title = textwrap.shorten(entry.get("title"), width = self.bot.ETiCL, placeholder = "...")
					# ETiCL: Embed Title Character Limit
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
					channel_records = await self.bot.db.fetch("SELECT channel_id FROM rss.feeds WHERE feed = $1", feed)
					for record in channel_records:
						text_channel = self.bot.get_channel(record["channel_id"])
						if text_channel:
							try:
								await text_channel.send(embed = embed)
							except discord.Forbidden:
								pass
							except discord.HTTPException as e:
								if e.status == 400 and e.code == 50035:
									if "In embed.url: Not a well formed URL." in e.text:
										embed.url = discord.Embed.Empty
									if "In embed.thumbnail.url: Not a well formed URL." in e.text:
										embed.set_thumbnail(url = "")
									await text_channel.send(embed = embed)
								else:
									raise
						# TODO: Remove text channel data if now non-existent
			except (aiohttp.ClientConnectionError, aiohttp.ClientPayloadError, 
					aiohttp.TooManyRedirects, asyncio.TimeoutError, 
					UnicodeDecodeError) as e:
				await self.bot.db.execute(
					"""
					INSERT INTO rss.errors (feed, type, message)
					VALUES ($1, $2, $3)
					""", 
					feed, type(e).__name__, str(e)
				)
				# Print error?
				await asyncio.sleep(10)
				# TODO: Add variable for sleep time
				# TODO: Remove persistently erroring feed or exponentially backoff?
			except Exception as e:
				print("Exception in RSS Task", file = sys.stderr)
				traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
				errors_logger.error("Uncaught RSS Task exception\n", exc_info = (type(e), e, e.__traceback__))
				print(f" (feed: {feed})")
				await asyncio.sleep(60)
	
	@check_rss_feeds.before_loop
	async def before_check_rss_feeds(self):
		await self.inititalize_database()
		await self.bot.wait_until_ready()
	
	@check_rss_feeds.after_loop
	async def after_check_rss_feeds(self):
		print(f"{self.bot.console_message_prefix}RSS task cancelled @ {datetime.datetime.now().isoformat()}")

