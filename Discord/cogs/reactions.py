
from discord.ext import commands

from utilities import checks


async def setup(bot):
    await bot.add_cog(Reactions(bot))

# meta.stats reaction_responses column:
#  Fixed to stop counting own reactions on 2019-10-25
#  Deprecated on 2020-01-04 in favor of menu_reactions

class Reactions(commands.Cog):

    @commands.command(aliases = ["reaction", "menus", "menu"])
    @checks.not_forbidden()
    async def reactions(self, ctx):
        '''Menu versions of commands'''
        await ctx.send_help(ctx.command)

