
import discord
from discord.ext import commands

import asyncio
import html
import logging
import sys
import traceback

from more_itertools import chunked
import tweepy
import tweepy.asynchronous

from utilities import checks

errors_logger = logging.getLogger("errors")

async def setup(bot):
	await bot.add_cog(Twitter(bot))

class TwitterStream(tweepy.asynchronous.AsyncStream):
	
	def __init__(self, bot):
		super().__init__(
			bot.TWITTER_CONSUMER_KEY, bot.TWITTER_CONSUMER_SECRET,
			bot.TWITTER_ACCESS_TOKEN, bot.TWITTER_ACCESS_TOKEN_SECRET
		)
		self.bot = bot
		self.feeds = {}
		self.unique_feeds = set()
		self.reconnect_ready = asyncio.Event()
		self.reconnect_ready.set()
		self.reconnecting = False
	
	async def start_feeds(self, *, feeds = None):
		if self.reconnecting:
			return await self.reconnect_ready.wait()
		self.reconnecting = True
		await self.reconnect_ready.wait()
		self.reconnect_ready.clear()
		if feeds:
			self.feeds = feeds
			self.unique_feeds = set(id for feeds in self.feeds.values() for id in feeds)
		if self.task:
			self.disconnect()
			await self.task
		if self.feeds:
			self.filter(follow = self.unique_feeds)
		self.bot.loop.call_later(120, self.reconnect_ready.set)
		self.reconnecting = False
	
	async def add_feed(self, channel, handle):
		user_id = self.bot.twitter_api.get_user(screen_name = handle).id_str
		self.feeds[channel.id] = self.feeds.get(channel.id, []) + [user_id]
		if user_id not in self.unique_feeds:
			self.unique_feeds.add(user_id)
			await self.start_feeds()
	
	async def remove_feed(self, channel, handle):
		self.feeds[channel.id].remove(self.bot.twitter_api.get_user(screen_name = handle).id_str)
		self.unique_feeds = set(id for feeds in self.feeds.values() for id in feeds)
		await self.start_feeds()  # Necessary?
	
	async def on_status(self, status):
		if status.in_reply_to_status_id:
			# Ignore replies
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
						try:
							await channel.send(embed = embed)
						except discord.Forbidden:
							# TODO: Handle unable to send embeds/messages in text channel
							self.bot.print(f"Twitter Stream: Missing permissions to send embed in #{channel.name} in {channel.guild.name}")
						except discord.DiscordServerError as e:
							self.bot.print(f"Twitter Stream Discord Server Error: {e}")
	
	async def on_request_error(self, status_code):
		self.bot.print(f"Twitter Error: {status_code}")

class Twitter(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.blacklisted_handles = []
		self.stream = TwitterStream(bot)
	
	async def cog_load(self):
		# Initialize database
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
		# Initialize blacklist
		try:
			response = await self.bot.twitter_client.get_me(
				user_fields = ["protected"]
			)
			account = response.data
			if account.protected:
				self.blacklisted_handles.append(
					account.username.lower()
				)
			# TODO: Handle more than 1000 friends/following
			response = await self.bot.twitter_client.get_users_following(
				account.id, max_results = 1000, user_fields = ["protected"],
				user_auth = True
			)
			following = response.data
			for friend in following:
				if friend.protected:
					self.blacklisted_handles.append(friend.username.lower())
		except (AttributeError, tweepy.TweepyException) as e:
			self.bot.print(f"Failed to initialize Twitter cog blacklist: {e}")
		# Start stream
		self.task = self.bot.loop.create_task(
			self.start_twitter_feeds(), name = "Start Twitter Stream"
		)
	
	def cog_unload(self):
		if self.stream:
			self.stream.disconnect()
		self.task.cancel()
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def twitter(self, ctx):
		'''Twitter'''
		await ctx.send_help(ctx.command)
	
	@twitter.command(name = "status")
	@checks.not_forbidden()
	async def twitter_status(self, ctx, handle: str, replies: bool = False, retweets: bool = False):
		'''
		Get twitter status
		Excludes replies and retweets by default
		Limited to 3200 most recent Tweets
		'''
		tweet = None
		if handle.lower().strip('@') in self.blacklisted_handles:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Unauthorized")
		try:
			for status in tweepy.Cursor(self.bot.twitter_api.user_timeline, screen_name = handle, 
										exclude_replies = not replies, include_rts = retweets, 
										tweet_mode = "extended", count = 200).items():
				tweet = status
				break
		except tweepy.NotFound:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: @{handle} not found")
		except tweepy.TweepyException as e:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
		if not tweet:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Status not found")
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
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def twitter_add(self, ctx, handle: str):
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
			await self.stream.add_feed(ctx.channel, handle)
		except tweepy.TweepyException as e:
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
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def twitter_remove(self, ctx, handle: str):
		'''
		Remove a Twitter handle from a text channel
		A delay of up to 2 min. is possible due to Twitter rate limits
		'''
		deleted = await ctx.bot.db.fetchval(
			"""
			DELETE FROM twitter.handles
			WHERE channel_id = $1 AND handle = $2
			RETURNING *
			""", 
			ctx.channel.id, handle
		)
		if not deleted:
			return await ctx.embed_reply(":no_entry: This text channel isn't following that Twitter handle")
		message = await ctx.embed_reply(":hourglass: Please wait")
		await self.stream.remove_feed(ctx.channel, handle)
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
		await ctx.embed_reply(
			'\n'.join(sorted(
				[record["handle"] for record in records],
				key = str.casefold
			))
		)
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
	
	async def start_twitter_feeds(self):
		await self.bot.wait_until_ready()
		feeds = {}
		try:
			records = await self.bot.db.fetch("SELECT * FROM twitter.handles")
			usernames = {}
			for record in records:
				usernames[record["handle"].lstrip('@').lower()] = (
					usernames.get(record["handle"].lstrip('@').lower(), []) +
					[record["channel_id"]]
				)
			for usernames_chunk in chunked(usernames, 100):
				response = await self.bot.twitter_client.get_users(
					usernames = usernames_chunk
				)
				for user in response.data:
					for channel_id in usernames[user.username.lower()]:
						feeds[channel_id] = (
							feeds.get(channel_id, []) + [user.id]
						)
			await self.stream.start_feeds(feeds = feeds)
		except Exception as e:
			print("Exception in Twitter Task", file = sys.stderr)
			traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
			errors_logger.error("Uncaught Twitter Task exception\n", exc_info = (type(e), e, e.__traceback__))
			return

