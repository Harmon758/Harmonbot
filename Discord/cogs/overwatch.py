
import discord
from discord.ext import commands

from utilities import checks

async def setup(bot):
	await bot.add_cog(Overwatch(bot))

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
	
	@overwatch.command(aliases = ["weapon"], hidden = True)
	async def ability(self, ctx):
		'''
		Overwatch Abilities/Weapons
		Deprecated, as the API this command used to use does not exist anymore
		https://overwatch-api.net/
		https://github.com/jamesmcfadden/overwatch-api
		'''
		await ctx.send_help(ctx.command)
	
	@overwatch.command(name = "achievement", hidden = True)
	async def overwatch_achievement(self, ctx):
		'''
		Overwatch Achievements
		Deprecated, as the API this command used to use does not exist anymore
		https://overwatch-api.net/
		https://github.com/jamesmcfadden/overwatch-api
		'''
		await ctx.send_help(ctx.command)
	
	@overwatch.command(name = "hero")
	async def overwatch_hero(self, ctx, *, hero : str):
		'''Heroes'''
		url = "https://overwatch-api.net/api/v1/hero"
		async with ctx.bot.aiohttp_session.get(url, params = {"limit": self.request_limit}) as resp:
			data = await resp.json()
		data = data["data"]
		hero_data = discord.utils.find(lambda h: h["name"].lower() == hero.lower(), data)
		if not hero_data:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Hero not found")
			return
		fields = [("Health", hero_data["health"]), ("Armor", hero_data["armour"]), 
					("Shield", hero_data["shield"]), ("Real Name", hero_data["real_name"])]
		for field in ("age", "height", "affiliation", "base_of_operations"):
			if hero_data.get(field):
				fields.append((field.replace('_', ' ').title(), hero_data[field]))
		fields.append(("Difficulty", '★' * hero_data["difficulty"] + '☆' * (3 - hero_data["difficulty"]), False))
		await ctx.embed_reply(hero_data["description"], title = hero_data["name"], fields = fields)
	
	@overwatch.command(hidden = True)
	async def item(self, ctx):
		'''
		Overwatch Items
		Deprecated, as the API this command used to use does not exist anymore
		https://overwatch-api.net/
		https://github.com/jamesmcfadden/overwatch-api
		'''
		await ctx.send_help(ctx.command)
	
	@overwatch.command(hidden = True)
	async def map(self, ctx):
		'''
		Overwatch Maps
		Deprecated, as the API this command used to use does not exist anymore
		https://overwatch-api.net/
		https://github.com/jamesmcfadden/overwatch-api
		'''
		await ctx.send_help(ctx.command)
	
	@overwatch.group(name = "stats", aliases = ["statistics"], 
						invoke_without_command = True, case_insensitive = True)
	async def stats(self, ctx, battletag : str):
		'''
		WIP
		Player statistics
		BattleTags are case sensitive
		'''
		url = f"https://owapi.net/api/v3/u/{battletag.replace('#', '-')}/stats"
		async with ctx.bot.aiohttp_session.get(url, headers = {"User-Agent": ctx.bot.user_agent}) as resp:
			data = await resp.json()
		if "error" in data:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: `{data.get('msg')}`")
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
				output.append(f"**Wins/Total**: {data['overall_stats']['wins']}/{data['overall_stats']['games']} ({100 * data['overall_stats']['wins'] / data['overall_stats']['wins'] + data['overall_stats']['losses']:g}%)")
				output.append(f"**Eliminations/Deaths**: {data['game_stats']['kpd']}, **Time Spent On Fire**: {data['game_stats']['time_spent_on_fire']:.2f}")
				output.append(f"__Most In One Game__ | **Time Spent On Fire**: {data['game_stats']['time_spent_on_fire_most_in_game']:.2f}")
				'''
				await ctx.send(embed = embed)
	
	@stats.group(name = "quickplay", aliases = ["qp"], 
					invoke_without_command = True, case_insensitive = True)
	async def stats_quickplay(self, ctx, battletag : str):
		'''
		Quick Play player statistics
		BattleTags are case sensitive
		'''
		url = f"https://owapi.net/api/v3/u/{battletag.replace('#', '-')}/stats"
		async with ctx.bot.aiohttp_session.get(url, headers = {"User-Agent": ctx.bot.user_agent}) as resp:
			data = await resp.json()
		if "error" in data:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: `{data.get('msg')}`")
			return
		for region in ("eu", "kr", "us"):
			if data.get(region):
				stats = data[region]["stats"]["quickplay"]
				embed = discord.Embed(title = f"{battletag} ({region.upper()})", color = ctx.bot.bot_color)
				embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar.url)
				embed.set_thumbnail(url = stats["overall_stats"]["avatar"])
				embed.add_field(name = "Level", value = stats["overall_stats"]["level"])
				embed.add_field(name = "Prestige", value = stats["overall_stats"]["prestige"])
				embed.add_field(name = "Wins", value = f"{stats['overall_stats']['wins']:,g}")
				embed.add_field(name = "Time Played", value = f"{stats['game_stats']['time_played']:,g}h")
				embed.add_field(name = "Cards", value = f"{stats['game_stats']['cards']:,g}")
				embed.add_field(name = "Medals", value = f":medal: {stats['game_stats']['medals']:,g} total\n:first_place_medal: {stats['game_stats']['medals_gold']:,g} gold\n:second_place_medal: {stats['game_stats']['medals_silver']:,g} silzer\n:third_place_medal: {stats['game_stats']['medals_bronze']:,g} bronze")
				embed.add_field(name = "Eliminations", value = f"{stats['game_stats']['eliminations_most_in_game']:,g} highest in one game\n{stats['average_stats'].get('eliminations_avg', -1):,g} average")
				embed.add_field(name = "Objective Kills", value = f"{stats['game_stats']['objective_kills_most_in_game']:,g} highest in one game\n{stats['average_stats'].get('objective_kills_avg', -1):,g} average")
				embed.add_field(name = "Objective Time", value = f"{stats['game_stats']['objective_time_most_in_game'] * 60:.2f}m highest in one game\n{stats['average_stats'].get('objective_time_avg', -1) * 60:.2f}m average")
				embed.add_field(name = "Hero Damage Done", value = f"{stats['game_stats']['hero_damage_done_most_in_game']:,g} highest in one game\n{stats['average_stats'].get('damage_done_avg', -1):,g} average")
				embed.add_field(name = "Healing Done", value = f"{stats['game_stats']['healing_done_most_in_game']:,g} highest in one game\n{stats['average_stats'].get('healing_done_avg', -1):,g} average")
				embed.add_field(name = "Deaths", value = f"{stats['game_stats']['deaths']:,g} total\n{stats['average_stats'].get('deaths_avg', -1):,g} average")
				await ctx.send(embed = embed)
	
	@stats.group(name = "competitive", aliases = ["comp"], 
					invoke_without_command = True, case_insensitive = True)
	async def stats_competitive(self, ctx, battletag : str):
		'''
		Competitive player statistics
		BattleTags are case sensitive
		'''
		url = f"https://owapi.net/api/v3/u/{battletag.replace('#', '-')}/stats"
		async with ctx.bot.aiohttp_session.get(url, headers = {"User-Agent": ctx.bot.user_agent}) as resp:
			data = await resp.json()
		if "error" in data:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: `{data.get('msg')}`")
			return
		for region in ("eu", "kr", "us"):
			if data.get(region):
				stats = data[region]["stats"]["competitive"]
				embed = discord.Embed(title = f"{battletag} ({region.upper()})", color = ctx.bot.bot_color)
				embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar.url)
				embed.set_thumbnail(url = stats["overall_stats"]["avatar"])
				embed.add_field(name = "Level", value = stats["overall_stats"]["level"])
				embed.add_field(name = "Prestige", value = stats["overall_stats"]["prestige"])
				embed.add_field(name = "Wins", value = f"{stats['overall_stats']['wins']:,g}")
				embed.add_field(name = "Time Played", value = f"{stats['game_stats']['time_played']:,g}h")
				embed.add_field(name = "Cards", value = f"{stats['game_stats']['cards']:,g}")
				embed.add_field(name = "Medals", value = f":medal: {stats['game_stats']['medals']:,g} total\n:first_place_medal: {stats['game_stats']['medals_gold']:,g} gold\n:second_place_medal: {stats['game_stats']['medals_silver']:,g} silzer\n:third_place_medal: {stats['game_stats']['medals_bronze']:,g} bronze")
				embed.add_field(name = "Eliminations", value = f"{stats['game_stats']['eliminations_most_in_game']:,g} highest in one game\n{stats['average_stats']['eliminations_avg']:,g} average")
				embed.add_field(name = "Objective Kills", value = f"{stats['game_stats']['objective_kills_most_in_game']:,g} highest in one game\n{stats['average_stats']['objective_kills_avg']:,g} average")
				embed.add_field(name = "Objective Time", value = f"{stats['game_stats']['objective_time_most_in_game'] * 60:.2f}m highest in one game\n{stats['average_stats']['objective_time_avg'] * 60:.2f}m average")
				embed.add_field(name = "Damage Done", value = f"{stats['game_stats']['damage_done_most_in_game']:,g} highest in one game\n{stats['average_stats']['damage_done_avg']:,g} average")
				embed.add_field(name = "Healing Done", value = f"{stats['game_stats']['healing_done_most_in_game']:,g} highest in one game\n{stats['average_stats']['healing_done_avg']:,g} average")
				embed.add_field(name = "Deaths", value = f"{stats['game_stats']['deaths']:,g} total\n{stats['average_stats']['deaths_avg']:,g} average")
				await ctx.send(embed = embed)
	
	@stats_quickplay.command(name = "heroes")
	async def stats_quickplay_heroes(self, ctx, battletag : str):
		'''
		Quick Play player hero statistics
		BattleTags are case sensitive
		'''
		url = f"https://owapi.net/api/v3/u/{battletag.replace('#', '-')}/heroes"
		async with ctx.bot.aiohttp_session.get(url, headers = {"User-Agent": ctx.bot.user_agent}) as resp:
			data = await resp.json()
		if "error" in data:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: `{data.get('msg')}`")
			return
		for region in ("eu", "kr", "us"):
			if data.get(region):
				output = ["", f"__{battletag.replace('-', '#')}__"]
				sorted_data = sorted(data[region]["heroes"]["playtime"]["quickplay"].items(), key = lambda h: h[1], reverse = True)
				for hero, time in sorted_data:
					if time >= 1:
						output.append(f"**{hero.capitalize()}**: {time:g} {ctx.bot.inflect_engine.plural('hour', int(time))}")
					else:
						output.append(f"**{hero.capitalize()}**: {time * 60:g} {ctx.bot.inflect_engine.plural('minute', int(time * 60))}")
				await ctx.embed_reply('\n'.join(output))

