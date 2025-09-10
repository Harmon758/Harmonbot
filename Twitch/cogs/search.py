
from twitchio.ext import commands


def prepare(bot):
    bot.add_cog(Search(bot))

class Search(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def google(self, ctx, *search):
        await ctx.reply("https://google.com/search?q=" + '+'.join(search))

    @commands.command()
    async def imfeelinglucky(self, ctx, *search):
        await ctx.reply("https://google.com/search?btnI&q=" + '+'.join(search))

    @commands.command()
    async def lmgtfy(self, ctx, *search):
        await ctx.reply("https://lmgtfy.com/?q=" + '+'.join(search))

    @commands.command(aliases = ("wiki",))
    async def wikipedia(self, ctx, *search):
        await ctx.reply("https://wikipedia.org/wiki/" + '_'.join(search))

