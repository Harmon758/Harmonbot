
import pydle

import asyncio
import datetime
import json
import logging
import logging.handlers
import os
import random
import re
import sys
import time
import unicodedata

import aiohttp
import dateutil.easter
import dateutil.parser
import dotenv
# import unicodedata2 as unicodedata

sys.path.insert(0, "..")
from units.location import get_geocode_data, get_timezone_data, UnitOutputError
sys.path.pop(0)

class TwitchClient(pydle.Client):
	
	def __init__(self, nickname):
		self.version = "2.4.3"
		# Pydle logger
		pydle_logger = logging.getLogger("pydle")
		pydle_logger.setLevel(logging.DEBUG)
		pydle_logger_handler = logging.FileHandler(filename = "data/logs/pydle.log", 
													encoding = "UTF-8", mode = 'a')
		pydle_logger_handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
		pydle_logger.addHandler(pydle_logger_handler)
		# Initialize
		super().__init__(nickname)
		# Constants
		self.CHANNELS = ["harmon758", "harmonbot", "mikki", "imagrill", "tirelessgod", "gameflubdojo", 
							"vayces", "tbestnuclear", "cantilena", "nordryd", "babyastron"]
		self.PING_TIMEOUT = 600
		# Credentials
		self.RIOT_GAMES_API_KEY = os.getenv("RIOT_GAMES_API_KEY")
		self.TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
		# aiohttp Client Session - initialized on connect
		self.aiohttp_session = None
		# Dynamically load commands
		for file in os.listdir("data/commands"):
			if file == "aliases":
				continue
			category = file[:-5]  # - .json
			with open(f"data/commands/{category}.json", 'r') as commands_file:
				setattr(self, f"{category}_commands", json.load(commands_file))
		# Dynamically load aliases
		for file in os.listdir("data/commands/aliases"):
			category = file[:-5]  # - .json
			with open(f"data/commands/aliases/{category}.json", 'r') as aliases_file:
				setattr(self, f"{category}_aliases", json.load(aliases_file))
		# Dynamically load variables
		for file in os.listdir("data/variables"):
			category = file[:-5]  # - .json
			with open(f"data/variables/{category}.json", 'r') as variables_file:
				setattr(self, f"{category}_variables", json.load(variables_file))
		self.status_settings = {"on": True, "off": False, "mod": None}
	
	async def on_connect(self):
		await super().on_connect()
		# Initialize aiohttp Client Session
		if not self.aiohttp_session:
			self.aiohttp_session = aiohttp.ClientSession(loop = self.eventloop)
		# Client logger
		self.logger.setLevel(logging.DEBUG)
		console_handler = logging.StreamHandler(sys.stdout)
		console_handler.setLevel(logging.ERROR)
		console_handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
		file_handler = logging.handlers.TimedRotatingFileHandler(
			filename = "data/logs/client/client.log", when = "midnight", 
			backupCount = 3650000, encoding = "UTF-8")
		file_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
		self.logger.addHandler(console_handler)
		self.logger.addHandler(file_handler)
		# Request capabilities
		await self.raw("CAP REQ :twitch.tv/membership\r\n")
		await self.raw("CAP REQ :twitch.tv/tags\r\n")
		await self.raw("CAP REQ :twitch.tv/commands\r\n")
		# Join channels + set up channel loggers
		for channel in self.CHANNELS:
			await self.join('#' + channel)
			channel_logger = logging.getLogger('#' + channel)
			channel_logger.setLevel(logging.DEBUG)
			channel_logger_handler = logging.FileHandler(filename = f"data/logs/channels/{channel}.log", 
															encoding = "UTF-8", mode = 'a')
			channel_logger_handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
			channel_logger.addHandler(channel_logger_handler)
		# Console output
		print(f"Started up Twitch Harmonbot | Connected to {' | '.join('#' + channel for channel in self.CHANNELS)}")
	
	async def on_join(self, channel, user):
		await super().on_join(channel,user)
		channel_logger = logging.getLogger(channel)
		channel_logger.info(f"JOIN: {user}")
	
	async def on_part(self, channel, user, message = None):
		await super().on_part(channel, user, message)
		channel_logger = logging.getLogger(channel)
		channel_logger.info(f"PART: {user}")
	
	async def on_raw_004(self, message):
		# super().on_raw_004(message)
		pass
	
	async def on_raw_whisper(self, message):
		await super().on_raw_privmsg(message)
	
	async def message(self, target, message):
		if target[0] != '#':
			await super().message("#harmonbot", f".w {target} {message}")
		else:
			await super().message(target, message)
	
	async def on_message(self, target, source, message):
		await super().on_message(target, source, message)
		
		channel_logger = logging.getLogger(target)
		channel_logger.info(f"{source}: {message}")
		
		if target == "harmonbot":
			target = source
		if source == "harmonbot":
			return
		
		# Test Command
		if message == "!test":
			await self.message(target, "Hello, World!")
		
		# Meta Commands
		if message.startswith('!') and message[1:] in self.meta_commands:
				await self.message(target, self.meta_commands[message[1:]])
		
		# Main Commands
		elif message.startswith("!averagefps"):
			url = "https://api.twitch.tv/kraken/streams/" + target[1:]
			params = {"client_id": self.TWITCH_CLIENT_ID}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if data.get("stream"):
				await self.message(target, f"Average FPS: {data['stream']['average_fps']}")
			else:
				await self.message(target, "Average FPS not found.")
		elif message.startswith(("!bday", "!birthday")):
			# TODO: Document
			# TODO: Add ability to reset
			# TODO: Handle leap day
			now = datetime.datetime.utcnow()
			if not hasattr(self, f"{target[1:]}_variables"):
				setattr(self, f"{target[1:]}_variables", {})
			channel_variables = getattr(self, f"{target[1:]}_variables")
			if (source == target[1:] and len(message.split()) >= 3 and 
				is_number(message.split()[1]) and is_number(message.split()[2])):
				month = int(message.split()[1])
				day = int(message.split()[2])
				try:
					date = datetime.date(year = now.year, month = month, day = day)
				except ValueError as e:
					await self.message(target, f"Error: {e}")
					return
				channel_variables["birthday_month"] = month
				channel_variables["birthday_day"] = day
				with open(f"data/variables/{target[1:]}.json", 'w') as variables_file:
					json.dump(channel_variables, variables_file, indent = 4)
				await self.message(target, f"Birthday set to {date.strftime('%B %#d')}")
				# %#d for removal of leading zero on Windows with native Python executable
			elif "birthday_month" in channel_variables and "birthday_day" in channel_variables:
				if "timezone_location" in channel_variables:
					try:
						timezone_data = await get_timezone_data(location = channel_variables["timezone_location"], 
																aiohttp_session = self.aiohttp_session)
					except UnitOutputError as e:
						await self.message(target, f"Error: {e}")
						return
					now = datetime.datetime.fromtimestamp(datetime.datetime.utcnow().timestamp() + 
															timezone_data["dstOffset"] + timezone_data["rawOffset"])
				birthday = datetime.datetime(now.year, channel_variables["birthday_month"], channel_variables["birthday_day"])
				if now > birthday:
					birthday = birthday.replace(year = birthday.year + 1)
				seconds = int((birthday - now).total_seconds())
				await self.message(target, f"{secs_to_duration(seconds)} until {target[1:].capitalize()}'s birthday!")
		elif message.startswith(("!char", "!character", "!unicode")):
			try:
				await self.message(target, unicodedata.lookup(' '.join(message.split()[1:])))
			except KeyError:
				await self.message(target, "\N{NO ENTRY} Unicode character not found")
		elif message.startswith("!element"):
			elements = {"ac": "Actinium", "ag": "Silver", "al": "Aluminum", "am": "Americium", "ar": "Argon", }
			if len(message.split()) > 1 and message.split()[1] in elements:
				await self.message(target, elements[message.split()[1]])
		elif message.startswith(("!followage", "!followed", "!howlong")):
			url = f"https://api.twitch.tv/kraken/users/{source}/follows/channels/{target[1:]}"
			params = {"client_id": self.TWITCH_CLIENT_ID}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if "created_at" in data:
				created_at = dateutil.parser.parse(data["created_at"])
				seconds = int((datetime.datetime.now(datetime.timezone.utc) - created_at).total_seconds())
				await self.message(target, f"{source.capitalize()} followed on {created_at.strftime('%B %#d %Y')}, {secs_to_duration(seconds)} ago")
				# %#d for removal of leading zero on Windows with native Python executable
			else:
				await self.message(target, f"{source.capitalize()}, you haven't followed yet!")
		elif message.startswith("!followers"):
			url = f"https://api.twitch.tv/kraken/channels/{target[1:]}/follows"
			params = {"client_id": self.TWITCH_CLIENT_ID}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			await self.message(target, f"There are currently {data['_total']} people following {target[1:].capitalize()}.")
		elif message.startswith("!highfive"):
			if len(message.split()) == 1:
				await self.message(target, f"{source.capitalize()} highfives no one. :-/")
			elif message.split()[1].lower() == "random":
				await self.message(target, f"{source.capitalize()} highfives {self.random_viewer(target)}!")
			elif message.split()[1].lower() == source:
				await self.message(target, f"{source.capitalize()} highfives themselves. o_O")
			elif message.split()[1].lower() == "harmonbot":
				await self.message(target, f"!highfive {source.capitalize()}")
			else:
				await self.message(target, f"{source.capitalize()} highfives {' '.join(message.split()[1:]).title()}!")
		elif message.startswith("!hug"):
			if len(message.split()) == 1:
				await self.message(target, f"{source.capitalize()} hugs no one. :-/")
			elif message.split()[1].lower() == "random":
				await self.message(target, f"{source.capitalize()} hugs {self.random_viewer(target)}!")
			elif message.split()[1].lower() == source:
				await self.message(target, f"{source.capitalize()} hugs themselves. o_O")
			elif message.split()[1].lower() == "harmonbot":
				await self.message(target, f"!hug {source.capitalize()}")
			else:
				await self.message(target, f"{source.capitalize()} hugs {' '.join(message.split()[1:]).title()}!")
		elif message.startswith("!mods"):
			mods = self.channels[target]["modes"].get('o', [])
			await self.message(target, f"Mods Online ({len(mods)}): {', '.join(mod.capitalize() for mod in mods)}")
		elif message.startswith("!randomviewer"):
			if not hasattr(self, f"{target[1:]}_variables"):
				setattr(self, f"{target[1:]}_variables", {})
			channel_variables = getattr(self, f"{target[1:]}_variables")
			if (self.is_mod(target, source) and len(message.split()) > 1
				and message.split()[1] in self.status_settings):
				status = message.split()[1]
				channel_variables["!randomviewer.status"] = self.status_settings[status]
				with open(f"data/variables/{target[1:]}.json", 'w') as variables_file:
					json.dump(channel_variables, variables_file, indent = 4)
				if status == "mod":
					status += " only"
				await self.message(target, f"!randomviewer is {status}")
			elif (channel_variables.get("!randomviewer.status", True) or 
					(self.is_mod(target, source) and channel_variables["!randomviewer.status"] is None)):
				await self.message(target, self.random_viewer(target))
		elif message.startswith("!rng"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, str(random.randint(1, int(message.split()[1]))))
			else:
				await self.message(target, str(random.randint(1, 10)))
		elif message.startswith("!roulette"):
			# TODO: Configurable flood/time limit settings, per channel + per user
			# TODO: Add configurable timeout on loss option
			if not hasattr(self, f"{target[1:]}_variables"):
				setattr(self, f"{target[1:]}_variables", {})
			channel_variables = getattr(self, f"{target[1:]}_variables")
			if (self.is_mod(target, source) and len(message.split()) > 1
				and message.split()[1] in self.status_settings):
				status = message.split()[1]
				channel_variables["!roulette.status"] = self.status_settings[status]
				with open(f"data/variables/{target[1:]}.json", 'w') as variables_file:
					json.dump(channel_variables, variables_file, indent = 4)
				if status == "mod":
					status += " only"
				await self.message(target, f"!roulette is {status}")
			elif (channel_variables.get("!roulette.status", True) or 
					(self.is_mod(target, source) and channel_variables["!roulette.status"] is None)):
				choices = [f"Roulette clicks!...Empty...You live to see another day, {source.capitalize()}", 
							f"{source.capitalize()} starts to shake, {source.capitalize()} tries to pull the trigger "
							f"but can't. {source.capitalize()} drops the gun, {source.capitalize()} isn't up to the "
							f"challenge of Roulette."]
				if self.is_mod(target, source):
					choices.append("BANG! ... You were shot, but live! "
									f"There must be secert powers in your mod armor, {source.capitalize()}")
					choices.append("BANG! ... The bullet missed, "
									f"you only have your born moderation powers to thank, {source.capitalize()}")
				else:
					choices.append(f"BANG!... Roulette claims another soul. R.I.P {source.capitalize()}")
					choices.append(f"BANG!... {source.capitalize()} was a great viewer, "
									f"and now {source.capitalize()} is a dead viewer. R.I.P")
				await self.message(target, random.choice(choices))
		elif message.startswith("!rps"):
			if len(message.split()) == 1:
				await self.message(target, "Please specify rock, paper, or scissors.")
				return
			if not hasattr(self, f"{target[1:]}_variables"):
				setattr(self, f"{target[1:]}_variables", {})
			channel_variables = getattr(self, f"{target[1:]}_variables")
			if (self.is_mod(target, source) and len(message.split()) > 1
				and message.split()[1] in self.status_settings):
				status = message.split()[1]
				channel_variables["!rps.status"] = self.status_settings[status]
				with open(f"data/variables/{target[1:]}.json", 'w') as variables_file:
					json.dump(channel_variables, variables_file, indent = 4)
				if status == "mod":
					status += " only"
				await self.message(target, f"!rps is {status}")
			elif (channel_variables.get("!rps.status", True) or 
					(self.is_mod(target, source) and channel_variables["!rps.status"] is None)):
				if message.split()[1].lower() == "rock":
					await self.message(target, 
										random.choice((f"PAPER -- Paper beats Rock! You lose, {source.capitalize()} !", 
														f"SCISSORS -- Hmm, I lose. Congrats, {source.capitalize()}", 
														"ROCK -- Dang it, it's a draw.")))
				elif message.split()[1].lower() == "paper":
					await self.message(target, 
										random.choice((f"SCISSORS -- Scissors beats Paper! You lose, {source.capitalize()} !", 
														f"ROCK -- Hmm, I lose. Congrats, {source.capitalize()}", 
														"PAPER -- Dang it, it's a draw.")))
				elif message.split()[1].lower() == "scissors":
					await self.message(target, 
										random.choice((f"ROCK -- Rock beats Scissors! You lose, {source.capitalize()} !", 
														f"PAPER -- Hmm, I lose. Congrats, {source.capitalize()}", 
														"SCISSORS -- Dang it, it's a draw.")))
				else:
					await self.message(target, f"{source.capitalize()} is a cheater. Reported.")
		elif message.startswith("!shout"):
			if len(message.split()) == 1:
				return await self.message(target, '\N{SPEAKING HEAD IN SILHOUETTE}')
			await self.message(target, "https://www.twitch.tv/" + message.split()[1])
		elif message.startswith("!time"):
			# TODO: Document
			# TODO: Add ability to reset
			if not hasattr(self, f"{target[1:]}_variables"):
				setattr(self, f"{target[1:]}_variables", {})
			channel_variables = getattr(self, f"{target[1:]}_variables")
			if source == target[1:] and len(message.split()) > 2 and message.split()[1].lower() == target[1:]:
				location = ' '.join(message.split()[2:])
				channel_variables["timezone_location"] = location
				with open(f"data/variables/{target[1:]}.json", 'w') as variables_file:
					json.dump(channel_variables, variables_file, indent = 4)
				await self.message(target, f"Timezone location set to {location}")
			else:
				if len(message.split()) == 1 or message.split()[1].lower() == target[1:]:
					if "timezone_location" not in channel_variables:
						await self.message(target, f"Error: Location not specified")
						return
					location = channel_variables["timezone_location"]
				else:
					location = ' '.join(message.split()[1:])
				try:
					geocode_data = await get_geocode_data(location, aiohttp_session = self.aiohttp_session)
					latitude = geocode_data["geometry"]["location"]["lat"]
					longitude = geocode_data["geometry"]["location"]["lng"]
					timezone_data = await get_timezone_data(latitude = latitude, longitude = longitude, 
															aiohttp_session = self.aiohttp_session)
				except UnitOutputError as e:
					await self.message(target, f"Error: {e}")
					return
				location_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(
								seconds = timezone_data["dstOffset"] + timezone_data["rawOffset"])))
				# TODO: Use method for Discord time command
				time_string = location_time.strftime(f"%#I:%M %p on %b. %#d (%a.) in {geocode_data['formatted_address']} (%Z)")
				await self.message(target, f"It is currently {time_string}.")
				# %#I and %#d for removal of leading zero on Windows with native Python executable
		elif message.startswith("!title"):
			url = "https://api.twitch.tv/kraken/streams/" + target[1:]
			params = {"client_id": self.TWITCH_CLIENT_ID}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if data.get("stream"):
				await self.message(target, data["stream"]["channel"]["status"])
			else:
				await self.message(target, "Title not found.")
		elif message.startswith("!uptime"):
			url = "https://api.twitch.tv/kraken/streams/" + target[1:]
			params = {"client_id": self.TWITCH_CLIENT_ID}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if data.get("stream"):
				await self.message(target, secs_to_duration(int((datetime.datetime.now(datetime.timezone.utc) - dateutil.parser.parse(data["stream"]["created_at"])).total_seconds())))
			else:
				await self.message(target, "Uptime not found.")
		elif message.startswith("!viewers"):
			url = "https://api.twitch.tv/kraken/streams/" + target[1:]
			params = {"client_id": self.TWITCH_CLIENT_ID}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if data.get("stream"):
				await self.message(target, f"{data['stream']['viewers']} viewers watching now.")
			else:
				await self.message(target, "Stream is offline.")
			# No one is watching right now :-/
		
		# Channel-specific commands and aliases
		channel_aliases = getattr(self, f"{target[1:]}_aliases", {})
		channel_commands = getattr(self, f"{target[1:]}_commands", {})
		if channel_commands:
			if message.startswith('!'):
				if message[1:] in channel_aliases:
					message = '!' + channel_aliases[message[1:]]
				if message[1:] in channel_commands:
					await self.message(target, channel_commands[message[1:]])
		
		# Mikki Commands
		if target == "#mikki":
			if any(s in message.lower() for s in ("3 accs", "3 accounts", "three accs", "three accounts")):
				if (self.is_mod(target, source) and len(message.split()) > 2
					and message.split()[2] in self.status_settings):
					status = message.split()[2]
					self.mikki_variables["3accs.status"] = self.status_settings[status]
					with open("data/variables/mikki.json", 'w') as variables_file:
						json.dump(self.mikki_variables, variables_file, indent = 4)
					if status == "mod":
						status += " only"
					await self.message(target, f"3 accs is {status}")
				elif (self.mikki_variables["3accs.status"] or 
						(self.is_mod(target, source) and self.mikki_variables["3accs.status"] is None)):
					self.mikki_variables["3accs"] += 1
					with open("data/variables/mikki.json", 'w') as variables_file:
						json.dump(self.mikki_variables, variables_file, indent = 4)
					await self.message(target, ("Yes, Mikki is playing 3 accounts. "
												f"This question has been asked {self.mikki_variables['3accs']} times."))
			elif "alt" in message.lower():
				if (self.is_mod(target, source) and len(message.split()) > 1
					and message.split()[1] in self.status_settings):
					status = message.split()[1]
					self.mikki_variables["alt.status"] = self.status_settings[status]
					with open("data/variables/mikki.json", 'w') as variables_file:
						json.dump(self.mikki_variables, variables_file, indent = 4)
					if status == "mod":
						status += " only"
					await self.message(target, f"alt is {status}")
				elif (self.mikki_variables["alt.status"] or 
						(self.is_mod(target, source) and self.mikki_variables["alt.status"] is None)):
					await self.message(target, f"Bad {source.capitalize()}!")
			elif message.startswith("!caught"):
				if len(message.split()) == 1:
					caught = source.capitalize()
				elif message.split()[1].lower() == "random":
					caught = self.random_viewer(target)
				else:
					caught = ' '.join(message.split()[1:]).capitalize()
				await self.message(target, f"Mikki has caught a wild {caught}!")
			elif message.split()[0] == "mirosz88autotimeout" and source != "mirosz88" and len(message.split()) > 1:
				if message.split()[1] == "on":
					self.mikki_variables["mirosz88autotimeout.status"] = True
					with open("data/variables/mikki.json", 'w') as variables_file:
						json.dump(self.mikki_variables, variables_file, indent = 4)
					await self.message(target, "mirosz88 auto timeout is on")
				elif message.split()[1] == "off":
					self.mikki_variables["mirosz88autotimeout.status"] = False
					with open("data/variables/mikki.json", 'w') as variables_file:
						json.dump(self.mikki_variables, variables_file, indent = 4)
					await self.message(target, "mirosz88 auto timeout is off")
			elif message.startswith("!pi"):
				if self.is_mod(target, source):
					await self.message(target, ("3.14159265358979323846264338327 9502884197169399375105820974944 "
												"5923078164062862089986280348253 4211706798214808651328230664709 "
												"3844609550582231725359408128481 1174502841027019385211055596446 "
												"2294895493038196442881097566593 3446128475648233786783165271201 "
												"9091456485669234603486104543266 4821339360726024914127372458700 "
												"6606315588174881520920962829254 0917153643678925903600113305305 "
												"4882046652138414695194151160943 3057270365759591953092186117381 "
												"9326117931051185480744623799627 4956735188575272489122793818301 "
												"1949129833673362440656643086021 3949463952247371907021798609437"))
				else:
					await self.message(target, "3.14")
			elif "sheep" in message.lower():
				if (self.is_mod(target, source) and len(message.split()) > 1
					and message.split()[1] in self.status_settings):
					status = message.split()[1]
					self.mikki_variables["sheep.status"] = self.status_settings[status]
					with open("data/variables/mikki.json", 'w') as variables_file:
						json.dump(self.mikki_variables, variables_file, indent = 4)
					if status == "mod":
						status += " only"
					await self.message(target, f"sheep is {status}")
				elif (self.mikki_variables["sheep.status"] or 
						(self.is_mod(target, source) and self.mikki_variables["sheep.status"] is None)):
					self.mikki_variables["sheep"] += 1
					with open("data/variables/mikki.json", 'w') as variables_file:
						json.dump(self.mikki_variables, variables_file, indent = 4)
					await self.message(target, f"\N{SHEEP} {self.mikki_variables['sheep']}")
			elif message.startswith("!tick"):
				self.mikki_variables["ticks"] += 1
				with open("data/variables/mikki.json", 'w') as variables_file:
					json.dump(self.mikki_variables, variables_file, indent = 4)
				await self.message(target, (f"Mikki has wasted {self.mikki_variables['ticks']} ticks. "
												"http://i.imgur.com/bSCnFb1.png"))
			
			if source == "mirosz88" and self.mikki_variables["mirosz88autotimeout.status"]:
				await self.message(target,  "/timeout mirosz88 1")
		
		# Imagrill Commands
		if target == "#imagrill":
			# TODO: Command for http://services.runescape.com/m=rswiki/en/Pronunciation_Guide ?
			triggers = {":|": "http://imgur.com/cbgVzj7", "-.-": "http://imgur.com/cbgVzj7", 
						":3": "http://puu.sh/iE7ik.jpg", ":p": "http://imgur.com/p3GH9uE http://imgur.com/xpCiJKh", 
						"banana": "BANANA http://imgur.com/TtRH7vU http://imgur.com/kTX3qa1", 
						"failfish": "http://imgur.com/CtscIDh", "lick it": "http://imgur.com/aCqNXmV", 
						"yawn": "Yawwwwwn"}
			for trigger in triggers:
				if trigger in message.lower():
					if (self.is_mod(target, source) and len(message.split()) > len(trigger.split())
						and message.split()[len(trigger.split())] in self.status_settings):
						status = message.split()[len(trigger.split())]
						self.imagrill_variables[f"{trigger}.status"] = self.status_settings[status]
						with open("data/variables/imagrill.json", 'w') as variables_file:
							json.dump(self.imagrill_variables, variables_file, indent = 4)
						if status == "mod":
							status += " only"
						await self.message(target, f"{trigger} is {status}")
					elif (self.imagrill_variables.get(f"{trigger}.status", True) or 
							(self.is_mod(target, source) and self.imagrill_variables[f"{trigger}.status"] is None)):
						await self.message(target, triggers[trigger])
			if message.startswith("!caught"):
				if len(message.split()) == 1:
					caught = source.capitalize()
				elif message.split()[1].lower() == "random":
					caught = self.random_viewer(target)
				else:
					caught = ' '.join(message.split()[1:]).capitalize()
				await self.message(target, f"Arts has caught a wild {caught}!")
			elif message.startswith("!death"):
				if self.is_mod(target, source) and len(message.split()) > 1 and message.split()[1] == "inc":
					self.imagrill_variables["deaths"] += 1
					with open("data/variables/imagrill.json", 'w') as variables_file:
						json.dump(self.imagrill_variables, variables_file, indent = 4)
				await self.message(target, f"Arts has died {self.imagrill_variables['deaths']} times.")
			elif message.startswith("!dsdeaths"):
				if self.is_mod(target, source) and len(message.split()) > 1 and message.split()[1] == "inc":
					self.imagrill_variables["dsdeaths"] += 1
					with open("data/variables/imagrill.json", 'w') as variables_file:
						json.dump(self.imagrill_variables, variables_file, indent = 4)
				await self.message(target, f"Arts has died {self.imagrill_variables['dsdeaths']} times.")
			elif message.startswith(("!ed8", "!edate")):
				trigger = message[1:4]
				if trigger.endswith('a'):
					trigger += "te"
				if (self.is_mod(target, source) and len(message.split()) > 1
					and message.split()[1] in self.status_settings):
					status = message.split()[1]
					self.imagrill_variables["!edate.status"] = self.status_settings[status]
					with open("data/variables/imagrill.json", 'w') as variables_file:
						json.dump(self.imagrill_variables, variables_file, indent = 4)
					if status == "mod":
						status += " only"
					await self.message(target, f"!{trigger} is {status}")
				elif (self.imagrill_variables["!edate.status"] or 
						(self.is_mod(target, source) and self.imagrill_variables["!edate.status"] is None)):
					self.imagrill_variables["edates"] += 1
					with open("data/variables/imagrill.json", 'w') as variables_file:
						json.dump(self.imagrill_variables, variables_file, indent = 4)
					await self.message(target, f"Arts has {self.imagrill_variables['edates']} {trigger}s.")
			elif message.startswith("!fail"):
				self.imagrill_variables["fail"] += 1
				with open("data/variables/imagrill.json", 'w') as variables_file:
					json.dump(self.imagrill_variables, variables_file, indent = 4)
				await self.message(target, f"Fail #{self.imagrill_variables['fail']} http://imgur.com/FWv07A9")
			elif message.startswith("!googer"):
				await self.message(target, "https://google.com/search?q=" + '+'.join(message.split()[1:]) + ' "RAISE YOUR GOOGERS" -Arts')
			elif message.startswith("!like"):
				if (self.is_mod(target, source) and len(message.split()) > 1
					and message.split()[1] in self.status_settings):
					status = message.split()[1]
					self.imagrill_variables["!like.status"] = self.status_settings[status]
					with open("data/variables/imagrill.json", 'w') as variables_file:
						json.dump(self.imagrill_variables, variables_file, indent = 4)
					if status == "mod":
						status += " only"
					await self.message(target, f"!like is {status}")
				elif (self.imagrill_variables["!like.status"] or 
						(self.is_mod(target, source) and self.imagrill_variables["!like.status"] is None)):
					await self.message(target, "like " + " like ".join(message.split()[1:]))
			elif message.startswith("!mic"):
				self.imagrill_variables["mic"] += 1
				with open("data/variables/imagrill.json", 'w') as variables_file:
					json.dump(self.imagrill_variables, variables_file, indent = 4)
				await self.message(target, f"Arts's mic has acted up {self.imagrill_variables['mic']} times.")
			elif message.startswith("!sneeze"):
				if len(message.split()) == 1 or not is_number(message.split()[1]) or 10 < int(message.split()[1]) or int(message.split()[1]) < 2:
					await self.message(target, "Bless you!")
				else:
					await self.message(target, ' '.join(["Bless you!" for i in range(int(message.split()[1]))]))
			elif message.startswith("!stats"):
				if (self.is_mod(target, source) and len(message.split()) > 1
					and message.split()[1] in self.status_settings):
					status = message.split()[1]
					self.imagrill_variables["!stats.status"] = self.status_settings[status]
					with open("data/variables/imagrill.json", 'w') as variables_file:
						json.dump(self.imagrill_variables, variables_file, indent = 4)
					if status == "mod":
						status += " only"
					await self.message(target, f"!stats is {status}")
				elif (self.imagrill_variables["!stats.status"] or 
						(self.is_mod(target, source) and self.imagrill_variables["!stats.status"] is None)):
					await self.message(target, 
										"http://services.runescape.com/m=hiscore_oldschool/hiscorepersonal.ws?user1=Arts")
			elif (message.startswith("what level is your") or message.endswith("stats?") or 
				"show stats" in message or re.search(r"^what.*s your.*(level|stats|xp.*\?$)|"
														r"(u (maxed|comped)|you got comp|"
														r"any (99.*s|120)|you 2595|"
														r"total (level|xp)).*\?", message)):
				await self.message(target, "http://services.runescape.com/m=hiscore_oldschool/hiscorepersonal.ws?user1=Arts")
			elif message.startswith("!tits") or "show tits" in message.lower():
				await self.message(target, "https://en.wikipedia.org/wiki/Tit_(bird) https://en.wikipedia.org/wiki/Great_tit http://i.imgur.com/40Ese5S.jpg")
			elif message.startswith("!troll"):
				if self.is_mod(target, source) and len(message.split()) > 1 and message.split()[1] == "inc":
					if len(message.split()) > 2 and is_number(message.split()[2]):
						self.imagrill_variables["trolls"] += int(message.split()[2])
					else:
						self.imagrill_variables["trolls"] += 1
					with open("data/variables/imagrill.json", 'w') as variables_file:
						json.dump(self.imagrill_variables, variables_file, indent = 4)
				await self.message(target, f"There have been {self.imagrill_variables['trolls']} trolls.")
			elif message.split()[0] == "pmpls" and source != "pmfornudes" and len(message.split()) > 1:
				if message.split()[1] == "on":
					self.imagrill_variables["pmpls"] = True
					with open("data/variables/imagrill.json", 'w') as variables_file:
						json.dump(self.imagrill_variables, variables_file, indent = 4)
					await self.message(target, f"pmpls is on.")
				elif message.split()[1] == "off":
					self.imagrill_variables["pmpls"] = False
					with open("data/variables/imagrill.json", 'w') as variables_file:
						json.dump(self.imagrill_variables, variables_file, indent = 4)
					await self.message(target, f"pmpls is off.")
			if self.imagrill_variables["pmpls"] and source == "pmfornudes":
				await self.message(target, "PMFornud pls")
		
		# Runescape Commands
		if message.startswith(("!07rswiki", "!rswiki07", "!osrswiki", "!rswikios")):
			await self.message(target, "oldschoolrunescape.wikia.com/wiki/" + '_'.join(message.split()[1:]))
		elif message.startswith("!cache"):
			await self.message(target, f"{secs_to_duration(int(10800 - time.time() % 10800))} until Guthixian Cache.")
		elif message.startswith(("!hiscore", "!highscore")):
			# TODO: Other RS3 hiscores?
			if len(message.split()) == 1:
				return await self.message(target, "Please enter a username. "
													"Format: !hiscores [username] [skill/total] [hiscores type] [rank/xp/level]")
			username = message.split()[1].replace('_', ' ')
			skill_order = ("total", "attack", "defence", "strength", "constitution", "ranged", "prayer", 
							"magic", "cooking", "woodcutting", "fletching", "fishing", "firemaking", 
							"crafting", "smithing", "mining", "herblore", "agility", "thieving", "slayer", 
							"farming", "runecrafting", "hunter", "construction", "summoning", "dungeoneering", 
							"divination", "invention")
			skill_aliases = {"att": "attack", "atk": "attack", "defense": "defence", "def": "defence", 
								"str": "strength", "hp": "constitution", "range": "ranged", "pray": "prayer", 
								"mage": "magic", "cook": "cooking", "wc": "woodcutting", "fletch": "fletching", 
								"fish": "fishing", "fm": "firemaking", "craft": "crafting", "smith": "smithing", 
								"mine": "mining", "herb": "herblore", "thief": "thieving", "slay": "slayer", 
								"farm": "farming", "rc": "runecrafting", "hunt": "hunter", "con": "construction", 
								"dung": "dungeoneering", "dg": "dungeonering", "div": "divination", 
								"inventor": "invention", "invent": "invention"}
			if len(message.split()) == 2:
				skill = "total"
			else:
				skill = message.split()[2].lower()
			if skill in skill_aliases:
				skill = skill_aliases[skill]
			if skill not in skill_order:
				return await self.message(target, "Invalid skill. Use _'s for spaces in usernames.")
			if len(message.split()) <= 3:
				hiscores_type = ""
			else:
				hiscores_type = message.split()[3].lower()
			hiscores_types = ("", "ironman", "hardcore_ironman", "oldschool", "oldschool_ironman", 
								"oldschool_ultimate", "oldschool_hardcore_ironman", "oldschool_deadman", 
								"oldschool_seasonal", "oldschool_tournament")
			hiscores_type_aliases = {"rs3": "", "runescape_3": "", "runescape3": "", 
										"07": "oldschool", "osrs": "oldschool", "os": "oldschool", 
										"hcim": "hardcore_ironman", "hc": "hardcore", "uim": "ultimate", 
										"tourny": "tournament"}
			hiscores_names = {"": "RS3", "ironman": "RS3 (Ironman)", "hardcore_ironman": "RS3 (Hardcore Ironman)", 
								"oldschool": "OSRS", "oldschool_ironman": "OSRS (Ironman)", 
								"oldschool_ultimate": "OSRS (Ultimate Ironman)", 
								"oldschool_hardcore_ironman": "OSRS (Hardcore Ironman)", 
								"oldschool_deadman": "OSRS (Deadman Mode)", "oldschool_seasonal": "OSRS (Seasonal)", 
								"oldschool_tournament": "OSRS (Tournament)"}
			for alias, name in hiscores_type_aliases.items():
				hiscores_type = hiscores_type.replace(alias, name)
			hiscores_type = hiscores_type.lstrip('_')
			if skill in ("dungeoneering", "divination", "invention") and hiscores_type.startswith("oldschool"):
				return await self.message(target, "Invalid skill for OSRS.")
			if hiscores_type not in hiscores_types:
				valid_types = []
				for type in hiscores_types:
					if not type.startswith("oldschool"):
						type = "runescape_3_" + type
						type = type.rstrip('_')
					valid_types.append(type)
				return await self.message(target, f"Invalid hiscores type. Valid types: {', '.join(valid_types)}")
			hiscores_name = hiscores_names[hiscores_type]
			if hiscores_type:
				hiscores_type = '_' + hiscores_type
			stat_types = ("rank", "level", "xp")
			stat_type_aliases = {"exp": "xp", "experience": "xp", "lvl": "level"}
			if len(message.split()) <= 4:
				stat_type = "level"
			else:
				stat_type = message.split()[4].lower()
			if stat_type in stat_type_aliases:
				stat_type = stat_type_aliases[stat_type]
			if stat_type not in stat_types:
				stat_type = "level"
			hiscores_url = f"https://secure.runescape.com/m=hiscore{hiscores_type}/index_lite.ws"
			params = {"player": username}
			async with self.aiohttp_session.get(hiscores_url, params = params) as resp:
				if resp.status == 404:
					return await self.message(target, "Username not found.")
				data = await resp.text()
			data = data.split()
			skill_data = data[skill_order.index(skill)].split(',')
			stat = int(skill_data[stat_types.index(stat_type)])
			if stat_type == "rank":
				if skill == "total":
					stat_text = f" is rank {stat:,} overall"
				else:
					stat_text = f" is rank {stat:,} in {skill.capitalize()}"
			elif stat_type == "xp":
				if skill == "total":
					stat_text = f" has {stat:,} total XP"
				else:
					stat_text = f" has {stat:,} XP in {skill.capitalize()}"
			else:
				if skill != "total":
					skill = skill.capitalize()
				stat_text = f"'s {skill} level is {stat:,}"
			await self.message(target, f"{username.capitalize()}{stat_text} on {hiscores_name}.")
		elif message.startswith("!level"):
			if len(message.split()) == 1:
				await self.message(target, "Please enter a level.")
			elif is_number(message.split()[1]):
				level = int(message.split()[1])
				if 1 <= level < 127:
					xp = 0
					for i in range(1, level):
						xp += int(i + 300 * 2 ** (i / 7))
					xp = int(xp / 4)
					await self.message(target, f"Runescape Level {level} = {xp:,} xp")
				elif level > 9000:
					await self.message(target, "It's over 9000!")
				elif level == 9000:
					await self.message(target, "Almost there.")
				elif level > 126 and level < 9000:
					await self.message(target, f"I was gonna calculate xp at Level {level}. Then I took an arrow to the knee.")
				else:
					await self.message(target, f"Level {level} does not exist.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!monster"):
			if len(message.split()) == 1:
				await self.message(target, "Please specify a monster.")
				return
			url = "http://services.runescape.com/m=itemdb_rs/bestiary/beastSearch.json?term="
			url += '+'.join(message.split()[1:])
			async with self.aiohttp_session.get(url) as resp:
				data = await resp.json(content_type = "text/html")
			if "value" in data[0]:
				monster_id = data[0]["value"]
				url = "http://services.runescape.com/m=itemdb_rs/bestiary/beastData.json"
				params = {"beastid": monster_id}
				async with self.aiohttp_session.get(url, params = params) as resp:
					data = await resp.json(content_type = "text/html")
				level = data.get("level", "N/A")
				weakness = data.get("weakness", "N/A")
				hp = data.get("lifepoints", "N/A")
				await self.message(target, f"{data['name']}: {data['description']}, Level: {level}, Weakness: {weakness}, XP/Kill: {data['xp']}, HP: {hp}, Members: {data['members']}, Aggressive: {data['aggressive']}")
			else:
				await self.message(target, "Monster not found.")
		elif message.startswith("!reset"):
			await self.message(target, f"{secs_to_duration(int(86400 - time.time() % 86400))} until reset.")
		elif message.startswith("!rswiki"):
			await self.message(target, "runescape.wikia.com/wiki/" + '_'.join(message.split()[1:]))
		elif message.startswith("!warbands"):
			await self.message(target, f"{secs_to_duration(int(25200 - time.time() % 25200))} until Warbands.")
		elif message.startswith("!xpat"):
			if len(message.split()) == 1:
				await self.message(target, "Please enter xp.")
				return
			xp = message.split()[1].replace(',', '')
			if is_number(xp):
				xp = float(xp)
				if 0 <= xp < 200000001:
					xp = int(xp)
					_level = 1
					_xp = 0
					while xp >= _xp:
						_xp *= 4
						_xp += int(_level + 300 * 2 ** (_level / 7))
						_xp /= 4
						_level += 1
					_level -= 1
					await self.message(target, f"{xp:,} xp = level {_level}")
				else:
					await self.message(target, "You can't have that much xp!")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!xpbetween"):
			if len(message.split()) >= 3 and is_number(message.split()[1]) and 1 <= float(message.split()[1]) < 127 and is_number(message.split()[2]) and 1 <= float(message.split()[2]) < 127:
				startlevel = int(message.split()[1])
				endlevel = int(message.split()[2])
				xp, startxp, betweenxp = 0, 0, 0
				for level in range(1, endlevel):
					if level == startlevel:
						startxp = int(xp / 4)
					xp += int(level + 300 * 2 ** (level / 7))
				betweenxp = int(xp / 4) - startxp
				await self.message(target, f"{betweenxp:,} xp between level {startlevel} and level {endlevel}")
			else:
				await self.message(target, "Syntax error.")
		
		# League of Legends Commands
		# WIP using development API key
		# TODO: Register permanent project
		# TODO: Handle missing input
		# TODO: Handle regions
		# TODO: Handle other errors besides 404
		# TODO: Subcommands
		# TODO: Expand
		if message.startswith("!lollvl"):
			username = message.split()[1]
			url = "https://na1.api.riotgames.com/lol/summoner/v3/summoners/by-name/" + username
			params = {"api_key": self.RIOT_GAMES_API_KEY}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
				if resp.status == 404:
					await self.message(target, "Account not found.")
					return
			await self.message(target, f"{data['name']} is level {data['summonerLevel']}.")
		elif message.startswith("!loltotalgames"):
			username = message.split()[1]
			url = "https://na1.api.riotgames.com/lol/summoner/v3/summoners/by-name/" + username
			params = {"api_key": self.RIOT_GAMES_API_KEY}
			async with self.aiohttp_session.get(url, params = params) as resp:
				account_data = await resp.json()
				if resp.status == 404:
					await self.message(target, "Account not found.")
					return
			account_id = account_data["accountId"]
			url = f"https://na1.api.riotgames.com/lol/match/v3/matchlists/by-account/{account_id}"
			async with self.aiohttp_session.get(url, params = params) as resp:
				matches_data = await resp.json()
				if resp.status == 404:
					await self.message(target, "Data not found.")
					return
			await self.message(target, f"{account_data['name']} has played {matches_data['totalGames']} total games.")
		elif message.startswith("!lolcurrentgame"):
			if message.split()[1] in ("time", "participants"):
				username = message.split()[2]
				url = "https://na1.api.riotgames.com/lol/summoner/v3/summoners/by-name/" + username
				params = {"api_key": self.RIOT_GAMES_API_KEY}
				async with self.aiohttp_session.get(url, params = params) as resp:
					account_data = await resp.json()
					if resp.status == 404:
						await self.message(target, "Account not found.")
						return
				summoner_id = account_data["id"]
				url = f"https://na1.api.riotgames.com/lol/spectator/v3/active-games/by-summoner/{summoner_id}"
				async with self.aiohttp_session.get(url, params = params) as resp:
					game_data = await resp.json()
					if resp.status == 404:
						await self.message(target, "Data not found.")
						return
				if message.split()[1] == "time":
					await self.message(target, f"{secs_to_duration(game_data['gameLength'])}")
				else:
					await self.message(target, ", ".join(p["summonerName"] for p in game_data["participants"]))
		
		# Miscellaneous Commands
		if message.startswith('!') and message[1:] in self.misc_commands:
			await self.message(target, self.misc_commands[message[1:]])
		elif message.startswith("!christmas"):
			now = datetime.datetime.utcnow()
			christmas = datetime.datetime(now.year, 12, 25)
			if now > christmas:
				christmas = christmas.replace(year = christmas.year + 1)
			seconds = int((christmas - now).total_seconds())
			await self.message(target, f"{secs_to_duration(seconds)} until Christmas!")
		elif message.startswith("!easter"):
			now = datetime.datetime.utcnow()
			easter = datetime.datetime.combine(dateutil.easter.easter(now.year), datetime.time.min)
			if now > easter:
				easter = datetime.datetime.combine(dateutil.easter.easter(now.year + 1), datetime.time.min)
			seconds = int((easter - now).total_seconds())
			await self.message(target, f"{secs_to_duration(seconds)} until Easter!")
		elif message.startswith(("!kitten", "!kitty")):
			await self.message(target, random.choice(("CoolCat", "DxCat")))
		elif message.startswith("!puppy"):
			await self.message(target, random.choice(("BegWan", "ChefFrank", "CorgiDerp", "FrankerZ", "RalpherZ")))
		
		# Unit Conversion Commands
		# TODO: Add support for non-integers/floats, improve formatting
		if message.startswith(("!ctof", "!ftoc", "!lbtokg", "!kgtolb", "!fttom", "!mtoft", "!mtofi", "!gtooz", "!oztog", "!mitokm", "!kmtomi", "!ozttog", "!gtoozt", "!ozttooz", "!oztoozt")):
			if len(message.split()) == 1:
				await self.message(target, "Please enter input.")
				return
			elif not is_number(message.split()[1]):
				await self.message(target, "Syntax error.")
				return
		if message.startswith("!ctof"):
			await self.message(target, f"{message.split()[1]} °C = {int(message.split()[1]) * 9 / 5 + 32} °F")
		elif message.startswith("!ftoc"):
			await self.message(target, f"{message.split()[1]} °F = {(int(message.split()[1]) - 32) * 5 / 9} °C")
		elif message.startswith("!lbtokg"):
			await self.message(target, f"{message.split()[1]} lb = {int(message.split()[1]) * 0.45359237} kg")
		elif message.startswith("!kgtolb"):
			await self.message(target, f"{message.split()[1]} kg = {int(message.split()[1]) * 2.2046} lb")
		elif message.startswith("!fttom"):
			await self.message(target, f"{message.split()[1]} ft = {int(message.split()[1]) * 0.3048} m")
		elif message.startswith("!mtoft"):
			await self.message(target, f"{message.split()[1]} m = {int(message.split()[1]) * 3.2808} ft")
		elif message.startswith("!fitom"):
			if len(message.split()) > 2 and is_number(message.split()[1]) and is_number(message.split()[2]):
				await self.message(target, f"{message.split()[1]} ft {message.split()[2]} in = {(int(message.split()[1]) + int(message.split()[2]) / 12) * 0.3048} m")
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!mtofi"):
			await self.message(target, f"{message.split()[1]} m = {int(message.split()[1]) * 39.37 // 12} ft {int(message.split()[1]) * 39.37 - (int(message.split()[1]) * 39.37 // 12) * 12} in")
		elif message.startswith("!gtooz"):
			await self.message(target, f"{message.split()[1]} g = {int(message.split()[1]) * 0.035274} oz")
		elif message.startswith("!oztog"):
			await self.message(target, f"{message.split()[1]} oz = {int(message.split()[1]) / 0.035274} g")
		elif message.startswith("!mitokm"):
			await self.message(target, f"{message.split()[1]} mi = {int(message.split()[1]) / 0.62137} km")
		elif message.startswith("!kmtomi"):
			await self.message(target, f"{message.split()[1]} km = {int(message.split()[1]) * 0.62137} mi")
		elif message.startswith("!ozttog"):
			await self.message(target, f"{message.split()[1]} oz t = {int(message.split()[1]) / 0.032151} g")
		elif message.startswith("!gtoozt"):
			await self.message(target, f"{message.split()[1]} g = {int(message.split()[1]) * 0.032151} oz t")
		elif message.startswith("!ozttooz"):
			await self.message(target, f"{message.split()[1]} oz t = {int(message.split()[1]) * 1.09714996656} oz")
		elif message.startswith("!oztoozt"):
			await self.message(target, f"{message.split()[1]} oz = {int(message.split()[1]) * 0.911452427176} oz t")
		
		if message == "!restart" and source == "harmon758":
			await self.message(target, "Restarting")
			print("Restarting Twitch Harmonbot...")
			await self.aiohttp_session.close()
			await self.disconnect()
	
	def is_mod(self, target, source):
		return source in self.channels[target]["modes"].get('o', [])
	
	def random_viewer(self, target):
		return random.choice(list(self.channels.get(target, {}).get("users", ["N/A"]))).capitalize()

def create_folder(folder):
	if not os.path.exists(folder):
		os.makedirs(folder)

def is_number(characters):
	try:
		float(characters)
		return True
	except ValueError:
		return False

def time_left(start, interval):
	if time.time() <= start or not interval:
		return start - time.time()
	else:
		return interval - (time.time() - start) % interval

def secs_to_duration(secs):
	output = ""
	for dur_name, dur_in_secs in (("year", 31536000), ("week", 604800), ("day", 86400), ("hour", 3600), ("minute", 60)):
		if secs >= dur_in_secs:
			num_dur = int(secs / dur_in_secs)
			output += f" {num_dur} {dur_name}"
			if (num_dur > 1): output += 's'
			secs -= num_dur * dur_in_secs
	if secs != 0:
		output += f" {secs} second"
		if (secs != 1): output += 's'
	return output[1:] if output else f"{secs} seconds"

if __name__ == "__main__":
	print("Starting up Twitch Harmonbot...")
	create_folder("data/commands/aliases")
	create_folder("data/logs/channels")
	create_folder("data/logs/client")
	create_folder("data/variables")
	# Load credentials from .env
	dotenv.load_dotenv()
	client = TwitchClient("Harmonbot")
	oauth_token = os.getenv("TWITCH_BOT_ACCOUNT_OAUTH_TOKEN")
	loop = asyncio.get_event_loop()
	asyncio.ensure_future(client.connect("irc.chat.twitch.tv", password = oauth_token), loop = loop)
	# DEFAULT_PORT = 6667
	loop.run_forever()

