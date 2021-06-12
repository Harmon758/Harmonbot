
import discord
from discord.ext import commands

from utilities import checks

def setup(bot):
	bot.add_cog(Overwatch(bot))

class Overwatch(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.request_limit = 1000
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	async def overwatch(self, ctx):
		'''BattleTags are case sensitive'''
		await ctx.send_help(ctx.command)
	
	# TODO: Finish Stats (Add Achievements, Improve)
	# TODO: Maps, Items
	
	@overwatch.command(name = "ability", aliases = ["weapon"])
	async def overwatch_ability(self, ctx, *, ability : str):
		'''Abilities/Weapons'''
		url = "https://overwatch-api.net/api/v1/ability"
		async with ctx.bot.aiohttp_session.get(url, params = {"limit": self.request_limit}) as resp:
			data = await resp.json()
		data = data["data"]
		ability_data = discord.utils.find(lambda a: a["name"].lower() == ability.lower(), data)
		if not ability_data:
			await ctx.embed_reply(":no_entry: Error: Ability not found")
			return
		fields = (("Hero", ability_data["hero"]["name"]), ("Ultimate", ability_data["is_ultimate"]))
		await ctx.embed_reply(ability_data["description"], title = ability_data["name"], fields = fields)
	
	@overwatch.command(name = "achievement")
	async def overwatch_achievement(self, ctx, *, achievement : str):
		'''Achievements'''
		url = "https://overwatch-api.net/api/v1/achievement"
		async with ctx.bot.aiohttp_session.get(url, params = {"limit": self.request_limit}) as resp:
			data = await resp.json()
		data = data["data"]
		achievement_data = discord.utils.find(lambda a: a["name"].lower() == achievement.lower(), data)
		if not achievement_data:
			await ctx.embed_reply(":no_entry: Error: Achievement not found")
			return
		fields = [("Reward", (achievement_data["reward"]["name"] + " " + 
								achievement_data["reward"]["type"]["name"]))]
		if achievement_data["hero"]:
			fields.append(("Hero", achievement_data["hero"]["name"]))
		await ctx.embed_reply(achievement_data["description"], title = achievement_data["name"], 
								fields = fields)
	
	@overwatch.command(name = "hero")
	async def overwatch_hero(self, ctx, *, hero : str):
		'''Heroes'''
		url = "https://overwatch-api.net/api/v1/hero"
		async with ctx.bot.aiohttp_session.get(url, params = {"limit": self.request_limit}) as resp:
			data = await resp.json()
		data = data["data"]
		hero_data = discord.utils.find(lambda h: h["name"].lower() == hero.lower(), data)
		if not hero_data:
			await ctx.embed_reply(":no_entry: Error: Hero not found")
			return
		fields = [("Health", hero_data["health"]), ("Armor", hero_data["armour"]), 
					("Shield", hero_data["shield"]), ("Real Name", hero_data["real_name"])]
		for field in ("age", "height", "affiliation", "base_of_operations"):
			if hero_data.get(field):
				fields.append((field.replace('_', ' ').title(), hero_data[field]))
		fields.append(("Difficulty", '★' * hero_data["difficulty"] + '☆' * (3 - hero_data["difficulty"]), False))
		await ctx.embed_reply(hero_data["description"], title = hero_data["name"], fields = fields)
	
	@overwatch.command()
	async def item(self, ctx, *, item : str):
		'''
		WIP
		Items
		'''
		...
	
	@overwatch.command()
	async def map(self, ctx, *, map : str):
		'''
		WIP
		Maps
		'''
		...
	
	@overwatch.group(name = "stats", aliases = ["statistics"], 
						invoke_without_command = True, case_insensitive = True)
	async def stats(self, ctx, battletag : str):
		'''
		WIP
		Player statistics
		BattleTags are case sensitive
		'''
		url = "https://owapi.net/api/v3/u/{}/stats".format(battletag.replace('#', '-'))
		async with ctx.bot.aiohttp_session.get(url, headers = {"User-Agent": ctx.bot.user_agent}) as resp:
			data = await resp.json()
		if "error" in data:
			await ctx.embed_reply(":no_entry: Error: `{}`".format(data.get("msg")))
			return
		for region in ("eu", "kr", "us"):
			if data.get(region):
				stats = data[region]["stats"]["quickplay"]
				embed = discord.Embed(title = battletag, color = ctx.bot.bot_color)
				embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar.url)
				embed.set_thumbnail(url = stats["overall_stats"]["avatar"])
				embed.add_field(name = "Level", value = stats["overall_stats"]["level"])
				embed.add_field(name = "Prestige", value = stats["overall_stats"]["prestige"])
				embed.add_field(name = "Rank", value = stats["overall_stats"]["comprank"])
				'''
				output.append("**Wins/Total**: {0[wins]}/{0[games]} ({1:g}%)".format(data["overall_stats"], 100 * data["overall_stats"]["wins"] / data["overall_stats"]["wins"] + data["overall_stats"]["losses"]))
				output.append("**Eliminations/Deaths**: {0[kpd]}, **Time Spent On Fire**: {0[time_spent_on_fire]:.2f}".format(data["game_stats"]))
				output.append("__Most In One Game__ | **Time Spent On Fire**: {0[time_spent_on_fire_most_in_game]:.2f}".format(data["game_stats"]))
				'''
				await ctx.send(embed = embed)
	
	@stats.group(name = "quickplay", aliases = ["qp"], 
					invoke_without_command = True, case_insensitive = True)
	async def stats_quickplay(self, ctx, battletag : str):
		'''
		Quick Play player statistics
		BattleTags are case sensitive
		'''
		url = "https://owapi.net/api/v3/u/{}/stats".format(battletag.replace('#', '-'))
		async with ctx.bot.aiohttp_session.get(url, headers = {"User-Agent": ctx.bot.user_agent}) as resp:
			data = await resp.json()
		if "error" in data:
			await ctx.embed_reply(":no_entry: Error: `{}`".format(data.get("msg")))
			return
		for region in ("eu", "kr", "us"):
			if data.get(region):
				stats = data[region]["stats"]["quickplay"]
				embed = discord.Embed(title = "{} ({})".format(battletag, region.upper()), color = ctx.bot.bot_color)
				embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar.url)
				embed.set_thumbnail(url = stats["overall_stats"]["avatar"])
				embed.add_field(name = "Level", value = stats["overall_stats"]["level"])
				embed.add_field(name = "Prestige", value = stats["overall_stats"]["prestige"])
				embed.add_field(name = "Wins", value = "{:,g}".format(stats["overall_stats"]["wins"]))
				embed.add_field(name = "Time Played", value = "{:,g}h".format(stats["game_stats"]["time_played"]))
				embed.add_field(name = "Cards", value = "{:,g}".format(stats["game_stats"]["cards"]))
				embed.add_field(name = "Medals", value = ":medal: {0[medals]:,g} total\n:first_place_medal: {0[medals_gold]:,g} gold\n:second_place_medal: {0[medals_silver]:,g} silzer\n:third_place_medal: {0[medals_bronze]:,g} bronze".format(stats["game_stats"]))
				embed.add_field(name = "Eliminations", value = "{:,g} highest in one game\n{:,g} average".format(stats["game_stats"]["eliminations_most_in_game"], stats["average_stats"].get("eliminations_avg", -1)))
				embed.add_field(name = "Objective Kills", value = "{:,g} highest in one game\n{:,g} average".format(stats["game_stats"]["objective_kills_most_in_game"], stats["average_stats"].get("objective_kills_avg", -1)))
				embed.add_field(name = "Objective Time", value = "{:.2f}m highest in one game\n{:.2f}m average".format(stats["game_stats"]["objective_time_most_in_game"] * 60, stats["average_stats"].get("objective_time_avg", -1) * 60))
				embed.add_field(name = "Hero Damage Done", value = "{:,g} highest in one game\n{:,g} average".format(stats["game_stats"]["hero_damage_done_most_in_game"], stats["average_stats"].get("damage_done_avg", -1)))
				embed.add_field(name = "Healing Done", value = "{:,g} highest in one game\n{:,g} average".format(stats["game_stats"]["healing_done_most_in_game"], stats["average_stats"].get("healing_done_avg", -1)))
				embed.add_field(name = "Deaths", value = "{:,g} total\n{:,g} average".format(stats["game_stats"]["deaths"], stats["average_stats"].get("deaths_avg", -1)))
				await ctx.send(embed = embed)
	
	@stats.group(name = "competitive", aliases = ["comp"], 
					invoke_without_command = True, case_insensitive = True)
	async def stats_competitive(self, ctx, battletag : str):
		'''
		Competitive player statistics
		BattleTags are case sensitive
		'''
		url = "https://owapi.net/api/v3/u/{}/stats".format(battletag.replace('#', '-'))
		async with ctx.bot.aiohttp_session.get(url, headers = {"User-Agent": ctx.bot.user_agent}) as resp:
			data = await resp.json()
		if "error" in data:
			await ctx.embed_reply(":no_entry: Error: `{}`".format(data.get("msg")))
			return
		for region in ("eu", "kr", "us"):
			if data.get(region):
				stats = data[region]["stats"]["competitive"]
				embed = discord.Embed(title = "{} ({})".format(battletag, region.upper()), color = ctx.bot.bot_color)
				embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar.url)
				embed.set_thumbnail(url = stats["overall_stats"]["avatar"])
				embed.add_field(name = "Level", value = stats["overall_stats"]["level"])
				embed.add_field(name = "Prestige", value = stats["overall_stats"]["prestige"])
				embed.add_field(name = "Wins", value = "{:,g}".format(stats["overall_stats"]["wins"]))
				embed.add_field(name = "Time Played", value = "{:,g}h".format(stats["game_stats"]["time_played"]))
				embed.add_field(name = "Cards", value = "{:,g}".format(stats["game_stats"]["cards"]))
				embed.add_field(name = "Medals", value = ":medal: {0[medals]:,g} total\n:first_place_medal: {0[medals_gold]:,g} gold\n:second_place_medal: {0[medals_silver]:,g} silzer\n:third_place_medal: {0[medals_bronze]:,g} bronze".format(stats["game_stats"]))
				embed.add_field(name = "Eliminations", value = "{:,g} highest in one game\n{:,g} average".format(stats["game_stats"]["eliminations_most_in_game"], stats["average_stats"]["eliminations_avg"]))
				embed.add_field(name = "Objective Kills", value = "{:,g} highest in one game\n{:,g} average".format(stats["game_stats"]["objective_kills_most_in_game"], stats["average_stats"]["objective_kills_avg"]))
				embed.add_field(name = "Objective Time", value = "{:.2f}m highest in one game\n{:.2f}m average".format(stats["game_stats"]["objective_time_most_in_game"] * 60, stats["average_stats"]["objective_time_avg"] * 60))
				embed.add_field(name = "Damage Done", value = "{:,g} highest in one game\n{:,g} average".format(stats["game_stats"]["damage_done_most_in_game"], stats["average_stats"]["damage_done_avg"]))
				embed.add_field(name = "Healing Done", value = "{:,g} highest in one game\n{:,g} average".format(stats["game_stats"]["healing_done_most_in_game"], stats["average_stats"]["healing_done_avg"]))
				embed.add_field(name = "Deaths", value = "{:,g} total\n{:,g} average".format(stats["game_stats"]["deaths"], stats["average_stats"]["deaths_avg"]))
				await ctx.send(embed = embed)
	
	@stats_quickplay.command(name = "heroes")
	async def stats_quickplay_heroes(self, ctx, battletag : str):
		'''
		Quick Play player hero statistics
		BattleTags are case sensitive
		'''
		url = "https://owapi.net/api/v3/u/{}/heroes".format(battletag.replace('#', '-'))
		async with ctx.bot.aiohttp_session.get(url, headers = {"User-Agent": ctx.bot.user_agent}) as resp:
			data = await resp.json()
		if "error" in data:
			await ctx.embed_reply(":no_entry: Error: `{}`".format(data.get("msg")))
			return
		for region in ("eu", "kr", "us"):
			if data.get(region):
				output = ["", "__{}__".format(battletag.replace('-', '#'))]
				sorted_data = sorted(data[region]["heroes"]["playtime"]["quickplay"].items(), key = lambda h: h[1], reverse = True)
				for hero, time in sorted_data:
					if time >= 1:
						output.append("**{}**: {:g} {}".format(hero.capitalize(), time, ctx.bot.inflect_engine.plural("hour", int(time))))
					else:
						output.append("**{}**: {:g} {}".format(hero.capitalize(), time * 60, ctx.bot.inflect_engine.plural("minute", int(time * 60))))
				await ctx.embed_reply('\n'.join(output))

