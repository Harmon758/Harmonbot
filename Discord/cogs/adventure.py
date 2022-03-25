
from discord.ext import commands

import asyncio
import datetime
import math
from operator import itemgetter
import random

from utilities import checks

CRAFTABLES = {("rock", "stick"): "rock attached to stick"}
EXAMINE_MESSAGES = {"boulder": "wow, that's a big rock", "rock": "it's a rock..", "rock attached to stick": "it must have taken you a long time to make this", "stick": "pointy", "stone": "it's a bigger rock.."}
FORAGEABLES = {"plant": ("shrub", "bush"), "rock": ("stone", "boulder"), "stick": ("branch", "trunk")}
MINERALS = {"talc": (1), "graphite": (1.5), "putnisite": (1.75, 1), "bauxite": (2, 10), "gypsum": (2), "halite": (2.25), "galena": (2.625), "chalcocite": (2.75), "copper": (3), "celestine": (3.25), "chalcopyrite": (3.5), "strontianite": (3.5), "azurite": (3.75), "cuprite": (3.75), "malachite": (3.75), "cassiterite": (6.5), "pollucite": (6.75), "qingsongite": (9.5, 1), "quartz": (7, 10)}
# https://en.wikipedia.org/wiki/Mohs_scale_of_mineral_hardness
SKILLS = ["fishing", "foraging", "mining", "woodcutting"]
WOOD_TYPES = ["cuipo", "balsa", "eastern white pine", "basswood", "western white pine", "hemlock", "chestnut", "larch", "red alder", "western juniper", "douglas fir", "southern yellow pine", "silver maple", "radiata pine", "shedua", "box elder", "sycamore", "parana", "honduran mahogany", "african mahogany", "lacewood", "eastern red cedar", "paper birch", "boire", "red maple", "imbusia", "cherry", "black walnut", "boreal", "peruvian walnut", "siberian larch", "makore", "english oak", "rose gum", "teak", "larch", "carapa guianensis", "heart pine", "movingui", "yellow birch", "caribbean heart pine", "red oak", "american beech", "ash", "ribbon gum", "tasmanian oak", "white oak", "australian cypress", "bamboo", "kentucky coffeetree", "caribbean walnut", "hard maple", "sweet birch", "curupixa", "sapele", "peroba", "true pine", "zebrawood", "tualang", "wenge", "highland beech", "black locust", "kempas", "merbau", "blackwood", "african padauk", "rosewood", "bangkirai", "afzelia", "hickory", "tigerwood", "purpleheart", "jarrah", "amendoim", "merbau", "tallowwood", "cameron", "bubinga", "sydney blue gum", "karri", "osage orange", "brushbox", "brazilian koa", "pradoo", "bocote", "balfourodendron riedelianum", "golden teak", "mesquite", "jatoba", "spotted gum", "southern chestnut", "live oak", "turpentine", "bloodwood", "cocobolo", "yvyraro", "massaranduba", "ebony", "ironwood", "sucupira", "cumaru", "lapacho", "bolivian cherry", "grey ironbark", "moabi", "lapacho", "brazilian ebony", "brazilian olivewood", "snakewood", "piptadenia macrocarpa", "lignum vitae", "schinopsis balansae", "schinopsis brasiliensis", "australian buloke"]
# https://en.wikipedia.org/wiki/Janka_hardness_test

def setup(bot):
	bot.add_cog(Adventure(bot))

class Adventure(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.adventure_players = {}
		
	async def cog_load(self):
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
				last_action_item	TEXT, 
				last_action_time	TIMESTAMPTZ
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS adventure.inventories (
				user_id			BIGINT REFERENCES adventure.players (user_id) ON DELETE CASCADE, 
				item			TEXT, 
				count			BIGINT, 
				PRIMARY KEY		(user_id, item)
			)
			"""
		)
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(aliases = ["rpg"], invoke_without_command = True, case_insensitive = True)
	async def adventure(self, ctx):
		'''WIP'''
		pass
	
	async def get_adventure_player(self, user_id):
		player = self.adventure_players.get(user_id)
		if not player:
			player = AdventurePlayer(self.bot, user_id)
			await player.initialized.wait()
			self.adventure_players[user_id] = player
		return player
	
	@adventure.command(aliases = ["make", "craft"])
	async def create(self, ctx, *items: str):
		'''
		Create item
		items: items to use to attempt to create something else
		Use quotes for spaces in item names
		'''
		player = await self.get_adventure_player(ctx.author.id)
		created = await player.create_item(items)
		if created is None:
			await ctx.embed_reply("You don't have those items")
		elif created is False:
			await ctx.embed_reply("You were unable to create anything with those items")
		else:
			await ctx.embed_reply(f"You have created {created}")
	
	@adventure.command()
	async def examine(self, ctx, *, item: str):
		'''Examine items'''
		player = await self.get_adventure_player(ctx.author.id)
		count = await player.inventory(item)
		if not count:
			return await ctx.embed_reply(":no_entry: You don't have that item")
		if item in EXAMINE_MESSAGES:
			await ctx.embed_reply(EXAMINE_MESSAGES[item])
		else:
			await ctx.embed_reply(item)
	
	@adventure.group(aliases = ["gather"], invoke_without_command = True, case_insensitive = True)
	async def forage(self, ctx, *, item: str = ""):
		'''Foraging'''
		player = await self.get_adventure_player(ctx.author.id)
		started = await player.start_foraging(item)
		if started == "foraging":
			stopped = await player.stop_foraging()
			output = (f":herb: You were foraging {stopped[0]} for {stopped[1]:,.2f} min. and received {stopped[2]:,} {stopped[0]} and xp.\n"
						f"While you were foraging, you also found {stopped[3]:,} {FORAGEABLES[stopped[0]][0]}")
			if stopped[4]:
				output += f" and {stopped[4]:,} {FORAGEABLES[stopped[0]][1]}!"
			await ctx.embed_reply(output)
			if item:
				started = await player.start_foraging(item)
			else:
				return
		if started is True:
			await ctx.embed_reply(f":herb: You have started foraging for {item}")
			# TODO: active option?
		elif started is False:
			await ctx.embed_reply(":no_entry: That item type doesn't exist")
		else:
			await ctx.embed_reply(f":no_entry: You're currently {started}! You can't start/stop foraging right now")
	
	@forage.command(name = "items", aliases = ["item", "type", "types"])
	async def forage_items(self, ctx):
		'''Forageable items'''
		await ctx.embed_reply(", ".join(FORAGEABLES.keys()))
	
	@forage.command(name = "start", aliases = ["on"])
	async def forage_start(self, ctx, *, item: str):
		'''Start foraging'''
		player = await self.get_adventure_player(ctx.author.id)
		started = await player.start_foraging(item)
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
		player = await self.get_adventure_player(ctx.author.id)
		stopped = await player.stop_foraging()
		if stopped[0]:
			output = (f":herb: You were foraging {stopped[0]} for {stopped[1]:,.2f} min. and received {stopped[2]:,} {stopped[0]} and xp.\n"
						f"While you were foraging, you also found {stopped[3]:,} {FORAGEABLES[stopped[0]][0]}")
			if stopped[4]:
				output += f" and {stopped[4]:,} {FORAGEABLES[stopped[0]][1]}!"
			await ctx.embed_reply(output)
		elif stopped[1]:
			await ctx.embed_reply(f":no_entry: You're currently {stopped[1]}! You aren't foraging right now")
		else:
			await ctx.embed_reply(":no_entry: You aren't foraging")
	
	@adventure.command()
	async def inventory(self, ctx, *, item: str = ""):
		'''Inventory'''
		player = await self.get_adventure_player(ctx.author.id)
		if item:
			count = await player.inventory(item)
			if count:
				return await ctx.embed_reply(f"{item}: {count}")
		records = await player.inventory()
		await ctx.embed_reply(", ".join(f"{record['item']}: {record['count']:,}" for record in sorted(records, key = itemgetter("item"))))
	
	@adventure.group(aliases = ["stat", "levels", "level", "lvls", "lvl"], invoke_without_command = True, case_insensitive = True)
	async def stats(self, ctx):
		'''Stats'''
		player = await self.get_adventure_player(ctx.author.id)
		await ctx.embed_reply(f":fishing_pole_and_fish: Fishing xp: {player.fishing_xp:,} (Level {player.fishing_lvl:,})\n"
								f":herb: Foraging xp: {player.foraging_xp:,} (Level {player.foraging_lvl:,})\n"
								f":pick: Mining xp: {player.mining_xp:,} (Level {player.mining_lvl:,})\n"
								f":evergreen_tree: Woodcutting xp: {player.woodcutting_xp:,} (Level {player.woodcutting_lvl:,})")
		# time started/played
	
	@stats.command(name = "foraging", aliases = ["forage", "gather", "gathering"])
	async def stats_foraging(self, ctx):
		'''Foraging stats'''
		player = await self.get_adventure_player(ctx.author.id)
		foraging_xp = player.foraging_xp
		await ctx.embed_reply(f":herb: Foraging xp: {foraging_xp:,}\n"
								f"{self.level_bar(foraging_xp)}\n"
								f"{xp_left_to_next_lvl(foraging_xp):,} xp to next level")
	
	@stats.command(name = "woodcutting", aliases = ["wc"])
	async def stats_woodcutting(self, ctx):
		'''Woodcutting stats'''
		player = await self.get_adventure_player(ctx.author.id)
		woodcutting_xp = player.woodcutting_xp
		await ctx.embed_reply(f":evergreen_tree: Woodcutting xp: {woodcutting_xp:,}\n"
								f"{self.level_bar(woodcutting_xp)}\n"
								f"{xp_left_to_next_lvl(woodcutting_xp):,} xp to next level")
	
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
		player = await self.get_adventure_player(ctx.author.id)
		started = await player.start_woodcutting(wood_type)
		if started == "woodcutting":
			stopped = await player.stop_woodcutting()
			await ctx.embed_reply(f":evergreen_tree: You were chopping {stopped[0]} for {stopped[1]:,.2f} min. and received {stopped[2]:,} {stopped[0]} and {stopped[3]:,} xp")
			if wood_type:
				started = await player.start_woodcutting(wood_type)
			else:
				return
		if started is True:
			await ctx.embed_reply(f":evergreen_tree: You have started chopping {wood_type} trees")
			await self.woodcutting_active(ctx, wood_type)
		elif started is False:
			await ctx.embed_reply(":no_entry: That wood type doesn't exist")
		else:
			await ctx.embed_reply(f":no_entry: You're currently {started}! You can't start/stop woodcutting right now")
	
	@woodcutting.command(name = "rate", aliases = ["rates"])
	async def woodcutting_rate(self, ctx, *, wood_type: str):
		'''Rate of chopping certain wood'''
		player = await self.get_adventure_player(ctx.author.id)
		if wood_type in WOOD_TYPES:
			await ctx.embed_reply(f"You will get {player.wood_rate(wood_type) * player.woodcutting_rate:.2f} {wood_type}/min. at your current level")
		else:
			await ctx.embed_reply(":no_entry: That wood type doesn't exist")
	
	@woodcutting.command(name = "start", aliases = ["on"])
	async def woodcutting_start(self, ctx, *, wood_type: str):
		'''Start chopping wood'''
		player = await self.get_adventure_player(ctx.author.id)
		started = await player.start_woodcutting(wood_type)
		if started is True:
			await ctx.embed_reply(f":evergreen_tree: You have started chopping {wood_type} trees")
			await self.woodcutting_active(ctx, wood_type)
		elif started is False:
			await ctx.embed_reply(":no_entry: That wood type doesn't exist")
		else:
			await ctx.embed_reply(f":no_entry: You're currently {started}! You can't start woodcutting right now")
	
	async def woodcutting_active(self, ctx, wood_type):
		player = await self.get_adventure_player(ctx.author.id)
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
				chopped = await player.chop_once(wood_type)
				if chopped_message:
					await self.bot.attempt_delete_message(chopped_message)
				chopped_message = await ctx.embed_reply(f":evergreen_tree: You chopped a {wood_type} tree.\n"
														f"You now have {chopped[0]:,} {wood_type} and {chopped[1]:,} woodcutting xp")
			finally:
				await self.bot.attempt_delete_message(prompt_message)
	
	@woodcutting.command(name = "stop", aliases = ["off"])
	async def woodcutting_stop(self, ctx):
		'''Stop chopping wood'''
		player = await self.get_adventure_player(ctx.author.id)
		stopped = await player.stop_woodcutting()
		if stopped[0]:
			await ctx.embed_reply(f":evergreen_tree: You were chopping {stopped[0]} for {stopped[1]:,.2f} min. and received {stopped[2]:,} {stopped[0]} and {stopped[3]:,} xp")
		elif stopped[1]:
			await ctx.embed_reply(f":no_entry: You're currently {stopped[1]}! You aren't woodcutting right now")
		else:
			await ctx.embed_reply(":no_entry: You aren't woodcutting")
	
	@woodcutting.command(name = "types", aliases = ["type", "item", "items"])
	async def woodcutting_types(self, ctx):
		'''Types of wood'''
		await ctx.embed_reply(", ".join(WOOD_TYPES))

def lvl_to_rate(lvl):
	return math.log10(lvl + 10)

def lvl_to_xp(lvl):
	return (lvl ** 2 - lvl + 2) * 50 - 100

def wood_lvl(wood_type):
	return WOOD_TYPES.index(wood_type) + 1

def xp_to_lvl(xp):
	return math.ceil((xp / 12.5 + 1.08) ** 0.5 / 2 - 0.5)

def xp_left_to_next_lvl(xp):
	lvl = xp_to_lvl(xp)
	return (lvl ** 2 + lvl + 2) * 50 - 100 - xp

def xp_to_rate(xp):
	return lvl_to_rate(xp_to_lvl(xp))

class AdventurePlayer:
	
	'''Adventure Player'''
	
	def __init__(self, bot, user_id):
		self.bot = bot
		self.user_id = user_id
		
		self.initialized = asyncio.Event()
		self.bot.loop.create_task(self.initialize_player(), name = "Initialize Adventure Player")
	
	async def initialize_player(self):
		await self.bot.db.execute(
			"""
			INSERT INTO adventure.players (user_id)
			VALUES ($1)
			ON CONFLICT DO NOTHING
			""", 
			self.user_id
		)
		record = await self.bot.db.fetchrow(
			"""
			SELECT * FROM adventure.players
			WHERE user_id = $1
			""", 
			self.user_id
		)
		for skill in SKILLS:
			setattr(self, skill + "_xp", record[skill + "_xp"])
		self.last_action = record["last_action"]
		self.last_action_item = record["last_action_item"]
		self.last_action_time = record["last_action_time"]
		self.initialized.set()
	
	async def add_to_inventory(self, item, count):
		return await self.bot.db.fetchval(
			"""
			INSERT INTO adventure.inventories (user_id, item, count)
			VALUES ($1, $2, $3)
			ON CONFLICT (user_id, item) DO
			UPDATE SET count = inventories.count + $3
			RETURNING count
			""", 
			self.user_id, item, count
		)
	
	async def create_item(self, items):
		'''Create/Craft an item'''
		for item in items:
			count = await self.inventory(item)
			if not count:
				return None
		sorted_items = tuple(sorted(items))
		if sorted_items not in CRAFTABLES:
			return False
		crafted_item = CRAFTABLES[sorted_items]
		for item in items:
			await self.add_to_inventory(item, -1)
		await self.add_to_inventory(crafted_item, 1)
		return crafted_item
	
	async def inventory(self, item = None):
		if item:
			return await self.bot.db.fetchval(
				"""
				SELECT count FROM adventure.inventories
				WHERE user_id = $1 AND item = $2
				""", 
				self.user_id, item
			)
		else:
			return await self.bot.db.fetch(
				"""
				SELECT item, count FROM adventure.inventories
				WHERE user_id = $1
				""", 
				self.user_id
			)
	
	async def start_action(self, action, item):
		self.last_action = action
		self.last_action_item = item
		self.last_action_time = datetime.datetime.now(datetime.timezone.utc)
		await self.bot.db.execute(
			"""
			UPDATE adventure.players
			SET last_action = $2, last_action_item = $3, last_action_time = $4
			WHERE user_id = $1
			""", 
			self.user_id, action, item, self.last_action_time
		)
	
	async def stop_action(self):
		self.last_action = None
		self.last_action_item = None
		self.last_action_time = None
		await self.bot.db.execute(
			"""
			UPDATE adventure.players
			SET last_action = NULL, last_action_item = NULL, last_action_time = NULL
			WHERE user_id = $1
			""", 
			self.user_id
		)
	
	async def start_foraging(self, item):
		if self.last_action:
			return self.last_action
		elif item.lower() in FORAGEABLES:
			await self.start_action("foraging", item)
			return True
		else:
			return False
	
	async def stop_foraging(self):
		if self.last_action == "foraging":
			item = self.last_action_item
			time_spent = math.ceil((datetime.datetime.now(datetime.timezone.utc) - self.last_action_time).total_seconds()) / 60
			await self.stop_action()
			item_amount = math.floor(time_spent * self.foraging_rate)
			await self.add_to_inventory(item, item_amount)
			secondary_item = FORAGEABLES[item][0]
			secondary_amount = random.randint(0, item_amount)
			await self.add_to_inventory(secondary_item, secondary_amount)
			tertiary_item = FORAGEABLES[item][1]
			tertiary_amount = math.floor(random.randint(0, item_amount) / 100)
			await self.add_to_inventory(tertiary_item, tertiary_amount)
			await self.add_foraging_xp(item_amount)
			return item, time_spent, item_amount, secondary_amount, tertiary_amount
		else:
			return False, self.last_action
	
	async def start_woodcutting(self, wood_type):
		if self.last_action:
			return self.last_action
		elif wood_type.lower() in WOOD_TYPES:
			await self.start_action("woodcutting", wood_type)
			return True
		else:
			return False
	
	async def stop_woodcutting(self):
		if self.last_action == "woodcutting":
			wood_type = self.last_action_item
			time_spent = math.ceil((datetime.datetime.now(datetime.timezone.utc) - self.last_action_time).total_seconds()) / 60
			await self.stop_action()
			current_wood_lvl = wood_lvl(wood_type)
			wood_amount = math.floor(time_spent * self.wood_rate(wood_type) * self.woodcutting_rate)
			xp_amount = current_wood_lvl * wood_amount
			await self.add_to_inventory(wood_type, wood_amount)
			await self.add_woodcutting_xp(xp_amount)
			return wood_type, time_spent, wood_amount, xp_amount
		else:
			return False, self.last_action
	
	async def chop_once(self, wood_type):
		'''Chop a tree once'''
		wood = await self.add_to_inventory(wood_type, 1)
		xp = await self.add_woodcutting_xp(wood_lvl(wood_type))
		return wood, xp
	
	def wood_rate(self, wood_type):
		return max(0, math.log10(self.woodcutting_lvl / wood_lvl(wood_type)) + 1)

for skill in SKILLS:
	setattr(AdventurePlayer, skill + "_lvl", property(lambda self, skill = skill: xp_to_lvl(getattr(self, skill + "_xp"))))
	setattr(AdventurePlayer, skill + "_rate", property(lambda self, skill = skill: xp_to_rate(getattr(self, skill + "_xp"))))
	async def add_xp(self, xp, skill = skill):
		setattr(self, skill + "_xp", getattr(self, skill + "_xp") + xp)
		return await self.bot.db.fetchval(
			f"""
			UPDATE adventure.players
			SET {skill}_xp = {skill}_xp + $2
			WHERE user_id = $1
			RETURNING {skill}_xp
			""", 
			self.user_id, xp
		)
	setattr(AdventurePlayer, f"add_{skill}_xp", add_xp)

