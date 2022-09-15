
from discord import app_commands
from discord.ext import commands

import logging
import sys
import traceback

import sentry_sdk


class CommandTree(app_commands.CommandTree):

    async def on_error(self, interaction, error):
        if (
            isinstance(error, app_commands.TransformerError) and
            isinstance(
                error.__cause__, commands.PartialEmojiConversionFailure
            )
        ):
            ctx = await interaction.client.get_context(interaction)
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} "
                f"`{error.value}` doesn't seem to be a custom emoji"
            )
            return

        sentry_sdk.capture_exception(error)
        print(
            f"Ignoring exception in slash command {interaction.command.name}",
            # TODO: Use full name
            file = sys.stderr
        )
        traceback.print_exception(
            type(error), error, error.__traceback__, file = sys.stderr
        )
        logging.getLogger("errors").error(
            "Uncaught exception\n",
            exc_info = (type(error), error, error.__traceback__)
        )
