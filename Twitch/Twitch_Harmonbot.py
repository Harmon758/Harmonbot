
import pydle

import asyncio
import datetime
import json
import logging
import logging.handlers
import os
import random
import sys
import time
# import unicodedata

import aiohttp
import dateutil.easter
import dateutil.parser
import unicodedata2 as unicodedata

import credentials

class TwitchClient(pydle.Client):
	
	def __init__(self, nickname):
		self.version = "2.2.0"
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
		# Clients
		self.aiohttp_session = aiohttp.ClientSession(loop = self.eventloop.loop)
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
	
	async def on_connect(self):
		await super().on_connect()
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
		elif message.startswith("!audiodefine"):
			url = f"http://api.wordnik.com:80/v4/word.json/{message.split()[1]}/audio"
			params = {"useCanonical": "false", "limit": 1, "api_key": credentials.wordnik_apikey}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if data:
				await self.message(target, data[0]["word"].capitalize() + ": " + data[0]["fileUrl"])
			else:
				await self.message(target, "Word or audio not found.")
		elif message.startswith("!averagefps"):
			url = "https://api.twitch.tv/kraken/streams/" + target[1:]
			params = {"client_id": credentials.twitch_client_id}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if data.get("stream"):
				await self.message(target, f"Average FPS: {data['stream']['average_fps']}")
			else:
				await self.message(target, "Average FPS not found.")
		elif message.startswith("!bye"):
			if len(message.split()) == 1 or message.split()[1].lower() == "harmonbot":
				#await self.message(target, "Bye, {source}!", source=source)
				await self.message(target, f"Bye, {source.capitalize()}!")
			else:
				await self.message(target, f"{' '.join(message.split()[1:]).title()}, {source.capitalize()} says goodbye!")
		elif message.startswith(("!char", "!character", "!unicode")):
			try:
				await self.message(target, unicodedata.lookup(' '.join(message.split()[1:])))
			except KeyError:
				await self.message(target, "\N{NO ENTRY} Unicode character not found")
		elif message.startswith("!define"):
			url = f"http://api.wordnik.com:80/v4/word.json/{message.split()[1]}/definitions"
			params = {"limit": 1, "includeRelated": "false", "useCanonical": "false", "includeTags": "false", 
						"api_key": credentials.wordnik_apikey}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if data:
				await self.message(target, data[0]["word"].capitalize() + ": " + data[0]["text"])
			else:
				await self.message(target, "Definition not found.")
		elif message.startswith("!element"):
			elements = {"ac": "Actinium", "ag": "Silver", "al": "Aluminum", "am": "Americium", "ar": "Argon", }
			if len(message.split()) > 1 and message.split()[1] in elements:
				await self.message(target, elements[message.split()[1]])
		elif message.startswith(("!followage", "!followed", "!howlong")):
			url = f"https://api.twitch.tv/kraken/users/{source}/follows/channels/{target[1:]}"
			params = {"client_id": credentials.twitch_client_id}
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
			params = {"client_id": credentials.twitch_client_id}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			await self.message(target, f"There are currently {data['_total']} people following {target[1:].capitalize()}.")
		elif message.startswith("!google"):
			await self.message(target, "https://google.com/search?q=" + '+'.join(message.split()[1:]))
		elif message.startswith(("!congrats", "!grats", "!gz")):
			if len(message.split()) == 1:
				await self.message(target, "Congratulations!!!!!")
			else:
				await self.message(target, f"Congratulations, {' '.join(message.split()[1:]).title()}!!!!!")
		elif message.startswith("!hello"):
			if len(message.split()) == 1 or message.split()[1].lower() == "harmonbot":
				await self.message(target, f"Hello, {source.capitalize()}!")
			else:
				await self.message(target, f"{' '.join(message.split()[1:]).title()}, {source.capitalize()} says hello!")
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
		elif message.startswith("!hi"):
			if message.split()[0] in ["!hiscores", "!hiscore", "!highscore", "!highscores"]: return
			elif len(message.split()) == 1 or message.split()[1].lower() == "harmonbot":
				await self.message(target, f"Hello, {source.capitalize()}!")
			else:
				await self.message(target, f"{' '.join(message.split()[1:]).title()}, {source.capitalize()} says hello!")
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
		elif message.startswith("!imfeelinglucky"):
			await self.message(target, "https://google.com/search?btnI&q=" + '+'.join(message.split()[1:]))
		elif message.startswith("!lmgtfy"):
			await self.message(target, "lmgtfy.com/?q=" + '+'.join(message.split()[1:]))
		elif message.startswith("!mods"):
			mods = self.channels[target]["modes"].get('o', [])
			await self.message(target, f"Mods Online ({len(mods)}): {', '.join(mod.capitalize() for mod in mods)}")
		elif message.startswith("!randomword"):
			url = "http://api.wordnik.com:80/v4/words.json/randomWord"
			params = {"hasDictionaryDef": "false", "minCorpusCount": 0, "maxCorpusCount": -1, 
						"minDictionaryCount": 1, "maxDictionaryCount": -1, "minLength": 5, "maxLength": -1, 
						"api_key": credentials.wordnik_apikey}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			await self.message(target, data["word"].capitalize())
			'''
			elif message.startswith("!randomviewer"): # on/off
				await self.message(target, self.random_viewer(target))
			'''
		elif message.startswith("!rng"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, str(random.randint(1, int(message.split()[1]))))
			else:
				await self.message(target, str(random.randint(1, 10)))
		elif message.startswith("!title"):
			url = "https://api.twitch.tv/kraken/streams/" + target[1:]
			params = {"client_id": credentials.twitch_client_id}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if data.get("stream"):
				await self.message(target, data["stream"]["channel"]["status"])
			else:
				await self.message(target, "Title not found.")
		elif message.startswith("!translate"):
			url = "https://translate.yandex.net/api/v1.5/tr.json/translate"
			params = {"lang": "en", "text": ' '.join(message.split()[1:]), "options": 1, 
						"key": credentials.yandex_translate_api_key}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if data["code"] != 200:
				await self.message(target, f"Error: {data['message']}")
				return
			await self.message(target, data["text"][0])
		elif message.startswith("!uptime"):
			url = "https://api.twitch.tv/kraken/streams/" + target[1:]
			params = {"client_id": credentials.twitch_client_id}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if data.get("stream"):
				await self.message(target, secs_to_duration(int((datetime.datetime.now(datetime.timezone.utc) - dateutil.parser.parse(data["stream"]["created_at"])).total_seconds())))
			else:
				await self.message(target, "Uptime not found.")
		elif message.startswith("!urband"):
			url = "http://api.urbandictionary.com/v0/define"
			params = {"term": '+'.join(message.split()[1:])}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if not data or "list" not in data or not data["list"]:
				await self.message(target, "No results found.")
				return
			definition = data["list"][0]
			message = f"{definition['word']}: " + definition['definition'].replace('\n', ' ')
			if len(message + definition["permalink"]) > 423:
				message = message[:423 - len(definition["permalink"]) - 4] + "..."
			message += ' ' + definition["permalink"]
			await self.message(target, message)
		elif message.startswith("!viewers"):
			url = "https://api.twitch.tv/kraken/streams/" + target[1:]
			params = {"client_id": credentials.twitch_client_id}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			if data.get("stream"):
				await self.message(target, f"{data['stream']['viewers']} viewers watching now.")
			else:
				await self.message(target, "Stream is offline.")
			# No one is watching right now :-/
		elif message.startswith("!wiki"):
			await self.message(target, "wikipedia.org/wiki/" + '_'.join(message.split()[1:]))
		
		# Channel-specific commands and aliases
		channel_aliases = getattr(self, f"{target[1:]}_aliases", None)
		channel_commands = getattr(self, f"{target[1:]}_commands", None)
		if channel_commands:
			if message.startswith('!'):
				if message[1:] in channel_aliases:
					message = '!' + channel_aliases[message[1:]]
				if message[1:] in channel_commands:
					await self.message(target, channel_commands[message[1:]])
		
		# Mikki Commands
		if target == "#mikki":
			if message.startswith("!caught"):
				if len(message.split()) == 1:
					caught = source.capitalize()
				elif message.split()[1].lower() == "random":
					caught = self.random_viewer(target)
				else:
					caught = ' '.join(message.split()[1:]).capitalize()
				await self.message(target, f"Mikki has caught a wild {caught}!")
			elif message.startswith("!mikkitime"):
				mikkitime = datetime.datetime.now(datetime.timezone(datetime.timedelta(minutes = 60 * 8)))
				await self.message(target, f"It is currently {mikkitime.strftime('%#I:%M %p on %b. %#d in Western Australia (%Z)')}.")
				# %#d for removal of leading zero on Windows with native Python executable
				# TODO: Include day of week
			elif message.startswith("!pi"):
				if self.is_mod(target, source):
					await self.message(target, "3.14159265358979323846264338327 9502884197169399375105820974944 5923078164062862089986280348253 4211706798214808651328230664709 3844609550582231725359408128481 1174502841027019385211055596446 2294895493038196442881097566593 3446128475648233786783165271201 9091456485669234603486104543266 4821339360726024914127372458700 6606315588174881520920962829254 0917153643678925903600113305305 4882046652138414695194151160943 3057270365759591953092186117381 9326117931051185480744623799627 4956735188575272489122793818301 1949129833673362440656643086021 3949463952247371907021798609437")
				else:
					await self.message(target, "3.14")
		
		# Imagrill Commands
		if target == "#imagrill":
			if message.startswith("!caught"):
				if len(message.split()) == 1:
					caught = source.capitalize()
				elif message.split()[1].lower() == "random":
					caught = self.random_viewer(target)
				else:
					caught = ' '.join(message.split()[1:]).capitalize()
				await self.message(target, f"Arts has caught a wild {caught}!")
			elif message.startswith("!googer"):
				await self.message(target, "https://google.com/search?q=" + '+'.join(message.split()[1:]) + ' "RAISE YOUR GOOGERS" -Arts')
			elif message.startswith("!sneeze"):
				if len(message.split()) == 1 or not is_number(message.split()[1]) or 10 < int(message.split()[1]) or int(message.split()[1]) < 2:
					await self.message(target, "Bless you!")
				else:
					await self.message(target, ' '.join(["Bless you!" for i in range(int(message.split()[1]))]))
			elif message.startswith("!tits") or "show tits" in message:
				await self.message(target, "https://en.wikipedia.org/wiki/Tit_(bird) https://en.wikipedia.org/wiki/Great_tit http://i.imgur.com/40Ese5S.jpg")
		
		# Runescape Commands
		if message.startswith(("!07rswiki", "!rswiki07", "!osrswiki", "!rswikios")):
			await self.message(target, "oldschoolrunescape.wikia.com/wiki/" + '_'.join(message.split()[1:]))
		elif message.startswith("!cache"):
			await self.message(target, f"{secs_to_duration(int(10800 - time.time() % 10800))} until Guthixian Cache.")
		elif message.startswith("!indecentcodehs"):
			await self.message(target, "indecentcode.com/hs/index.php?id=" + '+'.join(message.split()[1:]))
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
			url = "http://services.runescape.com/m=itemdb_rs/bestiary/beastSearch.json"
			params = {"term": '+'.join(message.split()[1:])}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json(content_type = "text/html")
			if "value" in data[0]:
				monster_id = data[0]["value"]
				url = "http://services.runescape.com/m=itemdb_rs/bestiary/beastData.json"
				params = {"beastid": monster_id}
				async with self.aiohttp_session.get(url, params = params) as resp:
					data = await resp.json(content_type = "text/html")
				await self.message(target, "{0[name]}: {0[description]}, Level: {0[level]}, Weakness: {0[weakness]}, XP/Kill: {0[xp]}, HP: {0[lifepoints]}, Members: {0[members]}, Aggressive: {0[aggressive]}".format(data))
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
			params = {"api_key": credentials.riot_games_api_key}
			async with self.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
				if resp.status == 404:
					await self.message(target, "Account not found.")
					return
			await self.message(target, f"{data['name']} is level {data['summonerLevel']}.")
		elif message.startswith("!loltotalgames"):
			username = message.split()[1]
			url = "https://na1.api.riotgames.com/lol/summoner/v3/summoners/by-name/" + username
			params = {"api_key": credentials.riot_games_api_key}
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
				params = {"api_key": credentials.riot_games_api_key}
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
				christmas = datetime.datetime(now.year + 1, 12, 25)
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
		# TODO: add support for non-integers/floats, improve formatting
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
			self.disconnect()
	
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
	create_folder("data/commands")
	create_folder("data/logs/channels")
	create_folder("data/logs/client")
	client = TwitchClient("Harmonbot")
	loop = asyncio.get_event_loop()
	asyncio.ensure_future(client.connect("irc.chat.twitch.tv", password = credentials.oauth_token), loop = loop)
	# DEFAULT_PORT = 6667
	loop.run_forever()

