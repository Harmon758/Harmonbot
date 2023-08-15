
from discord.ext import commands

from utilities import checks


async def setup(bot):
    await bot.add_cog(Overwatch())


class Overwatch(commands.Cog):

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.group(invoke_without_command = True, case_insensitive = True)
    async def overwatch(self, ctx):
        '''
        BattleTags are case sensitive

        The ability, achievement, hero, item, and map commands have been
        deprecated, as the API they used to use does not exist anymore
        '''
        await ctx.send_help(ctx.command)

    # TODO: Finish Stats (Add Achievements, Improve)

    @overwatch.command(aliases = ["weapon"], hidden = True)
    async def ability(self, ctx):
        """
        Overwatch Abilities/Weapons
        Deprecated, as the API this command used to use does not exist anymore
        https://overwatch-api.net/
        https://github.com/jamesmcfadden/overwatch-api
        """
        await ctx.send_help(ctx.command)

    @overwatch.command(hidden = True)
    async def achievement(self, ctx):
        """
        Overwatch Achievements
        Deprecated, as the API this command used to use does not exist anymore
        https://overwatch-api.net/
        https://github.com/jamesmcfadden/overwatch-api
        """
        await ctx.send_help(ctx.command)

    @overwatch.command(hidden = True)
    async def hero(self, ctx):
        """
        Overwatch Heroes
        Deprecated, as the API this command used to use does not exist anymore
        https://overwatch-api.net/
        https://github.com/jamesmcfadden/overwatch-api
        """
        await ctx.send_help(ctx.command)

    @overwatch.command(hidden = True)
    async def item(self, ctx):
        """
        Overwatch Items
        Deprecated, as the API this command used to use does not exist anymore
        https://overwatch-api.net/
        https://github.com/jamesmcfadden/overwatch-api
        """
        await ctx.send_help(ctx.command)

    @overwatch.command(hidden = True)
    async def map(self, ctx):
        """
        Overwatch Maps
        Deprecated, as the API this command used to use does not exist anymore
        https://overwatch-api.net/
        https://github.com/jamesmcfadden/overwatch-api
        """
        await ctx.send_help(ctx.command)

    @overwatch.group(
        name = "stats", aliases = ["statistics"], hidden = True,
        case_insensitive = True, invoke_without_command = True
    )
    async def stats(self, ctx):
        """
        This command is deprecated, as the API this command used to use has been discontinued
        https://github.com/Fuyukai/OWAPI/issues/302
        """
        await ctx.send_help(ctx.command)

    @stats.group(
        name = "quickplay", aliases = ["qp"], hidden = True,
        case_insensitive = True, invoke_without_command = True
    )
    async def stats_quickplay(self, ctx):
        """
        This command is deprecated, as the API this command used to use has been discontinued
        https://github.com/Fuyukai/OWAPI/issues/302
        """
        await ctx.send_help(ctx.command)

    @stats.command(name = "competitive", aliases = ["comp"], hidden = True)
    async def stats_competitive(self, ctx):
        """
        This command is deprecated, as the API this command used to use has been discontinued
        https://github.com/Fuyukai/OWAPI/issues/302
        """
        await ctx.send_help(ctx.command)

    @stats_quickplay.command(name = "heroes", hidden = True)
    async def stats_quickplay_heroes(self, ctx):
        '''
        This command is deprecated, as the API this command used to use has been discontinued
        https://github.com/Fuyukai/OWAPI/issues/302
        '''
        await ctx.send_help(ctx.command)

