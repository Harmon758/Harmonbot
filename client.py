
# import discord
from discord.ext import commands
# client = discord.Client()
import datetime

wait_time = 10.0

class Bot(commands.Bot):
	def reply(self, content, *args, **kwargs):
		author = commands.bot._get_variable('_internal_author')
		destination = commands.bot._get_variable('_internal_channel')
		fmt = '{0.mention}: {1}'.format(author, str(content))
		return self.send_message(destination, fmt, *args, **kwargs)

client = Bot(command_prefix = '!', description = "Harmonbot", pm_help = True)

rss_client = Bot(command_prefix = '!', description = "RSS Bot")

online_time = datetime.datetime.utcnow()

initial_extensions = ["commands.discord", "commands.meta", "commands.games", "commands.resources", "modules.voice"]
for extension in initial_extensions:
	client.load_extension(extension)
