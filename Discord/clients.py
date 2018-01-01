
import discord
from discord.ext import commands

import aiml
import aiohttp
import clarifai.rest
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
import credentials
from utilities.context import Context
from utilities import errors
from utilities.help_formatter import CustomHelpFormatter

beta = any("beta" in arg.lower() for arg in sys.argv)
data_path = "data/beta" if beta else "data"
stream_url = "https://www.twitch.tv/harmonbot"
listener_id = 180994984038760448
cache_channel_id = 254051856219635713
user_agent = "Discord Bot"
library_files = "D:/Data (D)/Music/"
bot_color = 0x738bd7
youtube_icon_url = "https://www.youtube.com/yt/brand/media/image/YouTube-icon-full_color.png"
wait_time = 15.0
delete_limit = 10000
code_block = "```\n{}\n```"
py_code_block = "```py\n{}\n```"
online_time = datetime.datetime.utcnow()
aiml_kernel = aiml.Kernel()
aiohttp_session = aiohttp.ClientSession()
inflect_engine = inflect.engine()
owm_client = pyowm.OWM(credentials.owm_api_key)
wordnik_client = swagger.ApiClient(credentials.wordnik_apikey, "http://api.wordnik.com/v4")
wordnik_word_api = WordApi.WordApi(wordnik_client)
wordnik_words_api = WordsApi.WordsApi(wordnik_client)
application_info = None
harmonbot_listener = None
# TODO: Include owner variable for user object?
sys.setrecursionlimit(5000)


aiml_predicates = {"name": "Harmonbot", "botmaster": "owner", "master": "Harmon", "domain": "tool", "kingdom": "machine", "phylum": "software", "class": "program", "order": "artificial intelligence", "family": "bot", "genus": "python bot", "species": "Discord bot"}
for predicate, value in aiml_predicates.items():
	aiml_kernel.setBotPredicate(predicate, value)
if os.path.isfile(data_path + "/aiml/aiml_brain.brn"):
	aiml_kernel.bootstrap(brainFile = data_path + "/aiml/aiml_brain.brn")
elif os.path.isfile(data_path + "/aiml/std-startup.xml"):
	aiml_kernel.bootstrap(learnFiles = data_path + "/aiml/std-startup.xml", commands = "load aiml b")
	aiml_kernel.saveBrain(data_path + "/aiml/aiml_brain.brn")

game_statuses = ("with i7-2670QM", "with mainframes", "with Cleverbot", "tic-tac-toe with Joshua", "tic-tac-toe with WOPR", "the Turing test", "with my memory", "with R2-D2", "with C-3PO", "with BB-8", "with machine learning", "gigs", "with Siri", "with TARS", "with KIPP", "with humans", "with Skynet", "Goldbach's conjecture", "Goldbach's conjecture solution", "with quantum foam", "with quantum entanglement", "with P vs NP", "the Reimann hypothesis", "the Reimann proof", "with the infinity gauntlet", "for the other team", "hard to get", "to win", "world domination", "with Opportunity", "with Spirit in the sand pit", "with Curiousity", "with Voyager 1", "music", "Google Ultron", "not enough space here to", "the meaning of life is", "with the NSA", "with neural networks", "with RSS Bot", "with Data", "with Harmon", " ")

class Bot(commands.Bot):
	
	def __init__(self, command_prefix):
		super().__init__(command_prefix = command_prefix, formatter = CustomHelpFormatter(), game = discord.Game(name = random.choice(game_statuses), url = stream_url, type = 1))
		
		# Constants
		self.version = "1.0.0-rc.1"
		self.owner_id = 115691005197549570
		self.changelog = "https://discord.gg/a2rbZPu"
		self.console_message_prefix = "Discord Harmonbot: "
		self.fake_ip = "nice try"
		self.fake_location = "Fort Yukon, Alaska"
		self.rss_color = 0xfa9b39 # other options: f26522, ee802f, ff6600; http://www.strawpoll.me/12384409
		self.twitch_color = 0x6441a4
		self.twitter_color = 0x00ACED
		self.youtube_color = 0xcd201f # change to ff0000?; previously on https://www.youtube.com/yt/brand/color.html
		self.twitch_icon_url = "https://s.jtvnw.net/jtv_user_pictures/hosted_images/GlitchIcon_purple.png"
		self.twitter_icon_url = "https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
		
		# Variables
		self.session_commands_executed = 0
		self.session_commands_usage = {}
		
		# External Clients
		## Clarifai
		self.clarifai_app = clarifai.rest.ClarifaiApp(app_id = credentials.clarifai_api_id, app_secret = credentials.clarifai_api_secret)
		self.clarifai_general_model = self.clarifai_app.models.get("general-v1.3")
		self.clarifai_nsfw_model = self.clarifai_app.models.get("nsfw-v1.0")
		## Imgur
		try:
			self.imgur_client = imgurpython.ImgurClient(credentials.imgur_client_id, credentials.imgur_client_secret)
		except imgurpython.helpers.error.ImgurClientError as e:
			print("{}Failed to load Imgur Client: {}".format(self.console_message_prefix, e))
		## Twitter
		self.twitter_auth = tweepy.OAuthHandler(credentials.twitter_consumer_key, credentials.twitter_consumer_secret)
		self.twitter_auth.set_access_token(credentials.twitter_access_token, credentials.twitter_access_token_secret)
		self.twitter_api = tweepy.API(self.twitter_auth)
		## Wolfram Alpha
		self.wolfram_alpha_client = wolframalpha.Client(credentials.wolframalpha_appid)
		
		# Remove default help command (to override)
		self.remove_command("help")
	
	async def on_resumed(self):
		print("{}resumed @ {}".format(self.console_message_prefix, datetime.datetime.now().time().isoformat()))
	
	# TODO: on_command_completion
	# TODO: optimize
	async def on_command(self, ctx):
		self.session_commands_executed += 1
		self.session_commands_usage[ctx.command.name] = self.session_commands_usage.get(ctx.command.name, 0) + 1
	
	# TODO: optimize/overhaul
	def send_embed(self, destination, description = None, *, title = discord.Embed.Empty, title_url = discord.Embed.Empty, 
	author_name = "", author_url = discord.Embed.Empty, author_icon_url = discord.Embed.Empty, 
	image_url = None, thumbnail_url = None, footer_text = discord.Embed.Empty, footer_icon_url = discord.Embed.Empty, 
	timestamp = discord.Embed.Empty, fields = []):
		embed = discord.Embed(title = title, url = title_url, timestamp = timestamp, color = bot_color)
		embed.description = str(description) if description else discord.Embed.Empty
		if author_name: embed.set_author(name = author_name, url = author_url, icon_url = author_icon_url)
		if image_url: embed.set_image(url = image_url)
		if thumbnail_url: embed.set_thumbnail(url = thumbnail_url)
		embed.set_footer(text = footer_text, icon_url = footer_icon_url)
		for field_name, field_value in fields:
			embed.add_field(name = field_name, value = field_value)
		return destination.send(embed = embed)
	
	async def attempt_delete_message(self, message):
		try:
			await message.delete()
		except (discord.Forbidden, discord.NotFound):
			pass
	
	# Case-Insensitive commands
	async def get_context(self, message, *, cls = Context):
		ctx = await super().get_context(message, cls = cls)
		if ctx.invoked_with: ctx.command = self.all_commands.get(ctx.invoked_with.lower())
		return ctx
	
	# TODO: Case-Insensitive subcommands (override Group)


# Create folders

def create_folder(folder):
	if not os.path.exists(folder):
		os.makedirs(folder)

create_folder(data_path)
create_folder(data_path + "/permissions")
create_folder(data_path + "/temp")


# Custom prefixes (Create files)

def create_file(filename, *, content = {}):
	try:
		with open(data_path + "/{}.json".format(filename), "x") as file:
			json.dump(content, file, indent = 4)
	except FileExistsError:
		pass
	except OSError:
		pass

create_file("prefixes")

def get_prefix(bot, message):
	with open(data_path + "/prefixes.json", 'r') as prefixes_file:
		all_prefixes = json.load(prefixes_file)
	if isinstance(message.channel, discord.DMChannel):
		prefixes = all_prefixes.get(message.channel.id, None)
	else:
		prefixes = all_prefixes.get(message.guild.id, None)
	return prefixes if prefixes else '!'


# Initialize client

client = Bot(command_prefix = get_prefix)


# Initialize/update info

async def _update_discord_bots_stats():
	async with aiohttp_session.post("https://bots.discord.pw/api/bots/{}/stats".format(client.user.id), 
	headers = {"authorization": credentials.discord_bots_api_token, "content-type": "application/json"}, 
	data = json.dumps({"server_count": len(client.guilds)})) as resp:
		# Change to check for 200?
		if resp.status in (500, 502, 504, 522):
			return "Error: {}".format(resp.status)
		response = await resp.json()
	return response

@client.listen()
async def on_ready():
	global application_info, harmonbot_listener
	application_info = await client.application_info()
	harmonbot_listener = await client.get_user_info(listener_id)
	await _update_discord_bots_stats()

@client.listen()
async def on_guild_join(guild):
	await _update_discord_bots_stats()

@client.listen()
async def on_guild_remove(guild):
	await _update_discord_bots_stats()


# Download FFMPEG

import imageio
imageio.plugins.ffmpeg.download()


# Load cogs

for file in sorted(os.listdir("cogs")):
	if file.endswith(".py") and not file.startswith(("random", "reactions")):
		client.load_extension("cogs." + file[:-3])
client.load_extension("cogs.random")
client.load_extension("cogs.reactions")


# Utilities

async def random_game_status():
	me = discord.utils.find(lambda s: s != None, client.guilds).me
	if not me:
		return
	elif not me.game:
		updated_game = discord.Game(name = random.choice(game_statuses))
	else:
		updated_game = me.game
		updated_game.name = random.choice(game_statuses)
	await client.change_presence(game = updated_game)

async def set_streaming_status(client):
	me = discord.utils.get(client.guilds).me
	if not me:
		return
	elif not me.game:
		updated_game = discord.Game(url = stream_url, type = 1)
	else:
		updated_game = me.game
		updated_game.url = stream_url
		updated_game.type = 1
	await client.change_presence(game = updated_game)


# Restart + Shutdown Tasks

async def restart_tasks(channel_id):
	# Increment restarts counter
	with open(data_path + "/stats.json", 'r') as stats_file:
		stats = json.load(stats_file)
	stats["restarts"] += 1
	with open(data_path + "/stats.json", 'w') as stats_file:
		json.dump(stats, stats_file, indent = 4)
	# Save restart text channel + voice channels
	audio_cog = client.get_cog("Audio")
	voice_channels = audio_cog.save_voice_channels() if audio_cog else []
	with open(data_path + "/temp/restart_channel.json", 'w') as restart_channel_file:
		json.dump({"restart_channel" : channel_id, "voice_channels" : voice_channels}, restart_channel_file)

async def shutdown_tasks():
	# Cancel audio tasks
	audio_cog = client.get_cog("Audio")
	if audio_cog: audio_cog.cancel_all_tasks()
	# Close aiohttp session
	aiohttp_session.close()
	# Save uptime
	with open(data_path + "/stats.json", 'r') as stats_file:
		stats = json.load(stats_file)
	now = datetime.datetime.utcnow()
	uptime = now - online_time
	stats["uptime"] += uptime.total_seconds()
	with open(data_path + "/stats.json", 'w') as stats_file:
		json.dump(stats, stats_file, indent = 4)

