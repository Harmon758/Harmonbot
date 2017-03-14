
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
	async def emojify(self, *, text : str):
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
			await self.bot.embed_reply(output)
		except discord.errors.HTTPException:
			await self.bot.embed_reply(":no_entry: Error")
	
	@commands.command()
	@checks.not_forbidden()
	async def fancify(self, *, text : str):
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
		await self.bot.embed_reply(output)
	
	@commands.command(aliases = ["full-width", "full_width"])
	@checks.not_forbidden()
	async def fullwidth(self, *, text : str):
		'''Make text fullwidth'''
		output = ""
		for character in text:
			if '!' <= character <= '~':
				output += chr(ord(character) + 65248)
			else:
				output += character
		await self.bot.embed_reply(output)
	
	@commands.command()
	@checks.not_forbidden()
	async def fingers(self, *, text : str):
		'''Add fingers'''
		await self.bot.embed_reply(":point_right::skin-tone-2: {} :point_left::skin-tone-2:".format(text))
	
	@commands.command()
	@checks.not_forbidden()
	async def loading_bar(self):
		'''
		A loading bar
		Currently does nothing.. or does it?
		'''
		counter = 0
		bar = chr(9633) * 10
		loading_message, embed = await self.bot.embed_reply("Loading: [" + bar + "]")
		while counter <= 10:
			counter += 1
			bar = chr(9632) + bar[:-1] #9608
			await asyncio.sleep(1)
			embed.description = "Loading: [" + bar + "]"
			await self.bot.edit_message(loading_message, embed = embed)
	
	@commands.command()
	async def ping(self):
		'''Basic ping - pong command'''
		await self.bot.embed_reply("pong")
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def poke(self, ctx, *, user : str):
		'''Poke someone'''
		to_poke = await utilities.get_user(ctx, user)
		if not to_poke:
			await self.bot.embed_reply(":no_entry: User not found")
		elif to_poke == self.bot.user:
			await self.bot.embed_reply("!poke {}".format(ctx.message.author.mention))
		else:
			utilities.create_folder("data/user_data/{}".format(ctx.message.author.id))
			utilities.create_file("user_data/{}/pokes".format(ctx.message.author.id))
			with open("data/user_data/{}/pokes.json".format(ctx.message.author.id), 'r') as pokes_file:
				pokes_data = json.load(pokes_file)
			pokes_data[to_poke.id] = pokes_data.get(to_poke.id, 0) + 1
			embed = discord.Embed(color = clients.bot_color)
			avatar = ctx.message.author.default_avatar_url if not ctx.message.author.avatar else ctx.message.author.avatar_url
			embed.set_author(name = ctx.message.author, icon_url = avatar)
			embed.description = "Poked you for the {} time!".format(clients.inflect_engine.ordinal(pokes_data[to_poke.id]))
			await self.bot.send_message(to_poke, embed = embed)
			await self.bot.embed_reply("You have poked {} for the {} time!".format(to_poke.mention, clients.inflect_engine.ordinal(pokes_data[to_poke.id])))
			with open("data/user_data/{}/pokes.json".format(ctx.message.author.id), 'w') as pokes_file:
				json.dump(pokes_data, pokes_file, indent = 4)

def emote_wrapper(name, emote = None):
	if emote is None: emote = name
	@commands.command(name = name, help = name.capitalize() + " emote")
	@checks.not_forbidden()
	async def emote_command(self):
		await self.bot.embed_reply(":{}:".format(emote))
	return emote_command

for emote in ("fish", "frog", "turtle", "gun", "tomato", "cucumber", "eggplant", "lizard", "minidisc"):
	setattr(Misc, emote, emote_wrapper(emote))
setattr(Misc, "dog", emote_wrapper("dog", emote = "dog2"))

