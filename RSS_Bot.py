
print("Starting up RSS Bot...")

from discord.ext import commands

#import os
#os.environ['PYTHONASYNCIODEBUG'] = '1'

import asyncio
import feedparser
import json
import time
import os

from modules.utilities import *

from utilities import checks

import keys
from client import rss_client as client

#import logging
#logging.basicConfig(level=logging.DEBUG)

@client.event
async def on_ready():
	print("Started up {0} ({1})".format(str(client.user), client.user.id))
	if os.path.isfile("data/rss_restart_channel.json"):
		with open("data/rss_restart_channel.json", "r") as restart_channel_file:
			restart_channel = client.get_channel(json.load(restart_channel_file)["restart_channel"])
		os.remove("data/rss_restart_channel.json")
		await client.send_message(restart_channel, "Restarted.")
	await client.change_status(game = discord.Game(name = "with Harmonbot"))
	await set_streaming_status(client)

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
		# print("RSS Bot | Checked feeds in: {0} sec.".format(str(elapsed)))
		await asyncio.sleep(60 - elapsed)

@client.command(hidden = True)
async def testrss():
	'''Basic test command'''
	await client.say("Hello, World!")

@client.command(hidden = True)
@checks.is_owner()
async def rss_updateavatar():
	'''Update my avatar'''
	with open("data/discord_rss_bot_icon.png", "rb") as avatar_file:
		await client.edit_profile(avatar = avatar_file.read())
	await client.reply("Avatar updated.")

@client.command(pass_context = True, aliases = ["addrss", "feedadd", "rssadd"])
@checks.is_owner()
async def addfeed(ctx, url : str):
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

@client.command(pass_context = True, aliases = ["removerss", "feedremove", "rssremove"])
@checks.is_owner()
async def removefeed(ctx, url : str):
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

@client.command(pass_context = True, aliases = ["rsss"])
async def feeds(ctx):
	'''Show feeds being followed in this channel'''
	with open("data/rss_feeds.json", "r") as feeds_file:
		feeds_info = json.load(feeds_file)
	for channel in feeds_info["channels"]:
		if ctx.message.channel.id == channel["id"]:
			feeds = ""
			for feed in channel["feeds"]:
				feeds += "\n" + feed
			await client.reply(feeds)

@client.command(pass_context = True, hidden = True)
@checks.is_owner()
async def restartrss(ctx):
	'''Restart RSS Bot'''
	await client.say("Restarting...")
	with open("data/rss_restart_channel.json", "x+") as restart_channel_file:
		json.dump({"restart_channel" : ctx.message.channel.id}, restart_channel_file)
	print("Shutting down RSS Bot...")
	await client.logout()

loop = asyncio.get_event_loop()
try:
	loop.create_task(check_rss_feeds())
	loop.run_until_complete(client.start(keys.rss_bot_token))
except KeyboardInterrupt:
	print("Shutting down RSS Bot...")
	loop.run_until_complete(client.logout())
finally:
	loop.close()
