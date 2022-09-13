
import discord
from discord import app_commands
from discord.ext import commands

import asyncio

from modules import utilities
from utilities import checks

async def setup(bot):
	await bot.add_cog(Misc(bot))

class Misc(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	async def cog_load(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS pokes")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS pokes.pokes (
				poker			BIGINT, 
				pokee			BIGINT, 
				count			INT, 
				PRIMARY KEY		(poker, pokee)
			)
			"""
		)
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.command(aliases = ["bigmote"])
	async def bigmoji(self, ctx, emoji: discord.PartialEmoji):
		"""See larger versions of custom emoji"""
		await ctx.embed_reply(image_url = emoji.url)
	
	@commands.command(aliases = ["count"])
	async def counter(self, ctx):
		"""A counter"""
		await ctx.embed_reply(
			title = "Counter", 
			footer_text = None, 
			view = Counter(timeout = None)
		)
	
	@commands.command(aliases = ["emotify"])
	async def emojify(self, ctx, *, text: str):
		"""Emojify text"""
		output = ""
		for character in text:
			if 'a' <= character.lower() <= 'z':
				output += f":regional_indicator_{character.lower()}:"
			elif '0' <= character <= '9':
				output += f":{ctx.bot.inflect_engine.number_to_words(int(character))}:"
			else:
				output += character
		try:
			await ctx.embed_reply(output)
		except discord.HTTPException:
			# TODO: use textwrap/paginate
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
	
	@commands.command()
	async def fancify(self, ctx, *, text: str):
		"""Fancify text"""
		output = ""
		for character in text:
			if 'A' <= character <= 'Z':
				output += chr(ord(character) + 119951)
				# ord('𝓐') - ord('A') = 119951
			elif 'a' <= character <= 'z':
				output += chr(ord(character) + 119945)
				# ord('𝓪') - ord('a') = 119945
			elif '0' <= character <= '9':
				output += chr(ord(character) + 120744)
				# ord('𝟘') - ord('0') = 120744
			else:
				output += character
		await ctx.embed_reply(output)
	
	@commands.hybrid_command(aliases = ["full-width", "full_width"])
	async def fullwidth(self, ctx, *, text: str):
		"""
		Make text fullwidth
		
		Parameters
		----------
		text
			Text to make fullwidth
		"""
		output = ""
		for character in text:
			if '!' <= character <= '~':
				output += chr(ord(character) + 65248)
			else:
				output += character
		await ctx.embed_reply(output)
	
	@commands.command()
	async def fingers(self, ctx, *, text: str = ""):
		"""Add fingers"""
		await ctx.embed_reply(
			f"\N{WHITE RIGHT POINTING BACKHAND INDEX}{ctx.bot.emoji_skin_tone}"
			f" {text} "
			f"\N{WHITE LEFT POINTING BACKHAND INDEX}{ctx.bot.emoji_skin_tone}"
		)
	
	@commands.command()
	async def loading_bar(self, ctx):
		'''
		A loading bar
		Currently does nothing.. or does it?
		'''
		counter = 0
		bar = chr(9633) * 10
		loading_message = await ctx.embed_reply("Loading: [{}]".format(bar))
		embed = loading_message.embeds[0]
		while counter <= 10:
			counter += 1
			bar = chr(9632) + bar[:-1] #9608
			await asyncio.sleep(1)
			embed.description = "Loading: [{}]".format(bar)
			await loading_message.edit(embed = embed)
	
	@commands.command()
	async def lorem(self, ctx):
		"""Lorem Ipsum generator"""
		# TODO: add options?
		url = "http://loripsum.net/api/plaintext"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			output = await resp.text()
		
		if len(output) > ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
			paragraphs = output.split("\n\n")
			output = ""
			while len(output) + len(paragraphs[0]) < ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
				output += "\n\n" + paragraphs.pop()
			output = output[2:]
		
		await ctx.embed_reply(output)
	
	@commands.command()
	async def poke(self, ctx, *, user: discord.Member):
		"""Poke someone"""
		if user == self.bot.user:
			await ctx.embed_reply(f"!poke {ctx.author.mention}")
			return
		
		times = await ctx.bot.db.fetchval(
			"""
			INSERT INTO pokes.pokes (poker, pokee, count)
			VALUES ($1, $2, 1)
			ON CONFLICT (poker, pokee) DO
			UPDATE SET count = pokes.count + 1
			RETURNING count
			""",
			ctx.message.author.id, user.id
		)
		times = ctx.bot.inflect_engine.ordinal(times)
		
		embed = discord.Embed(color = ctx.bot.bot_color)
		embed.set_author(name = ctx.author, icon_url = ctx.author.avatar.url)
		embed.description = f"Poked you for the {times} time!"
		
		try:
			await user.send(embed = embed)
		except discord.HTTPException as e:
			if e.code != 50007:  # 50007 - Cannot send messages to this user
				raise
		
		await ctx.embed_reply(
			f"You have poked {user.mention} for the {times} time!"
		)
	
	@commands.command(aliases = ["select"])
	async def selector(self, ctx, *options: str):
		"""A selector"""
		view = discord.ui.View(timeout = None)
		view.add_item(discord.ui.Select(
			options = [
				discord.SelectOption(label = option)
				for option in options[:25]
			]
		))
		await ctx.embed_reply(
			title = "Selector",
			footer_text = None,
			view = view
		)
	
	@commands.command()
	async def subscript(self, ctx, *, text: str):
		"""
		Subscript text
		Supports: 0 1 2 3 4 5 6 7 8 9 + - = ( ) a e o x ə h k l m n p s t
		"""
		await ctx.embed_reply(utilities.subscript(text))
	
	@commands.command()
	async def superscript(self, ctx, *, text: str):
		"""
		Superscript text
		Supports: 0 1 2 3 4 5 6 7 8 9 + - = ( ) i n
		"""
		await ctx.embed_reply(utilities.superscript(text))
	
	@app_commands.command()
	async def think(self, interaction):
		"""🤔"""
		await interaction.response.defer()
		await asyncio.sleep(600)
		await interaction.followup.send('\N{THINKING FACE}')

class Counter(discord.ui.View):

	@discord.ui.button(label = '0', style = discord.ButtonStyle.grey)
	async def count(self, interaction, button):
		button.label = str(int(button.label) + 1)
		await interaction.response.edit_message(view = self)

