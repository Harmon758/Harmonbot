
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

        await self.bot.db.execute("TRUNCATE users.points")
        async with self.bot.database_connection_pool.acquire() as connection:
            async with connection.transaction():
                # Postgres requires non-scrollable cursors to be created
                # and used in a transaction.
                async for record in connection.cursor(
                    "SELECT * FROM users.stats"
                ):
                    await connection.execute(
                        """
                        INSERT INTO users.points (user_id, points)
                        VALUES ($1, $2)
                        """,
                        record["user_id"],
                        (
                            (record["commands_invoked"] or 0) +
                            (record["slash_command_invocations"] or 0) +
                            (
                                record[
                                    "message_context_menu_command_invocations"
                                ] or 0
                             ) +
                            (
                                record[
                                    "user_context_menu_command_invocations"
                                ] or 0
                            )
                        )
                    )
                async for record in connection.cursor(
                    """SELECT * FROM respects.users"""
                ):
                    await connection.execute(
                        """
                        INSERT INTO users.points (user_id, points)
                        VALUES ($1, $2)
                        ON CONFLICT (user_id) DO
                        UPDATE SET points = points.points + $2
                        """,
                        record["user_id"], record["respects"]
                    )
                async for record in connection.cursor(
                    """SELECT * FROM trivia.users"""
                ):
                    await connection.execute(
                        """
                        INSERT INTO users.points (user_id, points)
                        VALUES ($1, $2)
                        ON CONFLICT (user_id) DO
                        UPDATE SET points = points.points + $2
                        """,
                        record["user_id"], record["correct"] * 10
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

    async def subtract(self, user, *, points = 1):
        return await self.add(user, point = -points)

    @commands.command()
    async def points(self, ctx):
        """
        Points (¤)
        • 1 for each command invoked
        • 1 for each respect paid
        • 10 for each trivia question answered correctly
        """
        user_points = await ctx.bot.db.fetchval(
            """
            SELECT points
            FROM users.points
            WHERE user_id = $1
            """, 
            ctx.author.id
        )
        await ctx.embed_reply(
            f"You have {user_points} (`\N{CURRENCY SIGN}`) points"
        )
