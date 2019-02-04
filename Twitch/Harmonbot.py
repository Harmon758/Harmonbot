
from twitchio.ext import commands

import asyncio
import os
import sys

import asyncpg
import dotenv

sys.path.insert(0, "..")
from units.games import eightball
sys.path.pop(0)

class Bot(commands.Bot):
	
	def __init__(self, loop = None, initial_channels = [], **kwargs):
		self.version = "3.0.0-b.2"
		
		loop = loop or asyncio.get_event_loop()
		initial_channels = list(initial_channels)
		
		# Credentials
		for credential in ("DATABASE_PASSWORD", "POSTGRES_HOST"):
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
	
	async def event_ready(self):
		print(f"Ready | {self.nick}")
	
	async def event_message(self, message):
		await self.handle_commands(message)
		if message.content.startswith('\N{BILLIARDS}'):
			await message.channel.send(f"\N{BILLIARDS} {eightball()}")
	
	@commands.command()
	async def test(self, ctx):
		await ctx.send("Hello, World!")
	
	@commands.command(aliases = ("8ball", '\N{BILLIARDS}'))
	async def eightball(self, ctx):
		await ctx.send(f"\N{BILLIARDS} {eightball()}")

dotenv.load_dotenv()
bot = Bot(irc_token = os.getenv("TWITCH_BOT_ACCOUNT_OAUTH_TOKEN"), 
			client_id = os.getenv("TWITCH_CLIENT_ID"), 
			nick = "harmonbot", prefix = '!')
bot.run()

