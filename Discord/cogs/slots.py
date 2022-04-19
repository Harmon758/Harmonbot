
from discord.ext import commands

import random


EMOJI = [
    '7\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}',
    '\N{BANANA}',
    '\N{BELL}',
    '\N{CHERRIES}',
    '\N{FOUR LEAF CLOVER}',
    '\N{GEM STONE}',
    '\N{GRAPES}',
    '\N{LEMON}',
    '\N{TANGERINE}',
    '\N{WATERMELON}',
]


async def setup(bot):
    await bot.add_cog(Slots(bot))


class Slots(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        await self.bot.connect_to_database()
        await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS slots")
        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS slots.users (
                user_id  BIGINT PRIMARY KEY,
                plays    INT
            )
            """
        )

    @commands.group(case_insensitive =True, invoke_without_command = True)
    async def slots(self, ctx):
        """
        Slot machine
        10 Points (¤) to play
        Win:
        • 10 ¤ for a 7️⃣
        • 10 ¤ for a pair
        • 77 ¤ for a pair of 7️⃣s
        • 100 ¤ for three of a kind
        • 1,000 ¤ for three 7️⃣s
        """
        if not (points_cog := ctx.bot.get_cog("Points")):
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Error: Unable to retrieve Points"
            )
            return

        points = await points_cog.get(ctx.author)

        if points < 10:
            await ctx.embed_reply(
                f"\N{NO ENTRY SIGN} You need 10 Points (\N{CURRENCY SIGN}) to play and you only have {points}\n"
                f"See {ctx.prefix}help points to see how you can earn more Points (\N{CURRENCY SIGN})"
            )
            return

        await ctx.bot.db.execute(
            """
            INSERT INTO slots.users (user_id, plays)
            VALUES ($1, 1)
            ON CONFLICT (user_id) DO
            UPDATE SET plays = users.plays + 1
            """, 
            ctx.author.id
        )

        emojis = [random.choice(EMOJI) for reel in range(3)]
        sevens = emojis.count(EMOJI[0])

        points = -10
        if sevens == 3:
            footer_text = "You won 1,000 \N{CURRENCY SIGN} !!!"
            points += 1000
        elif emojis[0] == emojis[1] == emojis[2]:
            footer_text = "You won 100 \N{CURRENCY SIGN} !!"
            points += 100
        elif sevens == 2:
            footer_text = "You won 77 \N{CURRENCY SIGN} !!"
            points += 77
        elif (
            emojis[0] == emojis[1] or
            emojis[1] == emojis[2] or
            emojis[0] == emojis[2]
        ):
            if sevens == 1:
                footer_text = "You won 20 \N{CURRENCY SIGN} !"
                points += 20
            else:
                footer_text = "You won 10 \N{CURRENCY SIGN} !"
                points += 10
        elif sevens == 1:
            footer_text = "You won 10 \N{CURRENCY SIGN} !"
            points += 10
        else:
            footer_text = "You didn't win anything this time"

        if points:
            await points_cog.add(user = ctx.author, points = points)

        await ctx.embed_reply(
            title = '\N{SLOT MACHINE}',
            description = ' '.join(emojis),
            footer_text = footer_text
        )

    @slots.command()
    async def plays(self, ctx):
        """How many times you've played slots"""
        plays = await ctx.bot.db.fetchval(
            """
            SELECT plays
            FROM slots.users
            WHERE user_id = $1
            """,
            ctx.author.id
        )
        if plays:
            times = ctx.bot.inflect_engine.plural("time", plays)
            await ctx.embed_reply(f"You've played slots {plays:,} {times}")
        else:
            await ctx.embed_reply(f"You haven't played slots yet")
