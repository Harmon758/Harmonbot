
import discord
from discord.ext import commands

from utilities import checks

def setup(bot):
	bot.add_cog(RotMG(bot))

class RotMG(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(aliases = ["realmofthemadgod"], invoke_without_command = True, case_insensitive = True)
	async def rotmg(self, ctx, player : str):
		'''Realm of the Mad God player information'''
		url = "https://nightfirec.at/realmeye-api/?player={}".format(player)
		# http://webhost.ischool.uw.edu/~joatwood/realmeye_api/0.3/
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		if "error" in data:
			await ctx.embed_reply("Error: " + data["error"])
			return
		embed = discord.Embed(title = data["player"], url = "https://www.realmeye.com/player/{}".format(player), color = ctx.bot.bot_color)
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
		if data["donator"] == "true": embed.description = "Donator"
		embed.add_field(name = "Characters", value = data["chars"])
		embed.add_field(name = "Total Fame", value = "{:,}".format(data["fame"]))
		embed.add_field(name = "Fame Rank", value = "{:,}".format(data["fame_rank"]))
		embed.add_field(name = "Class Quests Completed", value = data["rank"])
		embed.add_field(name = "Account Fame", value = "{:,}".format(data["account_fame"]))
		embed.add_field(name = "Account Fame Rank", value = "{:,}".format(data["account_fame_rank"]))
		if created := data.get("created"):
			embed.add_field(name = "Created", value = created)
		embed.add_field(name = "Total Exp", value = "{:,}".format(data["exp"]))
		embed.add_field(name = "Exp Rank", value = "{:,}".format(data["exp_rank"]))
		embed.add_field(name = "Last Seen", value = data["player_last_seen"])
		if guild := data.get("guild"):
			embed.add_field(name = "Guild", value = guild)
			embed.add_field(name = "Guild Position", value = data["guild_rank"])
		if data["desc1"] or data["desc2"] or data["desc3"]:
			embed.add_field(name = "Description", value = "{}\n{}\n{}".format(data["desc1"], data["desc2"], data["desc3"]))
		await ctx.send(embed = embed)
	
	@rotmg.command(name = "characters")
	async def rotmg_characters(self, ctx, player : str):
		'''Realm of the Mad God player characters information'''
		url = "https://nightfirec.at/realmeye-api/?player={}".format(player)
		# http://webhost.ischool.uw.edu/~joatwood/realmeye_api/0.3/
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		if "error" in data:
			await ctx.embed_reply("Error: " + data["error"])
			return
		embed = discord.Embed(title = "{}'s Characters".format(data["player"]), color = ctx.bot.bot_color)
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
		for character in data["characters"]:
			value = "Fame: {0[fame]:,}, Exp: {0[exp]:,}, Rank: {0[place]:,}, Class Quests Completed: {0[cqc]}, Stats Maxed: {0[stats_maxed]}".format(character)
			value += "\nHP: {0[hp]}, MP: {0[mp]}, Attack: {0[attack]}, Defense: {0[defense]}, Speed: {0[speed]}, Vitality: {0[vitality]}, Wisdom: {0[wisdom]}, Dexterity: {0[dexterity]}".format(character["stats"])
			equips = []
			for type, equip in character["equips"].items():
				equips.append("{}: {}".format(type.capitalize(), equip))
			value += '\n' + ", ".join(equips)
			value += "\nPet: {0[pet]}, Clothing Dye: {0[character_dyes][clothing_dye]}, Accessory Dye: {0[character_dyes][accessory_dye]}, Backpack: {0[backpack]}".format(character)
			value += "\nLast Seen: {0[last_seen]}, Last Server: {0[last_server]}".format(character)
			embed.add_field(name = "Level {0[level]} {0[class]}".format(character), value = value, inline = False)
		await ctx.send(embed = embed)

