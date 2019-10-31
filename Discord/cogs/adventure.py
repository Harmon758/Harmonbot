
from discord.ext import commands

import asyncio
import random

from modules import adventure
from utilities import checks

def setup(bot):
	bot.add_cog(Adventure(bot))

class Adventure(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.adventure_players = {}
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden_predicate(ctx)
	
	@commands.group(aliases = ["rpg"], invoke_without_command = True, case_insensitive = True)
	async def adventure(self, ctx):
		'''WIP'''
		pass
	
	def get_adventure_player(self, user_id):
		player = self.adventure_players.get(user_id)
		if not player:
			player = adventure.AdventurePlayer(user_id)
			self.adventure_players[user_id] = player
		return player
	
	@adventure.group(name = "stats", aliases = ["stat", "levels", "level", "lvls", "lvl"], invoke_without_command = True, case_insensitive = True)
	async def adventure_stats(self, ctx):
		'''Stats'''
		player = self.get_adventure_player(ctx.author.id)
		await ctx.embed_reply(f":fishing_pole_and_fish: Fishing xp: {player.fishing_xp:,} (Level {player.fishing_lvl:,})\n"
								f":herb: Foraging xp: {player.foraging_xp:,} (Level {player.foraging_lvl:,})\n"
								f":pick: Mining xp: {player.mining_xp:,} (Level {player.mining_lvl:,})\n"
								f":evergreen_tree: Woodcutting xp: {player.woodcutting_xp:,} (Level {player.woodcutting_lvl:,})")
		# time started/played
	
	@adventure_stats.command(name = "woodcutting", aliases = ["wc"])
	async def stats_woodcutting(self, ctx):
		'''Woodcutting stats'''
		player = self.get_adventure_player(ctx.author.id)
		woodcutting_xp = player.woodcutting_xp
		await ctx.embed_reply(f":evergreen_tree: Woodcutting xp: {woodcutting_xp:,}\n"
								f"{self.level_bar(woodcutting_xp)}\n"
								f"{adventure.xp_left_to_next_lvl(woodcutting_xp):,} xp to next level")
	
	@adventure_stats.command(name = "foraging", aliases = ["forage", "gather", "gathering"])
	async def stats_foraging(self, ctx):
		'''Foraging stats'''
		player = self.get_adventure_player(ctx.author.id)
		foraging_xp = player.foraging_xp
		await ctx.embed_reply(f":herb: Foraging xp: {foraging_xp:,}\n"
								f"{self.level_bar(foraging_xp)}\n"
								f"{adventure.xp_left_to_next_lvl(foraging_xp):,} xp to next level")
	
	def level_bar(self, xp):
		lvl = adventure.xp_to_lvl(xp)
		previous_xp = adventure.lvl_to_xp(lvl)
		next_xp = adventure.lvl_to_xp(lvl + 1)
		difference = next_xp - previous_xp
		shaded = int((xp - previous_xp) / difference * 10)
		bar = '\N{BLACK SQUARE}' * shaded + '\N{WHITE SQUARE}' * (10 - shaded)
		return f"Level {lvl:,} ({previous_xp:,} xp) [{bar}] Level {lvl + 1:,} ({next_xp:,} xp)"
	
	@adventure.command(name = "inventory")
	async def adventure_inventory(self, ctx, *, item: str = ""):
		'''Inventory'''
		player = self.get_adventure_player(ctx.author.id)
		inventory = player.inventory
		if item in inventory:
			await ctx.embed_reply(f"{item}: {inventory[item]}")
		else:
			await ctx.embed_reply(", ".join(f"{item}: {amount:,}" for item, amount in sorted(inventory.items())))
	
	@adventure.command(name = "examine")
	async def adventure_examine(self, ctx, *, item: str):
		'''Examine items'''
		player = self.get_adventure_player(ctx.author.id)
		inventory = player.inventory
		if item not in inventory:
			return await ctx.embed_reply(":no_entry: You don't have that item")
		if item in adventure.examine_messages:
			await ctx.embed_reply(adventure.examine_messages[item])
		else:
			await ctx.embed_reply(item)
	
	@adventure.group(name = "forage", aliases = ["gather"], invoke_without_command = True, case_insensitive = True)
	async def adventure_forage(self, ctx, *, item: str = ""):
		'''Foraging'''
		player = self.get_adventure_player(ctx.author.id)
		started = player.start_foraging(item)
		if started == "foraging":
			stopped = player.stop_foraging()
			output = (f":herb: You were foraging {stopped[0]} for {stopped[1]:,.2f} min. and received {stopped[2]:,} {stopped[0]} and xp.\n"
						f"While you were foraging, you also found {stopped[3]:,} {adventure.forageables[stopped[0]][0]}")
			if stopped[4]:
				output += f" and {stopped[4]:,} {adventure.forageables[stopped[0]][1]}!"
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
	
	@adventure_forage.command(name = "start", aliases = ["on"])
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
	
	@adventure_forage.command(name = "stop", aliases = ["off"])
	async def forage_stop(self, ctx):
		'''Stop foraging'''
		player = self.get_adventure_player(ctx.author.id)
		stopped = player.stop_foraging()
		if stopped[0]:
			output = (f":herb: You were foraging {stopped[0]} for {stopped[1]:,.2f} min. and received {stopped[2]:,} {stopped[0]} and xp.\n"
						f"While you were foraging, you also found {stopped[3]:,} {adventure.forageables[stopped[0]][0]}")
			if stopped[4]:
				output += f" and {stopped[4]:,} {adventure.forageables[stopped[0]][1]}!"
			await ctx.embed_reply(output)
		elif stopped[1]:
			await ctx.embed_reply(f":no_entry: You're currently {stopped[1][0]}! You aren't foraging right now")
		else:
			await ctx.embed_reply(":no_entry: You aren't foraging")
	
	@adventure_forage.command(name = "items", aliases = ["item", "type", "types"])
	async def forage_items(self, ctx):
		'''Forageable items'''
		await ctx.embed_reply(", ".join(adventure.forageables.keys()))
	
	@adventure.command(name = "create", aliases = ["make", "craft"])
	async def adventure_create(self, ctx, *items: str):
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
	
	@adventure.group(name = "chop", aliases = ["woodcutting", "wc"], invoke_without_command = True, case_insensitive = True)
	async def adventure_woodcutting(self, ctx, *, wood_type: str = ""):
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
	
	@adventure_woodcutting.command(name = "start", aliases = ["on"])
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
	
	@adventure_woodcutting.command(name = "stop", aliases = ["off"])
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
	
	@adventure_woodcutting.command(name = "types", aliases = ["type", "item", "items"])
	async def woodcutting_types(self, ctx):
		'''Types of wood'''
		await ctx.embed_reply(", ".join(adventure.wood_types))
	
	@adventure_woodcutting.command(name = "rate", aliases = ["rates"])
	async def woodcutting_rate(self, ctx, *, wood_type: str):
		'''Rate of chopping certain wood'''
		player = self.get_adventure_player(ctx.author.id)
		if wood_type in adventure.wood_types:
			await ctx.embed_reply(f"You will get {player.wood_rate(wood_type) * player.woodcutting_rate:.2f} {wood_type}/min. at your current level")
		else:
			await ctx.embed_reply(":no_entry: That wood type doesn't exist")

