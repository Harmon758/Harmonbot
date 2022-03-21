
from twitchio.ext import commands

import asyncio
import datetime
import os
import sys

import aiohttp
import asyncpg
import dotenv
import pyowm

from utilities import context
from utilities import logging

sys.path.insert(0, "..")
from units.games import eightball
sys.path.pop(0)

class Bot(commands.Bot):
	
	def __init__(self, loop = None, initial_channels = None, **kwargs):
		self.version = "3.0.0-b.138"
		
		loop = loop or asyncio.get_event_loop()
		if initial_channels is None:
			initial_channels = []
		initial_channels = list(initial_channels)
		
		# Constants
		self.char_limit = self.character_limit = 500
		
		# aiohttp Client Session - initialized on ready
		self.aiohttp_session = None
		
		# Credentials
		for credential in ("DATABASE_PASSWORD", "OWM_API_KEY", "POSTGRES_HOST", "WORDNIK_API_KEY", 
							"YANDEX_TRANSLATE_API_KEY"):
			setattr(self, credential, os.getenv(credential))
		if not self.POSTGRES_HOST:
			self.POSTGRES_HOST = "localhost"
		self.DATABASE_HOST = self.POSTGRES_HOST
		
		## OpenWeatherMap
		self.owm_client = pyowm.OWM(self.OWM_API_KEY)
		self.weather_manager = self.owm_client.weather_manager()
		# TODO: Async OWM calls
		# TODO: Weather functions in location unit
		
		# PostgreSQL database connection
		self.db = self.database = self.database_connection_pool = None
		self.connected_to_database = asyncio.Event()
		self.connected_to_database.set()
		loop.run_until_complete(self.initialize_database())
		
		records = loop.run_until_complete(self.db.fetch("SELECT channel FROM twitch.channels"))
		initial_channels.extend(record["channel"] for record in records)
		super().__init__(loop = loop, initial_channels = initial_channels, **kwargs)
		# TODO: Handle channel name changes, store channel ID
		
		# Add commands with set responses
		loop.run_until_complete(self.add_set_response_commands())
		
		# Load cogs
		for file in sorted(os.listdir("cogs")):
			if file.endswith(".py"):
				self.load_module("cogs." + file[:-3])
	
	async def connect_to_database(self):
		if self.database_connection_pool:
			return
		if self.connected_to_database.is_set():
			self.connected_to_database.clear()
			self.database_connection_pool = await asyncpg.create_pool(user = "harmonbot", 
																		password = self.DATABASE_PASSWORD, 
																		database = "harmonbot", host = self.DATABASE_HOST)
			self.db = self.database = self.database_connection_pool
			self.connected_to_database.set()
		else:
			await self.connected_to_database.wait()
	
	async def initialize_database(self):
		await self.connect_to_database()
		await self.db.execute("CREATE SCHEMA IF NOT EXISTS twitch")
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitch.birthdays (
				channel			TEXT PRIMARY KEY, 
				month			INT, 
				day				INT
			)
			"""
		)
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitch.channels (
				channel		TEXT PRIMARY KEY
			)
			"""
		)
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitch.commands (
				channel			TEXT, 
				name			TEXT, 
				response		TEXT, 
				PRIMARY KEY		(channel, name)
			)
			"""
		)
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitch.aliases (
				channel			TEXT, 
				name			TEXT, 
				alias			TEXT, 
				PRIMARY KEY		(channel, alias), 
				FOREIGN KEY		(channel, name) REFERENCES twitch.commands (channel, name) ON DELETE CASCADE
			)
			"""
		)
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitch.counters (
				channel			TEXT, 
				name			TEXT, 
				value			INT, 
				PRIMARY KEY		(channel, name)
			)
			"""
		)
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitch.messages (
				timestamp			TIMESTAMPTZ PRIMARY KEY DEFAULT NOW(), 
				channel				TEXT, 
				author				TEXT, 
				message				TEXT, 
				message_timestamp	TIMESTAMPTZ
			)
			"""
		)
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitch.locations (
				channel		TEXT PRIMARY KEY, 
				location	TEXT
			)
			"""
		)
		await self.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitch.toggles (
				channel			TEXT, 
				name			TEXT, 
				status			BOOLEAN, 
				PRIMARY KEY		(channel, name)
			)
			"""
		)
		# Migrate variables
		import json
		for file in os.listdir("data/variables"):
			channel = file[:-5]  # - .json
			with open(f"data/variables/{channel}.json", 'r') as variables_file:
				variables = json.load(variables_file)
				for name, value in variables.items():
					if isinstance(value, bool) or value is None:
						if name.endswith(".status"):
							name = name[:-7]
						await self.db.execute(
							"""
							INSERT INTO twitch.toggles (channel, name, status)
							VALUES ($1, $2, $3)
							ON CONFLICT (channel, name) DO
							UPDATE SET status = $3
							""", 
							channel, name, value
						)
					elif isinstance(value, int) and not name.startswith("birthday"):
						await self.db.execute(
							"""
							INSERT INTO twitch.counters (channel, name, value)
							VALUES ($1, $2, $3)
							ON CONFLICT (channel, name) DO
							UPDATE SET value = $3
							""", 
							channel, name, value
						)
	
	async def add_set_response_commands(self):
		"""Add commands with set responses"""
		records = await self.db.fetch("SELECT name, response FROM twitch.commands WHERE channel = 'harmonbot'")
		def set_response_command_wrapper(response):
			async def set_response_command(ctx):
				await ctx.send(response)
			return set_response_command
		for record in records:
			self.add_command(commands.Command(name = record["name"], 
												func = set_response_command_wrapper(record["response"])))
	
	async def event_ready(self):
		print(f"Ready | {self.nick}")
		
		# Initialize aiohttp Client Session
		if not self.aiohttp_session:
			self.aiohttp_session = aiohttp.ClientSession(loop = self.loop)
	
	async def event_message(self, message):
		# Log messages
		await self.db.execute(
			"""
			INSERT INTO twitch.messages (timestamp, channel, author, message, message_timestamp)
			VALUES ($1, $2, $3, $4, $5)
			""", 
			datetime.datetime.now(), message.channel.name, message.author.name, message.content, 
			None if message.echo else message.timestamp.replace(tzinfo = datetime.timezone.utc)
		)
		# Ignore own messages
		if message.author.name == "harmonbot":
			return
		# Get Context
		ctx = await self.get_context(message, cls = context.Context)
		# Handle channel-specific commands with set responses
		if ctx.prefix and ctx.channel.name != "harmonbot":
			arguments = message.content[len(ctx.prefix):].lstrip().lower().split()
			if arguments:
				command = arguments[0]
				aliased = await self.db.fetchval(
					"""
					SELECT name
					from twitch.aliases
					WHERE channel = $1 AND alias = $2
					""", 
					ctx.channel.name, command
				)
				if aliased:
					command = aliased
				response = await self.db.fetchval(
					"""
					SELECT response
					FROM twitch.commands
					WHERE channel = $1 AND name = $2
					""", 
					ctx.channel.name, command
				)
				if response:
					await ctx.send(response)
					ctx.channel_command = command
					# Return? Override main commands?
		# Handle commands
		await self.handle_commands(message, ctx = ctx)
		# TODO: command on/off settings
		# TODO: help command, command help?
		if message.content.startswith('\N{BILLIARDS}'):
			await ctx.send(f"\N{BILLIARDS} {eightball()}")
	
	async def event_command_error(self, ctx, error):
		if isinstance(error, commands.BadArgument):
			await ctx.send(str(error).replace('`', "'").replace("<class ", "").replace('>', ""))
		elif isinstance(error, commands.CommandNotFound):
			# TODO: Handle command not found
			if ctx.channel_command:
				return
		elif isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(str(error).rstrip('.').replace("argument", "input"))
		else:
			# TODO: Sentry
			await super().event_command_error(ctx, error)
	
	async def event_raw_data(self, data):
		logging.raw_data_logger.info(data)
	
	@commands.command()
	async def test(self, ctx):
		await ctx.send("Hello, World!")
	
	@commands.command(aliases = ("8ball", '\N{BILLIARDS}'))
	async def eightball(self, ctx):
		await ctx.send(f"\N{BILLIARDS} {eightball()}")

dotenv.load_dotenv()
bot = Bot(irc_token = os.getenv("TWITCH_BOT_ACCOUNT_OAUTH_TOKEN"), 
			client_id = os.getenv("TWITCH_CLIENT_ID"), 
			client_secret = os.getenv("TWITCH_CLIENT_SECRET"), 
			nick = "harmonbot", prefix = '!')
bot.run()

