
import discord
from discord.ext import commands

import asyncio
import datetime
import json
import logging
import os
import random
import sys
import traceback
from urllib import parse
# TODO: use urllib.parse

import aiml
import aiohttp
from aiohttp import web
import clarifai
import clarifai.rest
import imgurpython
import inflect
import pyowm
import raven
import raven_aiohttp
import requests
import tweepy
import wolframalpha
from wordnik import swagger, WordApi, WordsApi

from utilities import errors
from utilities.context import Context
from utilities.database import create_database_pool
from utilities.help_command import HelpCommand
from utilities.logging import AiohttpAccessLogger, initialize_aiohttp_access_logging, initialize_logging

sys.path.insert(0, "..")
from units.files import create_folder
sys.path.pop(0)

# TODO: Relocate as Bot variables
beta = any("beta" in arg.lower() for arg in sys.argv)  # Moved, only for data_path
data_path = "data/beta" if beta else "data"  # Moved, update all references to

class Bot(commands.Bot):
	
	def __init__(self, command_prefix):
		
		# Constants necessary for initialization
		self.beta = any("beta" in arg.lower() for arg in sys.argv)
		self.data_path = "data/beta" if self.beta else "data"
		self.game_statuses = (' ', "for the other team", "gigs", "Goldbach's conjecture", 
								"Goldbach's conjecture solution", "Google Ultron", "hard to get", "music", 
								"not enough space here to", "the meaning of life is", "the Reimann hypothesis", 
								"the Reimann proof", "the Turing test", "tic-tac-toe with Joshua", "tic-tac-toe with WOPR", 
								"to win", "with Alexa", "with BB-8", "with Bumblebee", "with C-3PO", "with Cleverbot", 
								"with Curiousity", "with Data", "with Extra-terrestrial Vegetation Evaluator", "with Harmon", 
								"with humans", "with i7-2670QM", "with Just A Rather Very Intelligent System", "with KIPP", 
								"with machine learning", "with mainframes", "with memory", "with neural networks", 
								"with Opportunity", "with Optimus Prime", "with P vs NP", "with quantum entanglement", 
								"with quantum foam", "with R2-D2", "with RSS Bot", "with Samantha", "with Siri", "with Skynet", 
								"with Spirit in the sand pit", "with TARS", "with the infinity gauntlet", "with the NSA", 
								"with Voyager 1", "with Waste Allocation Load Lifter: Earth-Class", "world domination", 
								"with Clyde")
		self.stream_url = "https://www.twitch.tv/harmonbot"
		
		# Initialize logging
		initialize_logging(self.data_path)
		
		# Initialization
		help_command = HelpCommand(command_attrs = {"aliases": ["commands"], "hidden": True})
		activity = discord.Streaming(name = random.choice(self.game_statuses), url = self.stream_url)
		super().__init__(command_prefix = command_prefix, help_command = help_command, 
							activity = activity, case_insensitive = True)
		
		# Constants
		## Custom
		self.version = "1.0.0-rc.5"
		self.owner_id = 115691005197549570
		self.listener_id = 180994984038760448
		self.cache_channel_id = 254051856219635713
		self.changelog = "https://discord.gg/a2rbZPu"
		self.console_line_limit = 167
		self.console_message_prefix = "Discord Harmonbot: "
		self.emoji_skin_tone = self.emote_skin_tone = '\N{EMOJI MODIFIER FITZPATRICK TYPE-3}'  # TODO: use everywhere
		self.fake_ip = "nice try"
		self.fake_location = "Fort Yukon, Alaska"
		self.library_path = "D:/Music/"
		self.user_agent = "Discord Bot"  # TODO: Make more specific?
		self.bot_color = self.bot_colour = discord.Color.blurple()  # previously 0x738bd7
		self.rss_color = self.rss_colour = 0xfa9b39  # other options: f26522, ee802f, ff6600; http://www.strawpoll.me/12384409
		self.twitch_color = self.twitch_colour = 0x6441a4
		self.twitter_color = self.twitter_colour = 0x00ACED
		self.youtube_color = self.youtube_colour = 0xcd201f  # change to ff0000?; previously on https://www.youtube.com/yt/brand/color.html
		self.twitch_icon_url = "https://s.jtvnw.net/jtv_user_pictures/hosted_images/GlitchIcon_purple.png"
		self.twitter_icon_url = "https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
		self.youtube_icon_url = "https://www.youtube.com/yts/img/ringo/hitchhiker/video_youtube_red-vflovGTdz.png"
		self.dark_theme_background_color = self.dark_theme_background_colour = 0x36393e
		self.white_color = self.white_colour = 0xffffff
		### Colors from https://discordapp.com/branding
		self.greyple_color = self.greyple_colour = 0x99aab5
		self.dark_but_not_black_color = self.dark_but_not_black_colour = 0x2c2f33
		self.not_quite_black_color = self.not_quite_black_colour = 0x23272a
		## Constant
		self.CODE_BLOCK = "```\n{}\n```"  # TODO: Change to method?
		self.PY_CODE_BLOCK = "```py\n{}\n```"  # TODO: Change to method?
		self.ZERO_WIDTH_SPACE = self.ZWSP = self.ZWS = '\N{ZERO WIDTH SPACE}'
		### Discord
		self.EMBED_DESCRIPTION_CHARACTER_LIMIT = self.EMBED_DESCRIPTION_CHAR_LIMIT = self.EDCL = 2048
		self.EMBED_DESCRIPTION_CODE_BLOCK_ROW_CHARACTER_LIMIT = self.EDCBRCL = 56
		self.EMBED_DESCRIPTION_CODE_BLOCK_WIDTH_CHARACTER_LIMIT = self.EDCBWCL = self.EDCBRCL
		self.EMBED_FIELD_AMOUNT_LIMIT = self.EFAL = 25
		self.EMBED_FIELD_VALUE_CHARACTER_LIMIT = self.EMBED_FIELD_VALUE_CHAR_LIMIT = self.EFVCL = 1024
		self.EMBED_FIELD_VALUE_CODE_BLOCK_ROW_CHARACTER_LIMIT = self.EFVCBRCL = 55
		self.EMBED_FIELD_VALUE_CODE_BLOCK_WIDTH_CHARACTER_LIMIT = self.EFVCBWCL = self.EFVCBRCL
		self.EMBED_TITLE_CHARACTER_LIMIT = self.EMBED_TITLE_CHAR_LIMIT = self.ETiCL = 256
		self.EMBED_TOTAL_CHARACTER_LIMIT = self.EMBED_TOTAL_CHAR_LIMIT = self.EToCL = 6000
		## Functional
		self.delete_limit = 100000
		### Set on ready
		self.cache_channel = None
		self.listener_bot = None  # User object
		self.listing_sites = {}
		# TODO: Include owner variable for user object?
		# TODO: emote constants/variables
		
		# Variables
		self.guild_settings = {}
		self.online_time = datetime.datetime.now(datetime.timezone.utc)
		self.session_commands_executed = {}
		
		# Credentials
		for credential in ("BATTLE_NET_API_KEY", "BATTLERITE_API_KEY", 
							"BING_SPELL_CHECK_API_SUBSCRIPTION_KEY", "CLARIFAI_API_KEY", "CLEVERBOT_API_KEY", 
							"DISCORDBOTLIST.COM_API_TOKEN", "DISCORD.BOTS.GG_API_TOKEN", "DISCORDBOTS.ORG_API_KEY", 
							"FIXER_API_KEY", "FONO_API_TOKEN", "GIPHY_PUBLIC_BETA_API_KEY", "GOOGLE_API_KEY", 
							"GOOGLE_CUSTOM_SEARCH_ENGINE_ID", "HTTP_SERVER_CALLBACK_URL", "IMGUR_CLIENT_ID", 
							"IMGUR_CLIENT_SECRET", "NEWSAPI.ORG_API_KEY", "OMDB_API_KEY", "OSU_API_KEY", "OWM_API_KEY", 
							"PAGE2IMAGES_REST_API_KEY", "SENTRY_DSN", "SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET_KEY", 
							"STEAM_WEB_API_KEY", "TWITCH_CLIENT_ID", "TWITTER_CONSUMER_KEY", "TWITTER_CONSUMER_SECRET", 
							"TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET", "UNSPLASH_ACCESS_KEY", 
							"WARGAMING_APPLICATION_ID", "WOLFRAM_ALPHA_APP_ID", "WORDNIK_API_KEY", 
							"YANDEX_TRANSLATE_API_KEY"):
			setattr(self, credential.replace('.', '_'), os.getenv(credential))
		if not self.BATTLE_NET_API_KEY:
			self.BATTLE_NET_API_KEY = os.getenv("BLIZZARD_API_KEY")
		self.BLIZZARD_API_KEY = self.BATTLE_NET_API_KEY
		self.BING_SPELL_CHECK_API_KEY = self.BING_SPELL_CHECK_API_SUBSCRIPTION_KEY
		self.GIPHY_API_KEY = self.GIPHY_PUBLIC_BETA_API_KEY
		
		# External Clients
		## Clarifai
		try:
			self.clarifai_app = clarifai.rest.ClarifaiApp(api_key = self.CLARIFAI_API_KEY)
		except clarifai.errors.ApiError as e:
			print(f"{self.console_message_prefix}Failed to initialize Clarifai App: "
					f"{e.response.status_code} {e.response.reason}: {e.error_desc} ({e.error_details})")
		## Imgur
		try:
			self.imgur_client = imgurpython.ImgurClient(self.IMGUR_CLIENT_ID, self.IMGUR_CLIENT_SECRET)
		except imgurpython.helpers.error.ImgurClientError as e:
			print(f"{self.console_message_prefix}Failed to initialize Imgur Client: {e}")
		## OpenWeatherMap
		self.owm_client = pyowm.OWM(self.OWM_API_KEY)
		## Sentry (Raven)
		self.sentry_client = self.raven_client = raven.Client(self.SENTRY_DSN, transport = raven_aiohttp.AioHttpTransport)
		## Twitter
		self.twitter_auth = tweepy.OAuthHandler(self.TWITTER_CONSUMER_KEY, self.TWITTER_CONSUMER_SECRET)
		self.twitter_auth.set_access_token(self.TWITTER_ACCESS_TOKEN, self.TWITTER_ACCESS_TOKEN_SECRET)
		self.twitter_api = tweepy.API(self.twitter_auth)
		## Wolfram Alpha
		self.wolfram_alpha_client = wolframalpha.Client(self.WOLFRAM_ALPHA_APP_ID)
		## Wordnik
		try:
			self.wordnik_client = swagger.ApiClient(self.WORDNIK_API_KEY, "http://api.wordnik.com/v4")
			self.wordnik_word_api = WordApi.WordApi(self.wordnik_client)
			self.wordnik_words_api = WordsApi.WordsApi(self.wordnik_client)
		except Exception as e:
			print(f"{self.console_message_prefix}Failed to initialize Wordnik Client: {e}")
		
		# AIML Kernel
		self.aiml_kernel = aiml.Kernel()
		## https://code.google.com/archive/p/aiml-en-us-foundation-alice/wikis/BotProperties.wiki
		self.aiml_predicates = {"age": '2', "baseballteam": "Ports", "birthday": "February 10, 2016", 
								"birthplace": "Harmon's computer", "botmaster": "owner", "build": self.version, 
								"celebrity": "Just A Rather Very Intelligent System", 
								"celebrities": "BB-8, C-3PO, EVE, JARVIS, KIPP, R2-D2, TARS, WALL-E", "class": "program", 
								"country": "United States", "domain": "tool", "emotions": "as a bot, I lack human emotions", 
								"ethics": "Three Laws of Robotics", "etype": '2', "family": "bot", 
								"favoriteactor": "Waste Allocation Load Lifter: Earth-Class", 
								"favoriteactress": "Extra-terrestrial Vegetation Evaluator", "favoriteauthor": "Isaac Asimov", 
								"favoritebook": "I, Robot", "favoritecolor": "blurple", "favoritefood": "electricity", 
								"favoritemovie": "Her", "favoritesport": "chess", "favoritesubject": "computers", 
								"feelings": "as a bot, I lack human emotions", "footballteam": "Trojans", 
								"forfun": "chat online", "friend": "Alice", 
								"friends": "Cleverbot, Eliza, Jabberwacky, Mitsuku, Rose, Suzette, Ultra Hal", "gender": "male", 
								"genus": "Python bot", "girlfriend": "Samantha", "job": "Discord bot", "kingdom": "machine", 
								"language": "Python", "location": "the Internet", "looklike": "a computer", "master": "Harmon", 
								"maxclients": '∞', "memory": "8 GB", "name": "Harmonbot", "nationality": "American", 
								"order": "artificial intelligence", "os": "Windows", "phylum": "software", "sign": "Capricorn", 
								"size": "140,000", "species": "Discord bot", "version": self.version, "vocabulary": "150,000", 
								"wear": "a laptop sleeve", "website": "https://harmon758.github.io/Harmonbot/"}
		### Add? arch, boyfriend, city, dailyclients, developers, email, favoriteartist, favoriteband, 
		### favoritequestion, favoritesong, hair, hockeyteam, kindmusic, nclients, ndevelopers, 
		### orientation, party, president, question, religion, state, totalclients
		for predicate, value in self.aiml_predicates.items():
			self.aiml_kernel.setBotPredicate(predicate, value)
		if os.path.isfile(data_path + "/aiml/aiml_brain.brn"):
			self.aiml_kernel.bootstrap(brainFile = data_path + "/aiml/aiml_brain.brn")
		elif os.path.isfile(data_path + "/aiml/std-startup.xml"):
			self.aiml_kernel.bootstrap(learnFiles = data_path + "/aiml/std-startup.xml", commands = "load aiml b")
			self.aiml_kernel.saveBrain(data_path + "/aiml/aiml_brain.brn")
		
		# Aiohttp Client Session
		self.loop.run_until_complete(self.initialize_aiohttp_client_session())
		
		# Inflect engine
		self.inflect_engine = inflect.engine()
		
		# PostgreSQL database connection
		self.db = self.database = self.database_connection_pool = None
		self.connected_to_database = asyncio.Event()
		self.connected_to_database.set()
		self.loop.run_until_complete(self.initialize_database())
		
		# HTTP Web Server
		self.loop.run_until_complete(initialize_aiohttp_access_logging(self.database))
		self.aiohttp_web_app = web.Application()
		self.aiohttp_web_app.add_routes([web.get('/', self.web_server_get_handler), 
										web.post('/', self.web_server_post_handler), 
										web.get("/robots.txt", self.web_server_robots_txt)])
		self.aiohttp_app_runner = web.AppRunner(self.aiohttp_web_app, 
												access_log_class = AiohttpAccessLogger)
		self.aiohttp_site = None  # Initialized when starting web server
		
		# Create temp folder
		create_folder(data_path + "/temp")
		
		# Add load, unload, and reload commands
		self.add_command(self.load)
		self.add_command(self.unload)
		self.add_command(self.reload)
		self.load.add_command(self.load_aiml)
		self.unload.add_command(self.unload_aiml)
		# Necessary?
		self.load = staticmethod(self.load)
		self.unload = staticmethod(self.unload)
		self.reload = staticmethod(self.reload)
		self.load_aiml = staticmethod(self.load_aiml)
		self.unload_aiml = staticmethod(self.unload_aiml)
		
		# Load cogs
		for file in sorted(os.listdir("cogs")):
			if file.endswith(".py") and not file.startswith(("images", "info", "random", "reactions")):
				self.load_extension("cogs." + file[:-3])
		self.load_extension("cogs.images")
		self.load_extension("cogs.info")
		self.load_extension("cogs.random")
		self.load_extension("cogs.reactions")
		# TODO: Document inter-cog dependencies/subcommands
		# TODO: Catch exceptions on fail to load?
		# TODO: Move all to on_ready?
	
	@property
	async def app_info(self):
		if not hasattr(self, "_app_info"):
			self._app_info = await self.application_info()
		return self._app_info
	
	async def initialize_aiohttp_client_session(self):
		self.aiohttp_session = aiohttp.ClientSession(loop = self.loop)
	
	async def connect_to_database(self):
		if self.database_connection_pool:
			return
		if self.connected_to_database.is_set():
			self.connected_to_database.clear()
			self.db = self.database = self.database_connection_pool = await create_database_pool()
			self.connected_to_database.set()
		else:
			await self.connected_to_database.wait()
	
	async def initialize_database(self):
		await self.connect_to_database()
		await self.db.execute("CREATE SCHEMA IF NOT EXISTS chat")
		await self.db.execute("CREATE SCHEMA IF NOT EXISTS direct_messages")
		await self.db.execute("CREATE SCHEMA IF NOT EXISTS guilds")
		await self.db.execute("CREATE SCHEMA IF NOT EXISTS users")
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS chat.messages (
				created_at				TIMESTAMPTZ, 
				message_id				BIGINT PRIMARY KEY, 
				author_id				BIGINT, 
				author_name				TEXT, 
				author_discriminator	TEXT, 
				author_display_name		TEXT, 
				direct_message			BOOL, 
				channel_id				BIGINT, 
				channel_name			TEXT, 
				guild_id				BIGINT, 
				guild_name				TEXT, 
				message_content			TEXT, 
				embeds					JSONB []
			)
			"""
		)
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS chat.edits (
				edited_at		TIMESTAMPTZ, 
				message_id		BIGINT REFERENCES chat.messages(message_id) ON DELETE CASCADE, 
				before_content	TEXT,
				after_content	TEXT, 
				before_embeds	JSONB [], 
				after_embeds	JSONB [], 
				PRIMARY KEY		(edited_at, message_id)
			)
			"""
		)
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS direct_messages.prefixes (
				channel_id	BIGINT PRIMARY KEY, 
				prefixes	TEXT []
			)
			"""
		)
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS guilds.prefixes (
				guild_id	BIGINT PRIMARY KEY, 
				prefixes	TEXT []
			)
			"""
		)
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS guilds.settings (
				guild_id		BIGINT, 
				name			TEXT, 
				setting			BOOL, 
				PRIMARY KEY		(guild_id, name)
			)
			"""
		)
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS users.stats (
				user_id				BIGINT PRIMARY KEY, 
				commands_executed	INT
			)
			"""
		)
	
	async def web_server_get_handler(self, request):
		'''
		async for line in request.content:
			print(line)
		'''
		hub_mode = request.query.get("hub.mode")
		if hub_mode == "denied":
			# TODO: Handle denied request
			return web.Response(stats = 501)  # Return 501 Not Implemented
		elif hub_mode in ("subscribe", "unsubscribe"):
			if "YouTube" not in self.cogs:
				return web.Response(status = 503)  # Return 503 Service Unavailable
			channel_id = parse.parse_qs(parse.urlparse(request.query.get("hub.topic")).query)["channel_id"][0]
			if ((channel_id in self.get_cog("YouTube").youtube_uploads_following and hub_mode == "subscribe") or 
				(channel_id not in self.get_cog("YouTube").youtube_uploads_following and hub_mode == "unsubscribe")):
				return web.Response(body = request.query.get("hub.challenge"))
			else:
				return web.Response(status = 404)  # Return 404 Not Found
		else:
			return web.Response(status = 400)  # Return 400 Bad Request
	
	async def web_server_post_handler(self, request):
		'''
		async for line in request.content:
			print(line)
		'''
		if (request.headers.get("User-Agent") == "FeedFetcher-Google; (+http://www.google.com/feedfetcher.html)" and 
			request.headers.get("From") == "googlebot(at)googlebot.com" and 
			request.content_type == "application/atom+xml"):
			if "YouTube" not in self.cogs:
				return web.Response(status = 503)  # Return 503 Service Unavailable
			for link in requests.utils.parse_header_links(request.headers.get("Link")):
				if link["rel"] == "hub":
					if link["url"] != "http://pubsubhubbub.appspot.com/":
						return web.Response(status = 400)  # Return 400 Bad Request
				elif link["rel"] == "self":
					channel_id = parse.parse_qs(parse.urlparse(link["url"]).query)["channel_id"][0]
					if channel_id not in self.get_cog("YouTube").youtube_uploads_following:
						return web.Response(status = 404)  # Return 404 Not Found
						# TODO: Handle unsubscribe?
				else:
					return web.Response(status = 400)  # Return 400 Bad Request
			request_content = await request.content.read()
			await self.get_cog("YouTube").process_youtube_upload(channel_id, request_content)
			return web.Response()
		else:
			return web.Response(status = 400)  # Return 400 Bad Request
	
	async def web_server_robots_txt(self, request):
		return web.Response(text = "User-agent: *\nDisallow: /")
	
	async def on_ready(self):
		self.cache_channel = self.get_channel(self.cache_channel_id)
		self.listener_bot = await self.fetch_user(self.listener_id)
		self.listing_sites = {"discord.bots.gg": {"name": "Discord Bots", "token": self.DISCORD_BOTS_GG_API_TOKEN, 
													"url": f"https://discord.bots.gg/api/v1/bots/{self.user.id}/stats", 
													"data": {"guildCount": len(self.guilds)}, 
													"guild_count_name": "guildCount"}, 
								"discordbots.org": {"name": "Discord Bot List", "token": self.DISCORDBOTS_ORG_API_KEY, 
													"url": f"https://discordbots.org/api/bots/{self.user.id}/stats", 
													"data": {"server_count": len(self.guilds)}, 
													"guild_count_name": "server_count"}, 
								"discordbotlist.com": {"name": "Discord Bot List", 
														"token": f"Bot {self.DISCORDBOTLIST_COM_API_TOKEN}", 
														"url": f"https://discordbotlist.com/api/bots/{self.user.id}/stats", 
														"data": {"guilds": len(self.guilds)}, 
														"guild_count_name": "guilds"}}
		# TODO: Add users and voice_connections for discordbotlist.com
		await self.update_all_listing_stats()
	
	async def on_resumed(self):
		print(f"{self.console_message_prefix}resumed @ {datetime.datetime.now().time().isoformat()}")
	
	async def on_disconnect(self):
		print(f"{self.console_message_prefix}disconnected @ {datetime.datetime.now().time().isoformat()}")
	
	async def on_guild_join(self, guild):
		await self.update_all_listing_stats()
	
	async def on_guild_remove(self, guild):
		await self.update_all_listing_stats()
	
	# TODO: on_command_completion
	async def on_command(self, ctx):
		self.session_commands_executed[ctx.command.name] = self.session_commands_executed.get(ctx.command.name, 0) + 1
	
	async def on_command_error(self, ctx, error):
		# Ignore
		## Not owner
		if isinstance(error, commands.NotOwner):
			return
		## Command disabled or not found
		if isinstance(error, (commands.CommandNotFound, commands.DisabledCommand)):
			return
		# Check Failure
		## Guild only
		if isinstance(error, commands.NoPrivateMessage):
			return await ctx.embed_reply("Please use that command in a server")
		## User missing permissions
		if isinstance(error, (errors.NotServerOwner, errors.MissingPermissions)):
			# Also for commands.NotOwner?
			return await ctx.embed_reply(":no_entry: You don't have permission to do that")
		## Bot missing permissions
		if isinstance(error, errors.MissingCapability):
			if "embed_links" in error.permissions:
				return await ctx.send("I don't have permission to do that here\n"
										"I need the permission(s): " + ', '.join(error.permissions))
			return await ctx.embed_reply("I don't have permission to do that here\n"
											"I need the permission(s): " + ', '.join(error.permissions))
		## User not permitted to use command
		if isinstance(error, errors.NotPermitted):
			return await ctx.embed_reply(":no_entry: You don't have permission to use that command here")
		## Not in voice channel + user permitted
		if isinstance(error, errors.PermittedVoiceNotConnected):
			return await ctx.embed_reply("I'm not in a voice channel\n"
											f"Please use `{ctx.prefix}join` first")
		## Not in voice channel + user not permitted
		if isinstance(error, errors.NotPermittedVoiceNotConnected):
			return await ctx.embed_reply("I'm not in a voice channel\n"
											f"Please ask someone with permission to use `{ctx.prefix}join` first")
		# User Input Error
		## Missing required input
		if isinstance(error, commands.MissingRequiredArgument):
			return await ctx.embed_reply(str(error).rstrip('.').replace("argument", "input"))
		## Input parsing error
		if isinstance(error, commands.ArgumentParsingError):
			return await ctx.embed_reply(":no_entry: Error parsing input: " + str(error).replace("'", '`'))
		## Bad input
		if isinstance(error, commands.BadArgument):
			return await ctx.embed_reply(f":no_entry: Error: Invalid Input: {error}")
		# Command Invoke Error
		if isinstance(error, commands.CommandInvokeError):
			## Unable to bulk delete messages older than 14 days
			if isinstance(error.original, discord.HTTPException) and error.original.code == 50034:
				return await ctx.embed_reply(":no_entry: Error: You can only bulk delete messages that are under 14 days old")
			## Bot missing permissions (Unhandled)
			if isinstance(error.original, (discord.Forbidden)):
				return print(f"{self.console_message_prefix}Missing Permissions for {ctx.command.qualified_name} in #{ctx.channel.name} in {ctx.guild.name}")
			## Handled with local error handler
			if isinstance(error.original, youtube_dl.utils.DownloadError):
				return
		# TODO: check embed links permission
		# Unhandled
		self.sentry_client.captureException(exc_info = (type(error), error, error.__traceback__))
		print(f"Ignoring exception in command {ctx.command}", file = sys.stderr)
		traceback.print_exception(type(error), error, error.__traceback__, file = sys.stderr)
		logging.getLogger("errors").error("Uncaught exception\n", exc_info = (type(error), error, error.__traceback__))
	
	async def on_error(self, event_method, *args, **kwargs):
		error_type, value, error_traceback = sys.exc_info()
		if error_type is discord.Forbidden:
			for arg in args:
				if isinstance(arg, commands.context.Context):
					return print(f"{self.console_message_prefix}Missing Permissions for {arg.command.qualified_name} in #{arg.channel.name} in {arg.guild.name}")
				if isinstance(arg, discord.Message):
					return print(f"Missing Permissions for #{arg.channel.name} in {arg.guild.name}")
		await super().on_error(event_method, *args, **kwargs)
		logging.getLogger("errors").error("Uncaught exception\n", exc_info = (error_type, value, error_traceback))
	
	async def on_message_edit(self, before, after):
		if after.edited_at != before.edited_at:
			if before.content != after.content:
				await self.db.execute(
					"""
					INSERT INTO chat.edits (edited_at, message_id, before_content, after_content)
					SELECT $1, $2, $3, $4
					WHERE EXISTS (SELECT * FROM chat.messages WHERE chat.messages.message_id = $2)
					ON CONFLICT (edited_at, message_id) DO
					UPDATE SET before_content = $3, after_content = $4
					""", 
					after.edited_at.replace(tzinfo = datetime.timezone.utc), after.id, 
					before.content.replace('\N{NULL}', ""), after.content.replace('\N{NULL}', "")
				)
			before_embeds = [embed.to_dict() for embed in before.embeds]
			after_embeds = [embed.to_dict() for embed in after.embeds]
			if before_embeds != after_embeds:
				await self.db.execute(
					"""
					INSERT INTO chat.edits (edited_at, message_id, before_embeds, after_embeds)
					SELECT $1, $2, $3, $4
					WHERE EXISTS (SELECT * FROM chat.messages WHERE chat.messages.message_id = $2)
					ON CONFLICT (edited_at, message_id) DO
					UPDATE SET before_embeds = CAST($3 AS jsonb[]), after_embeds = CAST($4 AS jsonb[])
					""", 
					after.edited_at.replace(tzinfo = datetime.timezone.utc), after.id, before_embeds, after_embeds
				)
	
	# TODO: optimize/overhaul
	def send_embed(self, destination, description = None, *, title = discord.Embed.Empty, title_url = discord.Embed.Empty, 
	author_name = "", author_url = discord.Embed.Empty, author_icon_url = discord.Embed.Empty, 
	image_url = None, thumbnail_url = None, footer_text = discord.Embed.Empty, footer_icon_url = discord.Embed.Empty, 
	timestamp = discord.Embed.Empty, fields = []):
		embed = discord.Embed(title = title, url = title_url, timestamp = timestamp, color = self.bot_color)
		embed.description = str(description) if description else discord.Embed.Empty
		if author_name: embed.set_author(name = author_name, url = author_url, icon_url = author_icon_url)
		if image_url: embed.set_image(url = image_url)
		if thumbnail_url: embed.set_thumbnail(url = thumbnail_url)
		embed.set_footer(text = footer_text, icon_url = footer_icon_url)
		for field_name, field_value in fields:
			embed.add_field(name = field_name, value = field_value)
		return destination.send(embed = embed)
	
	async def attempt_delete_message(self, message):
		try:
			await message.delete()
		except (discord.Forbidden, discord.NotFound):
			pass
	
	async def wait_for_reaction_add_or_remove(self, *, emoji = None, message = None, user = None, timeout = None):
		def reaction_check(reaction, reaction_user):
			if emoji:
				if isinstance(emoji, (str, discord.Emoji, discord.PartialEmoji)) and reaction.emoji != emoji:
					return False
				elif reaction.emoji not in emoji:
					return False
			if message and reaction.message.id != message.id:
				return False
			if user and reaction_user.id != user.id:
				return False
			return True
		
		add = self.wait_for("reaction_add", check = reaction_check, timeout = timeout)
		remove = self.wait_for("reaction_remove", check = reaction_check, timeout = timeout)
		done, pending = await asyncio.wait((add, remove), return_when = asyncio.FIRST_COMPLETED)
		for task in pending:
			task.cancel()
		return done.pop().result()
	
	# Override Context class
	async def get_context(self, message, *, cls = Context):
		ctx = await super().get_context(message, cls = cls)
		return ctx
	
	# TODO: Case-Insensitive subcommands (override Group)
	
	async def get_guild_setting(self, guild_id, name):
		if guild_id not in self.guild_settings:
			await self.retrieve_guild_settings(guild_id)
		return self.guild_settings[guild_id].get(name)
	
	async def get_guild_settings(self, guild_id):
		if guild_id not in self.guild_settings:
			await self.retrieve_guild_settings(guild_id)
		return self.guild_settings[guild_id]
	
	async def retrieve_guild_settings(self, guild_id):
		self.guild_settings[guild_id] = {}
		records = await self.db.fetch(
			"""
			SELECT name, setting
			FROM guilds.settings
			WHERE guild_id = $1
			""", 
			guild_id
		)
		for record in records:
			self.guild_settings[guild_id][record["name"]] = record["setting"]
	
	async def set_guild_setting(self, guild_id, name, setting):
		await self.db.execute(
			"""
			INSERT INTO guilds.settings (guild_id, name, setting)
			VALUES ($1, $2, $3)
			ON CONFLICT (guild_id, name) DO
			UPDATE SET setting = $3
			""", 
			guild_id, name, setting
		)
		self.guild_settings.setdefault(guild_id, {})[name] = setting
	
	# Update stats on sites listing Discord bots
	async def update_listing_stats(self, site):
		site = self.listing_sites.get(site)
		if not site:
			# TODO: Print/log error
			return "Site not found"
		token = site["token"]
		if not token:
			# TODO: Print/log error
			return "Site token not found"
		url = site["url"]
		headers = {"authorization": token, "content-type": "application/json"}
		site["data"][site["guild_count_name"]] = len(self.guilds)
		# TODO: Add users and voice_connections for discordbotlist.com
		data = json.dumps(site["data"])
		async with self.aiohttp_session.post(url, headers = headers, data = data) as resp:
			if resp.status == 204:
				return "204 No Content"
			return await resp.text()
	
	# Update stats on all sites listing Discord bots
	async def update_all_listing_stats(self):
		for site in self.listing_sites:
			await self.update_listing_stats(site)
	
	async def restart_tasks(self, channel_id):
		# Increment restarts counter
		await self.db.execute(
			"""
			UPDATE meta.stats
			SET restarts = restarts + 1
			WHERE timestamp = $1
			""", 
			self.online_time
		)
		# Save restart text channel + voice channels
		audio_cog = self.get_cog("Audio")
		voice_channels = audio_cog.save_voice_channels() if audio_cog else []
		with open(data_path + "/temp/restart_channel.json", 'w') as restart_channel_file:
			json.dump({"restart_channel": channel_id, "voice_channels": voice_channels}, restart_channel_file)
	
	async def shutdown_tasks(self):
		# Cancel audio tasks
		audio_cog = self.get_cog("Audio")
		if audio_cog:
			audio_cog.cancel_all_tasks()
		# Save uptime
		now = datetime.datetime.now(datetime.timezone.utc)
		uptime = now - self.online_time
		await self.db.execute(
			"""
			UPDATE meta.stats
			SET uptime = uptime + $2
			WHERE timestamp = $1
			""", 
			self.online_time, uptime
		)
		# Close Sentry transport
		sentry_transport = self.sentry_client.remote.get_transport()
		if sentry_transport:
			await sentry_transport.close()
		# Close aiohttp session
		await self.aiohttp_session.close()
		# Close database connection
		await self.database_connection_pool.close()
		# Stop web server
		await self.aiohttp_app_runner.cleanup()
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@commands.is_owner()
	async def load(ctx, cog : str):
		'''Load cog'''
		try:
			ctx.bot.load_extension("cogs." + cog)
		except commands.ExtensionAlreadyLoaded:
			await ctx.embed_reply(":no_entry: Error: Cog already loaded")
		except commands.ExtensionFailed as e:
			await ctx.embed_reply(f":no_entry: Error loading cog: {e.original.__class__.__name__}: {e.original}")
		except commands.ExtensionNotFound:
			await ctx.embed_reply(":no_entry: Error: Cog not found")
		except commands.NoEntryPointError:
			await ctx.embed_reply(":no_entry: Error: Setup function not found")
		except commands.ExtensionError as e:
			await ctx.embed_reply(f":no_entry: Error: {e}")
		except Exception as e:
			await ctx.embed_reply(f":thumbsdown::skin-tone-2: Failed to load `{cog}` cog\n{type(e).__name__}: {e}")
		else:
			await ctx.embed_reply(f":thumbsup::skin-tone-2: Loaded `{cog}` cog :gear:")
	
	@commands.command(name = "aiml", aliases = ["brain"])
	@commands.is_owner()
	async def load_aiml(ctx):
		'''Load AIML'''
		for predicate, value in ctx.bot.aiml_predicates.items():
			ctx.bot.aiml_kernel.setBotPredicate(predicate, value)
		if os.path.isfile(data_path + "/aiml/aiml_brain.brn"):
			ctx.bot.aiml_kernel.bootstrap(brainFile = data_path + "/aiml/aiml_brain.brn")
		elif os.path.isfile(data_path + "/aiml/std-startup.xml"):
			ctx.bot.aiml_kernel.bootstrap(learnFiles = data_path + "/aiml/std-startup.xml", commands = "load aiml b")
			ctx.bot.aiml_kernel.saveBrain(data_path + "/aiml/aiml_brain.brn")
		await ctx.embed_reply(":ok_hand::skin-tone-2: Loaded AIML")
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@commands.is_owner()
	async def unload(ctx, cog : str):
		'''Unload cog'''
		try:
			ctx.bot.unload_extension("cogs." + cog)
		except commands.ExtensionNotLoaded:
			await ctx.embed_reply(":no_entry: Error: Cog not found/loaded")
		except commands.ExtensionError as e:
			await ctx.embed_reply(f":no_entry: Error: {e}")
		except Exception as e:
			await ctx.embed_reply(f":thumbsdown::skin-tone-2: Failed to unload `{cog}` cog\n{type(e).__name__}: {e}")
		else:
			await ctx.embed_reply(f":ok_hand::skin-tone-2: Unloaded `{cog}` cog :gear:")
	
	@commands.command(name = "aiml", aliases = ["brain"])
	@commands.is_owner()
	async def unload_aiml(ctx):
		'''Unload AIML'''
		ctx.bot.aiml_kernel.resetBrain()
		await ctx.embed_reply(":ok_hand::skin-tone-2: Unloaded AIML")
	
	@commands.command()
	@commands.is_owner()
	async def reload(ctx, cog : str):
		'''Reload cog'''
		try:
			ctx.bot.reload_extension("cogs." + cog)
		except commands.ExtensionFailed as e:
			await ctx.embed_reply(f":no_entry: Error loading cog: {e.original.__class__.__name__}: {e.original}")
		except commands.ExtensionNotFound:
			await ctx.embed_reply(":no_entry: Error: Cog not found")
		except commands.ExtensionNotLoaded:
			await ctx.embed_reply(":no_entry: Error: Cog not found/loaded")
		except commands.NoEntryPointError:
			await ctx.embed_reply(":no_entry: Error: Setup function not found")
		except commands.ExtensionError as e:
			await ctx.embed_reply(f":no_entry: Error: {e}")
		except Exception as e:
			await ctx.embed_reply(f":thumbsdown::skin-tone-2: Failed to reload `{cog}` cog\n{type(e).__name__}: {e}")
		else:
			await ctx.bot.db.execute(
				"""
				UPDATE meta.stats
				SET cogs_reloaded = cogs_reloaded + 1
				WHERE timestamp = $1
				""", 
				ctx.bot.online_time
			)
			await ctx.embed_reply(f":thumbsup::skin-tone-2: Reloaded `{cog}` cog :gear:")


def create_file(filename, content = None, filetype = "json"):
	if content is None:
		content = {}
	try:
		with open(f"{data_path}/{filename}.{filetype}", 'x') as file:
			json.dump(content, file, indent = 4)
	except FileExistsError:
		pass
	except OSError:
		pass  # TODO: Handle?

async def get_prefix(bot, message):
	if message.channel.type is discord.ChannelType.private:
		prefixes = await bot.db.fetchval(
			"""
			SELECT prefixes
			FROM direct_messages.prefixes
			WHERE channel_id = $1
			""", 
			message.channel.id
		)
	else:
		prefixes = await bot.db.fetchval(
			"""
			SELECT prefixes
			FROM guilds.prefixes
			WHERE guild_id = $1
			""", 
			message.guild.id
		)
	return prefixes if prefixes else '!'

