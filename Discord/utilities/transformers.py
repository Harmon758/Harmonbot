
import discord
from discord import app_commands
from discord.ext import commands


class PartialEmojiTransformer(app_commands.Transformer):

    @classmethod
    async def transform(
        cls, interaction: discord.Interaction, value: str
    ) -> discord.PartialEmoji:
        ctx = await interaction.client.get_context(interaction)
        return await commands.PartialEmojiConverter().convert(ctx, value)

