
from discord import app_commands
from discord.ext import commands

import logging
import sys
import traceback

import sentry_sdk


class CommandTree(app_commands.CommandTree):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_command_models = {}

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
                    "permission", len(error.original.missing_permissions)
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

    async def fetch_commands(self, *, guild = None):
        app_command_models = await super().fetch_commands(guild = guild)

        if not guild:
            await self.update_app_command_models(app_command_models)

        return app_command_models

    async def sync(self, *, guild = None):
        app_command_models = await super().sync(guild = guild)

        if not guild:
            await self.update_app_command_models(app_command_models)

        return app_command_models

    async def update_app_command_models(self, app_command_models):
        self.app_command_models = {}
        for command in app_command_models:
            self.app_command_models[command.name] = command
            for option in command.options:
                if isinstance(option, app_commands.AppCommandGroup):
                    self.app_command_models[option.qualified_name] = option
                    for suboption in option.options:
                        if isinstance(suboption, app_commands.AppCommandGroup):
                            self.app_command_models[
                                suboption.qualified_name
                            ] = suboption

