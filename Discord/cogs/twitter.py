
import discord
from discord.ext import commands

import json
import tweepy

import credentials
from modules import utilities
from utilities import checks
import clients

def setup(bot):
	bot.add_cog(Twitter(bot))

class TwitterStreamListener(tweepy.StreamListener):
	
	def __init__(self, bot):
		super().__init__()
		self.bot = bot
		self.stream = tweepy.Stream(auth = clients.twitter_api.auth, listener = self)
		self.feeds = {}
	
	def __del__(self):
		self.stream.disconnect()
	
	def start_feeds(self, feeds):
		self.feeds = feeds
		self.stream.filter(follow = set([id for feeds in self.feeds.values() for id in feeds]), **{"async" : "True"})
	
	def add_feed(self, channel, handle):
		self.feeds[channel.id] = self.feeds.get(channel.id, []) + [clients.twitter_api.get_user(handle).id_str]
		self.stream.disconnect()
		self.stream.filter(follow = set([id for feeds in self.feeds.values() for id in feeds]), **{"async" : "True"})
	
	def remove_feed(self, channel, handle):
		self.feeds[channel.id].remove(clients.twitter_api.get_user(handle).id_str)
		self.stream.disconnect()
		self.stream.filter(follow = set([id for feeds in self.feeds.values() for id in feeds]), **{"async" : "True"})
	
	def on_status(self, status):
		# print(status.text)
		if status.user.id_str in set([id for feeds in self.feeds.values() for id in feeds]):
			for channel_id, channel_feeds in self.feeds.items():
				if status.user.id_str in channel_feeds:
					embed = discord.Embed(title = '@' + status.user.screen_name, url = "https://twitter.com/{}/status/{}".format(status.user.screen_name, status.id), description = status.text, timestamp = status.created_at, color = 0x00ACED)
					embed.set_footer(text = status.user.name, icon_url = status.user.profile_image_url)
					channel = self.bot.get_channel(channel_id)
					if channel:
						self.bot.loop.create_task(self.bot.send_message(channel, embed = embed))
	
	def on_error(self, status_code):
		print("Twitter Error: {}".format(status_code))
		return False

class Twitter:
	
	def __init__(self, bot):
		self.bot = bot
		self.stream_listener = TwitterStreamListener(bot)
		utilities.create_file("twitter_feeds", content = {"channels" : {}})
		with open("data/twitter_feeds.json", 'r') as feeds_file:
			self.feeds_info = json.load(feeds_file)
		self.task = self.bot.loop.create_task(self.start_twitter_feeds())
	
	def __unload(self):
		self.stream_listener.stream.disconnect()
		self.task.cancel()
	
	@commands.group(invoke_without_command = True)
	@checks.is_permitted()
	async def twitter(self):
		'''Twitter'''
		pass
	
	@twitter.command(name = "status", pass_context = True)
	@checks.not_forbidden()
	async def twitter_status(self, ctx, handle : str):
		'''Get twitter status'''
		tweet = clients.twitter_api.user_timeline(handle, count = 1)[0]
		embed = discord.Embed(title = '@' + tweet.user.screen_name, url = "https://twitter.com/{}/status/{}".format(tweet.user.screen_name, tweet.id), description = tweet.text, timestamp = tweet.created_at, color = 0x00ACED)
		avatar = ctx.message.author.default_avatar_url if not ctx.message.author.avatar else ctx.message.author.avatar_url
		embed.set_author(name = ctx.message.author.display_name, icon_url = avatar)
		embed.set_footer(text = tweet.user.name, icon_url = tweet.user.profile_image_url)
		await self.bot.say(embed = embed)
	
	@twitter.command(name = "add", aliases = ["addhandle", "handleadd"], pass_context = True)
	@checks.is_permitted()
	async def twitter_add(self, ctx, handle : str):
		'''Add a Twitter handle to a text channel'''
		if handle in self.feeds_info["channels"].get(ctx.message.channel.id, {}).get("handles", []):
			await self.bot.embed_reply(":no_entry: This text channel is already following that Twitter handle")
			return
		try:
			self.stream_listener.add_feed(ctx.message.channel, handle)
		except tweepy.error.TweepError as e:
			await self.bot.embed_reply(":no_entry: Error: {}".format(e))
			return
		if ctx.message.channel.id in self.feeds_info["channels"]:
			self.feeds_info["channels"][ctx.message.channel.id]["handles"].append(handle)
		else:
			self.feeds_info["channels"][ctx.message.channel.id] = {"name" : ctx.message.channel.name, "handles" : [handle]}
		with open("data/twitter_feeds.json", 'w') as feeds_file:
			json.dump(self.feeds_info, feeds_file, indent = 4)
		await self.bot.embed_reply("Added the Twitter handle, [`{0}`](https://twitter.com/{0}), to this text channel".format(handle))
	
	@twitter.command(name = "remove", aliases = ["delete", "removehandle", "handleremove", "deletehandle", "handledelete"], pass_context = True)
	@checks.is_permitted()
	async def twitter_remove(self, ctx, handle : str):
		'''Remove a Twitter handle from a text channel'''
		try:
			self.feeds_info["channels"].get(ctx.message.channel.id, {}).get("handles", []).remove(handle)
		except ValueError:
			await self.bot.embed_reply(":no_entry: This text channel isn't following that Twitter handle")
		else:
			with open("data/twitter_feeds.json", 'w') as feeds_file:
				json.dump(self.feeds_info, feeds_file, indent = 4)
			self.stream_listener.remove_feed(ctx.message.channel, handle)
			await self.bot.embed_reply("Removed the Twitter handle, [`{0}`](https://twitter.com/{0}), from this text channel.".format(handle))

	@twitter.command(aliases = ["handle", "feeds", "feed", "list"], pass_context = True)
	@checks.not_forbidden()
	async def handles(self, ctx):
		'''Show Twitter handles being followed in a text channel'''
		await self.bot.embed_reply('\n'.join(self.feeds_info["channels"].get(ctx.message.channel.id, {}).get("handles", [])))
	
	async def start_twitter_feeds(self):
		await self.bot.wait_until_ready()
		feeds = {}
		for channel_id, channel_info in self.feeds_info["channels"].items():
			for handle in channel_info["handles"]:
				feeds[channel_id] = feeds.get(channel_id, []) + [clients.twitter_api.get_user(handle).id_str]
		self.stream_listener.start_feeds(feeds)

