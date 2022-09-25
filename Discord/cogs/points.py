
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

    @commands.hybrid_group(
        aliases = ["credits"], case_insensitive =True, fallback = "balance"
    )
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

    @points.command(
        aliases = ["leaders", "most", "ranks", "scoreboard", "top"]
    )
    async def leaderboard(self, ctx, number: commands.Range[int, 1, 15] = 10):
        """
        Points (¤) leaderboard

        Parameters
        ----------
        number
            Number of Points (¤) leaders to show (between 1 and 15)
        """
        await ctx.defer()
        fields = []
        async with ctx.bot.database_connection_pool.acquire() as connection:
            async with connection.transaction():
                # Postgres requires non-scrollable cursors to be created
                # and used in a transaction.
                async for record in connection.cursor(
                    "SELECT * FROM users.points ORDER BY points DESC LIMIT $1",
                    number
                ):
                    if not (user := ctx.bot.get_user(record["user_id"])):
                        user = await ctx.bot.fetch_user(record["user_id"])
                    fields.append((str(user), f"{record['points']:,}"))

        await ctx.embed_reply(
            title = f"Points (¤) Top {number}", fields = fields
        )
