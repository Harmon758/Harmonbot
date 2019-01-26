
import discord
from discord.ext import commands

import asyncio
import json

from modules import utilities
from utilities import checks
import clients

def setup(bot):
	
	def emote_wrapper(name, emote = None):
		if emote is None: emote = name
		@commands.command(name = name, help = name.capitalize() + " emote")
		@checks.not_forbidden()
		async def emote_command(self, ctx):
			await ctx.embed_reply(":{}:".format(emote))
		return emote_command
	
	for emote in ("fish", "frog", "turtle", "gun", "tomato", "cucumber", "eggplant", "lizard", "minidisc", "horse", "penguin", "dragon", "eagle", "bird"):
		setattr(Misc, emote, emote_wrapper(emote))
	setattr(Misc, "cow", emote_wrapper("cow", emote = "cow2"))
	setattr(Misc, "panda", emote_wrapper("panda", emote = "panda_face"))
	
	bot.add_cog(Misc(bot))

class Misc:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command(aliases = ["bigmote"])
	@checks.not_forbidden()
	async def bigmoji(self, ctx, emoji : discord.PartialEmoji):
		'''See larger versions of custom emoji'''
		await ctx.embed_reply(image_url = emoji.url)
	
	@commands.command(aliases = ["emotify"])
	@checks.not_forbidden()
	async def emojify(self, ctx, *, text : str):
		'''Emojify text'''
		output = ""
		for character in text:
			if 'a' <= character.lower() <= 'z':
				output += f":regional_indicator_{character.lower()}:"
			elif '0' <= character <= '9':
				output += f":{clients.inflect_engine.number_to_words(int(character))}:"
			else:
				output += character
		try:
			await ctx.embed_reply(output)
		except discord.HTTPException:
			# TODO: use textwrap/paginate
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
		await ctx.embed_reply(f":point_right::skin-tone-2: {text} :point_left::skin-tone-2:")
	
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
	@checks.not_forbidden()
	async def lorem(self, ctx):
		'''Lorem Ipsum generator'''
		# TODO: add options?
		async with clients.aiohttp_session.get("http://loripsum.net/api/plaintext") as resp:
			data = await resp.text()
		await ctx.embed_reply(data)
	
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
			clients.create_folder(clients.data_path + "/user_data/{}".format(ctx.author.id))
			clients.create_file("user_data/{}/pokes".format(ctx.author.id))
			with open(clients.data_path + "/user_data/{}/pokes.json".format(ctx.author.id), 'r') as pokes_file:
				pokes_data = json.load(pokes_file)
			pokes_data[str(to_poke.id)] = pokes_data.get(str(to_poke.id), 0) + 1
			with open(clients.data_path + "/user_data/{}/pokes.json".format(ctx.author.id), 'w') as pokes_file:
				json.dump(pokes_data, pokes_file, indent = 4)
			embed = discord.Embed(color = ctx.bot.bot_color)
			embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
			embed.description = "Poked you for the {} time!".format(clients.inflect_engine.ordinal(pokes_data[str(to_poke.id)]))
			await to_poke.send(embed = embed)
			await ctx.embed_reply("You have poked {} for the {} time!".format(to_poke.mention, clients.inflect_engine.ordinal(pokes_data[str(to_poke.id)])), footer_text = "In response to: {}".format(ctx.message.clean_content))
	
	@commands.command()
	@checks.not_forbidden()
	async def subscript(self, ctx, *, text : str):
		'''
		Subscript text
		Supports: 0 1 2 3 4 5 6 7 8 9 + - = ( ) a e o x ə h k l m n p s t
		'''
		await ctx.embed_reply(utilities.subscript(text))
	
	@commands.command()
	@checks.not_forbidden()
	async def superscript(self, ctx, *, text : str):
		'''
		Superscript text
		Supports: 0 1 2 3 4 5 6 7 8 9 + - = ( ) i n
		'''
		await ctx.embed_reply(utilities.superscript(text))

