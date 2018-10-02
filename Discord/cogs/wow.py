
import discord
from discord.ext import commands

import datetime

import clients
import credentials
from utilities import checks

def setup(bot):
	bot.add_cog(WoW(bot))

class WoW:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.group(aliases = ["worldofwarcraft", "world_of_warcraft"], invoke_without_command = True)
	@checks.not_forbidden()
	async def wow(self, ctx):
		'''World of Warcraft'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@wow.command()
	@checks.not_forbidden()
	async def character(self, ctx, character : str, *, realm : str):
		'''WIP'''
		# get classes
		classes = {}
		async with clients.aiohttp_session.get("https://us.api.battle.net/wow/data/character/classes", params = {"apikey": ctx.bot.BATTLE_NET_API_KEY}) as resp:
			data = await resp.json()
		for wow_class in data["classes"]:
			classes[wow_class["id"]] = wow_class["name"]
		# get races
		races = {}
		async with clients.aiohttp_session.get("https://us.api.battle.net/wow/data/character/races", params = {"apikey": ctx.bot.BATTLE_NET_API_KEY}) as resp:
			data = await resp.json()
		for wow_race in data["races"]:
			races[wow_race["id"]] = wow_race["name"]
			# add side/faction?
		genders = {0: "Male", 1: "Female"}
		async with clients.aiohttp_session.get(f"https://us.api.battle.net/wow/character/{realm}/{character}", params = {"apikey": ctx.bot.BATTLE_NET_API_KEY}) as resp:
			data = await resp.json()
			if resp.status != 200:
				await ctx.embed_reply(f":no_entry: Error: {data['reason']}")
				return
		embed = discord.Embed(title = data["name"], url = f"http://us.battle.net/wow/en/character/{data['realm'].replace(' ', '-')}/{data['name']}/", description = f"{data['realm']} ({data['battlegroup']})", color = ctx.bot.bot_color)
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
		embed.add_field(name = "Level", value = data["level"])
		embed.add_field(name = "Achievement Points", value = data["achievementPoints"])
		embed.add_field(name = "Class", value = f"{classes.get(data['class'], 'Unknown')}\n[Talent Calculator](http://us.battle.net/wow/en/tool/talent-calculator#{data['calcClass']})")
		embed.add_field(name = "Race", value = races.get(data["race"], "Unknown"))
		embed.add_field(name = "Gender", value = genders.get(data["gender"], "Unknown"))
		embed.set_thumbnail(url = f"http://render-us.worldofwarcraft.com/character/{data['thumbnail']}")
		embed.set_footer(text = "Last seen")
		embed.timestamp = datetime.datetime.utcfromtimestamp(data["lastModified"] / 1000.0)
		await ctx.send(embed = embed)
		# faction and total honorable kills?
	
	@wow.command()
	@checks.not_forbidden()
	async def statistics(self, ctx, character : str, *, realm : str):
		'''WIP'''
		async with clients.aiohttp_session.get("https://us.api.battle.net/wow/character/{}/{}?fields=statistics&apikey={}".format(realm, character, ctx.bot.BATTLE_NET_API_KEY)) as resp:
			data = await resp.json()
		embed = discord.Embed(title = data["name"], url = "http://us.battle.net/wow/en/character/{}/{}/".format(data["realm"].replace(' ', '-'), data["name"]), description = "{} ({})".format(data["realm"], data["battlegroup"]), color = ctx.bot.bot_color)
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
		statistics = data["statistics"]

