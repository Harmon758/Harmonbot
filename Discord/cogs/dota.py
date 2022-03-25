
import discord
from discord.ext import commands

import io

import pycountry
from wordcloud import WordCloud

from utilities import checks
from utilities.converters import SteamID32

async def setup(bot):
	await bot.add_cog(DotA())

class DotA(commands.Cog):
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(aliases = ["dota2"], invoke_without_command = True, case_insensitive = True)
	async def dota(self, ctx):
		'''Defense of the Ancients 2'''
		await ctx.send_help(ctx.command)
	
	# TODO: Add dota buff subcommand alias
	@commands.command()
	async def dotabuff(self, ctx, account: SteamID32):
		'''Get Dotabuff link'''
		await ctx.embed_reply(f"https://www.dotabuff.com/players/{account}")
	
	@dota.group(invoke_without_command = True, case_insensitive = True)
	async def player(self, ctx, account: SteamID32):
		'''DotA 2 player'''
		url = f"https://api.opendota.com/api/players/{account}"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		if "profile" not in data:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: DotA 2 profile not found")
		url = f"https://api.opendota.com/api/players/{account}/wl"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			wl_data = await resp.json()
		fields = [("Wins", wl_data["win"]), ("Losses", wl_data["lose"])]
		if wl_data["win"] or wl_data["lose"]:
			fields.append(("Wins/Losees", f"{wl_data['win'] / (wl_data['win'] + wl_data['lose']) * 100:.2f}%"))
		fields.append(("MMR Estimate", data["mmr_estimate"]["estimate"]))
		if data["rank_tier"]:
			fields.append(("Rank Tier", data["rank_tier"]))
		if data["profile"]["loccountrycode"]:
			fields.append(("Country", pycountry.countries.get(alpha_2 = data["profile"]["loccountrycode"]).name))
		await ctx.embed_reply(title = data["profile"]["personaname"], title_url = data["profile"]["profileurl"], 
								thumbnail_url = data["profile"]["avatarfull"], fields = fields)
	
	@player.group(name = "words", invoke_without_command = True, case_insensitive = True)
	async def player_words(self, ctx):
		'''Words said or read in all chat'''
		await ctx.send_help(ctx.command)
	
	@player_words.command(name = "said", invoke_without_command = True, case_insensitive = True)
	async def player_words_said(self, ctx, account: SteamID32):
		'''Word cloud of words said in all chat'''
		url = f"https://api.opendota.com/api/players/{account}/wordcloud"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		if not data["my_word_counts"]:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: No words found")
		word_cloud = WordCloud()
		word_cloud.fit_words(data["my_word_counts"])
		buffer = io.BytesIO()
		word_cloud.to_image().save(buffer, "PNG")
		buffer.seek(0)
		await ctx.embed_reply(file = discord.File(buffer, filename = "word_cloud.png"), 
								image_url = "attachment://word_cloud.png")
	
	@player_words.command(name = "read", invoke_without_command = True, case_insensitive = True)
	async def player_words_read(self, ctx, account: SteamID32):
		'''Word cloud of words read in all chat'''
		url = f"https://api.opendota.com/api/players/{account}/wordcloud"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		if not data["all_word_counts"]:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: No words found")
		word_cloud = WordCloud()
		word_cloud.fit_words(data["all_word_counts"])
		buffer = io.BytesIO()
		word_cloud.to_image().save(buffer, "PNG")
		buffer.seek(0)
		await ctx.embed_reply(file = discord.File(buffer, filename = "word_cloud.png"), 
								image_url = "attachment://word_cloud.png")

