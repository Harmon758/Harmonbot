
import discord
from discord.ext import commands

import asyncio
from bs4 import BeautifulSoup
import datetime
import dateutil.parser
import feedparser
import json
import time

from modules import utilities
from utilities import checks
from clients import bot_color

def setup(bot):
	bot.add_cog(RSS(bot))

class RSS:
	
	def __init__(self, bot):
		self.bot = bot
		utilities.create_file("rss_feeds", content = {"channels" : []})
		with open("data/rss_feeds.json", 'r') as feeds_file:
			self.feeds_info = json.load(feeds_file)
	
	@commands.group(invoke_without_command = True)
	@checks.is_server_owner()
	async def rss(self):
		pass
	
	@rss.command(name = "add", aliases = ["addfeed", "feedadd"], pass_context = True)
	@checks.is_server_owner()
	async def rss_add(self, ctx, url : str):
		'''Add a feed to a channel'''
		channel = discord.utils.find(lambda c: c["id"] == ctx.message.channel.id, self.feeds_info["channels"])
		if channel:
			channel["feeds"].append(url)
		else:
			self.feeds_info["channels"].append({"name" : ctx.message.channel.name, "id" : ctx.message.channel.id, "feeds" : [url]})
		with open("data/rss_feeds.json", 'w') as feeds_file:
			json.dump(self.feeds_info, feeds_file, indent = 4)
		await self.bot.embed_reply("The feed, {}, has been added to this channel".format(url))

	@rss.command(name = "remove", aliases = ["delete", "removefeed", "feedremove", "deletefeed", "feeddelete"], pass_context = True)
	@checks.is_server_owner()
	async def rss_remove(self, ctx, url : str):
		'''Remove a feed from a channel'''
		for channel in self.feeds_info["channels"]:
			if ctx.message.channel.id == channel["id"]:
				for feed in channel["feeds"]:
					if feed == url:
						channel["feeds"].remove(feed)
						with open("data/rss_feeds.json", 'w') as feeds_file:
							json.dump(self.feeds_info, feeds_file, indent = 4)
						await self.bot.embed_reply("The feed, {}, has been removed from this channel".format(url))
						return

	@rss.command(aliases = ["feed"], pass_context = True)
	@checks.not_forbidden()
	async def feeds(self, ctx):
		'''Show feeds being followed in this channel'''
		for channel in self.feeds_info["channels"]:
			if ctx.message.channel.id == channel["id"]:
				await self.bot.embed_reply("\n".join(channel["feeds"]))
	
	async def check_rss_feeds(self):
		try:
			await self.bot.wait_until_ready()
			while not self.bot.is_closed:
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
									embed = discord.Embed(title = title, url = item.link, description = description, timestamp = datetime.datetime.utcnow(), color = bot_color) # timestamp = published_time ?
									embed.set_footer(text = feed_info.feed.title, icon_url = feed_info.feed.get("icon", discord.Embed.Empty))
									await self.bot.send_message(self.bot.get_channel(channel["id"]), embed = embed)
								elif time_difference.total_seconds() < 0:
									# print(feed)
									pass
							except Exception as e:
								print("RSS Exception: " + str(e))
				elapsed = time.time() - start
				# print("Checked feeds in: {0} sec.".format(str(elapsed)))
				await asyncio.sleep(60 - elapsed)
		except asyncio.CancelledError:
			return

