
from discord.ext import commands


# meta.stats reaction_responses column:
#  Fixed to stop counting own reactions on 2019-10-25
#  Deprecated on 2020-01-04 in favor of menu_reactions


async def setup(bot):
    await bot.add_cog(Reactions(bot))

class Reactions(commands.Cog):

    """Deprecated now that there are native buttons"""

    @commands.command(aliases = ["reaction", "menus", "menu"], hidden = True)
    async def reactions(self, ctx):
        '''Deprecated now that there are native buttons'''
        await ctx.send_help(ctx.command)

