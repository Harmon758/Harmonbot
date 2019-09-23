
import discord
from discord.ext import commands

import aiohttp
import asyncio
import dateutil.parser
import itertools
import json
import logging
import os
import sys
import traceback

import clients
from utilities import checks

errors_logger = logging.getLogger("errors")

def setup(bot):
	bot.add_cog(Twitch(bot))

class Twitch(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.streams_announced = {}
		self.old_streams_announced = {}
		clients.create_file("twitch_streams", content = {"channels" : {}})
		with open(clients.data_path + "/twitch_streams.json", 'r') as streams_file:
			self.streams_info = json.load(streams_file)
		self.task = self.bot.loop.create_task(self.check_twitch_streams())
	
	def cog_unload(self):
		self.task.cancel()
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.is_permitted()
	async def twitch(self, ctx):
		'''Twitch'''
		await ctx.send_help(ctx.command)
	
	@twitch.group(name = "add", invoke_without_command = True, case_insensitive = True)
	@checks.is_permitted()
	async def twitch_add(self, ctx):
		'''Add Twitch games, keywords, or channels to follow'''
		await ctx.send_help(ctx.command)
	
	@twitch_add.command(name = "filter")
	@checks.is_permitted()
	async def twitch_add_filter(self, ctx, *, string : str):
		'''Add string to filter Twitch stream titles by'''
		channel = self.streams_info["channels"].get(str(ctx.channel.id))
		# TODO: Check if already filtered
		if channel:
			channel["filters"].append(string)
		else:
			self.streams_info["channels"][str(ctx.channel.id)] = {"name": ctx.channel.name, "filters": [string], "games": [], "keywords": [], "streams": []}
		with open(clients.data_path + "/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await ctx.embed_reply(f"Added the filter, `{string}`, to this text channel\n"
								"I will now filter all streams for this string in the title")
	
	@twitch_add.command(name = "game")
	@checks.is_permitted()
	async def twitch_add_game(self, ctx, *, game : str):
		'''Add a Twitch game to follow'''
		channel = self.streams_info["channels"].get(str(ctx.channel.id))
		# TODO: Add documentation on 100 limit
		# TODO: Check if already following
		if channel:
			channel["games"].append(game)
		else:
			self.streams_info["channels"][str(ctx.channel.id)] = {"name": ctx.channel.name, "filters": [], "games": [game], "keywords": [], "streams": []}
		with open(clients.data_path + "/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await ctx.embed_reply(f"Added the game, [`{game}`](https://www.twitch.tv/directory/game/{game}), to this text channel\n"
								"I will now announce here when Twitch streams playing this game go live")
	
	@twitch_add.command(name = "keyword", aliases = ["query", "search"])
	@checks.is_permitted()
	async def twitch_add_keyword(self, ctx, *, keyword : str):
		'''Add a Twitch keyword(s) search to follow'''
		channel = self.streams_info["channels"].get(str(ctx.channel.id))
		# TODO: Add documentation on 100 limit
		# TODO: Check if already following
		if channel:
			channel["keywords"].append(keyword)
		else:
			self.streams_info["channels"][str(ctx.channel.id)] = {"name": ctx.channel.name, "filters": [], "games": [], "keywords": [keyword], "streams": []}
		with open(clients.data_path + "/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await ctx.embed_reply(f"Added the keyword search, `{keyword}`, to this text channel\n"
								"I will now announce here when Twitch streams with this keyword go live")
	
	@twitch_add.command(name = "channel", aliases = ["stream"])
	@checks.is_permitted()
	async def twitch_add_channel(self, ctx, username : str):
		'''Add a Twitch channel to follow'''
		channel = self.streams_info["channels"].get(str(ctx.channel.id))
		# TODO: Check if already following
		if channel:
			channel["streams"].append(username)
		else:
			self.streams_info["channels"][str(ctx.channel.id)] = {"name": ctx.channel.name, "filters": [], "games": [], "keywords": [], "streams": [username]}
		with open(clients.data_path + "/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await ctx.embed_reply(f"Added the Twitch channel, [`{username}`](https://www.twitch.tv/{username}), to this text channel\n"
								"I will now announce here when this Twitch channel goes live")
	
	@twitch.group(name = "remove", aliases = ["delete"], 
					invoke_without_command = True, case_insensitive = True)
	@checks.is_permitted()
	async def twitch_remove(self, ctx):
		'''Remove Twitch games, keywords, or channels being followed'''
		await ctx.send_help(ctx.command)
	
	@twitch_remove.command(name = "filter")
	@checks.is_permitted()
	async def twitch_remove_filter(self, ctx, *, string : str):
		'''Remove a string Twitch stream titles are being filtered by'''
		channel = self.streams_info["channels"].get(str(ctx.channel.id))
		if not channel or filter not in channel["filters"]:
			await ctx.embed_reply(":no_entry: This text channel doesn't have that filter")
			return
		channel["filters"].remove(filter)
		with open(clients.data_path + "/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await ctx.embed_reply(f"Removed the filter, `{string}`, from this text channel")
	
	@twitch_remove.command(name = "game")
	@checks.is_permitted()
	async def twitch_remove_game(self, ctx, *, game : str):
		'''Remove a Twitch game being followed'''
		channel = self.streams_info["channels"].get(str(ctx.channel.id))
		if not channel or game not in channel["games"]:
			await ctx.embed_reply(":no_entry: This text channel isn't following that game")
			return
		channel["games"].remove(game)
		with open(clients.data_path + "/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await ctx.embed_reply("Removed the game, [`{0}`](https://www.twitch.tv/directory/game/{0}), from this text channel".format(game))
	
	@twitch_remove.command(name = "keyword", aliases = ["query", "search"])
	@checks.is_permitted()
	async def twitch_remove_keyword(self, ctx, *, keyword : str):
		'''Remove a Twitch keyword(s) search being followed'''
		channel = self.streams_info["channels"].get(str(ctx.channel.id))
		if not channel or keyword not in channel["keywords"]:
			await ctx.embed_reply(":no_entry: This text channel isn't following that keyword")
			return
		channel["keywords"].remove(keyword)
		with open(clients.data_path + "/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await ctx.embed_reply("Removed the Twitch keyword search, `{}`, from this text channel".format(keyword))
	
	@twitch_remove.command(name = "channel", aliases = ["stream"])
	@checks.is_permitted()
	async def twitch_remove_channel(self, ctx, username : str):
		'''Remove a Twitch channel being followed'''
		channel = self.streams_info["channels"].get(str(ctx.channel.id))
		if not channel or username not in channel["streams"]:
			await ctx.embed_reply(":no_entry: This text channel isn't following that Twitch channel")
			return
		channel["streams"].remove(username)
		with open(clients.data_path + "/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await ctx.embed_reply("Removed the Twitch channel, [`{0}`](https://www.twitch.tv/{0}), from this text channel".format(username))
	
	@twitch.command(name = "filters")
	@checks.not_forbidden()
	async def twitch_filters(self, ctx):
		'''Show strings Twitch stream titles are being filtered by in this text channel'''
		await ctx.embed_reply('\n'.join(self.streams_info["channels"].get(str(ctx.channel.id), {}).get("filters", [])))
	
	@twitch.command(name = "games")
	@checks.not_forbidden()
	async def twitch_games(self, ctx):
		'''Show Twitch games being followed in this text channel'''
		await ctx.embed_reply('\n'.join(self.streams_info["channels"].get(str(ctx.channel.id), {}).get("games", [])))
	
	@twitch.command(name = "keywords", aliases = ["queries", "searches"])
	@checks.not_forbidden()
	async def twitch_keywords(self, ctx):
		'''Show Twitch keywords being followed in this text channel'''
		await ctx.embed_reply('\n'.join(self.streams_info["channels"].get(str(ctx.channel.id), {}).get("keywords", [])))
	
	@twitch.command(name = "channels", aliases = ["streams"])
	@checks.not_forbidden()
	async def twitch_channels(self, ctx):
		'''Show Twitch channels being followed in this text channel'''
		await ctx.embed_reply(ctx.bot.CODE_BLOCK.format('\n'.join(self.streams_info["channels"].get(str(ctx.channel.id), {}).get("streams", []))))
	
	async def check_twitch_streams(self):
		await self.bot.wait_until_ready()
		try:
			if os.path.isfile(clients.data_path + "/temp/twitch_streams_announced.json"):
				with open(clients.data_path + "/temp/twitch_streams_announced.json", 'r') as streams_file:
					self.streams_announced = json.load(streams_file)
				# Convert json string keys back to int
				self.streams_announced = {int(k): v for k, v in self.streams_announced.items()}
				for announced_stream_id, announcements in self.streams_announced.items():
					for announcement in announcements:
						text_channel = self.bot.get_channel(int(announcement[2]))
						# TODO: Handle text channel not existing anymore
						try:
							announcement[0] = await text_channel.fetch_message(announcement[0])
						except discord.NotFound:
							# Announcement was deleted
							continue
						embed_data = announcement[1]
						announcement[1] = discord.Embed(title = embed_data.get("title"), url = embed_data["url"], 
														description = embed_data.get("description", discord.Embed.Empty), 
														timestamp = dateutil.parser.parse(embed_data["timestamp"]), 
														color = embed_data["color"])
						announcement[1].set_author(name = embed_data["author"]["name"], 
													icon_url = embed_data["author"]["icon_url"])
						if embed_data.get("thumbnail", {}).get("url"):
							announcement[1].set_thumbnail(url = embed_data["thumbnail"]["url"])
						for field in embed_data["fields"]:
							announcement[1].add_field(name = field["name"], value = field["value"], inline = field["inline"])
						del announcement[2]
					# Remove deleted announcements
					self.streams_announced[announced_stream_id] = [announcement for announcement in announcements
																	if len(announcement) == 2]
			## os.remove(clients.data_path + "/temp/twitch_streams_announced.json")
		except Exception as e:
			print("Exception in Twitch Task", file = sys.stderr)
			traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
			errors_logger.error("Uncaught Twitch Task exception\n", exc_info = (type(e), e, e.__traceback__))
			return
		while not self.bot.is_closed():
			try:
				stream_ids = []
				# Games
				games = set(itertools.chain(*[channel["games"] for channel in self.streams_info["channels"].values()]))
				for game in games:
					url = "https://api.twitch.tv/kraken/streams"
					params = {"game": game, "client_id": self.bot.TWITCH_CLIENT_ID, "limit": 100}
					async with self.bot.aiohttp_session.get(url, params = params) as resp:
						games_data = await resp.json()
					streams = games_data.get("streams", [])
					stream_ids += [stream["_id"] for stream in streams]
					await self.process_twitch_streams(streams, "games", match = game)
					await asyncio.sleep(1)
				# Keywords
				keywords = set(itertools.chain(*[channel["keywords"] for channel in self.streams_info["channels"].values()]))
				for keyword in keywords:
					url = "https://api.twitch.tv/kraken/search/streams"
					params = {'q': keyword, "client_id": self.bot.TWITCH_CLIENT_ID, "limit": 100}
					async with self.bot.aiohttp_session.get(url, params = params) as resp:
						keywords_data = await resp.json()
					streams = keywords_data.get("streams", [])
					stream_ids += [stream["_id"] for stream in streams]
					await self.process_twitch_streams(streams, "keywords", match = keyword)
					await asyncio.sleep(1)
				# Streams
				streams = set(itertools.chain(*[channel["streams"] for channel in self.streams_info["channels"].values()]))
				url = "https://api.twitch.tv/kraken/streams"
				params = {"channel": ','.join(streams), "client_id": self.bot.TWITCH_CLIENT_ID, "limit": 100}
				async with self.bot.aiohttp_session.get(url, params = params) as resp:
					# TODO: Handle >100 streams
					if resp.status != 504:
						streams_data = await resp.json()
				streams = streams_data.get("streams", [])
				stream_ids += [stream["_id"] for stream in streams]
				await self.process_twitch_streams(streams, "streams")
				# Update streams announced
				for announced_stream_id, announcements in self.streams_announced.copy().items():
					if announced_stream_id not in stream_ids:
						for announcement in announcements:
							embed = announcement[1]
							embed.set_author(name = embed.author.name.replace("just went", "was"), 
												url = embed.author.url, icon_url = embed.author.icon_url)
							try:
								await announcement[0].edit(embed = embed)
							except discord.Forbidden:
								# Missing permission to edit?
								pass
							except discord.NotFound:
								# Announcement was deleted
								pass
						self.old_streams_announced[announced_stream_id] = self.streams_announced[announced_stream_id]
						del self.streams_announced[announced_stream_id]
					# TODO: Handle no longer being followed?
				await asyncio.sleep(20)
			except aiohttp.ClientConnectionError as e:
				print(f"{self.bot.console_message_prefix}Twitch Task Connection Error: {type(e).__name__}: {e}")
				await asyncio.sleep(10)
			except asyncio.CancelledError:
				for announced_stream_id, announcements in self.streams_announced.items():
					for announcement in announcements:
						announcement.append(announcement[0].channel.id)
						announcement[0] = announcement[0].id
						announcement[1] = announcement[1].to_dict()
				with open(clients.data_path + "/temp/twitch_streams_announced.json", 'w') as streams_file:
					json.dump(self.streams_announced, streams_file, indent = 4)
				print(f"{self.bot.console_message_prefix}Twitch task cancelled")
				return
			except Exception as e:
				print("Exception in Twitch Task", file = sys.stderr)
				traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
				errors_logger.error("Uncaught Twitch Task exception\n", exc_info = (type(e), e, e.__traceback__))
				await asyncio.sleep(60)
	
	async def process_twitch_streams(self, streams, type, match = None):
		# TODO: use textwrap
		for stream in streams:
			if stream["_id"] in self.old_streams_announced:
				for announcement in self.old_streams_announced[stream["_id"]]:
					embed = announcement[1]
					embed.set_author(name = embed.author.name.replace("was", "just went"), 
										url = embed.author.url, icon_url = embed.author.icon_url)
					await announcement[0].edit(embed = embed)
				self.streams_announced[stream["_id"]] = self.old_streams_announced[stream["_id"]]
				del self.old_streams_announced[stream["_id"]]
			elif stream["_id"] not in self.streams_announced:
				for channel_id, channel_info in self.streams_info["channels"].items():
					if ((match in channel_info[type] or 
							not match and stream["channel"]["name"] in [s.lower() for s in channel_info[type]]) and 
							all(filter in stream["channel"]["status"] for filter in channel_info["filters"])):
						if len(stream["channel"]["status"]) <= 256:
							title = stream["channel"]["status"]
						else:
							title = stream["channel"]["status"][:253] + "..."
						if stream["channel"]["game"]:
							description = f"{stream['channel']['display_name']} is playing {stream['game']}"
						else:
							description = discord.Embed.Empty
						embed = discord.Embed(title = title, url = stream["channel"]["url"], 
												description = description, 
												timestamp = dateutil.parser.parse(stream["created_at"]).replace(tzinfo = None), 
												color = self.bot.twitch_color)
						embed.set_author(name = f"{stream['channel']['display_name']} just went live on Twitch", 
											icon_url = self.bot.twitch_icon_url)
						if stream["channel"]["logo"]:
							embed.set_thumbnail(url = stream["channel"]["logo"])
						embed.add_field(name = "Followers", value = f"{stream['channel']['followers']:,}")
						embed.add_field(name = "Views", value = f"{stream['channel']['views']:,}")
						text_channel = self.bot.get_channel(int(channel_id))
						if not text_channel:
							# TODO: Remove text channel data if now non-existent
							continue
						message = await text_channel.send(embed = embed)
						self.streams_announced[stream["_id"]] = self.streams_announced.get(stream["_id"], []) + [[message, embed]]

