
import discord
from discord.ext import commands

import pycountry

from utilities import checks

async def setup(bot):
	await bot.add_cog(Osu(bot))

class Osu(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.load_emoji()
	
	@commands.Cog.listener()
	async def on_ready(self):
		self.load_emoji()
	
	def load_emoji(self):
		# TODO: Check only within Emoji Server emojis?
		self.ssh_emoji = discord.utils.get(self.bot.emojis, name = "osu_ssh") or "SS+"
		self.ss_emoji = discord.utils.get(self.bot.emojis, name = "osu_ss") or "SS"
		self.sh_emoji = discord.utils.get(self.bot.emojis, name = "osu_sh") or "S:"
		self.s_emoji = discord.utils.get(self.bot.emojis, name = "osu_s") or 'S'
		self.a_emoji = discord.utils.get(self.bot.emojis, name = "osu_a") or 'A'
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(aliases = ["osu!"], invoke_without_command = True, case_insensitive = True)
	async def osu(self, ctx):
		'''osu!'''
		await ctx.send_help(ctx.command)
	
	@osu.group(invoke_without_command = True, case_insensitive = True)
	async def taiko(self, ctx):
		'''Taiko'''
		await ctx.send_help(ctx.command)
	
	@osu.group(invoke_without_command = True, case_insensitive = True)
	async def mania(self, ctx):
		'''osu!mania'''
		await ctx.send_help(ctx.command)
	
	@osu.command()
	async def user(self, ctx, *, user: str):
		'''General user information'''
		await self.get_user(ctx, user)
	
	@taiko.command(name = "user")
	async def taiko_user(self, ctx, *, user: str):
		'''General user information'''
		await self.get_user(ctx, user, 1)
	
	@mania.command(name = "user")
	async def mania_user(self, ctx, *, user: str):
		'''General user information'''
		await self.get_user(ctx, user, 2)
	
	async def get_user(self, ctx, user, mode = 0):
		url = "https://osu.ppy.sh/api/get_user"
		params = {'k': ctx.bot.OSU_API_KEY, 'u': user, 'm': mode}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if not data:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: User not found")
		data = data[0]
		title_url = f"https://osu.ppy.sh/users/{data['user_id']}"
		country_name = pycountry.countries.get(alpha_2 = data["country"]).name
		fields = (("Ranked Score", f"{int(data['ranked_score']):,}"), 
					("Hit Accuracy", f"{float(data['accuracy']):6g}%"), 
					("Play Count", data["playcount"]), ("Total Score", f"{int(data['total_score']):,}"), 
					("Performance", f"{float(data['pp_raw']):,}pp"), ("Rank", f"#{int(data['pp_rank']):,}"), 
					("Level", data["level"]), ("Country Rank", f"{country_name} #{int(data['pp_country_rank']):,}"), 
					("Total Hits", f"{int(data['count300']) + int(data['count100']) + int(data['count50']):,}"), 
					("300 Hits", f"{int(data['count300']):,}"), ("100 Hits", f"{int(data['count100']):,}"), 
					("50 Hits", f"{int(data['count50']):,}"), (self.ssh_emoji, data["count_rank_ssh"]), 
					(self.ss_emoji, data["count_rank_ss"]), (self.sh_emoji, data["count_rank_sh"]), 
					(self.s_emoji, data["count_rank_s"]), (self.a_emoji, data["count_rank_a"]))
		await ctx.embed_reply(title = data["username"], title_url = title_url, fields = fields)

