
import discord
from discord.ext import commands

import asyncio
import json

from modules import utilities
from utilities import checks
import clients

def setup(bot):
	bot.add_cog(Misc(bot))

class Misc:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command(aliases = ["emotify"])
	@checks.not_forbidden()
	async def emojify(self, ctx, *, text : str):
		'''Emojify text'''
		output = ""
		for character in text:
			if 'a' <= character.lower() <= 'z':
				output += ":regional_indicator_{}:".format(character.lower())
			elif '0' <= character <= '9':
				output += ":{}:".format(clients.inflect_engine.number_to_words(int(character)))
			else:
				output += character
		try:
			await ctx.embed_reply(output)
		except discord.errors.HTTPException:
			await ctx.embed_reply(":no_entry: Error")
	
	@commands.command()
	@checks.not_forbidden()
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
	@checks.not_forbidden()
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
	@checks.not_forbidden()
	async def fingers(self, ctx, *, text : str):
		'''Add fingers'''
		await ctx.embed_reply(":point_right::skin-tone-2: {} :point_left::skin-tone-2:".format(text))
	
	@commands.command()
	@checks.not_forbidden()
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
	async def ping(self, ctx):
		'''Basic ping - pong command'''
		await ctx.embed_reply("pong")
	
	@commands.command()
	@checks.not_forbidden()
	async def poke(self, ctx, *, user : str):
		'''Poke someone'''
		to_poke = await utilities.get_user(ctx, user)
		if not to_poke:
			await ctx.embed_reply(":no_entry: User not found")
		elif to_poke == self.bot.user:
			await ctx.embed_reply("!poke {}".format(ctx.author.mention))
		else:
			utilities.create_folder("data/user_data/{}".format(ctx.author.id))
			utilities.create_file("user_data/{}/pokes".format(ctx.author.id))
			with open("data/user_data/{}/pokes.json".format(ctx.author.id), 'r') as pokes_file:
				pokes_data = json.load(pokes_file)
			pokes_data[to_poke.id] = pokes_data.get(to_poke.id, 0) + 1
			embed = discord.Embed(color = clients.bot_color)
			avatar = ctx.author.avatar_url or ctx.author.default_avatar_url
			embed.set_author(name = ctx.author, icon_url = avatar)
			embed.description = "Poked you for the {} time!".format(clients.inflect_engine.ordinal(pokes_data[to_poke.id]))
			await self.bot.send_message(to_poke, embed = embed)
			await self.bot.embed_reply("You have poked {} for the {} time!".format(to_poke.mention, clients.inflect_engine.ordinal(pokes_data[to_poke.id])))
			with open("data/user_data/{}/pokes.json".format(ctx.author.id), 'w') as pokes_file:
				json.dump(pokes_data, pokes_file, indent = 4)

def emote_wrapper(name, emote = None):
	if emote is None: emote = name
	@commands.command(name = name, help = name.capitalize() + " emote")
	@checks.not_forbidden()
	async def emote_command(self, ctx):
		await ctx.embed_reply(":{}:".format(emote))
	return emote_command

for emote in ("fish", "frog", "turtle", "gun", "tomato", "cucumber", "eggplant", "lizard", "minidisc"):
	setattr(Misc, emote, emote_wrapper(emote))
setattr(Misc, "dog", emote_wrapper("dog", emote = "dog2"))
setattr(Misc, "bunny", emote_wrapper("bunny", emote = "rabbit2"))

