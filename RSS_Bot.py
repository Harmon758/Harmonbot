
print("Starting up RSS Bot...")

from discord.ext import commands

#import os
#os.environ['PYTHONASYNCIODEBUG'] = '1'

import asyncio
import json
import time
import os

from modules.utilities import *

from utilities import checks

import keys
from client import rss_client

#import logging
#logging.basicConfig(level=logging.DEBUG)

@rss_client.event
async def on_ready():
	print("Started up {0} ({1})".format(str(rss_client.user), rss_client.user.id))
	if os.path.isfile("data/rss_restart_channel.json"):
		with open("data/rss_restart_channel.json", "r") as restart_channel_file:
			restart_channel = rss_client.get_channel(json.load(restart_channel_file)["restart_channel"])
		os.remove("data/rss_restart_channel.json")
		await rss_client.send_message(restart_channel, "Restarted.")
	await rss_client.change_status(game = discord.Game(name = "with Harmonbot"))
	await set_streaming_status(rss_client)
	while True:
		start = time.time()
		await check_rss_feeds()
		elapsed = time.time() - start
		print("RSS Bot | Checked feeds in: {0} sec.".format(str(elapsed)))
		await asyncio.sleep(60 - elapsed)


@rss_client.command(pass_context = True, aliases = ["addrss", "feedadd", "rssadd"])
@checks.is_owner()
async def addfeed(ctx, url : str):
	with open("data/rss_feeds.json", "r") as feeds_file:
		feeds_info = json.load(feeds_file)
	for channel in feeds_info["channels"]:
		if ctx.message.channel.id == channel["id"]:
			channel["feeds"].append(url)
			with open("data/rss_feeds.json", "w") as feeds_file:
				json.dump(feeds_info, feeds_file)
			await rss_client.reply("The feed, " + url + ", has been added to this channel.")
			return
	feeds_info["channels"].append({"name" : ctx.message.channel.name, "id" : ctx.message.channel.id, "feeds" : [url]})
	with open("data/rss_feeds.json", "w") as feeds_file:
		json.dump(feeds_info, feeds_file)
	await rss_client.reply("The feed, " + url + ", has been added to this channel.")

@rss_client.command(pass_context = True, aliases = ["removerss", "feedremove", "rssremove"])
@checks.is_owner()
async def removefeed(ctx, url : str):
	with open("data/rss_feeds.json", "r") as feeds_file:
		feeds_info = json.load(feeds_file)
	for channel in feeds_info["channels"]:
		if ctx.message.channel.id == channel["id"]:
			for feed in channel["feeds"]:
				if feed == url:
					channel["feeds"].remove(feed)
					with open("data/rss_feeds.json", "w") as feeds_file:
						json.dump(feeds_info, feeds_file)
					await rss_client.reply("The feed, " + url + ", has been removed from this channel.")
					return

@rss_client.command(pass_context = True, aliases = ["rsss"])
async def feeds(ctx):
	with open("data/rss_feeds.json", "r") as feeds_file:
		feeds_info = json.load(feeds_file)
	for channel in feeds_info["channels"]:
		if ctx.message.channel.id == channel["id"]:
			feeds = ""
			for feed in channel["feeds"]:
				feeds += "\n" + feed
			await rss_client.reply(feeds)

@rss_client.command(pass_context = True, hidden = True)
@checks.is_owner()
async def restartrss(ctx):
	await rss_client.say("Restarting RSS Bot...")
	with open("data/rss_restart_channel.json", "x+") as restart_channel_file:
		json.dump({"restart_channel" : ctx.message.channel.id}, restart_channel_file)
	raise KeyboardInterrupt


loop = asyncio.get_event_loop()
try:
	loop.run_until_complete(rss_client.start(keys.rss_bot_token))
except KeyboardInterrupt:
	print("Shutting down RSS Bot...")
	loop.run_until_complete(rss_client.logout())
finally:
	loop.close()
