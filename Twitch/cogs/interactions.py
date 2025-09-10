
from twitchio.ext import commands


def prepare(bot):
    bot.add_cog(Interactions(bot))

class Interactions(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = ("goodbye",))
    async def bye(self, ctx, *, user = None):
        if not user or user.lower() == "harmonbot":
            await ctx.reply(f"Bye, {ctx.author.name.capitalize()}!")
        else:
            await ctx.reply(f"{user.title().lstrip('/')}, {ctx.author.name.capitalize()} says goodbye!")

    @commands.command(aliases = ("hi",))
    async def hello(self, ctx, *, user = None):
        if not user or user.lower() == "harmonbot":
            await ctx.reply(f"Hello, {ctx.author.name.capitalize()}!")
        else:
            await ctx.reply(f"{user.title().lstrip('/')}, {ctx.author.name.capitalize()} says hello!")

    @commands.command(aliases = ("congrats", "grats", "gz"))
    async def congratulations(self, ctx, *, user = None):
        if not user:
            await ctx.reply("Congratulations!!!!!")
        else:
            await ctx.reply(f"Congratulations, {user.title()}!!!!!")

    @commands.command()
    async def highfive(self, ctx, *, user = None):
        if not user:
            await ctx.reply(f"{ctx.author.name.capitalize()} highfives no one. :-/")
        elif user.lower() == "random":
            await ctx.reply(f"{ctx.author.name.capitalize()} highfives {ctx.random_viewer().name.capitalize()}!")
        elif user.lower() == ctx.author.name:
            await ctx.reply(f"{ctx.author.name.capitalize()} highfives themselves. o_O")
        elif user.lower() == "harmonbot":
            await ctx.reply(f"!highfive {ctx.author.name.capitalize()}")
        else:
            await ctx.reply(f"{ctx.author.name.capitalize()} highfives {user.title()}!")

    @commands.command()
    async def hug(self, ctx, *, user = None):
        if not user:
            await ctx.reply(f"{ctx.author.name.capitalize()} hugs no one. :-/")
        elif user.lower() == "random":
            await ctx.reply(f"{ctx.author.name.capitalize()} hugs {ctx.random_viewer().name.capitalize()}!")
        elif user.lower() == ctx.author.name:
            await ctx.reply(f"{ctx.author.name.capitalize()} hugs themselves. o_O")
        elif user.lower() == "harmonbot":
            await ctx.reply(f"!hug {ctx.author.name.capitalize()}")
        else:
            await ctx.reply(f"{ctx.author.name.capitalize()} hugs {user.title()}!")

