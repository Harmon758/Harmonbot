
import discord
from discord.ext import commands

import asyncio
import datetime
import dateutil.parser
import itertools
import json
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
		self.recently_announced = {}
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
			self.streams_info["channels"][ctx.message.channel.id] = {"name": ctx.message.channel.name, "games": [game], "keywords": [], "streams": []}
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
			self.streams_info["channels"][ctx.message.channel.id] = {"name": ctx.message.channel.name, "games": [], "keywords": [keyword], "streams": []}
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
			self.streams_info["channels"][ctx.message.channel.id] = {"name": ctx.message.channel.name, "games": [], "keywords": [], "streams": [username]}
		with open("data/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await self.bot.embed_reply("Added the Twitch channel, [`{0}`](https://www.twitch.tv/{0}), to this text channel\n"
		"I will now announce here when this Twitch channel goes live".format(username))
	
	@twitch.group(name = "remove", aliases = ["delete"], invoke_without_command = True)
	@checks.is_permitted()
	async def twitch_remove(self):
		'''Remove Twitch games, keywords, or channels being followed'''
		pass
	
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
			await self.bot.embed_reply(":no_entry: This text channel isn't following that stream")
			return
		channel["streams"].remove(username)
		with open("data/twitch_streams.json", 'w') as streams_file:
			json.dump(self.streams_info, streams_file, indent = 4)
		await self.bot.embed_reply("Removed the Twitch channel, [`{0}`](https://www.twitch.tv/{0}), from this text channel".format(username))
	
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
		await self.bot.embed_reply('\n'.join(self.streams_info["channels"].get(ctx.message.channel.id, {}).get("streams", [])))
	
	async def check_twitch_streams(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed:
			try:
				# Games
				games = set(itertools.chain(*[channel["games"] for channel in self.streams_info["channels"].values()]))
				for game in games:
					async with clients.aiohttp_session.get("https://api.twitch.tv/kraken/streams?game={}&client_id={}&limit=100".format(game.replace(' ', '+'), credentials.twitch_client_id)) as resp:
						games_data = await resp.json()
					await self.process_twitch_streams(games_data["streams"], "games", match = game)
					await asyncio.sleep(1)
				# Keywords
				keywords = set(itertools.chain(*[channel["keywords"] for channel in self.streams_info["channels"].values()]))
				for keyword in keywords:
					async with clients.aiohttp_session.get("https://api.twitch.tv/kraken/search/streams?q={}&client_id={}&limit=100".format(keyword.replace(' ', '+'), credentials.twitch_client_id)) as resp:
						keywords_data = await resp.json()
					await self.process_twitch_streams(keywords_data.get("streams", []), "keywords", match = keyword)
					await asyncio.sleep(1)
				# Streams
				streams = set(itertools.chain(*[channel["streams"] for channel in self.streams_info["channels"].values()]))
				async with clients.aiohttp_session.get("https://api.twitch.tv/kraken/streams?channel={}&client_id={}&limit=100".format(','.join(streams), credentials.twitch_client_id)) as resp:
					# TODO: Handle >100 streams
					streams_data = await resp.json()
				await self.process_twitch_streams(streams_data.get("streams", []), "streams")
				# Wait + Update recently announced
				await asyncio.sleep(20)
				for stream, start_time in self.recently_announced.copy().items():
					if (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds() > 300:
						del self.recently_announced[stream]
			except asyncio.CancelledError:
				return
			except Exception as e:
				print("Exception in Twitch Task", file = sys.stderr)
				traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
				logging.errors_logger.error("Uncaught Twitch Task exception\n", exc_info = (type(e), e, e.__traceback__))
	
	async def process_twitch_streams(self, streams, type, match = None):
		for stream in streams:
			if (datetime.datetime.now(datetime.timezone.utc) - dateutil.parser.parse(stream["created_at"])).total_seconds() <= 300 and stream["channel"]["name"] not in self.recently_announced:
				self.recently_announced[stream["channel"]["name"]] = dateutil.parser.parse(stream["created_at"])
				for channel_id, channel_info in self.streams_info["channels"].items():
					if match in channel_info[type] or \
					not match and stream["channel"]["name"] in [s.lower() for s in channel_info[type]]:
						embed = discord.Embed(title = stream["channel"]["status"], description = "{0[channel][display_name]} is playing {0[game]}".format(stream) if stream["channel"]["game"] else discord.Embed.Empty, url = stream["channel"]["url"], timestamp = dateutil.parser.parse(stream["created_at"]).replace(tzinfo = None), color = clients.twitch_color)
						embed.set_author(name = "{} just went live on Twitch".format(stream["channel"]["display_name"]), icon_url = "https://s.jtvnw.net/jtv_user_pictures/hosted_images/GlitchIcon_purple.png")
						if stream["channel"]["logo"]: embed.set_thumbnail(url = stream["channel"]["logo"])
						embed.add_field(name = "Followers", value = stream["channel"]["followers"])
						embed.add_field(name = "Views", value = stream["channel"]["views"])
						text_channel = self.bot.get_channel(channel_id)
						if text_channel:
							await self.bot.send_message(text_channel, embed = embed)

