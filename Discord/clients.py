
import discord
from discord.ext import commands
from discord.ext.commands.view import StringView
from discord.ext.commands.context import Context
from discord.ext.commands.errors import CommandNotFound, CommandError
import aiohttp
import cleverbot
import datetime
import imgurpython
import inflect
import json
import os
import pyowm
import random
import sys
import tweepy
import wolframalpha
from wordnik import swagger, WordApi, WordsApi
from modules import utilities
from utilities.help_formatter import CustomHelpFormatter
from utilities import errors
import credentials

version = "0.35.0-6.17"
changelog = "https://discord.gg/a2rbZPu"
stream_url = "https://www.twitch.tv/harmonbot"
listener_id = "180994984038760448"
cache_channel_id = "254051856219635713"
fake_ip = "nice try"
fake_location = "Fort Yukon, Alaska"
bot_color = 0x738bd7
wait_time = 15.0
delete_limit = 10000
code_block = "```\n{}\n```"
py_code_block = "```py\n{}\n```"
online_time = datetime.datetime.utcnow()
session_commands_executed = 0
session_commands_usage = {}
aiohttp_session = aiohttp.ClientSession()
cleverbot_instance = cleverbot.Cleverbot("Harmonbot")
imgur_client = imgurpython.ImgurClient(credentials.imgur_client_id, credentials.imgur_client_secret)
inflect_engine = inflect.engine()
owm_client = pyowm.OWM(credentials.owm_api_key)
twitter_auth = tweepy.OAuthHandler(credentials.twitter_consumer_key, credentials.twitter_consumer_secret)
twitter_auth.set_access_token(credentials.twitter_access_token, credentials.twitter_access_token_secret)
twitter_api = tweepy.API(twitter_auth)
wordnik_client = swagger.ApiClient(credentials.wordnik_apikey, "http://api.wordnik.com/v4")
wordnik_word_api = WordApi.WordApi(wordnik_client)
wordnik_words_api = WordsApi.WordsApi(wordnik_client)
wolfram_alpha_client = wolframalpha.Client(credentials.wolframalpha_appid)
application_info = None
harmonbot_listener = None
sys.setrecursionlimit(5000)

class Bot(commands.Bot):
	
	def reply(self, content, *args, **kwargs):
		author = commands.bot._get_variable('_internal_author')
		destination = commands.bot._get_variable('_internal_channel')
		fmt = '{0.display_name}: {1}'.format(author, str(content)) # , -> :
		extensions = ('delete_after',)
		params = {k: kwargs.pop(k, None) for k in extensions}
		coro = self.send_message(destination, fmt, *args, **kwargs)
		return self._augmented_msg(coro, embed = kwargs.get("embed"), **params) # embed
	
	def embed_reply(self, content, *args, **kwargs):
		author = commands.bot._get_variable('_internal_author')
		destination = commands.bot._get_variable('_internal_channel')
		embed = discord.Embed(description = str(content) if content else None, color = bot_color)
		avatar = author.avatar_url or author.default_avatar_url
		embed.set_author(name = author.display_name, icon_url = avatar) # url?
		title = kwargs.pop("title", None)
		if title: embed.title = title
		title_url = kwargs.pop("title_url", None)
		if title_url: embed.url = title_url
		image_url = kwargs.pop("image_url", None)
		if image_url: embed.set_image(url = image_url)
		thumbnail_url = kwargs.pop("thumbnail_url", None)
		if thumbnail_url: embed.set_thumbnail(url = thumbnail_url)
		footer_text = kwargs.pop("footer_text", None)
		if footer_text: embed.set_footer(text = footer_text)
		timestamp = kwargs.pop("timestamp", None)
		if timestamp: embed.timestamp = timestamp
		extensions = ('delete_after',)
		params = {k: kwargs.pop(k, None) for k in extensions}
		coro = self.send_message(destination, embed = embed, *args, **kwargs)
		if destination.is_private or getattr(destination.permissions_for(destination.server.me), "embed_links", None):
			return self._augmented_msg(coro, embed = embed, **params)
		elif not (title or title_url or image_url or thumbnail_url or footer_text or timestamp):
			fmt = '{0.display_name}: {1}'.format(author, str(content))
			coro = self.send_message(destination, fmt, *args, **kwargs)
			return self._augmented_msg(coro, **params)
		else:
			permissions = ["embed_links"]
			raise errors.MissingCapability(permissions)
	
	def say(self, *args, **kwargs):
		destination = commands.bot._get_variable('_internal_channel')
		extensions = ('delete_after',)
		params = {k: kwargs.pop(k, None) for k in extensions}
		coro = self.send_message(destination, *args, **kwargs)
		return self._augmented_msg(coro, embed = kwargs.get("embed"), **params) # embed
	
	def embed_say(self, *args, **kwargs):
		destination = commands.bot._get_variable('_internal_channel')
		embed = discord.Embed(description = str(args[0]) if args[0] else None, color = bot_color)
		# TODO: add author_name and author_icon_url
		title = kwargs.pop("title", None)
		if title: embed.title = title
		title_url = kwargs.pop("title_url", None)
		if title_url: embed.url = title_url
		image_url = kwargs.pop("image_url", None)
		if image_url: embed.set_image(url = image_url)
		thumbnail_url = kwargs.pop("thumbnail_url", None)
		if thumbnail_url: embed.set_thumbnail(url = thumbnail_url)
		footer_text = kwargs.pop("footer_text", None)
		if footer_text: embed.set_footer(text = footer_text)
		timestamp = kwargs.pop("timestamp", None)
		if timestamp: embed.timestamp = timestamp
		extensions = ('delete_after',)
		params = {k: kwargs.pop(k, None) for k in extensions}
		coro = self.send_message(destination, embed = embed, *args[1:], **kwargs)
		return self._augmented_msg(coro, embed = embed, **params)
	
	def whisper(self, *args, **kwargs):
		destination = commands.bot._get_variable('_internal_author')
		extensions = ('delete_after',)
		params = {k: kwargs.pop(k, None) for k in extensions}
		coro = self.send_message(destination, *args, **kwargs)
		return self._augmented_msg(coro, embed = kwargs.get("embed"), **params) # embed
	
	def embed_whisper(self, *args, **kwargs):
		destination = commands.bot._get_variable('_internal_author')
		embed = discord.Embed(description = args[0], color = bot_color)
		extensions = ('delete_after',)
		params = {k: kwargs.pop(k, None) for k in extensions}
		coro = self.send_message(destination, embed = embed, *args[1:], **kwargs)
		return self._augmented_msg(coro, embed = embed, **params)
	
	def send_embed(self, destination, content):
		embed = discord.Embed(description = content, color = bot_color)
		return self.send_message(destination, embed = embed)
	
	async def _augmented_msg(self, coro, **kwargs):
		msg = await coro
		delete_after = kwargs.get('delete_after')
		if delete_after is not None:
			async def delete():
				await asyncio.sleep(delete_after)
				await self.delete_message(msg)

			discord.compat.create_task(delete(), loop=self.loop)
		# return embed
		embed = kwargs.get("embed")
		return msg, embed
	
	async def attempt_delete_message(self, message):
		try:
			await self.delete_message(message)
		except discord.errors.Forbidden:
			pass
		except discord.errors.NotFound:
			pass
	
	async def process_commands(self, message):
		_internal_channel = message.channel
		_internal_author = message.author
		view = StringView(message.content)
		if self._skip_check(message.author, self.user):
			return
		prefix = await self._get_prefix(message)
		invoked_prefix = prefix
		if not isinstance(prefix, (tuple, list)):
			if not view.skip_string(prefix):
				return
		else:
			invoked_prefix = discord.utils.find(view.skip_string, prefix)
			if invoked_prefix is None:
				return
		invoker = view.get_word().lower() # case-insensitive commands
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

# Make Subcommands Case-Insensitive

class Group(commands.GroupMixin, commands.Command):

	def __init__(self, **attrs):
		self.invoke_without_command = attrs.pop('invoke_without_command', False)
		super().__init__(**attrs)

	async def invoke(self, ctx):
		early_invoke = not self.invoke_without_command
		if early_invoke:
			await self.prepare(ctx)
		view = ctx.view
		previous = view.index
		view.skip_ws()
		trigger = view.get_word().lower() # case-insensitive subcommands
		if trigger:
			ctx.subcommand_passed = trigger
			ctx.invoked_subcommand = self.commands.get(trigger, None)
		if early_invoke:
			injected = commands.core.inject_context(ctx, self.callback)
			await injected(*ctx.args, **ctx.kwargs)
		if trigger and ctx.invoked_subcommand:
			ctx.invoked_with = trigger
			await ctx.invoked_subcommand.invoke(ctx)
		elif not early_invoke:
			# undo the trigger parsing
			view.index = previous
			view.previous = previous
			await super().invoke(ctx)

def group(name=None, **attrs):
    return commands.command(name=name, cls=Group, **attrs)

commands.Group = Group
commands.group = group


# Create Folders

utilities.create_folder("data")
utilities.create_folder("data/permissions")
utilities.create_folder("data/temp")


# Custom prefixes

utilities.create_file("prefixes")

def get_prefix(bot, message):
	with open("data/prefixes.json", 'r') as prefixes_file:
		all_prefixes = json.load(prefixes_file)
	if message.channel.is_private:
		prefixes = all_prefixes.get(message.channel.id, None)
	else:
		prefixes = all_prefixes.get(message.server.id, None)
	return prefixes if prefixes else '!'


# Customize help command

_CustomHelpFormatter = CustomHelpFormatter()

client = Bot(command_prefix = get_prefix, formatter = _CustomHelpFormatter, pm_help = None)
client.remove_command("help")


# Initialize/update info

async def _update_discord_bots_stats():
	async with aiohttp_session.post("https://bots.discord.pw/api/bots/{}/stats".format(client.user.id), 
	headers = {"authorization": credentials.discord_bots_api_token, "content-type": "application/json"}, 
	data = json.dumps({"server_count": len(client.servers)})) as resp:
		response = await resp.json()
	return response

@client.listen()
async def on_ready():
	global application_info, harmonbot_listener
	application_info = await client.application_info()
	harmonbot_listener = await client.get_user_info(listener_id)
	await _update_discord_bots_stats()

@client.listen()
async def on_server_join(server):
	await _update_discord_bots_stats()

@client.listen()
async def on_server_remove(server):
	await _update_discord_bots_stats()

@client.listen()
async def on_command(command, ctx):
	global session_commands_executed, session_commands_usage
	session_commands_executed += 1
	session_commands_usage[command.name] = session_commands_usage.get(command.name, 0) + 1


# Download FFMPEG

import imageio
imageio.plugins.ffmpeg.download()


# Load cogs

for file in os.listdir("cogs"):
	if file.endswith(".py") and not file.startswith(("random", "reactions")):
		client.load_extension("cogs." + file[:-3])
client.load_extension("cogs.random")
client.load_extension("cogs.reactions")


# Utilities

async def random_game_status():
	statuses = ["with i7-2670QM", "with mainframes", "with Cleverbot",
	"tic-tac-toe with Joshua", "tic-tac-toe with WOPR", "the Turing test",
	"with my memory", "with R2-D2", "with C-3PO", "with BB-8",
	"with machine learning", "gigs", "with Siri", "with TARS", "with KIPP",
	"with humans", "with Skynet", "Goldbach's conjecture",
	"Goldbach's conjecture solution", "with quantum foam",
	"with quantum entanglement", "with P vs NP", "the Reimann hypothesis",
	"the Reimann proof", "with the infinity gauntlet", "for the other team",
	"hard to get", "to win", "world domination", "with Opportunity",
	"with Spirit in the sand pit", "with Curiousity", "with Voyager 1",
	"music", "Google Ultron", "not enough space here to",
	"the meaning of life is", "with the NSA", "with neural networks", 
	"with RSS Bot", "with Data", "with Harmon", " "]
	me = discord.utils.find(lambda s: s != None, client.servers).me
	if not me:
		return
	elif not me.game:
		updated_game = discord.Game(name = random.choice(statuses))
	else:
		updated_game = me.game
		updated_game.name = random.choice(statuses)
	await client.change_presence(game = updated_game)

async def set_streaming_status(client):
	me = discord.utils.get(client.servers).me
	if not me:
		return
	elif not me.game:
		updated_game = discord.Game(url = stream_url, type = 1)
	else:
		updated_game = me.game
		updated_game.url = stream_url
		updated_game.type = 1
	await client.change_presence(game = updated_game)

async def reply(message, response):
	return await client.send_message(message.channel, "{}: {}".format(message.author.mention, response))

async def embed_reply(message, response):
	embed = discord.Embed(description = response, color = bot_color)
	avatar = message.author.avatar_url or message.author.default_avatar_url
	embed.set_author(name = message.author.display_name, icon_url = avatar)
	return await client.send_message(message.channel, embed = embed)


# Restart + Shutdown Tasks

async def restart_tasks(channel_id):
	# Increment restarts counter
	with open("data/stats.json", 'r') as stats_file:
		stats = json.load(stats_file)
	stats["restarts"] += 1
	with open("data/stats.json", 'w') as stats_file:
		json.dump(stats, stats_file, indent = 4)
	# Save restart text channel + voice channels
	audio_cog = client.get_cog("Audio")
	voice_channels = audio_cog.save_voice_channels() if audio_cog else []
	with open("data/temp/restart_channel.json", 'w') as restart_channel_file:
		json.dump({"restart_channel" : channel_id, "voice_channels" : voice_channels}, restart_channel_file)

async def shutdown_tasks():
	# Cancel audio tasks
	audio_cog = client.get_cog("Audio")
	if audio_cog: audio_cog.cancel_all_tasks()
	# Close aiohttp session
	aiohttp_session.close()
	# Save uptime
	with open("data/stats.json", 'r') as stats_file:
		stats = json.load(stats_file)
	now = datetime.datetime.utcnow()
	uptime = now - online_time
	stats["uptime"] += uptime.total_seconds()
	with open("data/stats.json", 'w') as stats_file:
		json.dump(stats, stats_file, indent = 4)

