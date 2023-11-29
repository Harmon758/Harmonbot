
import discord
from discord.ext import commands

from utilities import checks

async def setup(bot):
	await bot.add_cog(RotMG(bot))

class RotMG(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(
		aliases = ["realmofthemadgod"],
		case_insensitive = True, invoke_without_command = True
	)
	async def rotmg(self, ctx, player: str):
		'''Realm of the Mad God player information'''
		# http://webhost.ischool.uw.edu/~joatwood/realmeye_api/0.3/
		async with ctx.bot.aiohttp_session.get(
			"https://nightfirec.at/realmeye-api/",
			params = {"player": player}
		) as resp:
			data = await resp.json()
		
		if "error" in data:
			await ctx.embed_reply("Error: " + data["error"])
			return
		
		fields = [
			("Characters", data["chars"]),
			("Total Fame", f"{data['fame']:,}"),
			("Fame Rank", f"{data['fame_rank']:,}"),
			("Class Quests Completed", data["rank"]),
			("Account Fame", f"{data['account_fame']:,}"),
			("Account Fame Rank", f"{data['account_fame_rank']:,}")
		]
		if created := data.get("created"):
			fields.append(("Created", created))
		fields.extend((
			("Total Exp", f"{data['exp']:,}"),
			("Exp Rank", f"{data['exp_rank']:,}"),
			("Last Seen", data["player_last_seen"])
		))
		if guild := data.get("guild"):
			fields.extend((
				("Guild", guild),
				("Guild Position", data["guild_rank"])
			))
		if data["desc1"] or data["desc2"] or data["desc3"]:
			fields.append((
				"Description",
				f"{data['desc1']}\n{data['desc2']}\n{data['desc3']}"
			))
		await ctx.embed_reply(
			title = data["player"],
			title_url = f"https://www.realmeye.com/player/{player}",
			description = "Donator" if data["donator"] == "true" else None,
			fields = fields
		)
	
	@rotmg.command(name = "characters")
	async def rotmg_characters(self, ctx, player : str):
		'''Realm of the Mad God player characters information'''
		url = "https://nightfirec.at/realmeye-api/"
		# http://webhost.ischool.uw.edu/~joatwood/realmeye_api/0.3/
		async with ctx.bot.aiohttp_session.get(
			url, params = {"player": player}
		) as resp:
			data = await resp.json()
		if "error" in data:
			await ctx.embed_reply("Error: " + data["error"])
			return
		embed = discord.Embed(title = f"{data['player']}'s Characters", color = ctx.bot.bot_color)
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.display_avatar.url)
		for character in data["characters"]:
			value = "Fame: {0[fame]:,}, Exp: {0[exp]:,}, Rank: {0[place]:,}, Class Quests Completed: {0[cqc]}, Stats Maxed: {0[stats_maxed]}".format(character)
			value += "\nHP: {0[hp]}, MP: {0[mp]}, Attack: {0[attack]}, Defense: {0[defense]}, Speed: {0[speed]}, Vitality: {0[vitality]}, Wisdom: {0[wisdom]}, Dexterity: {0[dexterity]}".format(character["stats"])
			equips = []
			for type, equip in character["equips"].items():
				equips.append(f"{type.capitalize()}: {equip}")
			value += '\n' + ", ".join(equips)
			value += "\nPet: {0[pet]}, Clothing Dye: {0[character_dyes][clothing_dye]}, Accessory Dye: {0[character_dyes][accessory_dye]}, Backpack: {0[backpack]}".format(character)
			value += f"\nLast Seen: {character['last_seen']}, Last Server: {character['last_server']}"
			embed.add_field(name = f"Level {character['level']} {character['class']}", value = value, inline = False)
		await ctx.send(embed = embed)

