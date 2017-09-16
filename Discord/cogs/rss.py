
import discord
from discord.ext import commands

import asyncio
from bs4 import BeautifulSoup
import datetime
import dateutil.parser
import feedparser
import json
import sys
import time
import traceback

import clients
from utilities import checks
from modules import logging

def setup(bot):
	bot.add_cog(RSS(bot))

class RSS:
	
	def __init__(self, bot):
		self.bot = bot
		clients.create_file("rss_feeds", content = {"channels" : []})
		with open(clients.data_path + "/rss_feeds.json", 'r') as feeds_file:
			self.feeds_info = json.load(feeds_file)
		self.task = self.bot.loop.create_task(self.check_rss_feeds())
	
	def __unload(self):
		self.task.cancel()
	
	@commands.group(invoke_without_command = True)
	@checks.is_permitted()
	async def rss(self, ctx):
		'''RSS'''
		pass
	
	@rss.command(name = "add", aliases = ["addfeed", "feedadd"])
	@checks.is_permitted()
	async def rss_add(self, ctx, url : str):
		'''Add a feed to a channel'''
		channel = discord.utils.find(lambda c: c["id"] == ctx.channel.id, self.feeds_info["channels"])
		if channel:
			channel["feeds"].append(url)
		else:
			self.feeds_info["channels"].append({"name": ctx.channel.name, "id": ctx.channel.id, "feeds": [url]})
		with open(clients.data_path + "/rss_feeds.json", 'w') as feeds_file:
			json.dump(self.feeds_info, feeds_file, indent = 4)
		await ctx.embed_reply("The feed, {}, has been added to this channel".format(url))

	@rss.command(name = "remove", aliases = ["delete", "removefeed", "feedremove", "deletefeed", "feeddelete"])
	@checks.is_permitted()
	async def rss_remove(self, ctx, url : str):
		'''Remove a feed from a channel'''
		channel = discord.utils.find(lambda c: c["id"] == ctx.channel.id, self.feeds_info["channels"])
		if not channel or url not in channel["feeds"]:
			await ctx.embed_reply(":no_entry: This channel isn't following that feed")
			return
		channel["feeds"].remove(url)
		with open(clients.data_path + "/rss_feeds.json", 'w') as feeds_file:
			json.dump(self.feeds_info, feeds_file, indent = 4)
		await ctx.embed_reply("The feed, {}, has been removed from this channel".format(url))

	@rss.command(aliases = ["feed"])
	@checks.not_forbidden()
	async def feeds(self, ctx):
		'''Show feeds being followed in this channel'''
		for channel in self.feeds_info["channels"]:
			if ctx.channel.id == channel["id"]:
				await ctx.embed_reply("\n".join(channel["feeds"]))
	
	async def check_rss_feeds(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed:
			try:
				start = time.time()
				for channel in self.feeds_info["channels"]:
					for feed in channel["feeds"]:
						feed_info = await self.bot.loop.run_in_executor(None, feedparser.parse, feed)
						for item in feed_info.entries:
							try:
								if "published" in item:
									published_time = dateutil.parser.parse(item.published)
								elif "updated" in item:
									published_time = dateutil.parser.parse(item.updated)
								else:
									# print(feed)
									continue
								if published_time.tzinfo:
									time_difference = datetime.datetime.now(datetime.timezone.utc) - published_time
								else:
									time_difference = datetime.datetime.utcnow() - published_time
								if 0 <= time_difference.total_seconds() <= 60:
									description = item.get("summary")
									if description:
										description = BeautifulSoup(description).text
										if len(description) > 2048: description = description[:2045] + "..."
									title = item.get("title")
									if len(title) > 256: title = title[:253] + "..."
									embed = discord.Embed(title = title, url = item.link, description = description, timestamp = datetime.datetime.utcnow(), color = self.bot.rss_color) # timestamp = published_time ?
									embed.set_footer(text = feed_info.feed.title, icon_url = feed_info.feed.get("icon", discord.Embed.Empty))
									text_channel = self.bot.get_channel(channel["id"])
									if text_channel:
										await self.bot.send_message(text_channel, embed = embed)
								elif time_difference.total_seconds() < 0:
									# print(feed)
									pass
							except Exception as e:
								print("Exception in RSS Task", file = sys.stderr)
								traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
								logging.errors_logger.error("Uncaught RSS Task exception\n", exc_info = (type(e), e, e.__traceback__))
				elapsed = time.time() - start
				# print("Checked feeds in: {0} sec.".format(str(elapsed)))
				await asyncio.sleep(60 - elapsed)
			except asyncio.CancelledError:
				return

