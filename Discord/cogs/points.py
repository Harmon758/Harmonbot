
from discord.ext import commands


async def setup(bot):
    await bot.add_cog(Points(bot))


class Points(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        await self.bot.connect_to_database()
        await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS users")
        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS users.points (
                user_id  BIGINT PRIMARY KEY,
                points   BIGINT
            )
            """
        )

    async def add(self, *, user, points = 1):
        return await self.bot.db.fetchval(
            """
            INSERT INTO users.points (user_id, points)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO
            UPDATE SET points = points.points + $2
            RETURNING points
            """,
            user.id, points
        )

    async def get(self, user):
        points = await self.bot.db.fetchval(
            """
            SELECT points
            FROM users.points
            WHERE user_id = $1
            """,
            user.id
        )
        return points or 0

    async def subtract(self, *, user, points = 1):
        return await self.add(user = user, points = -points)

    @commands.command()
    async def points(self, ctx):
        """
        Points (¤)
        • 1 for each command invoked
        • 1 for each respect paid
        • 10 for each trivia question answered correctly
        You can also earn Points (¤) from:
        • Slots
        You can spend Points (¤) on:
        • Slots
        """
        user_points = await self.get(ctx.author)
        await ctx.embed_reply(
            f"You have {user_points:,} (`\N{CURRENCY SIGN}`) points"
        )
