
import discord
from discord.ext import commands
from discord.ext.commands.view import StringView
from discord.ext.commands.context import Context
from discord.ext.commands.errors import CommandNotFound, CommandError
import aiohttp
import cleverbot
import datetime
import inflect
import json
import os
from utilities.help_formatter import CustomHelpFormatter

version = "0.30.17"
changelog = "https://discord.gg/a2rbZPu"
wait_time = 15.0
code_block = "```\n{}\n```"
py_code_block = "```py\n{}\n```"
online_time = datetime.datetime.utcnow()
aiohttp_session = aiohttp.ClientSession()
cleverbot_instance = cleverbot.Cleverbot()
inflect_engine = inflect.engine()
application_info = None

class Bot(commands.Bot):
	
	def reply(self, content, *args, **kwargs):
		author = commands.bot._get_variable('_internal_author')
		destination = commands.bot._get_variable('_internal_channel')
		fmt = '{0.mention}: {1}'.format(author, str(content)) # , -> :
		extensions = ('delete_after',)
		params = {k: kwargs.pop(k, None) for k in extensions}
		coro = self.send_message(destination, fmt, *args, **kwargs)
		return self._augmented_msg(coro, **params)
	
	async def process_commands(self, message):
		_internal_channel = message.channel
		_internal_author = message.author
		view = StringView(message.content)
		if self._skip_check(message.author, self.user):
			return
		prefix = self._get_prefix(message)
		invoked_prefix = prefix
		if not isinstance(prefix, (tuple, list)):
			if not view.skip_string(prefix):
				return
		else:
			invoked_prefix = discord.utils.find(view.skip_string, prefix)
			if invoked_prefix is None:
				return
		invoker = view.get_word().lower() # case insensitive commands
		tmp = {'bot': self, 'invoked_with': invoker, 'message': message, 'view': view, 'prefix': invoked_prefix}
		ctx = Context(**tmp)
		del tmp
		if invoker in self.commands:
			command = self.commands[invoker]
			self.dispatch('command', command, ctx)
			try:
				await command.invoke(ctx)
			except CommandError as e:
				ctx.command.dispatch_error(e, ctx)
			else:
				self.dispatch('command_completion', command, ctx)
		elif invoker:
			exc = CommandNotFound('Command "{}" is not found'.format(invoker))
			self.dispatch('command_error', exc, ctx)

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

_CustomHelpFormatter = CustomHelpFormatter()

client = Bot(command_prefix = get_prefix, formatter = _CustomHelpFormatter, pm_help = None)
client.remove_command("help")

@client.listen()
async def on_ready():
	global application_info
	application_info = await client.application_info()

for file in os.listdir("cogs"):
	if file.endswith(".py"):
		client.load_extension("cogs." + file[:-3])

