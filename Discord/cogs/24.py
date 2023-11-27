
import discord
from discord import ui
from discord.ext import commands

from units.twenty_four import check_solution, generate_numbers
from utilities import checks


async def setup(bot):
    await bot.add_cog(TwentyFour())


class TwentyFour(commands.Cog, name = "24"):

    @commands.hybrid_command(name = "24", aliases = ["twenty-four"])
    @checks.not_forbidden()
    async def twenty_four(self, ctx):
        """24 Game"""
        await ctx.defer()

        numbers = list(map(str, generate_numbers()))
        CEK = '\N{COMBINING ENCLOSING KEYCAP}'
        view = TwentyFourView(ctx.bot, numbers)
        if ctx.interaction:
            response = await ctx.send(
                f"{numbers[0]}{CEK}{numbers[1]}{CEK}\n"
                f"{numbers[2]}{CEK}{numbers[3]}{CEK}",
                view = view
            )
            # InteractionMessage token expires after 15 min.
            try:
                response = await response.fetch()
            except discord.Forbidden:
                view.timeout = 600
                response = await response.edit(view = view)
        else:
            response = await ctx.embed_reply(
                f"{numbers[0]}{CEK}{numbers[1]}{CEK}\n"
                f"{numbers[2]}{CEK}{numbers[3]}{CEK}",
                footer_text = None,
                view = view
            )
        view.message = response
        ctx.bot.views.append(view)

        async def incorrect(message, value):
            response_ctx = await ctx.bot.get_context(message)
            solution = message.content.replace('\\', "")
            await response_ctx.embed_reply(
                reference = response,
                title = "Incorrect",
                description = f"`{solution} = {value}`",
                in_response_to = False,
                attempt_delete = False
            )

        def check(message):
            if message.channel != ctx.channel:
                return False
            if (value := check_solution(numbers, message.content)) is False:
                return False
            if value != 24:
                ctx.bot.loop.create_task(
                    incorrect(message, int(value)),
                    name = "Send response to incorrect solution for 24 Game"
                )
                return False
            return True

        message = await ctx.bot.wait_for('message', check = check)
        ctx = await ctx.bot.get_context(message)
        solution = message.content.replace('\\', "")
        await ctx.embed_reply(
            reference = response,
            title = "Correct!",
            description = f"`{solution} = 24`",
            in_response_to = False,
            attempt_delete = False
        )
        await view.stop()


class TwentyFourView(ui.View):

    def __init__(self, bot, numbers):
        super().__init__(timeout = None)

        self.bot = bot

        self.add_item(TwentyFourSubmitSolutionButton(numbers))
        self.add_item(
            ui.Button(
                style = discord.ButtonStyle.link,
                emoji = '\N{INFORMATION SOURCE}',
                url = "https://en.wikipedia.org/wiki/24_(puzzle)"
            )
        )

        self.message = None

    async def on_timeout(self):
        await self.stop()

    async def stop(self):
        self.children[0].disabled = True

        if self.message:
            await self.bot.attempt_edit_message(self.message, view = self)

        super().stop()


class TwentyFourSubmitSolutionButton(ui.Button):

    def __init__(self, numbers):
        super().__init__(label = "Submit Solution")
        self.numbers = numbers

    async def callback(self, interaction):
        await interaction.response.send_modal(
            TwentyFourSubmitSolutionModal(self.numbers)
        )


class TwentyFourSubmitSolutionModal(ui.Modal, title = "Submit Solution"):

    solution = ui.TextInput(label = "Solution")

    def __init__(self, numbers):
        super().__init__()
        self.numbers = numbers

    async def on_submit(self, interaction):
        await interaction.response.defer(thinking = True)

        solution = self.solution.value.replace('\\', "")

        value = check_solution(self.numbers, solution)

        embed = discord.Embed(color = interaction.client.bot_color)
        embed.set_author(
            name = interaction.user.display_name,
            icon_url = interaction.user.display_avatar.url
        )
        if value is False:
            embed.title = "Invalid"
            embed.description = f"`{solution}` is an invalid solution"
        elif value == 24:
            embed.title = "Correct!"
            embed.description = f"||`{solution} = 24`||"
        else:
            embed.title = "Incorrect"
            embed.description = f"`{solution} = {value}`"

        await interaction.followup.send(embed = embed)

