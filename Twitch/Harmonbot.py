
from twitchio.ext import commands

import asyncio
import os

import asyncpg
import dotenv

class Bot(commands.Bot):
	
	def __init__(self, loop = None, **kwargs):
		self.version = "3.0.0-a.1"
		
		loop = loop or asyncio.get_event_loop()
		
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
		
		super().__init__(loop = loop, **kwargs)
	
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
	
	async def event_ready(self):
		print(f"Ready | {self.nick}")

dotenv.load_dotenv()
bot = Bot(irc_token = os.getenv("TWITCH_BOT_ACCOUNT_OAUTH_TOKEN"), 
			client_id = os.getenv("TWITCH_CLIENT_ID"), 
			nick = "harmonbot", prefix = '!', initial_channels = ("harmonbot",))
bot.run()

