
import discord
from discord.ext import commands

import collections
import csv

import clients
from utilities import checks

def setup(bot):
	bot.add_cog(Runescape(bot))

class Runescape:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.group(aliases = ["rs"], invoke_without_command = True)
	@checks.not_forbidden()
	async def runescape(self, ctx):
		'''Runescape'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@runescape.command(aliases = ["grandexchange", "grand_exchange"])
	@checks.not_forbidden()
	async def ge(self, ctx, *, item):
		'''Grand Exchange'''
		# https://runescape.wiki/w/Application_programming_interface#Grand_Exchange_Database_API
		# https://www.mediawiki.org/wiki/API:Opensearch
		# TODO: Handle redirects?
		async with clients.aiohttp_session.get("https://runescape.wiki/api.php", params = {"action": "opensearch", "search": item}) as resp:
			data = await resp.json()
		if not data[1]:
			await ctx.embed_reply(":no_entry: Item not found")
			return
		for i in data[1]:
			# https://www.semantic-mediawiki.org/wiki/Help:Ask
			# https://www.semantic-mediawiki.org/wiki/Help:Inline_queries
			async with clients.aiohttp_session.get("https://runescape.wiki/api.php", params = {"action": "ask", "query": f"[[{i}]]|?Item_ID", "format": "json"}) as resp:
				data = await resp.json()
			item_id = list(data["query"]["results"].values())[0]["printouts"]["Item ID"]
			if item_id:
				item = i
				item_id = item_id[0]
				break
		if not item_id:
			await ctx.embed_reply(f":no_entry: {item} is not an item")
			return
		async with clients.aiohttp_session.get("https://services.runescape.com/m=itemdb_rs/api/catalogue/detail.json", params = {"item": item_id}) as resp:
			if resp.status == 404:
				await ctx.embed_reply(f":no_entry: Error: {item} not found on the Grand Exchange")
				return
			data = await resp.json(content_type = "text/html")
		data = data["item"]
		await ctx.embed_reply(data["description"], title = data["name"], title_url = f"https://services.runescape.com/m=itemdb_rs/viewitem?obj={item_id}", thumbnail_url = data["icon_large"], fields = (("Current", data["current"]["price"]), ("Today", data["today"]["price"]), ("30 Day", data["day30"]["change"]), ("90 Day", data["day90"]["change"]), ("180 Day", data["day180"]["change"]), ("Category", data["type"])))
		# id?, members
	
	@runescape.command(aliases = ["bestiary"])
	@checks.not_forbidden()
	async def monster(self, ctx, *, monster : str):
		'''Bestiary'''
		url = "http://services.runescape.com/m=itemdb_rs/bestiary/beastSearch.json?term={}".format(monster.replace(' ', '+'))
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json(content_type = "text/html")
		if data[0] == "none":
			await ctx.embed_reply(":no_entry: Monster not found")
			return
		url = "http://services.runescape.com/m=itemdb_rs/bestiary/beastData.json?beastid={}".format(data[0]["value"])
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json(content_type = "text/html")
		await ctx.embed_reply(data["description"], title = data["name"], fields = (("Level", data["level"]), ("Weakness", data["weakness"]), ("XP/Kill", data["xp"]), ("Lifepoints", data["lifepoints"]), ("Members", "Yes" if data["members"] else "No"), ("Aggressive", "Yes" if data["aggressive"] else "No")))
		# add other? - http://runescape.wikia.com/wiki/RuneScape_Bestiary#beastData
	
	@runescape.command(aliases = ["levels", "level", "xp", "ranks", "rank"])
	@checks.not_forbidden()
	async def stats(self, ctx, *, username : str):
		'''Stats'''
		async with clients.aiohttp_session.get("http://services.runescape.com/m=hiscore/index_lite.ws?player={}".format(username.replace(' ', '+'))) as resp:
			if resp.status == 404:
				await ctx.embed_reply(":no_entry: Player not found")
				return
			data = await resp.text()
		data = csv.DictReader(data.splitlines(), fieldnames = ("rank", "level", "xp"))
		stats = collections.OrderedDict()
		stats_names = ("Overall", "Attack", "Defence", "Strength", "Constitution", "Ranged", "Prayer", "Magic", "Cooking", "Woodcutting", "Fletching", "Fishing", "Firemaking", "Crafting", "Smithing", "Mining", "Herblore", "Agility", "Thieving", "Slayer", "Farming", "Runecrafting", "Hunter", "Construction", "Summoning", "Dungeoneering", "Divination", "Invention")
		for stat in stats_names:
			stats[stat] = next(data)
		embed = discord.Embed(title = username, url = "http://services.runescape.com/m=hiscore/compare?user1={}".format(username.replace(' ', '+')), color = ctx.bot.bot_color)
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)

		output = ["`{}`".format(name) for name in stats_names]
		embed.add_field(name = "Skill", value = '\n'.join(output))
		
		max_length = max([len("{:,d}".format(int(values["rank"]))) for values in stats.values()])
		output = ["`| {}`".format("{:,d}".format(int(values["rank"])).rjust(max_length)) for values in stats.values()]
		embed.add_field(name = "| Rank", value = '\n'.join(output))
		
		max_length = max([len("{:,d}".format(int(values["xp"]))) for values in stats.values()])
		output = ["`| {}| {}`".format(values["level"].rjust(4).ljust(5), "{:,d}".format(int(values["xp"])).rjust(max_length)) for values in stats.values()]
		embed.add_field(name = "| Level | Experience", value = '\n'.join(output))
		
		await ctx.send(embed = embed)
	
	@runescape.command()
	@checks.not_forbidden()
	async def wiki(self, ctx):
		'''WIP'''
		...
	
	@runescape.command(hidden = True)
	@checks.not_forbidden()
	async def zybez(self, ctx):
		'''
		This command has been deprecated
		Zybez RuneScape Community was shut down on September 17th, 2018
		https://forums.zybez.net/topic/1783583-exit-post-the-end/
		'''
		# Previously used https://forums.zybez.net/runescape-2007-prices/api/?info
		await ctx.embed_reply("See https://forums.zybez.net/topic/1783583-exit-post-the-end/")

