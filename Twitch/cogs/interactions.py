
from twitchio.ext import commands

@commands.cog()
class Interactions:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	async def bye(self, ctx, *, user = None):
		if not user or user.lower() == "harmonbot":
			await ctx.send(f"Bye, {ctx.author.name.capitalize()}!")
		else:
			await ctx.send(f"{user.title()}, {ctx.author.name.capitalize()} says goodbye!")
	
	@commands.command(aliases = ("hi",))
	async def hello(self, ctx, *, user = None):
		if not user or user.lower() == "harmonbot":
			await ctx.send(f"Hello, {ctx.author.name.capitalize()}!")
		else:
			await ctx.send(f"{user.title()}, {ctx.author.name.capitalize()} says hello!")
	
	@commands.command(aliases = ("congrats", "grats", "gz"))
	async def congratulations(self, ctx, *, user = None):
		if not user:
			await ctx.send("Congratulations!!!!!")
		else:
			await ctx.send(f"Congratulations, {user.title()}!!!!!")

