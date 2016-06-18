
from discord.ext import commands
import aiohttp
import cleverbot
import datetime
import inflect
import json
import os

wait_time = 15.0
code_block = "```\n{}\n```"
py_code_block = "```py\n{}\n```"
online_time = datetime.datetime.utcnow()
aiohttp_session = aiohttp.ClientSession()
cleverbot_instance = cleverbot.Cleverbot()
inflect_engine = inflect.engine()

class Bot(commands.Bot):
	
	def reply(self, content, *args, **kwargs):
		author = commands.bot._get_variable('_internal_author')
		destination = commands.bot._get_variable('_internal_channel')
		fmt = '{0.mention}: {1}'.format(author, str(content))
		return self.send_message(destination, fmt, *args, **kwargs)

try:
	with open("data/prefixes.json", "x") as prefixes_file:
		json.dump({}, prefixes_file)
except FileExistsError:
	pass

def get_prefix(bot, message):
	with open("data/prefixes.json", "r") as prefixes_file:
		all_prefixes = json.load(prefixes_file)
	if message.channel.is_private:
		prefixes = all_prefixes.get(message.channel.id, None)
	else:
		prefixes = all_prefixes.get(message.server.id, None)
	return prefixes if prefixes else '!'
	
client = Bot(command_prefix = get_prefix, description = "Harmonbot", pm_help = None)
# help_attrs = {hidden = True} ?

for file in os.listdir("cogs"):
	if file.endswith(".py"):
		client.load_extension("cogs." + file[:-3])

