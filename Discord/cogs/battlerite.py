
import discord
from discord.ext import commands

import json
import os

import clients
import credentials
from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Battlerite(bot))

class Battlerite:
	
	def __init__(self, bot):
		self.bot = bot
		
		# TODO: Wait until ready
		
		# TODO: Check only within Emoji Server emojis?
		for champion in ("alysia", "ashka", "bakko", "blossom", "croak", "destiny", "ezmo", "freya", "iva", "jade", "jumong", "lucie", "oldur", "pearl", "pestilus", "poloma", "raigon", "rook", "ruh_kaan", "shifu", "sirius", "taya", "thorn", "varesh", "zander"):
			setattr(self, champion + "_emoji", discord.utils.get(self.bot.emojis, name = "battlerite_" + champion) or "")
		# TODO: Get champion names dynamically?
		
		self.bot.loop.create_task(self.load_mappings())
	
	async def load_mappings(self):
		clients.create_folder(clients.data_path + "/battlerite")
		if os.path.isfile(clients.data_path + "/battlerite/mappings.json"):
			with open(clients.data_path + "/battlerite/mappings.json", 'r') as mappings_file:
				self.mappings = json.load(mappings_file)
			return
		if not os.path.isfile(clients.data_path + "/battlerite/stackables.json"):
			# TODO: get revision dynamically?
			url = ("https://raw.githubusercontent.com/StunlockStudios/battlerite-assets/master/mappings/"
					"40703/stackables.json")
			async with clients.aiohttp_session.get(url) as resp:
				data = await resp.content.read()
			with open(clients.data_path + "/battlerite/stackables.json", "wb") as stackables_file:
				stackables_file.write(data)
		if not os.path.isfile(clients.data_path + "/battlerite/English.ini"):
			# TODO: get revision dynamically?
			url = ("https://raw.githubusercontent.com/StunlockStudios/battlerite-assets/master/mappings/"
					"40703/Localization/English.ini")
			async with clients.aiohttp_session.get(url) as resp:
				data = await resp.content.read()
			with open(clients.data_path + "/battlerite/English.ini", "wb") as localization_file:
				localization_file.write(data)
		with open(clients.data_path + "/battlerite/stackables.json", 'r') as stackables_file:
			stackables = json.load(stackables_file)
		localization = {}
		with open(clients.data_path + "/battlerite/English.ini", 'r') as localization_file:
			for line in localization_file:
				id_name = line.strip().split('=', maxsplit = 1)
				localization[id_name[0]] = id_name[1]
		self.mappings = {}
		for item in stackables["Mappings"]:
			if item["LocalizedName"]:
				name = localization[item["LocalizedName"]]
			else:
				name = item["DevName"]
			self.mappings[str(item["StackableId"])] = {"Name": name, "Type": item["StackableRangeName"]}
		with open(clients.data_path + "/battlerite/mappings.json", 'w') as mappings_file:
			json.dump(self.mappings, mappings_file, indent = 4)
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def battlerite(self, ctx):
		'''
		Battlerite
		Using revision 40703 mappings
		'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	async def get_player(self, player):
		url = "https://api.developer.battlerite.com/shards/global/players"
		headers = {"Authorization": credentials.battlerite_api_key, "Accept": "application/vnd.api+json"}
		params = {"filter[playerNames]": player}
		async with clients.aiohttp_session.get(url, headers = headers, params = params) as resp:
			data = await resp.json()
		return(next(iter(data["data"]), None))
	# TODO: optimize modularization?
	
	@battlerite.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def player(self, ctx, player : str):
		'''Player'''
		data = await self.get_player(player)
		if not data:
			await ctx.embed_reply(":no_entry: Error: Player not found")
			return
		stats = data["attributes"]["stats"]
		'''
		for stat, value in stats.items():
			if stat in self.mappings:
				print("{0[Name]} {0[Type]} ({1}): {2}".format(self.mappings[stat], stat, value))
			else:
				print("Missing Mapping ({}): {}".format(stat, value))
		'''
		fields = (("Account Level", stats["26"]), ("Account XP", "{:,}".format(stats["25"])), 
					("Time Played", utilities.secs_to_letter_format(stats['8'], limit = 3600)), 
					("Wins", stats['2']), ("Losses", stats['3']), 
					("Winrate", "{:.2f}%".format(stats['2'] / (stats['2'] + stats['3']) * 100)), 
					("Ranked 2v2 Wins - Losses (Winrate)", "{} - {} ({:.2f}%)".format(
						stats["14"], stats["15"], stats["14"] / (stats["14"] + stats["15"]) * 100)), 
					("Ranked 3v3 Wins - Losses (Winrate)", "{} - {} ({:.2f}%)".format(
						stats["16"], stats["17"], stats["16"] / (stats["16"] + stats["17"]) * 100)), 
					("Casual 2v2 Wins - Losses (Winrate)", "{} - {} ({:.2f}%)".format(
						stats["10"], stats["11"], stats["10"] / (stats["10"] + stats["11"]) * 100)), 
					("Casual 3v3 Wins - Losses (Winrate)", "{} - {} ({:.2f}%)".format(
						stats["12"], stats["13"], stats["12"] / (stats["12"] + stats["13"]) * 100)))
		await ctx.embed_reply("ID: {}".format(data["id"]), title = data["attributes"]["name"], fields = fields)
		# TODO: get values safely + handle division by zero
		# TODO: get values by type name
	
	@player.command(name = "brawl")
	@checks.not_forbidden()
	async def player_brawl(self, ctx, player : str):
		'''Brawl'''
		data = await self.get_player(player)
		if not data:
			await ctx.embed_reply(":no_entry: Error: Player not found")
			return
		stats = data["attributes"]["stats"]
		wins = stats.get("18", 0)
		losses = stats.get("19", 0)
		fields = [("Brawl Wins", wins), ("Brawl Losses", losses)]
		if wins + losses != 0: fields.append(("Brawl Winrate", "{:.2f}%".format(wins / (wins + losses) * 100)))
		await ctx.embed_reply("ID: {}".format(data["id"]), title = data["attributes"]["name"], fields = fields)
	
	@player.group(name = "casual", aliases = ["unranked"])
	@checks.not_forbidden()
	async def player_casual(self, ctx, player : str):
		'''Casual'''
		data = await self.get_player(player)
		if not data:
			await ctx.embed_reply(":no_entry: Error: Player not found")
			return
		stats = data["attributes"]["stats"]
		wins_2v2 = stats.get("10", 0)
		losses_2v2 = stats.get("11", 0)
		wins_3v3 = stats.get("12", 0)
		losses_3v3 = stats.get("13", 0)
		fields = [("Casual 2v2 Wins", wins_2v2), ("Casual 2v2 Losses", losses_2v2)]
		if wins_2v2 + losses_2v2 != 0: fields.append(("Casual 2v2 Winrate", "{:.2f}%".format(wins_2v2 / (wins_2v2 + losses_2v2) * 100)))
		elif wins_3v3 + losses_3v3 != 0: fields.append(("Casual 2v2 Winrate", "N/A"))
		fields.extend((("Casual 3v3 Wins", wins_3v3), ("Casual 3v3 Losses", losses_3v3)))
		if wins_3v3 + losses_3v3 != 0: fields.append(("Casual 3v3 Winrate", "{:.2f}%".format(wins_3v3 / (wins_3v3 + losses_3v3) * 100)))
		elif wins_2v2 + losses_2v2 != 0: fields.append(("Casual 3v3 Winrate", "N/A"))
		await ctx.embed_reply("ID: {}".format(data["id"]), title = data["attributes"]["name"], fields = fields)
	
	@player_casual.command(name = "2v2", aliases = ['2'])
	@checks.not_forbidden()
	async def player_casual_2v2(self, ctx, player : str):
		'''WIP'''
		...
	
	@player_casual.command(name = "3v3", aliases = ['3'])
	@checks.not_forbidden()
	async def player_casual_3v3(self, ctx, player : str):
		'''WIP'''
	
	@player.command(name = "levels", aliases = ["level", "xp", "exp", "experience"])
	@checks.not_forbidden()
	async def player_levels(self, ctx, player : str):
		'''Levels'''
		data = await self.get_player(player)
		if not data:
			await ctx.embed_reply(":no_entry: Error: Player not found")
			return
		stats = data["attributes"]["stats"]
		fields = [("Account Level", "{} ({:,} XP)".format(stats["26"], stats["25"]), False)]
		levels = {}
		xp = {}
		for stat, value in stats.items():
			if self.mappings.get(stat, {}).get("Type") == "Level" and stat != "40040": # != Random Champion
				levels[self.mappings[stat]["Name"]] = value
			elif self.mappings.get(stat, {}).get("Type") == "XP":
				xp[self.mappings[stat]["Name"]] = value
		xp = sorted(xp.items(), key = lambda x: x[1], reverse = True)
		for name, value in xp:
			fields.append(("{} {}".format(getattr(self, name.lower().replace(' ', '_') + "_emoji", ""), name), "{} ({:,} XP)".format(levels[name], value)))
		await ctx.embed_reply("ID: {}".format(data["id"]), title = data["attributes"]["name"], fields = fields)
	
	@player.group(name = "ranked", aliases = ["comp", "competitive", "league"])
	@checks.not_forbidden()
	async def player_ranked(self, ctx, player : str):
		'''Ranked'''
		data = await self.get_player(player)
		if not data:
			await ctx.embed_reply(":no_entry: Error: Player not found")
			return
		stats = data["attributes"]["stats"]
		wins_2v2 = stats.get("14", 0)
		losses_2v2 = stats.get("15", 0)
		wins_3v3 = stats.get("16", 0)
		losses_3v3 = stats.get("17", 0)
		fields = [("Ranked 2v2 Wins", wins_2v2), ("Ranked 2v2 Losses", losses_2v2)]
		if wins_2v2 + losses_2v2 != 0: fields.append(("Ranked 2v2 Winrate", "{:.2f}%".format(wins_2v2 / (wins_2v2 + losses_2v2) * 100)))
		elif wins_3v3 + losses_3v3 != 0: fields.append(("Ranked 2v2 Winrate", "N/A"))
		fields.extend((("Ranked 3v3 Wins", wins_3v3), ("Ranked 3v3 Losses", losses_3v3)))
		if wins_3v3 + losses_3v3 != 0: fields.append(("Ranked 3v3 Winrate", "{:.2f}%".format(wins_3v3 / (wins_3v3 + losses_3v3) * 100)))
		elif wins_2v2 + losses_2v2 != 0: fields.append(("Ranked 3v3 Winrate", "N/A"))
		await ctx.embed_reply("ID: {}".format(data["id"]), title = data["attributes"]["name"], fields = fields)
	
	@player_ranked.command(name = "2v2", aliases = ['2'])
	@checks.not_forbidden()
	async def player_ranked_2v2(self, ctx, player : str):
		'''WIP'''
		...
	
	@player_ranked.command(name = "3v3", aliases = ['3'])
	@checks.not_forbidden()
	async def player_ranked_3v3(self, ctx, player : str):
		'''WIP'''
	
	@player.command(name = "time", aliases = ["played"])
	@checks.not_forbidden()
	async def player_time(self, ctx, player : str):
		'''Time Played'''
		data = await self.get_player(player)
		if not data:
			await ctx.embed_reply(":no_entry: Error: Player not found")
			return
		stats = data["attributes"]["stats"]
		fields = [("Total Time Played", utilities.secs_to_letter_format(stats['8'], limit = 3600), False)]
		time_played = {}
		for stat, value in stats.items():
			if self.mappings.get(stat, {}).get("Type") == "CharacterTimePlayed" and stat != "16040": # != Random Champion
				time_played[self.mappings[stat]["Name"]] = value
		time_played = sorted(time_played.items(), key = lambda x: x[1], reverse = True)
		for name, value in time_played:
			fields.append(("{} {}".format(getattr(self, name.lower().replace(' ', '_') + "_emoji", ""), name), utilities.secs_to_letter_format(value, limit = 3600)))
		await ctx.embed_reply("ID: {}".format(data["id"]), title = data["attributes"]["name"], fields = fields)
	
	@player.command(name = "wins", aliases = ["losses"])
	@checks.not_forbidden()
	async def player_wins(self, ctx, player : str):
		'''Wins/Losses'''
		data = await self.get_player(player)
		if not data:
			await ctx.embed_reply(":no_entry: Error: Player not found")
			return
		stats = data["attributes"]["stats"]
		fields = [("Total Wins - Losses (Winrate)", "{} - {} ({:.2f}%)".format(stats['2'], stats['3'], stats['2'] / (stats['2'] + stats['3']) * 100), False)]
		wins = {}
		losses = {}
		for stat, value in stats.items():
			if self.mappings.get(stat, {}).get("Type") == "CharacterWins":
				wins[self.mappings[stat]["Name"]] = value
			elif self.mappings.get(stat, {}).get("Type") == "CharacterLosses":
				losses[self.mappings[stat]["Name"]] = value
		wins = sorted(wins.items(), key = lambda x: losses.get(x[0], 0) + x[1], reverse = True)
		for name, value in wins:
			fields.append(("{} {}".format(getattr(self, name.lower().replace(' ', '_') + "_emoji", ""), name), "{} - {} ({:.2f}%)".format(value, losses.get(name, 0), value / (value + losses.get(name, 0)) * 100)))
		await ctx.embed_reply("ID: {}".format(data["id"]), title = data["attributes"]["name"], fields = fields)
	
	# TODO: dynamic? champion commands

