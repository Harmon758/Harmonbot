
# import discord
from discord.ext import commands
# client = discord.Client()
import datetime
import sys

from utilities import errors
from modules import utilities

wait_time = 10.0

class Bot(commands.Bot):
	
	def reply(self, content, *args, **kwargs):
		author = commands.bot._get_variable('_internal_author')
		destination = commands.bot._get_variable('_internal_channel')
		fmt = '{0.mention}: {1}'.format(author, str(content))
		return self.send_message(destination, fmt, *args, **kwargs)
	
	async def on_error(self, event_method, message, *args, **kwargs):
		type, value, traceback = sys.exc_info()
		if type is errors.NoTags:
			await utilities.send_mention_space(message, "You don't have any tags :slight_frown: Add one with `!tag add <tag> <content>`")
		elif type is errors.NoTag:
			await utilities.send_mention_space(message, "You don't have that tag.")
		else:
			print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
			traceback.print_exc()
	

client = Bot(command_prefix = '!', description = "Harmonbot", pm_help = True)

rss_client = Bot(command_prefix = '!', description = "RSS Bot")

online_time = datetime.datetime.utcnow()

initial_extensions = ["commands.discord", "commands.meta", "commands.games", "commands.resources"]
for extension in initial_extensions:
	client.load_extension(extension)
