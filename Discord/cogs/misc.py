
import discord
from discord.ext import commands

import asyncio

from modules import utilities
from utilities import checks

def setup(bot):
	
	def emote_wrapper(emote):
		async def emote_command(self, ctx):
			await ctx.embed_reply(f":{emote}:")
		return emote_command
	
	for emote in ("fish", "frog", "turtle", "gun", "tomato", "cucumber", "eggplant", "lizard", "minidisc", "horse", "penguin", "dragon", "eagle", "bird"):
		command = commands.Command(emote_wrapper(emote), name = emote, help = emote.capitalize() + " emote", checks = [checks.not_forbidden().predicate])
		setattr(Misc, emote, command)
		Misc.__cog_commands__.append(command)
	for name, emote in (("cow", "cow2"), ("panda", "panda_face")):
		command = commands.Command(emote_wrapper(emote), name = name, help = name.capitalize() + " emote", checks = [checks.not_forbidden().predicate])
		setattr(Misc, name, command)
		Misc.__cog_commands__.append(command)
	
	bot.add_cog(Misc(bot))

class Misc(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.bot.loop.create_task(self.initialize_database(), name = "Initialize database")
	
	async def initialize_database(self):
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
		'''See larger versions of custom emoji'''
		await ctx.embed_reply(image_url = emoji.url)
	
	@commands.command(aliases = ["emotify"])
	async def emojify(self, ctx, *, text : str):
		'''Emojify text'''
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
			await ctx.embed_reply(":no_entry: Error")
	
	@commands.command()
	async def fancify(self, ctx, *, text : str):
		'''Fancify text'''
		output = ""
		for character in text:
			if 'A' <= character <= 'Z':
				output += chr(ord(character) + 119951)
			elif 'a' <= character <= 'z':
				output += chr(ord(character) + 119919)
			elif '0' <= character <= '9':
				output += chr(ord(character) + 120744)
			else:
				output += character
		await ctx.embed_reply(output)
	
	@commands.command(aliases = ["full-width", "full_width"])
	async def fullwidth(self, ctx, *, text : str):
		'''Make text fullwidth'''
		output = ""
		for character in text:
			if '!' <= character <= '~':
				output += chr(ord(character) + 65248)
			else:
				output += character
		await ctx.embed_reply(output)
	
	@commands.command()
	async def fingers(self, ctx, *, text: str):
		'''Add fingers'''
		await ctx.embed_reply(f":point_right::skin-tone-2: {text} :point_left::skin-tone-2:")
	
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
		'''Lorem Ipsum generator'''
		# TODO: add options?
		async with ctx.bot.aiohttp_session.get("http://loripsum.net/api/plaintext") as resp:
			data = await resp.text()
		await ctx.embed_reply(data)
	
	@commands.command()
	async def ping(self, ctx):
		'''Basic ping - pong command'''
		await ctx.embed_reply("pong")
	
	@commands.command()
	async def poke(self, ctx, *, user : discord.Member):
		'''Poke someone'''
		if user == self.bot.user:
			return await ctx.embed_reply(f"!poke {ctx.author.mention}")
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
		embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
		embed.description = f"Poked you for the {times} time!"
		await user.send(embed = embed)
		await ctx.embed_reply(f"You have poked {user.mention} for the {times} time!")
	
	@commands.command()
	async def subscript(self, ctx, *, text: str):
		'''
		Subscript text
		Supports: 0 1 2 3 4 5 6 7 8 9 + - = ( ) a e o x ə h k l m n p s t
		'''
		await ctx.embed_reply(utilities.subscript(text))
	
	@commands.command()
	async def superscript(self, ctx, *, text: str):
		'''
		Superscript text
		Supports: 0 1 2 3 4 5 6 7 8 9 + - = ( ) i n
		'''
		await ctx.embed_reply(utilities.superscript(text))

