
import discord
from discord.ext import commands

import asyncio
import datetime
import dateutil.parser
import itertools
import json
import os
import sys
import traceback

import clients
import credentials
from utilities import checks
from modules import logging
from modules import utilities

def setup(bot):
	bot.add_cog(Twitch(bot))

class Twitch:
	
	def __init__(self, bot):
		self.bot = bot
		self.streams_announced = {}
		self.old_streams_announced = {}
		utilities.create_file("twitch_streams", content = {"channels" : {}})
		with open("data/twitch_streams.json", 'r') as streams_file:
			self.streams_info = json.load(streams_file)
		self.task = self.bot.loop.create_task(self.check_twitch_streams())
	
	def __unload(self):
		self.task.cancel()
	
	@commands.group(invoke_without_command = True)
	@checks.is_permitted()
	async def twitch(self):
		'''Twitch'''
		pass
	
	@twitch.group(name = "add", invoke_without_command = True)
	@checks.is_permitted()
	async def twitch_add(self):
		'''Add Twitch games, keywords, or channels to follow'''
		pass
	
	@twitch_add.command(name = "filter", pass_context = True)
	@checks.is_permitted()
	async def twitch_add_filter(self, ctx, *, string : str):
		'''Add string to filter Twitch stream titles by'''
		channel = self.streams_info["channels"].get(ctx.message.channel.id)
		# TODO: Check if already filtered
		if channel:
			channel["filters"].append(string)
		else:
			self.streams_info["channels"][ctx.message.channel.id] = {"name": ctx.message.channel.name, "filters": [string], "games": [], "keywords": [], "streams": []}
		with open("data/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await self.bot.embed_reply("Added the filter, `{}`, to this text channel\n"
		"I will now filter all streams for this string in the title".format(string))
	
	@twitch_add.command(name = "game", pass_context = True)
	@checks.is_permitted()
	async def twitch_add_game(self, ctx, *, game : str):
		'''Add a Twitch game to follow'''
		channel = self.streams_info["channels"].get(ctx.message.channel.id)
		# TODO: Add documentation on 100 limit
		# TODO: Check if already following
		if channel:
			channel["games"].append(game)
		else:
			self.streams_info["channels"][ctx.message.channel.id] = {"name": ctx.message.channel.name, "filters": [], "games": [game], "keywords": [], "streams": []}
		with open("data/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await self.bot.embed_reply("Added the game, [`{0}`](https://www.twitch.tv/directory/game/{0}), to this text channel\n"
		"I will now announce here when Twitch streams playing this game go live".format(game))
	
	@twitch_add.command(name = "keyword", aliases = ["query", "search"], pass_context = True)
	@checks.is_permitted()
	async def twitch_add_keyword(self, ctx, *, keyword : str):
		'''Add a Twitch keyword(s) search to follow'''
		channel = self.streams_info["channels"].get(ctx.message.channel.id)
		# TODO: Add documentation on 100 limit
		# TODO: Check if already following
		if channel:
			channel["keywords"].append(keyword)
		else:
			self.streams_info["channels"][ctx.message.channel.id] = {"name": ctx.message.channel.name, "filters": [], "games": [], "keywords": [keyword], "streams": []}
		with open("data/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await self.bot.embed_reply("Added the keyword search, `{}`, to this text channel\n"
		"I will now announce here when Twitch streams with this keyword go live".format(keyword))
	
	@twitch_add.command(name = "channel", aliases = ["stream"], pass_context = True)
	@checks.is_permitted()
	async def twitch_add_channel(self, ctx, username : str):
		'''Add a Twitch channel to follow'''
		channel = self.streams_info["channels"].get(ctx.message.channel.id)
		# TODO: Check if already following
		if channel:
			channel["streams"].append(username)
		else:
			self.streams_info["channels"][ctx.message.channel.id] = {"name": ctx.message.channel.name, "filters": [], "games": [], "keywords": [], "streams": [username]}
		with open("data/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await self.bot.embed_reply("Added the Twitch channel, [`{0}`](https://www.twitch.tv/{0}), to this text channel\n"
		"I will now announce here when this Twitch channel goes live".format(username))
	
	@twitch.group(name = "remove", aliases = ["delete"], invoke_without_command = True)
	@checks.is_permitted()
	async def twitch_remove(self):
		'''Remove Twitch games, keywords, or channels being followed'''
		pass
	
	@twitch_remove.command(name = "filter", pass_context = True)
	@checks.is_permitted()
	async def twitch_remove_filter(self, ctx, *, string : str):
		'''Remove a string Twitch stream titles are being filtered by'''
		channel = self.streams_info["channels"].get(ctx.message.channel.id)
		if not channel or filter not in channel["filters"]:
			await self.bot.embed_reply(":no_entry: This text channel doesn't have that filter")
			return
		channel["filters"].remove(filter)
		with open("data/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await self.bot.embed_reply("Removed the filter, `{}`, from this text channel".format(string))
	
	@twitch_remove.command(name = "game", pass_context = True)
	@checks.is_permitted()
	async def twitch_remove_game(self, ctx, *, game : str):
		'''Remove a Twitch game being followed'''
		channel = self.streams_info["channels"].get(ctx.message.channel.id)
		if not channel or game not in channel["games"]:
			await self.bot.embed_reply(":no_entry: This text channel isn't following that game")
			return
		channel["games"].remove(game)
		with open("data/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await self.bot.embed_reply("Removed the game, [`{0}`](https://www.twitch.tv/directory/game/{0}), from this text channel".format(game))
	
	@twitch_remove.command(name = "keyword", aliases = ["query", "search"], pass_context = True)
	@checks.is_permitted()
	async def twitch_remove_keyword(self, ctx, *, keyword : str):
		'''Remove a Twitch keyword(s) search being followed'''
		channel = self.streams_info["channels"].get(ctx.message.channel.id)
		if not channel or keyword not in channel["keywords"]:
			await self.bot.embed_reply(":no_entry: This text channel isn't following that keyword")
			return
		channel["keywords"].remove(keyword)
		with open("data/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await self.bot.embed_reply("Removed the Twitch keyword search, `{}`, from this text channel".format(keyword))
	
	@twitch_remove.command(name = "channel", aliases = ["stream"], pass_context = True)
	@checks.is_permitted()
	async def twitch_remove_channel(self, ctx, username : str):
		'''Remove a Twitch channel being followed'''
		channel = self.streams_info["channels"].get(ctx.message.channel.id)
		if not channel or username not in channel["streams"]:
			await self.bot.embed_reply(":no_entry: This text channel isn't following that Twitch channel")
			return
		channel["streams"].remove(username)
		with open("data/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await self.bot.embed_reply("Removed the Twitch channel, [`{0}`](https://www.twitch.tv/{0}), from this text channel".format(username))
	
	@twitch.command(name = "filters", pass_context = True)
	@checks.not_forbidden()
	async def twitch_filters(self, ctx):
		'''Show strings Twitch stream titles are being filtered by in this text channel'''
		await self.bot.embed_reply('\n'.join(self.streams_info["channels"].get(ctx.message.channel.id, {}).get("filters", [])))
	
	@twitch.command(name = "games", pass_context = True)
	@checks.not_forbidden()
	async def twitch_games(self, ctx):
		'''Show Twitch games being followed in this text channel'''
		await self.bot.embed_reply('\n'.join(self.streams_info["channels"].get(ctx.message.channel.id, {}).get("games", [])))
	
	@twitch.command(name = "keywords", aliases = ["queries", "searches"], pass_context = True)
	@checks.not_forbidden()
	async def twitch_keywords(self, ctx):
		'''Show Twitch keywords being followed in this text channel'''
		await self.bot.embed_reply('\n'.join(self.streams_info["channels"].get(ctx.message.channel.id, {}).get("keywords", [])))
	
	@twitch.command(name = "channels", aliases = ["streams"], pass_context = True)
	@checks.not_forbidden()
	async def twitch_channels(self, ctx):
		'''Show Twitch channels being followed in this text channel'''
		await self.bot.embed_reply(clients.code_block.format('\n'.join(self.streams_info["channels"].get(ctx.message.channel.id, {}).get("streams", []))))
	
	async def check_twitch_streams(self):
		await self.bot.wait_until_ready()
		try:
			if os.path.isfile("data/temp/twitch_streams_announced.json"):
				with open("data/temp/twitch_streams_announced.json", 'r') as streams_file:
					self.streams_announced = json.load(streams_file)
				for announced_stream_id, announcements in self.streams_announced.items():
					for announcement in announcements:
						text_channel = self.bot.get_channel(announcement[2])
						# TODO: Handle text channel not existing anymore
						announcement[0] = await self.bot.get_message(text_channel, announcement[0])
						# TODO: Handle message deleted
						embed_data = announcement[1]
						announcement[1] = discord.Embed(title = embed_data.get("title"), description = embed_data["description"], url = embed_data["url"], timestamp = dateutil.parser.parse(embed_data["timestamp"]), color = embed_data["color"]).set_author(name = embed_data["author"]["name"], icon_url = embed_data["author"]["icon_url"])
						if embed_data.get("thumbnail", {}).get("url"):
							announcement[1].set_thumbnail(url = embed_data["thumbnail"]["url"])
						for field in embed_data["fields"]:
							announcement[1].add_field(name = field["name"], value = field["value"], inline = field["inline"])
						del announcement[2]
			## os.remove("data/temp/twitch_streams_announced.json")
		except Exception as e:
			print("Exception in Twitch Task", file = sys.stderr)
			traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
			logging.errors_logger.error("Uncaught Twitch Task exception\n", exc_info = (type(e), e, e.__traceback__))
			return
		while not self.bot.is_closed:
			try:
				stream_ids = []
				# Games
				games = set(itertools.chain(*[channel["games"] for channel in self.streams_info["channels"].values()]))
				for game in games:
					async with clients.aiohttp_session.get("https://api.twitch.tv/kraken/streams?game={}&client_id={}&limit=100".format(game.replace(' ', '+'), credentials.twitch_client_id)) as resp:
						games_data = await resp.json()
					streams = games_data.get("streams", [])
					stream_ids += [stream["_id"] for stream in streams]
					await self.process_twitch_streams(streams, "games", match = game)
					await asyncio.sleep(1)
				# Keywords
				keywords = set(itertools.chain(*[channel["keywords"] for channel in self.streams_info["channels"].values()]))
				for keyword in keywords:
					async with clients.aiohttp_session.get("https://api.twitch.tv/kraken/search/streams?q={}&client_id={}&limit=100".format(keyword.replace(' ', '+'), credentials.twitch_client_id)) as resp:
						keywords_data = await resp.json()
					streams = keywords_data.get("streams", [])
					stream_ids += [stream["_id"] for stream in streams]
					await self.process_twitch_streams(streams, "keywords", match = keyword)
					await asyncio.sleep(1)
				# Streams
				streams = set(itertools.chain(*[channel["streams"] for channel in self.streams_info["channels"].values()]))
				async with clients.aiohttp_session.get("https://api.twitch.tv/kraken/streams?channel={}&client_id={}&limit=100".format(','.join(streams), credentials.twitch_client_id)) as resp:
					# TODO: Handle >100 streams
					streams_data = await resp.json()
				streams = streams_data.get("streams", [])
				stream_ids += [stream["_id"] for stream in streams]
				await self.process_twitch_streams(streams, "streams")
				# Update streams announced
				for announced_stream_id, announcements in self.streams_announced.copy().items():
					if announced_stream_id not in stream_ids:
						for announcement in announcements:
							embed = announcement[1]
							embed.set_author(name = embed.author.name.replace("just went", "was"), url = embed.author.url, icon_url = embed.author.icon_url)
							await self.bot.edit_message(announcement[0], embed = embed)
							# TODO: Handle message deleted
							self.old_streams_announced[announced_stream_id] = self.streams_announced[announced_stream_id]
							del self.streams_announced[announced_stream_id]
					# TODO: Handle no longer being followed?
				await asyncio.sleep(20)
			except asyncio.CancelledError:
				for announced_stream_id, announcements in self.streams_announced.items():
					for announcement in announcements:
						announcement.append(announcement[0].channel.id)
						announcement[0] = announcement[0].id
						announcement[1] = announcement[1].to_dict()
				with open("data/temp/twitch_streams_announced.json", 'w') as streams_file:
					json.dump(self.streams_announced, streams_file, indent = 4)
				return
			except Exception as e:
				print("Exception in Twitch Task", file = sys.stderr)
				traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
				logging.errors_logger.error("Uncaught Twitch Task exception\n", exc_info = (type(e), e, e.__traceback__))
				await asyncio.sleep(60)
	
	async def process_twitch_streams(self, streams, type, match = None):
		for stream in streams:
			if stream["_id"] in self.old_streams_announced:
				for announcement in self.old_streams_announced[stream["_id"]]:
					embed = announcement[1]
					embed.set_author(name = embed.author.name.replace("was", "just went"), url = embed.author.url, icon_url = embed.author.icon_url)
					await self.bot.edit_message(announcement[0], embed = embed)
				self.streams_announced[stream["_id"]] = self.old_streams_announced[stream["_id"]]
				del self.old_streams_announced[stream["_id"]]
			elif stream["_id"] not in self.streams_announced:
				for channel_id, channel_info in self.streams_info["channels"].items():
					if (match in channel_info[type] or \
					not match and stream["channel"]["name"] in [s.lower() for s in channel_info[type]]) and \
					all(filter in stream["channel"]["status"] for filter in channel_info["filters"]):
						embed = discord.Embed(title = stream["channel"]["status"] if len(stream["channel"]["status"]) <= 256 else stream["channel"]["status"][:253] + "...", description = "{0[channel][display_name]} is playing {0[game]}".format(stream) if stream["channel"]["game"] else discord.Embed.Empty, url = stream["channel"]["url"], timestamp = dateutil.parser.parse(stream["created_at"]).replace(tzinfo = None), color = clients.twitch_color)
						embed.set_author(name = "{} just went live on Twitch".format(stream["channel"]["display_name"]), icon_url = clients.twitch_icon_url)
						if stream["channel"]["logo"]: embed.set_thumbnail(url = stream["channel"]["logo"])
						embed.add_field(name = "Followers", value = stream["channel"]["followers"])
						embed.add_field(name = "Views", value = stream["channel"]["views"])
						text_channel = self.bot.get_channel(channel_id)
						if not text_channel:
							# TODO: Remove text channel data if now non-existent
							continue
						message = await self.bot.send_message(text_channel, embed = embed)
						self.streams_announced[stream["_id"]] = self.streams_announced.get(stream["_id"], []) + [[message, embed]]

