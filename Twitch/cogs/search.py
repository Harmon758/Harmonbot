
from twitchio.ext import commands


@commands.cog()
class Search:

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def google(self, ctx, *search):
        await ctx.send("https://google.com/search?q=" + '+'.join(search))

    @commands.command()
    async def imfeelinglucky(self, ctx, *search):
        await ctx.send("https://google.com/search?btnI&q=" + '+'.join(search))

    @commands.command()
    async def lmgtfy(self, ctx, *search):
        await ctx.send("https://lmgtfy.com/?q=" + '+'.join(search))

    @commands.command(aliases = ("wiki",))
    async def wikipedia(self, ctx, *search):
        await ctx.send("https://wikipedia.org/wiki/" + '_'.join(search))

