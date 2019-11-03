
from discord.ext import commands

import asyncio
import math
import json
import random
import sys
import time

import clients
from utilities import checks

sys.path.insert(0, "..")
from units.files import create_folder
sys.path.pop(0)

INITIAL_DATA = {"xp": {"woodcutting": 0, "mining": 0, "fishing": 0, "foraging": 0}, "inventory": {}, "last_action": None, "last_action_time": None, "time_started": None}
SKILLS = ["woodcutting", "mining", "fishing", "foraging"]
FORAGEABLES = {"rock": ("stone", "boulder"), "stick": ("branch", "trunk"), "plant": ("shrub", "bush")}
CRAFTABLES = {("rock", "stick"): "rock attached to stick"}
WOOD_TYPES = ["cuipo", "balsa", "eastern white pine", "basswood", "western white pine", "hemlock", "chestnut", "larch", "red alder", "western juniper", "douglas fir", "southern yellow pine", "silver maple", "radiata pine", "shedua", "box elder", "sycamore", "parana", "honduran mahogany", "african mahogany", "lacewood", "eastern red cedar", "paper birch", "boire", "red maple", "imbusia", "cherry", "black walnut", "boreal", "peruvian walnut", "siberian larch", "makore", "english oak", "rose gum", "teak", "larch", "carapa guianensis", "heart pine", "movingui", "yellow birch", "caribbean heart pine", "red oak", "american beech", "ash", "ribbon gum", "tasmanian oak", "white oak", "australian cypress", "bamboo", "kentucky coffeetree", "caribbean walnut", "hard maple", "sweet birch", "curupixa", "sapele", "peroba", "true pine", "zebrawood", "tualang", "wenge", "highland beech", "black locust", "kempas", "merbau", "blackwood", "african padauk", "rosewood", "bangkirai", "afzelia", "hickory", "tigerwood", "purpleheart", "jarrah", "amendoim", "merbau", "tallowwood", "cameron", "bubinga", "sydney blue gum", "karri", "osage orange", "brushbox", "brazilian koa", "pradoo", "bocote", "balfourodendron riedelianum", "golden teak", "mesquite", "jatoba", "spotted gum", "southern chestnut", "live oak", "turpentine", "bloodwood", "cocobolo", "yvyraro", "massaranduba", "ebony", "ironwood", "sucupira", "cumaru", "lapacho", "bolivian cherry", "grey ironbark", "moabi", "lapacho", "brazilian ebony", "brazilian olivewood", "snakewood", "piptadenia macrocarpa", "lignum vitae", "schinopsis balansae", "schinopsis brasiliensis", "australian buloke"]
# https://en.wikipedia.org/wiki/Janka_hardness_test
MINERALS = {"talc": (1), "graphite": (1.5), "putnisite": (1.75, 1), "bauxite": (2, 10), "gypsum": (2), "halite": (2.25), "galena": (2.625), "chalcocite": (2.75), "copper": (3), "celestine": (3.25), "chalcopyrite": (3.5), "strontianite": (3.5), "azurite": (3.75), "cuprite": (3.75), "malachite": (3.75), "cassiterite": (6.5), "pollucite": (6.75), "qingsongite": (9.5, 1), "quartz": (7, 10)}
# https://en.wikipedia.org/wiki/Mohs_scale_of_mineral_hardness
EXAMINE_MESSAGES = {"rock": "it's a rock..", "stone": "it's a bigger rock..", "boulder": "wow, that's a big rock", "stick": "pointy", "rock attached to stick": "it must have taken you a long time to make this"}

def setup(bot):
	bot.add_cog(Adventure(bot))

class Adventure(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.adventure_players = {}
		
		create_folder(clients.data_path + "/adventure_players")
		self.bot.loop.create_task(self.initialize_database())
	
	async def initialize_database(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS adventure")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS adventure.players (
				user_id				BIGINT PRIMARY KEY, 
				creation_time		TIMESTAMPTZ DEFAULT NOW(), 
				fishing_xp			BIGINT DEFAULT 0, 
				foraging_xp			BIGINT DEFAULT 0, 
				mining_xp			BIGINT DEFAULT 0, 
				woodcutting_xp		BIGINT DEFAULT 0, 
				last_action			TEXT, 
				last_action_object	TEXT, 
				last_action_time	TIMESTAMPTZ
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS adventure.inventories (
				user_id			BIGINT REFERENCES adventure.players (user_id) ON DELETE CASCADE, 
				object			TEXT, 
				count			BIGINT, 
				PRIMARY KEY		(user_id, object)
			)
			"""
		)
		# Migrate existing data
		import datetime
		import os
		for filename in os.listdir(self.bot.data_path + "/adventure_players"):
			with open(f"{self.bot.data_path}/adventure_players/{filename}", 'r') as player_file:
				data = json.load(player_file)
			user_id = int(filename[:-5])
			await self.bot.db.execute(
				"""
				INSERT INTO adventure.players (user_id, creation_time, fishing_xp, foraging_xp, mining_xp, woodcutting_xp, last_action, last_action_object, last_action_time)
				VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
				ON CONFLICT DO NOTHING
				""", 
				user_id, datetime.datetime.fromtimestamp(data["time_started"], tz = datetime.timezone.utc), 
				data["xp"]["fishing"], data["xp"]["foraging"], data["xp"]["mining"], data["xp"]["woodcutting"], 
				data["last_action"] and data["last_action"][0], data["last_action"] and data["last_action"][1], 
				datetime.datetime.fromtimestamp(data["last_action_time"], tz = datetime.timezone.utc)
			)
			for object_name, count in data["inventory"].items():
				await self.bot.db.execute(
					"""
					INSERT INTO adventure.inventories (user_id, object, count)
					VALUES ($1, $2, $3)
					ON CONFLICT DO NOTHING
					""", 
					user_id, object_name, count
				)
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden_predicate(ctx)
	
	@commands.group(aliases = ["rpg"], invoke_without_command = True, case_insensitive = True)
	async def adventure(self, ctx):
		'''WIP'''
		pass
	
	def get_adventure_player(self, user_id):
		player = self.adventure_players.get(user_id)
		if not player:
			player = AdventurePlayer(user_id)
			self.adventure_players[user_id] = player
		return player
	
	@adventure.command(aliases = ["make", "craft"])
	async def create(self, ctx, *items: str):
		'''
		Create item
		items: items to use to attempt to create something else
		Use quotes for spaces in item names
		'''
		player = self.get_adventure_player(ctx.author.id)
		created = player.create_item(items)
		if created is None:
			await ctx.embed_reply("You don't have those items")
		elif created is False:
			await ctx.embed_reply("You were unable to create anything with those items")
		else:
			await ctx.embed_reply(f"You have created {created}")
	
	@adventure.command()
	async def examine(self, ctx, *, item: str):
		'''Examine items'''
		player = self.get_adventure_player(ctx.author.id)
		inventory = player.inventory
		if item not in inventory:
			return await ctx.embed_reply(":no_entry: You don't have that item")
		if item in EXAMINE_MESSAGES:
			await ctx.embed_reply(EXAMINE_MESSAGES[item])
		else:
			await ctx.embed_reply(item)
	
	@adventure.group(aliases = ["gather"], invoke_without_command = True, case_insensitive = True)
	async def forage(self, ctx, *, item: str = ""):
		'''Foraging'''
		player = self.get_adventure_player(ctx.author.id)
		started = player.start_foraging(item)
		if started == "foraging":
			stopped = player.stop_foraging()
			output = (f":herb: You were foraging {stopped[0]} for {stopped[1]:,.2f} min. and received {stopped[2]:,} {stopped[0]} and xp.\n"
						f"While you were foraging, you also found {stopped[3]:,} {FORAGEABLES[stopped[0]][0]}")
			if stopped[4]:
				output += f" and {stopped[4]:,} {FORAGEABLES[stopped[0]][1]}!"
			await ctx.embed_reply(output)
			if item:
				started = player.start_foraging(item)
			else:
				return
		if started is True:
			await ctx.embed_reply(f":herb: You have started foraging for {item}")
			# TODO: active option?
		elif started is False:
			await ctx.embed_reply(":no_entry: That item type doesn't exist")
		else:
			await ctx.embed_reply(f":no_entry: You're currently {started}! You can't start/stop foraging right now")
	
	@forage.command(name = "start", aliases = ["on"])
	async def forage_start(self, ctx, *, item: str):
		'''Start foraging'''
		player = self.get_adventure_player(ctx.author.id)
		started = player.start_foraging(item)
		if started is True:
			await ctx.embed_reply(f":herb: You have started foraging for {item}")
			# TODO: active option?
		elif started is False:
			await ctx.embed_reply(":no_entry: That item type doesn't exist")
		else:
			await ctx.embed_reply(f":no_entry: You're currently {started}! You can't start foraging right now")
	
	@forage.command(name = "stop", aliases = ["off"])
	async def forage_stop(self, ctx):
		'''Stop foraging'''
		player = self.get_adventure_player(ctx.author.id)
		stopped = player.stop_foraging()
		if stopped[0]:
			output = (f":herb: You were foraging {stopped[0]} for {stopped[1]:,.2f} min. and received {stopped[2]:,} {stopped[0]} and xp.\n"
						f"While you were foraging, you also found {stopped[3]:,} {FORAGEABLES[stopped[0]][0]}")
			if stopped[4]:
				output += f" and {stopped[4]:,} {FORAGEABLES[stopped[0]][1]}!"
			await ctx.embed_reply(output)
		elif stopped[1]:
			await ctx.embed_reply(f":no_entry: You're currently {stopped[1][0]}! You aren't foraging right now")
		else:
			await ctx.embed_reply(":no_entry: You aren't foraging")
	
	@forage.command(name = "items", aliases = ["item", "type", "types"])
	async def forage_items(self, ctx):
		'''Forageable items'''
		await ctx.embed_reply(", ".join(FORAGEABLES.keys()))
	
	@adventure.command()
	async def inventory(self, ctx, *, item: str = ""):
		'''Inventory'''
		player = self.get_adventure_player(ctx.author.id)
		inventory = player.inventory
		if item in inventory:
			await ctx.embed_reply(f"{item}: {inventory[item]}")
		else:
			await ctx.embed_reply(", ".join(f"{item}: {amount:,}" for item, amount in sorted(inventory.items())))
	
	@adventure.group(aliases = ["stat", "levels", "level", "lvls", "lvl"], invoke_without_command = True, case_insensitive = True)
	async def stats(self, ctx):
		'''Stats'''
		player = self.get_adventure_player(ctx.author.id)
		await ctx.embed_reply(f":fishing_pole_and_fish: Fishing xp: {player.fishing_xp:,} (Level {player.fishing_lvl:,})\n"
								f":herb: Foraging xp: {player.foraging_xp:,} (Level {player.foraging_lvl:,})\n"
								f":pick: Mining xp: {player.mining_xp:,} (Level {player.mining_lvl:,})\n"
								f":evergreen_tree: Woodcutting xp: {player.woodcutting_xp:,} (Level {player.woodcutting_lvl:,})")
		# time started/played
	
	@stats.command(name = "woodcutting", aliases = ["wc"])
	async def stats_woodcutting(self, ctx):
		'''Woodcutting stats'''
		player = self.get_adventure_player(ctx.author.id)
		woodcutting_xp = player.woodcutting_xp
		await ctx.embed_reply(f":evergreen_tree: Woodcutting xp: {woodcutting_xp:,}\n"
								f"{self.level_bar(woodcutting_xp)}\n"
								f"{xp_left_to_next_lvl(woodcutting_xp):,} xp to next level")
	
	@stats.command(name = "foraging", aliases = ["forage", "gather", "gathering"])
	async def stats_foraging(self, ctx):
		'''Foraging stats'''
		player = self.get_adventure_player(ctx.author.id)
		foraging_xp = player.foraging_xp
		await ctx.embed_reply(f":herb: Foraging xp: {foraging_xp:,}\n"
								f"{self.level_bar(foraging_xp)}\n"
								f"{xp_left_to_next_lvl(foraging_xp):,} xp to next level")
	
	@staticmethod
	def level_bar(xp):
		lvl = xp_to_lvl(xp)
		previous_xp = lvl_to_xp(lvl)
		next_xp = lvl_to_xp(lvl + 1)
		difference = next_xp - previous_xp
		shaded = int((xp - previous_xp) / difference * 10)
		bar = '\N{BLACK SQUARE}' * shaded + '\N{WHITE SQUARE}' * (10 - shaded)
		return f"Level {lvl:,} ({previous_xp:,} xp) [{bar}] Level {lvl + 1:,} ({next_xp:,} xp)"
	
	@adventure.group(name = "chop", aliases = ["woodcutting", "wc"], invoke_without_command = True, case_insensitive = True)
	async def woodcutting(self, ctx, *, wood_type: str = ""):
		'''Woodcutting'''
		player = self.get_adventure_player(ctx.author.id)
		started = player.start_woodcutting(wood_type)
		if started == "woodcutting":
			stopped = player.stop_woodcutting()
			await ctx.embed_reply(f":evergreen_tree: You were chopping {stopped[0]} for {stopped[1]:,.2f} min. and received {stopped[2]:,} {stopped[0]} and {stopped[3]:,} xp")
			if wood_type:
				started = player.start_woodcutting(wood_type)
			else:
				return
		if started is True:
			await ctx.embed_reply(f":evergreen_tree: You have started chopping {wood_type} trees")
			await self.woodcutting_active(ctx, wood_type)
		elif started is False:
			await ctx.embed_reply(":no_entry: That wood type doesn't exist")
		else:
			await ctx.embed_reply(f":no_entry: You're currently {started}! You can't start/stop woodcutting right now")
	
	@woodcutting.command(name = "start", aliases = ["on"])
	async def woodcutting_start(self, ctx, *, wood_type: str):
		'''Start chopping wood'''
		player = self.get_adventure_player(ctx.author.id)
		started = player.start_woodcutting(wood_type)
		if started is True:
			await ctx.embed_reply(f":evergreen_tree: You have started chopping {wood_type} trees")
			await self.woodcutting_active(ctx, wood_type)
		elif started is False:
			await ctx.embed_reply(":no_entry: That wood type doesn't exist")
		else:
			await ctx.embed_reply(f":no_entry: You're currently {started}! You can't start woodcutting right now")
	
	async def woodcutting_active(self, ctx, wood_type):
		player = self.get_adventure_player(ctx.author.id)
		ask_message = await ctx.embed_reply(f":grey_question: Would you like to chop {wood_type} trees actively? Yes/No")
		try:
			message = await self.bot.wait_for("message", timeout = 60, check = lambda m: m.author == ctx.author and m.content.lower() in ('y', "yes", 'n', "no"))
		except asyncio.TimeoutError:
			return
		finally:
			await self.bot.attempt_delete_message(ask_message)
		if message.content.lower() in ('n', "no"):
			return await self.bot.attempt_delete_message(message)
		rate = player.wood_rate(wood_type) * player.woodcutting_rate
		if rate == 0:
			return await ctx.embed_reply(":no_entry: You can't chop this wood yet")
		time = int(60 / rate)
		chopped_message = None
		while message:
			chopping = await ctx.embed_reply(":evergreen_tree: Chopping..",
												footer_text = f"This could take up to {time} seconds")
			await asyncio.sleep(random.randint(1, time))
			await self.bot.attempt_delete_message(message)
			await self.bot.attempt_delete_message(chopping)
			prompt = random.choice(("chop", "whack", "swing", "cut"))
			prompt_message = await ctx.embed_reply(f'Reply with "{prompt}" in the next 10 seconds to continue')
			try:
				message = await self.bot.wait_for("message", timeout = 10, check = lambda m: m.author == ctx.author and m.content == prompt)
			except asyncio.TimeoutError:
				return await ctx.embed_reply(f":stop_sign: You have stopped actively chopping {wood_type}")
			else:
				chopped = player.chop_once(wood_type)
				if chopped_message:
					await self.bot.attempt_delete_message(chopped_message)
				chopped_message = await ctx.embed_reply(f":evergreen_tree: You chopped a {wood_type} tree.\n"
														f"You now have {chopped[0]:,} {wood_type} and {chopped[1]:,} woodcutting xp")
			finally:
				await self.bot.attempt_delete_message(prompt_message)
	
	@woodcutting.command(name = "stop", aliases = ["off"])
	async def woodcutting_stop(self, ctx):
		'''Stop chopping wood'''
		player = self.get_adventure_player(ctx.author.id)
		stopped = player.stop_woodcutting()
		if stopped[0]:
			await ctx.embed_reply(f":evergreen_tree: You were chopping {stopped[0]} for {stopped[1]:,.2f} min. and received {stopped[2]:,} {stopped[0]} and {stopped[3]:,} xp")
		elif stopped[1]:
			await ctx.embed_reply(f":no_entry: You're currently {stopped[1][0]}! You aren't woodcutting right now")
		else:
			await ctx.embed_reply(":no_entry: You aren't woodcutting")
	
	@woodcutting.command(name = "types", aliases = ["type", "item", "items"])
	async def woodcutting_types(self, ctx):
		'''Types of wood'''
		await ctx.embed_reply(", ".join(WOOD_TYPES))
	
	@woodcutting.command(name = "rate", aliases = ["rates"])
	async def woodcutting_rate(self, ctx, *, wood_type: str):
		'''Rate of chopping certain wood'''
		player = self.get_adventure_player(ctx.author.id)
		if wood_type in WOOD_TYPES:
			await ctx.embed_reply(f"You will get {player.wood_rate(wood_type) * player.woodcutting_rate:.2f} {wood_type}/min. at your current level")
		else:
			await ctx.embed_reply(":no_entry: That wood type doesn't exist")

def xp_to_lvl(xp):
	return math.ceil((xp / 12.5 + 1.08) ** 0.5 / 2 - 0.5)

def xp_left_to_next_lvl(xp):
	lvl = xp_to_lvl(xp)
	return (lvl ** 2 + lvl + 2) * 50 - 100 - xp

def lvl_to_xp(lvl):
	return (lvl ** 2 - lvl + 2) * 50 - 100

def lvl_to_rate(lvl):
	return math.log10(lvl + 10)

def xp_to_rate(xp):
	return lvl_to_rate(xp_to_lvl(xp))

def wood_lvl(wood_type):
	return WOOD_TYPES.index(wood_type) + 1

class AdventurePlayer:
	
	'''Adventure Player'''
	
	def __init__(self, user_id):
		self.user_id = user_id
		_initial_data = INITIAL_DATA.copy()
		_initial_data["time_started"] = time.time()
		clients.create_file("adventure_players/{}".format(user_id), content = _initial_data)
		with open(clients.data_path + "/adventure_players/{}.json".format(user_id), 'r') as player_file:
			self.data = json.load(player_file)
			
	def write_data(self):
		with open(clients.data_path + "/adventure_players/{}.json".format(self.user_id), 'w') as player_file:
			json.dump(self.data, player_file, indent = 4)
	
	def wood_rate(self, wood_type):
		return max(0, math.log10(self.woodcutting_lvl / wood_lvl(wood_type)) + 1)
	
	def start_foraging(self, item):
		if self.last_action is not None:
			return self.last_action[0]
		elif item.lower() in FORAGEABLES:
			self.last_action = ("foraging", item)
			self.last_action_time = time.time()
			self.write_data()
			return True
		else:
			return False
	
	def stop_foraging(self):
		if self.last_action and self.last_action[0] == "foraging":
			item = self.last_action[1]
			time_spent = math.ceil(time.time() - self.last_action_time) / 60
			self.last_action = None
			self.last_action_time = None
			item_amount = math.floor(time_spent * self.foraging_rate)
			self.inventory[item] = self.inventory.get(item, 0) + item_amount
			if self.inventory[item] == 0:
				del self.inventory[item]
			self.foraging_xp += item_amount
			secondary_item = FORAGEABLES[item][0]
			tertiary_item = FORAGEABLES[item][1]
			secondary_amount = random.randint(0, item_amount)
			tertiary_amount = math.floor(random.randint(0, item_amount) / 100)
			self.inventory[secondary_item] = self.inventory.get(secondary_item, 0) + secondary_amount
			if self.inventory[secondary_item] == 0:
				del self.inventory[secondary_item]
			self.inventory[tertiary_item] = self.inventory.get(tertiary_item, 0) + tertiary_amount
			if self.inventory[tertiary_item] == 0:
				del self.inventory[tertiary_item]
			self.write_data()
			return item, time_spent, item_amount, secondary_amount, tertiary_amount
		else:
			return False, self.last_action
	
	def create_item(self, items):
		'''Create/Craft an item'''
		for item in items:
			if item not in self.inventory:
				return None
		sorted_items = tuple(sorted(items))
		if sorted_items not in CRAFTABLES:
			return False
		crafted_item = CRAFTABLES[sorted_items]
		for item in items:
			self.inventory[item] -= 1
			if self.inventory[item] == 0:
				del self.inventory[item]
		self.inventory[crafted_item] = self.inventory.get(crafted_item, 0) + 1
		return crafted_item
	
	def start_woodcutting(self, wood_type):
		if self.last_action is not None:
			return self.last_action[0]
		elif wood_type.lower() in WOOD_TYPES:
			self.last_action = ("woodcutting", wood_type)
			self.last_action_time = time.time()
			self.write_data()
			return True
		else:
			return False
	
	def stop_woodcutting(self):
		if self.last_action and self.last_action[0] == "woodcutting":
			wood_type = self.last_action[1]
			time_spent = math.ceil(time.time() - self.last_action_time) / 60
			self.last_action = None
			self.last_action = None
			current_wood_lvl = wood_lvl(wood_type)
			wood_amount = math.floor(time_spent * self.wood_rate(wood_type) * self.woodcutting_rate)
			xp_amount = current_wood_lvl * wood_amount
			self.inventory[wood_type] = self.inventory.get(wood_type, 0) + wood_amount
			if self.inventory[wood_type] == 0:
				del self.inventory[wood_type]
			self.woodcutting_xp += xp_amount
			self.write_data()
			return wood_type, time_spent, wood_amount, xp_amount
		else:
			return False, self.last_action
	
	def chop_once(self, wood_type):
		'''Chop a tree once'''
		wood = self.inventory[wood_type] = self.inventory.get(wood_type, 0) + 1
		xp = self.woodcutting_xp = self.woodcutting_xp + wood_lvl(wood_type)
		self.write_data()
		return wood, xp

for info in INITIAL_DATA:
	def set_info(self, value, info = info):
		self.data[info] = value
		# write_data?
	setattr(AdventurePlayer, info, property(lambda self, info = info: self.data[info], set_info))

for skill in SKILLS:
	def set_xp(self, value, skill = skill):
		self.data["xp"][skill] = value
		# write data?
	setattr(AdventurePlayer, skill + "_xp", property(lambda self, skill = skill: self.data["xp"][skill], set_xp))
	setattr(AdventurePlayer, skill + "_lvl", property(lambda self, skill = skill: xp_to_lvl(self.data["xp"][skill])))
	setattr(AdventurePlayer, skill + "_rate", property(lambda self, skill = skill: xp_to_rate(self.data["xp"][skill])))

