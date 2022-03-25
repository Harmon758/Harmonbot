
from discord.ext import commands

import sys

from utilities import checks

sys.path.insert(0, "..")
from units.twenty_four import check_solution, generate_numbers
sys.path.pop(0)


def setup(bot):
    bot.add_cog(TwentyFour())


class TwentyFour(commands.Cog, name = "24"):

    @commands.command(name = "24", aliases = ["twenty-four"])
    @checks.not_forbidden()
    async def twenty_four(self, ctx):
        '''24 Game'''
        numbers = generate_numbers()

        CEK = '\N{COMBINING ENCLOSING KEYCAP}'
        numbers = list(map(str, numbers))
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
