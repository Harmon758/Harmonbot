
import discord
from discord import ui
from discord.ext import commands

import itertools
import random


EMOJI = [
    '7\N{COMBINING ENCLOSING KEYCAP}',
    '\N{BANANA}',
    '\N{BELL}',
    '\N{CHERRIES}',
    '\N{CROWN}',
    '\N{FOUR LEAF CLOVER}',
    '\N{GEM STONE}',
    '\N{GRAPES}',
    '\N{LEMON}',
    '\N{TANGERINE}',
    '\N{WATERMELON}',
    '\N{WHITE MEDIUM STAR}'
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

    @commands.hybrid_group(case_insensitive = True, fallback = "play")
    async def slots(self, ctx):
        """
        Slot machine
        10 Points (¤) to play
        Win:
        • 7 ¤ for a 7️⃣
        • 20 ¤ for a pair
        • 77 ¤ for a pair of 7️⃣s
        • 300 ¤ for three of a kind
        • 777 ¤ for three 7️⃣s
        """
        await play_slots(ctx)

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
            time_declension = ctx.bot.inflect_engine.plural("time", plays)
            await ctx.embed_reply(
                f"You've played slots {plays:,} {time_declension}"
            )
        else:
            await ctx.embed_reply("You haven't played slots yet")

    @slots.command(with_app_command = False)
    @commands.is_owner()
    async def value(self, ctx):
        value = 0
        for reels in itertools.product(EMOJI, repeat = 3):
            value += calculate_slots_points(list(reels))
        await ctx.embed_reply(value / (len(EMOJI) ** 3))


async def play_slots(ctx_or_interaction, *, message = None, view = None):
    if isinstance(ctx_or_interaction, commands.Context):
        if message:
            raise RuntimeError("play_slots passed Context with message")
        if view:
            raise RuntimeError("play_slots passed Context with view")
        ctx = ctx_or_interaction
        bot = ctx.bot
        user = ctx.author
    elif isinstance(ctx_or_interaction, discord.Interaction):
        if not message:
            raise RuntimeError("play_slots passed Interaction without message")
        if not view:
            raise RuntimeError("play_slots passed Interaction without view")
        interaction = ctx_or_interaction
        bot = interaction.client
        user = interaction.user
    else:
        raise RuntimeError("play_slots passed neither Context nor Interaction")

    if not (points_cog := bot.get_cog("Points")):
        error = f"{bot.error_emoji} Error: Unable to retrieve Points"
        if message:
            await interaction.response.send_message(error)
        else:
            await ctx.embed_reply(error)
        return

    points = await points_cog.get(user)

    if points < 10:
        error = (
            f"\N{NO ENTRY SIGN} You need 10 Points (\N{CURRENCY SIGN}) to play and you only have {points}\n"
            f"See `help points` to see how you can earn more Points (\N{CURRENCY SIGN})"
        )  # TODO: Use prefix
        if message:
            await interaction.response.send_message(error)
        else:
            await ctx.embed_reply(error)
        return

    await bot.db.execute(
        """
        INSERT INTO slots.users (user_id, plays)
        VALUES ($1, 1)
        ON CONFLICT (user_id) DO
        UPDATE SET plays = users.plays + 1
        """, 
        user.id
    )

    emojis = [random.choice(EMOJI) for reel in range(3)]

    if points := calculate_slots_points(emojis):
        footer_text = (
            f"You won {points} \N{CURRENCY SIGN} {'!' * len(str(points))}"
        )
    else:
        footer_text = "You didn't win anything this time"

    points -= 10

    await points_cog.add(user = user, points = points)

    if message:
        view.count += 1
        embed = message.embeds[0]
        embed.description = ' '.join(emojis)
        embed.set_footer(
            text = f"{footer_text} | You've played {view.count} times"
        )
        await interaction.response.edit_message(embed = embed)
    else:
        view = SlotsView(bot = ctx.bot, user = ctx.author)
        message = await ctx.embed_reply(
            title = '\N{SLOT MACHINE}',
            description = ' '.join(emojis),
            footer_text = footer_text,
            view = view
        )
        view.message = message
        bot.views.append(view)

def calculate_slots_points(emojis):
    sevens = emojis.count(EMOJI[0])

    if sevens == 3:
        return 777
    elif emojis[0] == emojis[1] == emojis[2]:
        return 300
    elif sevens == 2:
        return 77
    elif (
        emojis[0] == emojis[1] or
        emojis[1] == emojis[2] or
        emojis[0] == emojis[2]
    ):
        if sevens == 1:
            return 27
        else:
            return 20
    elif sevens == 1:
        return 7
    else:
        return 0


class SlotsView(ui.View):

    def __init__(self, *, bot, user):
        super().__init__(timeout = 600)

        self.bot = bot
        self.user = user

        self.count = 1
        self.message = None

    @ui.button(label = "Play Again", style = discord.ButtonStyle.green)
    async def play_again(self, interaction, button):
        await play_slots(interaction, message = self.message, view = self)

    async def interaction_check(self, interaction):
        if interaction.user.id not in (
            self.user.id, interaction.client.owner_id
        ):
            await interaction.response.send_message(
                "You aren't the one playing this slots game.",
                ephemeral = True
            )
            return False
        return True

    async def stop(self):
        self.play_again.disabled = True

        if self.message:
            await self.bot.attempt_edit_message(self.message, view = self)

        super().stop()

    async def on_timeout(self):
        await self.stop()
