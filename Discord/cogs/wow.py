
import discord
from discord.ext import commands

import datetime

from utilities import checks

async def setup(bot):
	await bot.add_cog(WoW(bot))

class WoW(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(aliases = ["worldofwarcraft", "world_of_warcraft"], 
					invoke_without_command = True, case_insensitive = True)
	async def wow(self, ctx):
		'''World of Warcraft'''
		await ctx.send_help(ctx.command)
	
	@wow.command()
	async def character(self, ctx, character : str, *, realm : str):
		'''WIP'''
		# get classes
		classes = {}
		url = "https://us.api.battle.net/wow/data/character/classes"
		params = {"apikey": ctx.bot.BATTLE_NET_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		for wow_class in data["classes"]:
			classes[wow_class["id"]] = wow_class["name"]
		# get races
		races = {}
		url = "https://us.api.battle.net/wow/data/character/races"
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		for wow_race in data["races"]:
			races[wow_race["id"]] = wow_race["name"]
			# add side/faction?
		genders = {0: "Male", 1: "Female"}
		url = f"https://us.api.battle.net/wow/character/{realm}/{character}"
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
			if resp.status != 200:
				return await ctx.embed_reply(f":no_entry: Error: {data['reason']}")
		title_url = f"https://worldofwarcraft.com/en-us/character/{data['realm'].replace(' ', '-')}/{data['name']}"
		thumbnail_url = f"https://render-us.worldofwarcraft.com/character/{data['thumbnail']}"
		fields = [("Level", data["level"]), ("Achievement Points", data["achievementPoints"]), 
					("Class", f"{classes.get(data['class'], 'Unknown')}"), 
					("Race", races.get(data["race"], "Unknown")), 
					("Gender", genders.get(data["gender"], "Unknown"))]
		timestamp = datetime.datetime.utcfromtimestamp(data["lastModified"] / 1000.0)
		await ctx.embed_reply(f"{data['realm']} ({data['battlegroup']})", title = data["name"], 
								title_url = title_url, thumbnail_url = thumbnail_url, fields = fields, 
								footer_text = "Last seen", timestamp = timestamp)
		# faction and total honorable kills?
	
	@wow.command()
	async def statistics(self, ctx, character : str, *, realm : str):
		'''WIP'''
		url = f"https://us.api.battle.net/wow/character/{realm}/{character}"
		params = {"fields": "statistics", "apikey": ctx.bot.BATTLE_NET_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		statistics = data["statistics"]
		title_url = f"https://worldofwarcraft.com/en-us/character/{data['realm'].replace(' ', '-')}/{data['name']}/"
		# await ctx.embed_reply(f"{data['realm']} ({data['battlegroup']})", 
		# 						title = data["name"], title_url = title_url)

