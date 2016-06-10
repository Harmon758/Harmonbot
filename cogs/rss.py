
from discord.ext import commands

import asyncio
import feedparser
import json
import time

from modules.utilities import *

from utilities import checks

import keys
from client import client

def setup(bot):
	bot.add_cog(RSS())

async def check_rss_feeds():
	await client.wait_until_ready()
	while not client.is_closed:
		with open("data/rss_feeds.json", "r") as feeds_file:
			#feeds_info = await client.loop.run_in_executor(None, json.load, feeds_file)
			feeds_info = json.load(feeds_file)
		start = time.time()
		for channel in feeds_info["channels"]:
			for feed in channel["feeds"]:
				feed_info = await client.loop.run_in_executor(None, feedparser.parse, feed)
				#feed_info = feedparser.parse(feed)
				for item in feed_info.entries:
					try:
						if 0 <= (datetime.datetime.now(datetime.timezone.utc) - dateutil.parser.parse(item.published)).total_seconds() <= 60:
							await client.send_message(discord.utils.get(client.get_all_channels(), id = channel["id"]), feed_info.feed.title + ": " + item.title + "\n<" + item.link + '>')
					except:
						try:
							if 0 <= (datetime.datetime.now(datetime.timezone.utc) - dateutil.parser.parse(item.updated)).total_seconds() <= 60:
								await client.send_message(discord.utils.get(client.get_all_channels(), id = channel["id"]), feed_info.feed.title + ": " + item.title + "\n<" + item.link + '>')
						except:
							pass
		elapsed = time.time() - start
		# print("Checked feeds in: {0} sec.".format(str(elapsed)))
		await asyncio.sleep(60 - elapsed)

class RSS:

	@commands.command(pass_context = True, aliases = ["addrss", "feedadd", "rssadd"])
	@checks.is_server_owner()
	async def addfeed(self, ctx, url : str):
		'''Add a feed to a channel'''
		with open("data/rss_feeds.json", "r") as feeds_file:
			feeds_info = json.load(feeds_file)
		for channel in feeds_info["channels"]:
			if ctx.message.channel.id == channel["id"]:
				channel["feeds"].append(url)
				with open("data/rss_feeds.json", "w") as feeds_file:
					json.dump(feeds_info, feeds_file)
				await client.reply("The feed, " + url + ", has been added to this channel.")
				return
		feeds_info["channels"].append({"name" : ctx.message.channel.name, "id" : ctx.message.channel.id, "feeds" : [url]})
		with open("data/rss_feeds.json", "w") as feeds_file:
			json.dump(feeds_info, feeds_file)
		await client.reply("The feed, " + url + ", has been added to this channel.")

	@commands.command(pass_context = True, aliases = ["removerss", "feedremove", "rssremove, deletefeed, deleterss, rssdelete, feeddelete"])
	@checks.is_server_owner()
	async def removefeed(self, ctx, url : str):
		'''Remove a feed from a channel'''
		with open("data/rss_feeds.json", "r") as feeds_file:
			feeds_info = json.load(feeds_file)
		for channel in feeds_info["channels"]:
			if ctx.message.channel.id == channel["id"]:
				for feed in channel["feeds"]:
					if feed == url:
						channel["feeds"].remove(feed)
						with open("data/rss_feeds.json", "w") as feeds_file:
							json.dump(feeds_info, feeds_file)
						await client.reply("The feed, " + url + ", has been removed from this channel.")
						return

	@commands.command(pass_context = True, aliases = ["rss"])
	async def feeds(self, ctx):
		'''Show feeds being followed in this channel'''
		with open("data/rss_feeds.json", "r") as feeds_file:
			feeds_info = json.load(feeds_file)
		for channel in feeds_info["channels"]:
			if ctx.message.channel.id == channel["id"]:
				feeds = ""
				for feed in channel["feeds"]:
					feeds += "\n" + feed
				await client.reply(feeds)

