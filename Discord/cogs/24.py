
import discord
from discord import app_commands, ui
from discord.ext import commands

import sys

from utilities import checks

sys.path.insert(0, "..")
from units.twenty_four import check_solution, generate_numbers
sys.path.pop(0)


async def setup(bot):
    await bot.add_cog(TwentyFour())


class TwentyFour(commands.Cog, name = "24"):

    @commands.command(name = "24", aliases = ["twenty-four"])
    @checks.not_forbidden()
    async def twenty_four(self, ctx):
        """24 Game"""
        numbers = list(map(str, generate_numbers()))
        CEK = '\N{COMBINING ENCLOSING KEYCAP}'
        await ctx.embed_reply(
            f"{numbers[0]}{CEK}{numbers[1]}{CEK}\n"
            f"{numbers[2]}{CEK}{numbers[3]}{CEK}\n"
        )

        async def incorrect(message, value):
            response_ctx = await ctx.bot.get_context(message)
            await response_ctx.embed_reply(
                title = "Incorrect",
                description = f"`{message.content} = {value}`",
                in_response_to = False, attempt_delete = False
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
        await ctx.embed_reply(
            title = "Correct!", description = f"`{message.content} = 24`",
            in_response_to = False, attempt_delete = False
        )

    @app_commands.command(name = "24")
    async def slash_twenty_four(self, interaction):
        """24 Game"""
        numbers = list(map(str, generate_numbers()))
        CEK = '\N{COMBINING ENCLOSING KEYCAP}'
        view = TwentyFourView(numbers)
        await interaction.response.send_message(
            f"{numbers[0]}{CEK}{numbers[1]}{CEK}\n"
            f"{numbers[2]}{CEK}{numbers[3]}{CEK}",
            view = view
        )

        view.message = await interaction.original_message()
        interaction.client.views.append(view)


class TwentyFourView(ui.View):

    def __init__(self, numbers):
        super().__init__(timeout = None)

        self.add_item(TwentyFourSubmitSolutionButton(numbers))

        self.message = None

    async def stop(self):
        self.children[0].disabled = True

        if self.message:
            try:
                await self.message.edit(view = self)
            except discord.HTTPException as e:
                if e.code != 50083:  # 50083 == Thread is archived
                    raise

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
        value = check_solution(self.numbers, self.solution.value)

        if value is False:
            await interaction.response.send_message(
                f"`{self.solution.value}` is an invalid solution",
                ephemeral = True
            )
            return

        embed = discord.Embed(color = interaction.client.bot_color)
        embed.set_author(
            name = interaction.user.display_name,
            icon_url = interaction.user.avatar.url
        )
        if value == 24:
            embed.title = "Correct!"
            embed.description = f"||`{self.solution.value} = 24`||"
            await interaction.response.send_message(embed = embed)
        else:
            embed.title = "Incorrect"
            embed.description = f"`{self.solution.value} = {value}`"
            await interaction.response.send_message(embed = embed)
