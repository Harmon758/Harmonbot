
from discord.ext import commands


async def setup(bot):
    await bot.add_cog(Points())


class Points(commands.Cog):

    @commands.command()
    async def points(self, ctx):
        '''WIP'''
        commands_invoked = await ctx.bot.db.fetchval(
            """
            SELECT commands_invoked
            FROM users.stats
            WHERE user_id = $1
            """, 
            ctx.author.id
        )
        await ctx.embed_reply(f"You have {commands_invoked} points")
