
from discord import app_commands
from discord.ext import commands

import logging
import sys
import traceback

import sentry_sdk


class CommandTree(app_commands.CommandTree):

    async def on_error(self, interaction, error):
        # Command Invoke Error
        if isinstance(error, app_commands.CommandInvokeError):
            # Bot missing permissions
            if isinstance(error.original, commands.BotMissingPermissions):
                bot = interaction.client
                ctx = await bot.get_context(interaction)
                missing_permissions = bot.inflect_engine.join([
                    f"`{permission}`"
                    for permission in error.original.missing_permissions
                ])
                permission_declension = bot.inflect_engine.plural(
                    'permission', len(error.original.missing_permissions)
                )
                await ctx.embed_reply(
                    "I don't have permission to do that here\n"
                    f"I need the {missing_permissions} {permission_declension}"
                )
                return

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
            "Ignoring exception in slash command /" +
            interaction.command.qualified_name,
            file = sys.stderr
        )
        traceback.print_exception(
            type(error), error, error.__traceback__, file = sys.stderr
        )
        logging.getLogger("errors").error(
            "Uncaught exception\n",
            exc_info = (type(error), error, error.__traceback__)
        )
