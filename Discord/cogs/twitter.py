
import discord
from discord.ext import commands

import asyncio
import functools
import html
import logging
import sys
import traceback

import tweepy
import urllib3

from utilities import checks

errors_logger = logging.getLogger("errors")

def setup(bot):
	bot.add_cog(Twitter(bot))

class TwitterStreamListener(tweepy.StreamListener):
	
	def __init__(self, bot, blacklisted_handles = None):
		super().__init__()
		self.bot = bot
		if blacklisted_handles is None:
			blacklisted_handles = []
		self.blacklisted_handles = blacklisted_handles
		self.stream = None
		self.feeds = {}
		self.unique_feeds = set()
		self.reconnect_ready = asyncio.Event()
		self.reconnect_ready.set()
		self.reconnecting = False
	
	def __del__(self):
		if self.stream:
			self.stream.disconnect()
	
	async def start_feeds(self, *, feeds = None):
		if self.reconnecting:
			return await self.reconnect_ready.wait()
		self.reconnecting = True
		await self.reconnect_ready.wait()
		self.reconnect_ready.clear()
		if feeds:
			self.feeds = feeds
			self.unique_feeds = set(id for feeds in self.feeds.values() for id in feeds)
		if self.stream:
			self.stream.disconnect()
		self.stream = tweepy.Stream(auth = self.bot.twitter_api.auth, listener = self)
		if self.feeds:
			self.stream.filter(follow = self.unique_feeds, is_async = True)
		self.bot.loop.call_later(120, self.reconnect_ready.set)
		self.reconnecting = False
	
	async def add_feed(self, channel, handle):
		user_id = self.bot.twitter_api.get_user(handle).id_str
		self.feeds[channel.id] = self.feeds.get(channel.id, []) + [user_id]
		if user_id not in self.unique_feeds:
			self.unique_feeds.add(user_id)
			await self.start_feeds()
	
	async def remove_feed(self, channel, handle):
		self.feeds[channel.id].remove(self.bot.twitter_api.get_user(handle).id_str)
		self.unique_feeds = set(id for feeds in self.feeds.values() for id in feeds)
		await self.start_feeds()  # Necessary?
	
	def on_status(self, status):
		if status.in_reply_to_status_id:
			# Ignore replies
			return
		if status.user.screen_name.lower() in self.blacklisted_handles:
			return
		if status.user.id_str in self.unique_feeds:
			# TODO: Settings for including replies, retweets, etc.
			for channel_id, channel_feeds in self.feeds.items():
				if status.user.id_str in channel_feeds:
					channel = self.bot.get_channel(channel_id)
					if channel:
						if hasattr(status, "extended_tweet"):
							text = status.extended_tweet["full_text"]
							entities = status.extended_tweet["entities"]
							extended_entities = status.extended_tweet.get("extended_entities")
						else:
							text = status.text
							entities = status.entities
							extended_entities = getattr(status, "extended_entities", None)
						embed = discord.Embed(title = '@' + status.user.screen_name, 
												url = f"https://twitter.com/{status.user.screen_name}/status/{status.id}", 
												description = self.bot.cogs["Twitter"].process_tweet_text(text, entities), 
												timestamp = status.created_at, color = self.bot.twitter_color)
						embed.set_author(name = status.user.name, icon_url = status.user.profile_image_url)
						if extended_entities and extended_entities["media"][0]["type"] == "photo":
							embed.set_image(url = extended_entities["media"][0]["media_url_https"])
							embed.description = embed.description.replace(extended_entities["media"][0]["url"], "")
						embed.set_footer(text = "Twitter", icon_url = self.bot.twitter_icon_url)
						self.bot.loop.create_task(channel.send(embed = embed))
	
	def on_error(self, status_code):
		print(f"Twitter Error: {status_code}")
		return False
	
	def on_exception(self, exception):
		if isinstance(exception, urllib3.exceptions.ReadTimeoutError):
			print(f"{self.bot.console_message_prefix}Twitter stream timed out | Recreating stream..")
			self.bot.loop.create_task(self.start_feeds())
		elif isinstance(exception, urllib3.exceptions.ProtocolError):
			print(f"{self.bot.console_message_prefix}Twitter stream Incomplete Read error | Recreating stream..")
			self.bot.loop.create_task(self.start_feeds())

class Twitter(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.blacklisted_handles = []
		try:
			twitter_account = self.bot.twitter_api.verify_credentials()
			if twitter_account.protected:
				self.blacklisted_handles.append(twitter_account.screen_name.lower())
			# TODO: Handle more than 5000 friends/following
			twitter_friends = self.bot.twitter_api.friends_ids(screen_name = twitter_account.screen_name)
			for interval in range(0, len(twitter_friends), 100):
				some_friends = self.bot.twitter_api.lookup_users(twitter_friends[interval:interval + 100])
				for friend in some_friends:
					if friend.protected:
						self.blacklisted_handles.append(friend.screen_name.lower())
		except tweepy.error.TweepError as e:
			print(f"{self.bot.console_message_prefix}Failed to initialize Twitter cog blacklist: {e}")
		self.stream_listener = TwitterStreamListener(bot, self.blacklisted_handles)
		self.task = self.bot.loop.create_task(self.start_twitter_feeds())
	
	def cog_unload(self):
		if self.stream_listener.stream:
			self.stream_listener.stream.disconnect()
		self.task.cancel()
	
	async def initialize_database(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS twitter")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitter.handles (
				channel_id		BIGINT, 
				handle			TEXT, 
				replies			BOOL, 
				retweets		BOOL, 
				PRIMARY KEY		(channel_id, handle)
			)
			"""
		)
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.is_permitted()
	async def twitter(self, ctx):
		'''Twitter'''
		await ctx.send_help(ctx.command)
	
	@twitter.command(name = "status")
	@checks.not_forbidden()
	async def twitter_status(self, ctx, handle : str, replies : bool = False, retweets : bool = False):
		'''
		Get twitter status
		Excludes replies and retweets by default
		Limited to 3200 most recent Tweets
		'''
		tweet = None
		if handle.lower().strip('@') in self.blacklisted_handles:
			return await ctx.embed_reply(":no_entry: Error: Unauthorized")
		try:
			for status in tweepy.Cursor(self.bot.twitter_api.user_timeline, screen_name = handle, 
										exclude_replies = not replies, include_rts = retweets, 
										tweet_mode = "extended", count = 200).items():
				tweet = status
				break
		except tweepy.error.TweepError as e:
			if e.api_code == 34:
				return await ctx.embed_reply(f":no_entry: Error: @{handle} not found")
			else:
				return await ctx.embed_reply(f":no_entry: Error: {e}")
		if not tweet:
			return await ctx.embed_reply(":no_entry: Error: Status not found")
		text = self.process_tweet_text(tweet.full_text, tweet.entities)
		image_url = None
		if hasattr(tweet, "extended_entities") and tweet.extended_entities["media"][0]["type"] == "photo":
			image_url = tweet.extended_entities["media"][0]["media_url_https"]
			text = text.replace(tweet.extended_entities["media"][0]["url"], "")
		await ctx.embed_reply(text, title = '@' + tweet.user.screen_name, image_url = image_url, 
								title_url = f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}", 
								footer_text = tweet.user.name, footer_icon_url = tweet.user.profile_image_url, 
								timestamp = tweet.created_at, color = self.bot.twitter_color)
	
	@twitter.command(name = "add", aliases = ["addhandle", "handleadd"])
	@checks.is_permitted()
	async def twitter_add(self, ctx, handle : str):
		'''
		Add a Twitter handle to a text channel
		A delay of up to 2 min. is possible due to Twitter rate limits
		'''
		following = await ctx.bot.db.fetchval(
			"""
			SELECT EXISTS (
				SELECT FROM twitter.handles
				WHERE channel_id = $1 AND handle = $2
			)
			""", 
			ctx.channel.id, handle
		)
		if following:
			return await ctx.embed_reply(":no_entry: This text channel is already following that Twitter handle")
		message = await ctx.embed_reply(":hourglass: Please wait")
		embed = message.embeds[0]
		try:
			await self.stream_listener.add_feed(ctx.channel, handle)
		except tweepy.error.TweepError as e:
			embed.description = f":no_entry: Error: {e}"
			return await message.edit(embed = embed)
		await ctx.bot.db.execute(
			"""
			INSERT INTO twitter.handles (channel_id, handle)
			VALUES ($1, $2)
			""", 
			ctx.channel.id, handle
		)
		embed.description = f"Added the Twitter handle, [`{handle}`](https://twitter.com/{handle}), to this text channel"
		await message.edit(embed = embed)
	
	@twitter.command(name = "remove", aliases = ["delete", "removehandle", "handleremove", "deletehandle", "handledelete"])
	@checks.is_permitted()
	async def twitter_remove(self, ctx, handle : str):
		'''
		Remove a Twitter handle from a text channel
		A delay of up to 2 min. is possible due to Twitter rate limits
		'''
		deleted = await ctx.bot.db.execute(
			"""
			DELETE FROM twitter.handles
			WHERE channel_id = $1 AND handle = $2
			""", 
			ctx.channel.id, handle
		)
		if not int(deleted[-1]):
			return await ctx.embed_reply(":no_entry: This text channel isn't following that Twitter handle")
		message = await ctx.embed_reply(":hourglass: Please wait")
		await self.stream_listener.remove_feed(ctx.channel, handle)
		embed = message.embeds[0]
		embed.description = f"Removed the Twitter handle, [`{handle}`](https://twitter.com/{handle}), from this text channel."
		await message.edit(embed = embed)

	@twitter.command(aliases = ["handle", "feeds", "feed", "list"])
	@checks.not_forbidden()
	async def handles(self, ctx):
		'''Show Twitter handles being followed in a text channel'''
		records = await ctx.bot.db.fetch(
			"""
			SELECT handle FROM twitter.handles
			WHERE channel_id = $1
			""", 
			ctx.channel.id
		)
		await ctx.embed_reply('\n'.join(record["handle"] for record in records))
		# TODO: Add message if none
	
	def process_tweet_text(self, text, entities):
		mentions = {}
		for mention in entities["user_mentions"]:
			mentions[text[mention["indices"][0]:mention["indices"][1]]] = mention["screen_name"]
		for mention, screen_name in mentions.items():
			text = text.replace(mention, f"[{mention}](https://twitter.com/{screen_name})")
		for hashtag in entities["hashtags"]:
			text = text.replace('#' + hashtag["text"], 
								f"[#{hashtag['text']}](https://twitter.com/hashtag/{hashtag['text']})")
		for symbol in entities["symbols"]:
			text = text.replace('$' + symbol["text"],
								f"[${symbol['text']}](https://twitter.com/search?q=${symbol['text']})")
		for url in entities["urls"]:
			text = text.replace(url["url"], url["expanded_url"])
		# Remove Variation Selector-16 characters
		# Unescape HTML entities (&gt;, &lt;, &amp;, etc.)
		return html.unescape(text.replace('\uFE0F', ""))
	
	# TODO: move to on_ready
	async def start_twitter_feeds(self):
		await self.initialize_database()
		await self.bot.wait_until_ready()
		feeds = {}
		try:
			async with self.bot.database_connection_pool.acquire() as connection:
				async with connection.transaction():
					# Postgres requires non-scrollable cursors to be created and used in a transaction.
					async for record in connection.cursor("SELECT * FROM twitter.handles"):
						try:
							partial = functools.partial(self.bot.twitter_api.get_user, record["handle"])
							user = await self.bot.loop.run_in_executor(None, partial)
							feeds[record["channel_id"]] = feeds.get(record["channel_id"], []) + [user.id_str]
						except tweepy.error.TweepError as e:
							# TODO: Handle rate limit
							if e.api_code in (50, 63):
								# User not found (50) or suspended (63)
								continue
							raise e
			await self.stream_listener.start_feeds(feeds = feeds)
		except Exception as e:
			print("Exception in Twitter Task", file = sys.stderr)
			traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
			errors_logger.error("Uncaught Twitter Task exception\n", exc_info = (type(e), e, e.__traceback__))
			return

