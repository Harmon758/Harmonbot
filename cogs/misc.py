
from discord.ext import commands

import json

from modules import utilities
from utilities import checks
from clients import inflect_engine

def setup(bot):
	bot.add_cog(Misc(bot))

class Misc:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	@checks.not_forbidden()
	async def fingers(self, *, text : str):
		'''Add fingers'''
		await self.bot.reply(":point_right::skin-tone-2: {} :point_left::skin-tone-2:".format(text))
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def poke(self, ctx, *, user : str):
		'''
		Poke someone
		'''
		to_poke = await utilities.get_user(ctx, user)
		if not to_poke:
			await self.bot.reply("User not found.")
		elif to_poke == self.bot.user:
			await self.bot.say("!poke {}".format(ctx.message.author))
		else:
			utilities.create_folder("data/user_data/{}".format(ctx.message.author.id))
			utilities.create_file("user_data/{}/pokes".format(ctx.message.author.id))
			with open("data/user_data/{}/pokes.json".format(ctx.message.author.id), 'r') as pokes_file:
				pokes_data = json.load(pokes_file)
			if to_poke.id not in pokes_data:
				pokes_data[to_poke.id] = 1
			else:
				pokes_data[to_poke.id] += 1
			await self.bot.send_message(to_poke, "{} has poked you for the {} time!".format(ctx.message.author, inflect_engine.ordinal(pokes_data[to_poke.id])))
			await self.bot.reply("You have poked {} for the {} time!".format(user, inflect_engine.ordinal(pokes_data[to_poke.id])))
			with open("data/user_data/{}/pokes.json".format(ctx.message.author.id), 'w') as pokes_file:
				json.dump(pokes_data, pokes_file, indent = 4)

def emote_wrapper(name, emote = None):
	if emote is None: emote = name
	@commands.command(name = name, help = name.capitalize() + " emote")
	@checks.not_forbidden()
	async def emote_command(self):
		await self.bot.reply(":{}:".format(emote))
	return emote_command

for emote in ("fish", "frog", "turtle"):
	setattr(Misc, emote, emote_wrapper(emote))
setattr(Misc, "dog", emote_wrapper("dog", emote = "dog2"))

