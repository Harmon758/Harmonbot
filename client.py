
from discord.ext import commands
from aiohttp import ClientSession
from cleverbot import Cleverbot
from datetime import datetime
from os import listdir

wait_time = 15.0
online_time = datetime.utcnow()
aiohttp_session = ClientSession()
cleverbot_instance = Cleverbot()

class Bot(commands.Bot):
	
	def reply(self, content, *args, **kwargs):
		author = commands.bot._get_variable('_internal_author')
		destination = commands.bot._get_variable('_internal_channel')
		fmt = '{0.mention}: {1}'.format(author, str(content))
		return self.send_message(destination, fmt, *args, **kwargs)
	
client = Bot(command_prefix = '!', description = "Harmonbot", pm_help = None)

for file in listdir("cogs"):
	if file.endswith(".py"):
		client.load_extension("cogs." + file[:-3])
