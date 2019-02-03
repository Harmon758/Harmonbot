
from twitchio.ext import commands

import os

import dotenv

class Bot(commands.Bot):
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.version = "3.0.0-a.0"
	
	async def event_ready(self):
		print(f"Ready | {self.nick}")

dotenv.load_dotenv()
bot = Bot(irc_token = os.getenv("TWITCH_BOT_ACCOUNT_OAUTH_TOKEN"), 
			client_id = os.getenv("TWITCH_CLIENT_ID"), 
			nick = "harmonbot", prefix = '!', initial_channels = ("harmonbot",))
bot.run()

