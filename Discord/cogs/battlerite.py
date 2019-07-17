
import discord
from discord.ext import commands

import json
import os
import sys

from modules import utilities
from utilities import checks

sys.path.insert(0, "..")
from units.files import create_folder
sys.path.pop(0)

def setup(bot):
	bot.add_cog(Battlerite(bot))

class Battlerite(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.mappings = {}
		if self.bot.is_ready():
			self.bot.loop.create_task(self.on_ready())
	
	@commands.Cog.listener()
	async def on_ready(self):
		await self.load_mappings()
		self.load_emoji()
	
	def load_emoji(self):
		# TODO: Check only within Emoji Server emojis?
		champions = filter(lambda m: m["Type"] == "Characters", self.mappings.values())
		champions = set(c["Name"].lower().replace(' ', '_') for c in champions)
		champions.discard("random_champion")
		champions.discard("egg_bakko")
		champions.discard("rabbit")  # For Battlerite Royale?
		# https://www.reddit.com/r/BattleRite/comments/8u7ab9/next_champion_critter/
		for champion in champions:
			setattr(self, champion + "_emoji", discord.utils.get(self.bot.emojis, name = "battlerite_" + champion) or "")
	
	async def load_mappings(self):
		create_folder(self.bot.data_path + "/battlerite")
		if os.path.isfile(self.bot.data_path + "/battlerite/mappings.json"):
			with open(self.bot.data_path + "/battlerite/mappings.json", 'r') as mappings_file:
				self.mappings = json.load(mappings_file)
			return
		if not os.path.isfile(self.bot.data_path + "/battlerite/stackables.json"):
			# TODO: get revision dynamically?
			# https://api.github.com/repos/StunlockStudios/battlerite-assets/contents/mappings
			url = ("https://raw.githubusercontent.com/StunlockStudios/battlerite-assets/master/mappings/"
					"61319/stackables.json")
			async with self.bot.aiohttp_session.get(url) as resp:
				data = await resp.content.read()
			with open(self.bot.data_path + "/battlerite/stackables.json", "wb") as stackables_file:
				stackables_file.write(data)
		if not os.path.isfile(self.bot.data_path + "/battlerite/English.ini"):
			# TODO: get revision dynamically?
			# https://api.github.com/repos/StunlockStudios/battlerite-assets/contents/mappings
			url = ("https://raw.githubusercontent.com/StunlockStudios/battlerite-assets/master/mappings/"
					"61319/Localization/English.ini")
			async with self.bot.aiohttp_session.get(url) as resp:
				data = await resp.content.read()
			with open(self.bot.data_path + "/battlerite/English.ini", "wb") as localization_file:
				localization_file.write(data)
		with open(self.bot.data_path + "/battlerite/stackables.json", 'r') as stackables_file:
			stackables = json.load(stackables_file)
		localization = {}
		with open(self.bot.data_path + "/battlerite/English.ini", 'r', encoding = "UTF-16") as localization_file:
			for line in localization_file:
				id_name = line.strip().split('=', maxsplit = 1)
				localization[id_name[0]] = id_name[1]
		self.mappings = {}
		for item in stackables["Mappings"]:
			name = localization.get(item.get("LocalizedName"), item["DevName"])
			self.mappings[str(item["StackableId"])] = {"Name": name, "Type": item["StackableRangeName"]}
		with open(self.bot.data_path + "/battlerite/mappings.json", 'w') as mappings_file:
			json.dump(self.mappings, mappings_file, indent = 4)
	
	# TODO: Handle 25+ fields
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def battlerite(self, ctx):
		'''
		Battlerite
		Using revision 61319 mappings
		'''
		await ctx.send_help(ctx.command)
	
	# TODO: optimize modularization?
	async def get_player(self, player):
		url = "https://api.developer.battlerite.com/shards/global/players"
		headers = {"Authorization": self.bot.BATTLERITE_API_KEY, "Accept": "application/vnd.api+json"}
		params = {"filter[playerNames]": player}
		async with self.bot.aiohttp_session.get(url, headers = headers, params = params) as resp:
			data = await resp.json()
		return(next(iter(data["data"]), None))
	
	@battlerite.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def player(self, ctx, player : str):
		'''Player'''
		# TODO: Handle missing Battlerite Arena stats
		data = await self.get_player(player)
		if not data:
			await ctx.embed_reply(":no_entry: Error: Player not found")
			return
		stats = data["attributes"]["stats"]
		'''
		for stat, value in stats.items():
			if stat in self.mappings:
				print(f"{self.mappings[stat]['Name']} {self.mappings[stat]['Type']} ({stat}): {value}")
			else:
				print(f"Missing Mapping ({stat}): {value}")
		'''
		fields = (("Account Level", stats["26"]), ("Account XP", f"{stats['25']:,}"), 
					("Time Played", utilities.secs_to_letter_format(stats['8'], limit = 3600)), 
					("Wins", stats['2']), ("Losses", stats['3']), 
					("Winrate", f"{stats['2'] / (stats['2'] + stats['3']) * 100:.2f}%"), 
					("Ranked 2v2 Wins - Losses (Winrate)", 
						f"{stats['14']} - {stats['15']} ({stats['14'] / (stats['14'] + stats['15']) * 100:.2f}%)"), 
					("Ranked 3v3 Wins - Losses (Winrate)", 
						f"{stats['16']} - {stats['17']} ({stats['16'] / (stats['16'] + stats['17']) * 100:.2f}%)"), 
					("Casual 2v2 Wins - Losses (Winrate)", 
						f"{stats['10']} - {stats['11']} ({stats['10'] / (stats['10'] + stats['11']) * 100:.2f}%)"), 
					("Casual 3v3 Wins - Losses (Winrate)", 
						f"{stats['12']} - {stats['13']} ({stats['12'] / (stats['12'] + stats['13']) * 100:.2f}%)"))
		await ctx.embed_reply(f"ID: {data['id']}", title = data["attributes"]["name"], fields = fields)
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
		if wins + losses:
			fields.append(("Brawl Winrate", f"{wins / (wins + losses) * 100:.2f}%"))
		await ctx.embed_reply(f"ID: {data['id']}", title = data["attributes"]["name"], fields = fields)
	
	@player.group(name = "casual", aliases = ["unranked"], case_insensitive = True)
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
		if wins_2v2 + losses_2v2:
			fields.append(("Casual 2v2 Winrate", f"{wins_2v2 / (wins_2v2 + losses_2v2) * 100:.2f}%"))
		elif wins_3v3 + losses_3v3:
			fields.append(("Casual 2v2 Winrate", "N/A"))
		fields.extend((("Casual 3v3 Wins", wins_3v3), ("Casual 3v3 Losses", losses_3v3)))
		if wins_3v3 + losses_3v3:
			fields.append(("Casual 3v3 Winrate", f"{wins_3v3 / (wins_3v3 + losses_3v3) * 100:.2f}%"))
		elif wins_2v2 + losses_2v2:
			fields.append(("Casual 3v3 Winrate", "N/A"))
		await ctx.embed_reply(f"ID: {data['id']}", title = data["attributes"]["name"], fields = fields)
	
	@player_casual.command(name = "2v2", aliases = ['2'])
	@checks.not_forbidden()
	async def player_casual_2v2(self, ctx, player : str):
		'''WIP'''
		...
	
	@player_casual.command(name = "3v3", aliases = ['3'])
	@checks.not_forbidden()
	async def player_casual_3v3(self, ctx, player : str):
		'''WIP'''
		...
	
	@player.command(name = "levels", aliases = ["level", "xp", "exp", "experience"])
	@checks.not_forbidden()
	async def player_levels(self, ctx, player : str):
		'''Levels'''
		data = await self.get_player(player)
		if not data:
			await ctx.embed_reply(":no_entry: Error: Player not found")
			return
		stats = data["attributes"]["stats"]
		fields = [("Account Level", f"{stats['26']} ({stats['25']:,} XP)", False)]
		levels = {}
		xp = {}
		for stat, value in stats.items():
			if self.mappings.get(stat, {}).get("Type") == "Level":
				levels[self.mappings[stat]["Name"]] = value
			elif self.mappings.get(stat, {}).get("Type") == "XP":
				xp[self.mappings[stat]["Name"]] = value
		# levels.pop("Random Champion", None)
		xp = sorted(xp.items(), key = lambda x: x[1], reverse = True)
		for name, value in xp:
			emoji = getattr(self, name.lower().replace(' ', '_') + "_emoji", "")
			fields.append((f"{emoji} {name}", f"{levels[name]} ({value:,} XP)"))
		await ctx.embed_reply(f"ID: {data['id']}", title = data["attributes"]["name"], fields = fields)
	
	@player.group(name = "ranked", aliases = ["comp", "competitive", "league"], case_insensitive = True)
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
		if wins_2v2 + losses_2v2:
			fields.append(("Ranked 2v2 Winrate", f"{wins_2v2 / (wins_2v2 + losses_2v2) * 100:.2f}%"))
		elif wins_3v3 + losses_3v3:
			fields.append(("Ranked 2v2 Winrate", "N/A"))
		fields.extend((("Ranked 3v3 Wins", wins_3v3), ("Ranked 3v3 Losses", losses_3v3)))
		if wins_3v3 + losses_3v3:
			fields.append(("Ranked 3v3 Winrate", f"{wins_3v3 / (wins_3v3 + losses_3v3) * 100:.2f}%"))
		elif wins_2v2 + losses_2v2:
			fields.append(("Ranked 3v3 Winrate", "N/A"))
		await ctx.embed_reply(f"ID: {data['id']}", title = data["attributes"]["name"], fields = fields)
	
	@player_ranked.command(name = "2v2", aliases = ['2'])
	@checks.not_forbidden()
	async def player_ranked_2v2(self, ctx, player : str):
		'''WIP'''
		...
	
	@player_ranked.command(name = "3v3", aliases = ['3'])
	@checks.not_forbidden()
	async def player_ranked_3v3(self, ctx, player : str):
		'''WIP'''
		...
	
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
			if self.mappings.get(stat, {}).get("Type") == "CharacterTimePlayed":
				time_played[self.mappings[stat]["Name"]] = value
		time_played.pop("Random Champion", None)
		time_played = sorted(time_played.items(), key = lambda x: x[1], reverse = True)
		for name, value in time_played:
			emoji = getattr(self, name.lower().replace(' ', '_') + "_emoji", "")
			fields.append((f"{emoji} {name}", utilities.secs_to_letter_format(value, limit = 3600)))
		await ctx.embed_reply(f"ID: {data['id']}", title = data["attributes"]["name"], fields = fields)
	
	@player.command(name = "wins", aliases = ["losses"])
	@checks.not_forbidden()
	async def player_wins(self, ctx, player : str):
		'''Wins/Losses'''
		data = await self.get_player(player)
		if not data:
			await ctx.embed_reply(":no_entry: Error: Player not found")
			return
		stats = data["attributes"]["stats"]
		field_value = f"{stats['2']} - {stats['3']} ({stats['2'] / (stats['2'] + stats['3']) * 100:.2f}%)"
		# TODO: Handle division by 0
		fields = [("Total Wins - Losses (Winrate)", field_value, False)]
		wins = {}
		losses = {}
		for stat, value in stats.items():
			if self.mappings.get(stat, {}).get("Type") == "CharacterWins":
				wins[self.mappings[stat]["Name"]] = value
			elif self.mappings.get(stat, {}).get("Type") == "CharacterLosses":
				losses[self.mappings[stat]["Name"]] = value
		wins = sorted(wins.items(), key = lambda x: losses.get(x[0], 0) + x[1], reverse = True)
		# TODO: Handle character with losses and no wins
		for name, value in wins:
			emoji = getattr(self, name.lower().replace(' ', '_') + "_emoji", "")
			field_value = f"{value} - {losses.get(name, 0)} ({value / (value + losses.get(name, 0)) * 100:.2f}%)"
			# TODO: Handle division by 0
			fields.append((f"{emoji} {name}", field_value))
		await ctx.embed_reply(f"ID: {data['id']}", title = data["attributes"]["name"], fields = fields)
	
	# TODO: dynamic? champion commands
	
	@battlerite.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def royale(self, ctx):
		'''Battlerite Royale'''
		await ctx.send_help(ctx.command)
	
	@royale.group(name = "player", invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def royale_player(self, ctx, player: str):
		'''Player'''
		data = await self.get_player(player)
		if not data:
			return await ctx.embed_reply(":no_entry: Error: Player not found")
		stats = data["attributes"]["stats"]
		fields = []
		level_id = discord.utils.find(lambda m: m[1]["Type"] == "RoyaleAccountLevel", self.mappings.items())[0]
		if level_id in stats:
			fields.append(("Account Level", stats[level_id]))
		xp_id = discord.utils.find(lambda m: m[1]["Type"] == "RoyaleAccountXP", self.mappings.items())[0]
		if xp_id in stats:
			fields.append(("Account XP", f"{stats[xp_id]:,}"))
		time_id = discord.utils.find(lambda m: m[1]["Type"] == "RoyaleTimePlayed", self.mappings.items())[0]
		if time_id in stats:
			fields.append(("Time Played", utilities.secs_to_letter_format(stats[time_id], limit = 3600)))
		await ctx.embed_reply(f"ID: {data['id']}", title = data["attributes"]["name"], fields = fields)
	
	@royale_player.command(name = "levels", aliases = ["level", "xp", "exp", "experience"])
	@checks.not_forbidden()
	async def royale_player_levels(self, ctx, player: str):
		'''Levels'''
		data = await self.get_player(player)
		if not data:
			return await ctx.embed_reply(":no_entry: Error: Player not found")
		stats = data["attributes"]["stats"]
		fields = []
		account_level_id = discord.utils.find(lambda m: m[1]["Type"] == "RoyaleAccountLevel", self.mappings.items())[0]
		account_xp_id = discord.utils.find(lambda m: m[1]["Type"] == "RoyaleAccountXP", self.mappings.items())[0]
		if account_level_id in stats and account_xp_id in stats:
			fields.append(("Account Level", f"{stats[account_level_id]} ({stats[account_xp_id]:,} XP)", False))
		levels = {}
		xp = {}
		for stat, value in stats.items():
			if self.mappings.get(stat, {}).get("Type") == "RoyaleChampionLevel":
				levels[self.mappings[stat]["Name"]] = value
			elif self.mappings.get(stat, {}).get("Type") == "RoyaleChampionXP":
				xp[self.mappings[stat]["Name"]] = value
		xp = sorted(xp.items(), key = lambda x: x[1], reverse = True)
		for name, value in xp:
			emoji = getattr(self, name.lower().replace(' ', '_') + "_emoji", "")
			fields.append((f"{emoji} {name}", f"{levels[name]} ({value:,} XP)"))
		await ctx.embed_reply(f"ID: {data['id']}", title = data["attributes"]["name"], fields = fields)

