
from discord import app_commands

import logging
import sys
import traceback

import sentry_sdk


class CommandTree(app_commands.CommandTree):

    async def on_error(self, interaction, error):
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
