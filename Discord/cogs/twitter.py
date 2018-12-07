
import discord
from discord.ext import commands

import asyncio
import html
import json
import sys
import traceback
import tweepy

import clients
import credentials
from modules import logging
from utilities import checks

def setup(bot):
	bot.add_cog(Twitter(bot))

class TwitterStreamListener(tweepy.StreamListener):
	
	def __init__(self, bot):
		super().__init__()
		self.bot = bot
		self.stream = None
		self.feeds = {}
		self.reconnect_ready = asyncio.Event()
		self.reconnect_ready.set()
		self.reconnecting = False
	
	def __del__(self):
		self.stream.disconnect()
	
	async def start_feeds(self, *, feeds = None):
		if self.reconnecting:
			await self.reconnect_ready.wait()
			return
		self.reconnecting = True
		await self.reconnect_ready.wait()
		self.reconnect_ready.clear()
		if feeds: self.feeds = feeds
		if self.stream: self.stream.disconnect()
		self.stream = tweepy.Stream(auth = self.bot.twitter_api.auth, listener = self)
		if self.feeds: self.stream.filter(follow = set([id for feeds in self.feeds.values() for id in feeds]), **{"is_async" : "True"})
		self.bot.loop.call_later(120, self.reconnect_ready.set)
		self.reconnecting = False
	
	async def add_feed(self, channel, handle):
		self.feeds[str(channel.id)] = self.feeds.get(str(channel.id), []) + [self.bot.twitter_api.get_user(handle).id_str]
		# TODO: Check if stream already following
		await self.start_feeds()
	
	async def remove_feed(self, channel, handle):
		self.feeds[str(channel.id)].remove(self.bot.twitter_api.get_user(handle).id_str)
		await self.start_feeds() # necessary?
	
	def on_status(self, status):
		## print(status.text)
		if not status.in_reply_to_status_id and status.user.id_str in set([id for feeds in self.feeds.values() for id in feeds]):
			# TODO: Settings for including replies, retweets, etc.
			for channel_id, channel_feeds in self.feeds.items():
				if status.user.id_str in channel_feeds:
					embed = discord.Embed(title = '@' + status.user.screen_name, url = f"https://twitter.com/{status.user.screen_name}/status/{status.id}", description = status.text, timestamp = status.created_at, color = self.bot.twitter_color)
					embed.set_author(name = status.user.name, icon_url = status.user.profile_image_url)
					embed.set_footer(text = "Twitter", icon_url = self.bot.twitter_icon_url)
					channel = self.bot.get_channel(int(channel_id))
					if channel:
						self.bot.loop.create_task(channel.send(embed = embed))
	
	def on_error(self, status_code):
		print("Twitter Error: {}".format(status_code))
		return False

class Twitter:
	
	def __init__(self, bot):
		self.bot = bot
		self.stream_listener = TwitterStreamListener(bot)
		clients.create_file("twitter_feeds", content = {"channels" : {}})
		with open(clients.data_path + "/twitter_feeds.json", 'r') as feeds_file:
			self.feeds_info = json.load(feeds_file)
		self.task = self.bot.loop.create_task(self.start_twitter_feeds())
	
	def __unload(self):
		self.stream_listener.stream.disconnect()
		self.task.cancel()
	
	@commands.group(invoke_without_command = True)
	@checks.is_permitted()
	async def twitter(self, ctx):
		'''Twitter'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@twitter.command(name = "status")
	@checks.not_forbidden()
	async def twitter_status(self, ctx, handle : str):
		'''Get twitter status'''
		try:
			tweet = self.bot.twitter_api.user_timeline(handle, count = 1, tweet_mode = "extended")[0]
		except tweepy.error.TweepError as e:
			if e.api_code == 34:
				return await ctx.embed_reply(f":no_entry: Error: @{handle} not found")
			else:
				return await ctx.embed_reply(f":no_entry: Error: {e}")
		text = tweet.full_text
		mentions = {}
		for mention in tweet.entities["user_mentions"]:
			mentions[text[mention["indices"][0]:mention["indices"][1]]] = mention["screen_name"]
		for mention, screen_name in mentions.items():
			text = text.replace(mention, f"[{mention}](https://twitter.com/{screen_name})")
		for hashtag in tweet.entities["hashtags"]:
			text = text.replace('#' + hashtag["text"], 
								f"[#{hashtag['text']}](https://twitter.com/hashtag/{hashtag['text']})")
		for symbol in tweet.entities["symbols"]:
			text = text.replace('$' + symbol["text"],
								f"[${symbol['text']}](https://twitter.com/search?q=${symbol['text']})")
		for url in tweet.entities["urls"]:
			text = text.replace(url["url"], url["expanded_url"])
		image_url = None
		if hasattr(tweet, "extended_entities") and tweet.extended_entities["media"][0]["type"] == "photo":
			image_url = tweet.extended_entities["media"][0]["media_url_https"]
			text = text.replace(tweet.extended_entities["media"][0]["url"], "")
		await ctx.embed_reply(html.unescape(text), title = '@' + tweet.user.screen_name, image_url = image_url, 
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
		if handle in self.feeds_info["channels"].get(str(ctx.channel.id), {}).get("handles", []):
			await ctx.embed_reply(":no_entry: This text channel is already following that Twitter handle")
			return
		message = await ctx.embed_reply(":hourglass: Please wait")
		embed = message.embeds[0]
		try:
			await self.stream_listener.add_feed(ctx.channel, handle)
		except tweepy.error.TweepError as e:
			embed.description = ":no_entry: Error: {}".format(e)
			await message.edit(embed = embed)
			return
		if str(ctx.channel.id) in self.feeds_info["channels"]:
			self.feeds_info["channels"][str(ctx.channel.id)]["handles"].append(handle)
		else:
			self.feeds_info["channels"][str(ctx.channel.id)] = {"name" : ctx.channel.name, "handles" : [handle]}
		with open(clients.data_path + "/twitter_feeds.json", 'w') as feeds_file:
			json.dump(self.feeds_info, feeds_file, indent = 4)
		embed.description = "Added the Twitter handle, [`{0}`](https://twitter.com/{0}), to this text channel".format(handle)
		await message.edit(embed = embed)
	
	@twitter.command(name = "remove", aliases = ["delete", "removehandle", "handleremove", "deletehandle", "handledelete"])
	@checks.is_permitted()
	async def twitter_remove(self, ctx, handle : str):
		'''
		Remove a Twitter handle from a text channel
		A delay of up to 2 min. is possible due to Twitter rate limits
		'''
		try:
			self.feeds_info["channels"].get(str(ctx.channel.id), {}).get("handles", []).remove(handle)
		except ValueError:
			await ctx.embed_reply(":no_entry: This text channel isn't following that Twitter handle")
		else:
			with open(clients.data_path + "/twitter_feeds.json", 'w') as feeds_file:
				json.dump(self.feeds_info, feeds_file, indent = 4)
			message = await ctx.embed_reply(":hourglass: Please wait")
			await self.stream_listener.remove_feed(ctx.channel, handle)
			embed = message.embeds[0]
			embed.description = "Removed the Twitter handle, [`{0}`](https://twitter.com/{0}), from this text channel.".format(handle)
			await message.edit(embed = embed)

	@twitter.command(aliases = ["handle", "feeds", "feed", "list"])
	@checks.not_forbidden()
	async def handles(self, ctx):
		'''Show Twitter handles being followed in a text channel'''
		await ctx.embed_reply('\n'.join(self.feeds_info["channels"].get(str(ctx.channel.id), {}).get("handles", [])))
		# TODO: Add message if none
	
	# TODO: move to on_ready
	async def start_twitter_feeds(self):
		await self.bot.wait_until_ready()
		feeds = {}
		try:
			for channel_id, channel_info in self.feeds_info["channels"].items():
				for handle in channel_info["handles"]:
					try:
						feeds[channel_id] = feeds.get(channel_id, []) + [self.bot.twitter_api.get_user(handle).id_str]
					except tweepy.error.TweepError as e:
						if e.api_code == 50:
							# User not found
							continue
						else:
							raise e
			await self.stream_listener.start_feeds(feeds = feeds)
		except Exception as e:
			print("Exception in Twitter Task", file = sys.stderr)
			traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
			logging.errors_logger.error("Uncaught Twitter Task exception\n", exc_info = (type(e), e, e.__traceback__))
			return

