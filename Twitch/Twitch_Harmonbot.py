
import pydle

import asyncio
import datetime
import json
import logging
import os
import random
import time
# import unicodedata

import aiohttp
import dateutil.parser
import unicodedata2 as unicodedata

import credentials

channels = ["_harmon758_1434735958584", "_harmon758_1478092370962", "_harmon758_1478092378893", "harmon758", "harmonbot", "mikki", "imagrill", "tirelessgod", "gameflubdojo", "vayces", "tbestnuclear", "cantilena", "nordryd", "babyastron"]
# "_harmon758_1474528138348" old public channel

# TODO: Fix pydle failure to reconnect issue
# TODO: Add pydle Python 3.7 support

class TwitchClient(pydle.Client):
	
	def __init__(self, nickname):
		super().__init__(nickname)
		self.PING_TIMEOUT = 600
		# self.logger.setLevel(logging.ERROR)
		self.version = "2.1.5"
		self.aiohttp_session = aiohttp.ClientSession(loop = self.eventloop.loop)
		
		for file in os.listdir("data/commands"):
			category = file[:-5]  # - .json
			with open(f"data/commands/{category}.json", 'r') as commands_file:
				setattr(self, f"{category}_commands", json.load(commands_file))
	
	async def on_connect(self):
		await super().on_connect()
		self.logger.setLevel(logging.ERROR)
		await self.raw("CAP REQ :twitch.tv/membership\r\n")
		await self.raw("CAP REQ :twitch.tv/tags\r\n")
		await self.raw("CAP REQ :twitch.tv/commands\r\n")
		for channel in channels:
			await self.join('#' + channel)
		print("Started up Twitch Harmonbot | Connected to {}".format(' | '.join(['#' + channel for channel in channels])))
	
	async def on_raw(self, message):
		await super().on_raw(message)
		# print(message)
	
	async def on_raw_004(self, message):
		# super().on_raw_004(message)
		pass
	
	async def on_raw_whisper(self, message):
		await super().on_raw_privmsg(message)
	
	async def message(self, target, message):
		if target[0] != '#':
			await super().message("#harmonbot", ".w {} {}".format(target, message))
		else:
			await super().message(target, message)
	
	async def on_message(self, target, source, message):
		await super().on_message(target, source, message)
		# print("Twitch Harmonbot | Message | {} | {}: {}".format(target, source, message))
		if target == "harmonbot":
			target = source
		if source == "harmonbot":
			return
		
		# Meta Commands
		if message.startswith('!') and message[1:] in self.meta_commands:
				await self.message(target, self.meta_commands[message[1:]])
		
		# Main Commands
		elif message.startswith("!audiodefine"):
			async with self.aiohttp_session.get("http://api.wordnik.com:80/v4/word.json/{}/audio?" "useCanonical=false&limit=1&api_key={}".format(message.split()[1], credentials.wordnik_apikey)) as resp:
				data = await resp.json()
			if data:
				await self.message(target, data[0]["word"].capitalize() + ": " + data[0]["fileUrl"])
			else:
				await self.message(target, "Word or audio not found.")
		elif message.startswith("!averagefps"):
			url = "https://api.twitch.tv/kraken/streams/{}?client_id={}".format(target[1:], credentials.twitch_client_id)
			async with self.aiohttp_session.get(url) as resp:
				data = await resp.json()
			if data.get("stream"):
				await self.message(target, "Average FPS: {}".format(data["stream"]["average_fps"]))
			else:
				await self.message(target, "Average FPS not found.")
		elif message.startswith("!bye"):
			if len(message.split()) == 1 or message.split()[1].lower() == "harmonbot":
				#await self.message(target, "Bye, {source}!", source=source)
				await self.message(target, "Bye, {}!".format(source.capitalize()))
			else:
				await self.message(target, "{}, {} says goodbye!".format(' '.join([m.capitalize() for m in message.split()[1:]]), source.capitalize()))
		elif message.startswith(("!char", "!character", "!unicode")):
			try:
				await self.message(target, unicodedata.lookup(' '.join(message.split()[1:])))
			except KeyError:
				await self.message(target, "\N{NO ENTRY} Unicode character not found")
		elif message.startswith("!define"):
			async with self.aiohttp_session.get("http://api.wordnik.com:80/v4/word.json/{}/definitions?" "limit=1&includeRelated=false&useCanonical=false&includeTags=false&api_key={}".format(message.split()[1], credentials.wordnik_apikey)) as resp:
				data = await resp.json()
			if data:
				await self.message(target, data[0]["word"].capitalize() + ": " + data[0]["text"])
			else:
				await self.message(target, "Definition not found.")
		elif message.startswith("!element"):
			elements = {"ac": "Actinium", "ag": "Silver", "al": "Aluminum", "am": "Americium", "ar": "Argon", }
			if len(message.split()) > 1 and message.split()[1] in elements:
				await self.message(target, elements[message.split()[1]])
		elif message.startswith(("!followed", "!followage", "!howlong")):
			url = "https://api.twitch.tv/kraken/users/{}/follows/channels/{}?client_id={}".format(source, target[1:], credentials.twitch_client_id)
			async with self.aiohttp_session.get(url) as resp:
				data = await resp.json()
			if "created_at" in data:
				created_at = dateutil.parser.parse(data["created_at"])
				seconds = int((datetime.datetime.now(datetime.timezone.utc) - created_at).total_seconds())
				await self.message(target, "{} followed on {}, {} ago".format(source.capitalize(), created_at.strftime("%B %#d %Y"), secs_to_duration(seconds)))
			else:
				await self.message(target, "{}, you haven't followed yet!".format(source.capitalize()))
		elif message.startswith("!followers"):
			url = "https://api.twitch.tv/kraken/channels/{}/follows?client_id={}".format(target[1:], credentials.twitch_client_id)
			async with self.aiohttp_session.get(url) as resp:
				data = await resp.json()
			await self.message(target, "There are currently {} people following {}.".format(data["_total"], target[1:].capitalize()))
		elif message.startswith("!google"):
			await self.message(target, "https://google.com/search?q=" + '+'.join(message.split()[1:]))
		elif message.startswith(("!congrats", "!grats", "!gz")):
			if len(message.split()) == 1:
				await self.message(target, "Congratulations!!!!!")
			else:
				await self.message(target, "Congratulations, {}!!!!!".format(' '.join([m.capitalize() for m in message.split()[1:]])))
		elif message.startswith("!hello"):
			if len(message.split()) == 1 or message.split()[1].lower() == "harmonbot":
				await self.message(target, "Hello, {}!".format(source.capitalize()))
			else:
				await self.message(target, "{}, {} says hello!".format(' '.join([m.capitalize() for m in message.split()[1:]]), source.capitalize()))
		elif message.startswith("!highfive"):
			if message.split()[1].lower() == "random":
				await self.message(target, "{} highfives {}!".format(source.capitalize(), self.random_viewer(target)))
			elif message.split()[1].lower() == source:
				await self.message(target, "{} highfives themselves. o_O".format(source.capitalize()))
			elif message.split()[1].lower() == "harmonbot":
				await self.message(target, "!highfive {}".format(source.capitalize()))
			elif len(message.split()) == 1:
				await self.message(target, "{} highfives no one. :-/".format(source.capitalize()))
			else:
				await self.message(target, "{} highfives {}!".format(source.capitalize(), ' '.join([m.capitalize() for m in message.split()[1:]])))
		elif message.startswith("!hi"):
			if message.split()[0] in ["!hiscores", "!hiscore", "!highscore", "!highscores"]: return
			elif len(message.split()) == 1 or message.split()[1].lower() == "harmonbot":
				await self.message(target, "Hello, {}!".format(source.capitalize()))
			else:
				await self.message(target, "{}, {} says hello!".format(' '.join([m.capitalize() for m in message.split()[1:]]), source.capitalize()))
		elif message.startswith("!hug"):
			if message.split()[1].lower() == "random":
				await self.message(target, "{} hugs {}!".format(source.capitalize(), self.random_viewer(target)))
			elif message.split()[1].lower() == source:
				await self.message(target, "{} hugs themselves. o_O".format(source.capitalize()))
			elif message.split()[1].lower() == "harmonbot":
				await self.message(target, "!hug {}".format(source.capitalize()))
			elif len(message.split()) == 1:
				await self.message(target, "{} hugs no one. :-/".format(source.capitalize()))
			else:
				await self.message(target, "{} hugs {}!".format(source.capitalize(), ' '.join([m.capitalize() for m in message.split()[1:]])))
		elif message.startswith("!imfeelinglucky"):
			await self.message(target, "https://google.com/search?btnI&q=" + '+'.join(message.split()[1:]))
		elif message.startswith("!lmgtfy"):
			await self.message(target, "lmgtfy.com/?q=" + '+'.join(message.split()[1:]))
		elif message.startswith("!mods"):
			mods = self.channels[target]["modes"].get('o', [])
			await self.message(target, "Mods Online ({}): {}".format(len(mods), ", ".join(mod.capitalize() for mod in mods)))
		elif message.startswith("!randomword"):
			async with self.aiohttp_session.get("http://api.wordnik.com:80/v4/words.json/randomWord?" "hasDictionaryDef=false&minCorpusCount=0&maxCorpusCount=-1&minDictionaryCount=1&maxDictionaryCount=-1&minLength=5&maxLength=-1&api_key={0}".format(credentials.wordnik_apikey)) as resp:
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
			url = "https://api.twitch.tv/kraken/streams/{}?client_id={}".format(target[1:], credentials.twitch_client_id)
			async with self.aiohttp_session.get(url) as resp:
				data = await resp.json()
			if data.get("stream"):
				await self.message(target, "{}".format(data["stream"]["channel"]["status"]))
			else:
				await self.message(target, "Title not found.")
		elif message.startswith("!translate"):
			url = "https://translate.yandex.net/api/v1.5/tr.json/translate?key={}&lang=en&text={}&options=1".format(credentials.yandex_translate_api_key, ' '.join(message.split()[1:]))
			async with self.aiohttp_session.get(url) as resp:
				data = await resp.json()
			if data["code"] != 200:
				await self.message(target, "Error: {}".format(data["message"]))
				return
			await self.message(target, data["text"][0])
		elif message.startswith("!uptime"):
			url = "https://api.twitch.tv/kraken/streams/{}?client_id={}".format(target[1:], credentials.twitch_client_id)
			async with self.aiohttp_session.get(url) as resp:
				data = await resp.json()
			if data.get("stream"):
				await self.message(target, secs_to_duration(int((datetime.datetime.now(datetime.timezone.utc) - dateutil.parser.parse(data["stream"]["created_at"])).total_seconds())))
			else:
				await self.message(target, "Uptime not found.")
		elif message.startswith("!urband"):
			url = "http://api.urbandictionary.com/v0/define?term={}".format('+'.join(message.split()[1:]))
			async with self.aiohttp_session.get(url) as resp:
				data = await resp.json()
			if not data or "list" not in data or not data["list"]:
				await self.message(target, "No results found.")
				return
			definition = data["list"][0]
			message = "{}: {}".format(definition["word"], definition["definition"].replace('\n', ' '))
			if len(message + definition["permalink"]) > 423 :
				message = message[:423 - len(definition["permalink"]) - 4] + "..."
			message += ' ' + definition["permalink"]
			await self.message(target, message)
		elif message.startswith("!viewers"):
			url = "https://api.twitch.tv/kraken/streams/{}?client_id={}".format(target[1:], credentials.twitch_client_id)
			async with self.aiohttp_session.get(url) as resp:
				data = await resp.json()
			if data.get("stream"):
				await self.message(target, "{} viewers watching now.".format(data["stream"]["viewers"]))
			else:
				await self.message(target, "Stream is offline.")
			# No one is watching right now :-/
		elif message.startswith("!wiki"):
			await self.message(target, "wikipedia.org/wiki/" + '_'.join(message.split()[1:]))
		
		# Mikki Commands
		if target == "#mikki":
			if message.startswith('!') and message[1:] in self.mikki_commands:
				await self.message(target, self.mikki_commands[message[1:]])
			elif message.startswith(("!bully", "!cyberbully")):
				await self.message(target, "http://www.stopcyberbullying.org/ Please check out this site before you continue bullying other viewers.")
			elif message.startswith("!caught"):
				if message.split()[1].lower() == "random":
					caught = self.random_viewer(target)
				elif message.split()[1]:
					caught = ' '.join(message.split()[1:]).capitalize()
				else:
					caught = source.capitalize()
				await self.message(target, "Mikki has caught a wild {}!".format(caught))
			elif message.startswith(("!links", "!social")):
				await self.message(target, "https://twitter.com/crystal_mikki https://www.instagram.com/crystalmikki/ https://discord.gg/vWbFxmu http://steamcommunity.com/id/mikkipuppy https://www.youtube.com/user/mikscape")
			elif message.startswith("!mikkitime"):
				mikkitime = datetime.datetime.now(datetime.timezone(datetime.timedelta(minutes = 60 * 8)))
				await self.message(target, "It is currently {} on {} in Western Australia ({}).".format(mikkitime.strftime("%#I:%M %p"), mikkitime.strftime("%b. %#d"), mikkitime.strftime("%Z")))
				# TODO: Include day of week
			elif message.startswith(("!music", "!spotify")):
				await self.message(target, "http://open.spotify.com/user/mikkirs/playlist/5OBCdMNiGiTRGL0cqWL9CT")
			elif message.startswith(("!o.o", "!o_o")):
				await self.message(target, "http://i.imgur.com/K00oLxo.png")
			elif message.startswith("!pi"):
				if self.is_mod(target, source):
					await self.message(target, "3.14159265358979323846264338327 9502884197169399375105820974944 5923078164062862089986280348253 4211706798214808651328230664709 3844609550582231725359408128481 1174502841027019385211055596446 2294895493038196442881097566593 3446128475648233786783165271201 9091456485669234603486104543266 4821339360726024914127372458700 6606315588174881520920962829254 0917153643678925903600113305305 4882046652138414695194151160943 3057270365759591953092186117381 9326117931051185480744623799627 4956735188575272489122793818301 1949129833673362440656643086021 3949463952247371907021798609437")
				else:
					await self.message(target, "3.14")
			elif message.startswith(("!pouch", "!repair")):
				await self.message(target, "REPAIR POUCH! REPAIR POUCH! REPAIR POUCH! REPAIR POUCH!")
		
		# Imagrill Commands
		if target == "#imagrill":
			if message.startswith('!') and message[1:] in self.imagrill_commands:
				await self.message(target, self.imagrill_commands[message[1:]])
			elif message.startswith("!caught"):
				if message.split()[1].lower() == "random":
					caught = self.random_viewer(target)
				elif message.split()[1]:
					caught = ' '.join(message.split()[1:]).capitalize()
				else:
					caught = source.capitalize()
				await self.message(target, "Arts has caught a wild {}!".format(caught))
			elif message.startswith("!googer"):
				await self.message(target, "https://google.com/search?q=" + '+'.join(message.split()[1:]) + ' "RAISE YOUR GOOGERS" -Arts')
			elif message.startswith(("!rebirth1", "!re;birth1")):
				await self.message(target, "http://hyperdimensionneptunia.wikia.com/wiki/Hyperdimension_Neptunia_Re;Birth_1")
			elif message.startswith(("!scooter", "!scoots")):
				await self.message(target, "http://imgur.com/WNj2HbM")
			elif message.startswith("!sneeze"):
				if len(message.split()) == 1 or not is_number(message.split()[1]) or 10 < int(message.split()[1]) or int(message.split()[1]) < 2:
					await self.message(target, "Bless you!")
				else:
					await self.message(target, ' '.join(["Bless you!" for i in range(int(message.split()[1]))]))
			elif message.startswith("!tits") or "show tits" in message:
				await self.message(target, "https://en.wikipedia.org/wiki/Tit_(bird) https://en.wikipedia.org/wiki/Great_tit http://i.imgur.com/40Ese5S.jpg")
		
		# TirelessGod Commands
		if target == "#tirelessgod":
			if message.startswith('!') and message[1:] in self.tirelessgod_commands:
				await self.message(target, self.tirelessgod_commands[message[1:]])
		
		# Runescape Commands
		if message.startswith(("!07rswiki", "!rswiki07", "!osrswiki", "!rswikios")):
			await self.message(target, "2007.runescape.wikia.com/wiki/" + '_'.join(message.split()[1:]))
		elif message.startswith("!cache"):
			await self.message(target, "{} until Guthixian Cache.".format(secs_to_duration(int(10800 - time.time() % 10800))))
		elif message.startswith("!indecentcodehs"):
			await self.message(target, "indecentcode.com/hs/index.php?id=" + '+'.join(message.split()[1:]))
		elif message.startswith("!level"):
			if len(message.split()) == 1:
				await self.message(target, "Please enter a level.")
			elif is_number(message.split()[1]):
				level = float(message.split()[1])
				if 1 <= level < 127:
					level = int(level)
					xp = 0
					for i in range(1, level):
						xp += int(i + 300 * 2 ** (i / 7))
					xp = int(xp / 4)
					await self.message(target, "Runescape Level {} = {:,} xp".format(level, xp))
				elif level > 9000:
					await self.message(target, "It's over 9000!")
				elif level == 9000:
					await self.message(target, "Almost there.")
				elif level > 126 and level < 9000:
					await self.message(target, "I was gonna calculate xp at Level {}. Then I took an arrow to the knee.".format(level))
				else:
					await self.message(target, "Level {} does not exist.".format(level))
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!monster"):
			if len(message.split()) == 1:
				await self.message(target, "Please specify a monster.")
				return
			async with self.aiohttp_session.get("http://services.runescape.com/m=itemdb_rs/bestiary/beastSearch.json?term={}".format('+'.join(message.split()[1:]))) as resp:
				data = await resp.json()
			if "value" in data[0]:
				monster_id = data[0]["value"]
				async with self.aiohttp_session.get("http://services.runescape.com/m=itemdb_rs/bestiary/beastData.json?beastid={}".format(monster_id)) as resp:
					data = await resp.json()
				await self.message(target, "{0[name]}: {0[description]}, Level: {0[level]}, Weakness: {0[weakness]}, XP/Kill: {0[xp]}, HP: {0[lifepoints]}, Members: {0[members]}, Aggressive: {0[aggressive]}".format(data))
			else:
				await self.message(target, "Monster not found.")
		elif message.startswith("!reset"):
			await self.message(target, "{} until reset.".format(secs_to_duration(int(86400 - time.time() % 86400))))
		elif message.startswith("!rswiki"):
			await self.message(target, "runescape.wikia.com/wiki/" + '_'.join(message.split()[1:]))
		elif message.startswith("!warbands"):
			await self.message(target, "{} until Warbands.".format(secs_to_duration(int(25200 - time.time() % 25200))))
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
					await self.message(target, "{:,} xp = level {}".format(xp, _level))
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
				await self.message(target, "{:,} xp between level {} and level {}".format(betweenxp, startlevel, endlevel))
			else:
				await self.message(target, "Syntax error.")
		
		# Miscellaneous Commands
		if message.startswith('!') and message[1:] in self.misc_commands:
			await self.message(target, self.misc_commands[message[1:]])
		# on *:text:!christmas*:#:{ msg # $my_duration($timeleft($ctime(December 24 2016 18:00:00))) until Christmas! }
		# on *:text:!easter*:#:{ msg # $my_duration($timeleft($ctime(March 27 2016 18:00:00))) until Easter! }
		elif message.startswith("!kitty"):
			await self.message(target, "BionicBunion")  # update?
		# on *:text:!puppy*:#:{ msg # RalpherZ }
		
		# Unit Conversion Commands
		# TODO: add support for non-integers/floats, improve formatting
		if message.startswith("!ctof"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} °C = {} °F".format(message.split()[1], int(message.split()[1]) * 9 / 5 + 32))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!ftoc"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} °F = {} °C".format(message.split()[1], (int(message.split()[1]) - 32) * 5 / 9))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!lbtokg"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} lb = {} kg".format(message.split()[1], int(message.split()[1]) * 0.45359237))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!kgtolb"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} kg = {} lb".format(message.split()[1], int(message.split()[1]) * 2.2046))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!fttom"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} ft = {} m".format(message.split()[1], int(message.split()[1]) * 0.3048))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!mtoft"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} m = {} ft".format(message.split()[1], int(message.split()[1]) * 3.2808))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!fitom"):
			if len(message.split()) > 2 and is_number(message.split()[1]) and is_number(message.split()[2]):
				await self.message(target, "{} ft {} in = {} m".format(message.split()[1], message.split()[2], (int(message.split()[1]) + int(message.split()[2]) / 12) * 0.3048))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!mtofi"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} m = {} ft {} in".format(message.split()[1], int(message.split()[1]) * 39.37 // 12, int(message.split()[1]) * 39.37 - (int(message.split()[1]) * 39.37 // 12) * 12))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!gtooz"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} g = {} oz".format(message.split()[1], int(message.split()[1]) * 0.035274))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!oztog"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} oz = {} g".format(message.split()[1], int(message.split()[1]) / 0.035274))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!mitokm"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} mi = {} km".format(message.split()[1], int(message.split()[1]) / 0.62137))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!kmtomi"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} km = {} mi".format(message.split()[1], int(message.split()[1]) * 0.62137))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!ozttog"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} oz t = {} g".format(message.split()[1], int(message.split()[1]) / 0.032151))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!gtoozt"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} g = {} oz t".format(message.split()[1], int(message.split()[1]) * 0.032151))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!ozttooz"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} oz t = {} oz".format(message.split()[1], int(message.split()[1]) * 1.09714996656))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		elif message.startswith("!oztoozt"):
			if len(message.split()) > 1 and is_number(message.split()[1]):
				await self.message(target, "{} oz = {} oz t".format(message.split()[1], int(message.split()[1]) * 0.911452427176))
			elif len(message.split()) == 1:
				await self.message(target, "Please enter input.")
			else:
				await self.message(target, "Syntax error.")
		
		if message == "!restart" and source == "harmon758":
			await self.message(target, "Restarting")
			print("Restarting Twitch Harmonbot...")
			await self.aiohttp_session.close()
			self.disconnect()
	
	def is_mod(self, target, source):
		return source in self.channels[target]["modes"].get('o', [])
	
	def random_viewer(self, target):
		return random.choice(list(self.channels.get(target, {}).get("users", ["N/A"]))).capitalize()

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
			output += " {} {}".format(num_dur, dur_name)
			if (num_dur > 1): output += 's'
			secs -= num_dur * dur_in_secs
	if secs != 0:
		output += " {} second".format(secs)
		if (secs != 1): output += 's'
	return output[1:] if output else "{} seconds".format(secs)

print("Starting up Twitch Harmonbot...")
client = TwitchClient("Harmonbot")
loop = asyncio.get_event_loop()
asyncio.ensure_future(client.connect("irc.chat.twitch.tv", password = credentials.oauth_token), loop = loop)
# DEFAULT_PORT = 6667
loop.run_forever()

