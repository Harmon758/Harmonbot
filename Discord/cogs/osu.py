
import discord
from discord.ext import commands

import pycountry

import clients
import credentials
from utilities import checks

def setup(bot):
	bot.add_cog(Osu(bot))

class Osu:
	
	def __init__(self, bot):
		self.bot = bot
		
		# TODO: Wait until ready
		
		# TODO: Check only within Emoji Server emojis?
		self.ssh_emoji = discord.utils.get(self.bot.emojis, name = "osu_ssh") or "SS+"
		self.ss_emoji = discord.utils.get(self.bot.emojis, name = "osu_ss") or "SS"
		self.sh_emoji = discord.utils.get(self.bot.emojis, name = "osu_sh") or "S:"
		self.s_emoji = discord.utils.get(self.bot.emojis, name = "osu_s") or 'S'
		self.a_emoji = discord.utils.get(self.bot.emojis, name = "osu_a") or 'A'
	
	@commands.group(aliases = ["osu!"], invoke_without_command = True)
	@checks.not_forbidden()
	async def osu(self, ctx):
		'''osu!'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@osu.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def taiko(self, ctx):
		'''Taiko'''
		await ctx.invoke(self.bot.get_command("help"), "osu", ctx.invoked_with)
	
	@osu.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def mania(self, ctx):
		'''osu!mania'''
		await ctx.invoke(self.bot.get_command("help"), "osu", ctx.invoked_with)
	
	@osu.command()
	@checks.not_forbidden()
	async def user(self, ctx, *, user : str):
		'''General user information'''
		await self.get_user(ctx, user)
	
	@taiko.command(name = "user")
	@checks.not_forbidden()
	async def taiko_user(self, ctx, *, user : str):
		'''General user information'''
		await self.get_user(ctx, user, 1)
	
	@mania.command(name = "user")
	@checks.not_forbidden()
	async def mania_user(self, ctx, *, user : str):
		'''General user information'''
		await self.get_user(ctx, user, 2)
	
	async def get_user(self, ctx, user, mode = 0):
		async with clients.aiohttp_session.get("https://osu.ppy.sh/api/get_user", params = {'k': credentials.osu_api_key, 'u': user, 'm': mode}) as resp:
			data = await resp.json()
		if not data:
			await ctx.embed_reply(":no_entry: Error: User not found")
			return
		data = data[0]
		await ctx.embed_reply(title = data["username"], title_url = "https://osu.ppy.sh/users/{}".format(data["user_id"]), fields = (("Ranked Score", "{:,}".format(int(data["ranked_score"]))), ("Hit Accuracy", data["accuracy"]), ("Play Count", data["playcount"]), ("Total Score", "{:,}".format(int(data["total_score"]))), ("Performance", "{:,}pp".format(float(data["pp_raw"]))), ("Rank", "#{:,}".format(int(data["pp_rank"]))), ("Level", data["level"]), ("Country Rank", "{} #{:,}".format(pycountry.countries.get(alpha_2 = data["country"]).name, int(data["pp_country_rank"]))), ("Total Hits", "{:,}".format(int(data["count300"]) + int(data["count100"]) + int(data["count50"]))), ("300 Hits", "{:,}".format(int(data["count300"]))), ("100 Hits", "{:,}".format(int(data["count100"]))), ("50 Hits", "{:,}".format(int(data["count50"]))), (self.ssh_emoji, data["count_rank_ssh"]), (self.ss_emoji, data["count_rank_ss"]), (self.sh_emoji, data["count_rank_sh"]), (self.s_emoji, data["count_rank_s"]), (self.a_emoji, data["count_rank_a"])))

