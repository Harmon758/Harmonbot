
from twitchio.ext import commands

import asyncio
import datetime
import os
import sys

import aiohttp
import asyncpg
import dotenv

from utilities import logging

sys.path.insert(0, "..")
from units.games import eightball
sys.path.pop(0)

class Bot(commands.Bot):
	
	def __init__(self, loop = None, initial_channels = [], **kwargs):
		self.version = "3.0.0-b.26"
		
		loop = loop or asyncio.get_event_loop()
		initial_channels = list(initial_channels)
		
		# Constants
		self.char_limit = self.character_limit = 500
		
		# aiohttp Client Session - initialized on ready
		self.aiohttp_session = None
		
		# Credentials
		for credential in ("DATABASE_PASSWORD", "POSTGRES_HOST", "WORDNIK_API_KEY", "YANDEX_TRANSLATE_API_KEY"):
			setattr(self, credential, os.getenv(credential))
		if not self.POSTGRES_HOST:
			self.POSTGRES_HOST = "localhost"
		self.DATABASE_HOST = self.POSTGRES_HOST
		
		# PostgreSQL database connection
		self.db = self.database = self.database_connection_pool = None
		self.connected_to_database = asyncio.Event()
		self.connected_to_database.set()
		loop.run_until_complete(self.initialize_database())
		
		records = loop.run_until_complete(self.db.fetch("SELECT channel FROM twitch.channels"))
		initial_channels.extend(record["channel"] for record in records)
		super().__init__(loop = loop, initial_channels = initial_channels, **kwargs)
		# TODO: Handle channel name changes?
		
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
			CREATE TABLE IF NOT EXISTS twitch.channels (
				channel		TEXT PRIMARY KEY
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
	
	async def event_ready(self):
		print(f"Ready | {self.nick}")
		
		# Initialize aiohttp Client Session
		self.aiohttp_session = aiohttp.ClientSession(loop = self.loop)
	
	async def event_message(self, message):
		# Log messages
		await self.db.execute(
			"""
			INSERT INTO twitch.messages (channel, author, message, message_timestamp)
			VALUES ($1, $2, $3, $4)
			""", 
			message.channel.name, message.author.name, message.content, 
			None if message.echo else message.timestamp.replace(tzinfo = datetime.timezone.utc)
		)
		# Ignore own messages
		if message.author.name == "harmonbot":
			return
		# Handle commands
		await self.handle_commands(message)
		if message.content.startswith('\N{BILLIARDS}'):
			await message.channel.send(f"\N{BILLIARDS} {eightball()}")
	
	async def event_command_error(self, ctx, error):
		# TODO: Handle command not found
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(str(error).rstrip('.').replace("argument", "input"))
		else:
			# TODO: Sentry
			await super().event_command_error(ctx, error)
	
	async def event_raw_data(self, data):
		logging.raw_data_logger.info(data)
	
	@commands.command()
	async def test(self, ctx):
		await ctx.send("Hello, World!")
	
	@commands.command()
	async def bye(self, ctx, *, user = None):
		if not user or user.lower() == "harmonbot":
			await ctx.send(f"Bye, {ctx.author.name.capitalize()}!")
		else:
			await ctx.send(f"{user.title()}, {ctx.author.name.capitalize()} says goodbye!")
	
	@commands.command(aliases = ("hi",))
	async def hello(self, ctx, *, user = None):
		if not user or user.lower() == "harmonbot":
			await ctx.send(f"Hello, {ctx.author.name.capitalize()}!")
		else:
			await ctx.send(f"{user.title()}, {ctx.author.name.capitalize()} says hello!")
	
	@commands.command(aliases = ("congrats", "grats", "gz"))
	async def congratulations(self, ctx, *, user = None):
		if not user:
			await ctx.send("Congratulations!!!!!")
		else:
			await ctx.send(f"Congratulations, {user.title()}!!!!!")
	
	@commands.command(aliases = ("8ball", '\N{BILLIARDS}'))
	async def eightball(self, ctx):
		await ctx.send(f"\N{BILLIARDS} {eightball()}")

dotenv.load_dotenv()
bot = Bot(irc_token = os.getenv("TWITCH_BOT_ACCOUNT_OAUTH_TOKEN"), 
			client_id = os.getenv("TWITCH_CLIENT_ID"), 
			nick = "harmonbot", prefix = '!')
bot.run()

