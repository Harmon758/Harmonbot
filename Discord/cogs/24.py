
from __future__ import annotations

import discord
from discord import app_commands, ui
from discord.ext import commands

from typing import TYPE_CHECKING

from units.twenty_four import check_solution, generate_numbers
from utilities import checks

if TYPE_CHECKING:
    from utilities.context import Context


CEK = '\N{COMBINING ENCLOSING KEYCAP}'


async def setup(bot):
    await bot.add_cog(TwentyFour())


class TwentyFour(commands.Cog, name = "24"):

    @commands.hybrid_command(name = "24", aliases = ["twenty-four"])
    @app_commands.allowed_installs(guilds = True, users = False)
    @app_commands.allowed_contexts(
        guilds = True, dms = False, private_channels = False
    )
    @checks.not_forbidden()
    async def twenty_four(self, ctx: Context):
        """24 Game"""
        await ctx.defer()

        numbers = list(map(str, generate_numbers()))
        view = TwentyFourLayoutView(ctx, numbers)
        response = await ctx.send(
            view = view, allowed_mentions = discord.AllowedMentions.none()
        )
        if ctx.interaction:
            # InteractionMessage token expires after 15 min.
            try:
                response = await response.fetch()
            except discord.Forbidden:
                view.timeout = 600
                response = await response.edit(
                    view = view,
                    allowed_mentions = discord.AllowedMentions.none()
                )
        view.message = response
        ctx.bot.views.append(view)

        async def incorrect(message, value):
            solution = message.content.replace('\\', "")
            solution_view = ui.LayoutView(timeout = 0)
            solution_view.add_item(
                ui.Container(
                    ui.TextDisplay(
                        f"### {message.author.mention}: Incorrect\n"
                        f"`{solution} = {value}`"
                    )
                )
            )
            await message.channel.send(
                reference = response,
                view = solution_view,
                allowed_mentions = discord.AllowedMentions.none()
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
        solution = message.content.replace('\\', "")
        solution_view = ui.LayoutView(timeout = 0)
        solution_view.add_item(
            ui.Container(
                ui.TextDisplay(
                    f"### {message.author.mention}: Correct!\n"
                    f"`{solution} = 24`"
                )
            )
        )
        solution_message = await ctx.send(
            reference = response,
            view = solution_view,
            allowed_mentions = discord.AllowedMentions.none()
        )
        await view.add_solver(message.author, solution_message)
        await view.stop()


class TwentyFourLayoutView(ui.LayoutView):

    def __init__(self, ctx, numbers):
        super().__init__(timeout = None)

        self.bot = ctx.bot

        if not ctx.interaction:
            self.add_item(
                ui.TextDisplay(
                    f"-# In response to {ctx.author.mention}:\n"
                    f"-# > {ctx.message.clean_content}"
                )
            )

        self.add_item(
            ui.Container(
                ui.TextDisplay(
                    f"# {numbers[0]}{CEK}   {numbers[1]}{CEK}\n"
                    f"# {numbers[2]}{CEK}   {numbers[3]}{CEK}",
                )
            )
        )

        action_row = ui.ActionRow()
        self.submit_solution_button = TwentyFourSubmitSolutionButton(numbers)
        action_row.add_item(self.submit_solution_button)
        action_row.add_item(
            ui.Button(
                style = discord.ButtonStyle.link,
                emoji = '\N{INFORMATION SOURCE}',
                url = "https://en.wikipedia.org/wiki/24_(puzzle)"
            )
        )
        self.add_item(action_row)

        self.message = None
        self.solvers = ""

    async def add_solver(self, solver, solution_message):
        if self.solvers:
            self.remove_item(self.children[-1])

        self.solvers += (
            f"[Solved]({solution_message.jump_url}) by {solver.mention}\n"
        )
        self.add_item(ui.Container(ui.TextDisplay(self.solvers)))

        await self.bot.attempt_edit_message(
            self.message, view = self,
            allowed_mentions = discord.AllowedMentions.none()
        )

    async def on_timeout(self):
        await self.stop()

    async def stop(self):
        self.submit_solution_button.disabled = True

        if self.message:
            await self.bot.attempt_edit_message(
                self.message, view = self,
                allowed_mentions = discord.AllowedMentions.none()
            )

        super().stop()


class TwentyFourSubmitSolutionButton(ui.Button):

    def __init__(self, numbers):
        super().__init__(label = "Submit Solution")
        self.numbers = numbers

    async def callback(self, interaction):
        await interaction.response.send_modal(
            TwentyFourSubmitSolutionModal(self.view, self.numbers)
        )


class TwentyFourSubmitSolutionModal(ui.Modal, title = "Submit Solution"):

    solution = ui.TextInput(label = "Solution")

    def __init__(self, view, numbers):
        super().__init__()
        self.numbers = numbers
        self.view = view

    async def on_submit(self, interaction):
        await interaction.response.defer(thinking = True)

        solution = self.solution.value.replace('\\', "")
        value = check_solution(self.numbers, solution)
        text = f"### {interaction.user.mention}: "
        if value is False:
            text += "Invalid\n"
            text += f"`{solution}` is an invalid solution"
        elif value == 24:
            text += "Correct!\n"
            text += f"||`{solution} = 24`||"
        else:
            text += "Incorrect\n"
            text += f"`{solution} = {value}`"

        view = ui.LayoutView(timeout = 0)
        view.add_item(ui.Container(ui.TextDisplay(text)))

        solution_message = await interaction.followup.send(
            view = view, allowed_mentions = discord.AllowedMentions.none()
        )

        if value == 24:
            await self.view.add_solver(interaction.user, solution_message)

