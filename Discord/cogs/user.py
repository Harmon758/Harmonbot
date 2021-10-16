
import discord
from discord.ext import commands

import inspect
from typing import Optional

from utilities import checks


def setup(bot):
    bot.add_cog(User(bot))


class User(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        for name, command in inspect.getmembers(self):
            if isinstance(command, commands.Command) and command.parent is None and name != "user":
                self.bot.add_command(command)
                self.user.add_command(command)

    # TODO: Add commands
    #       ban, role removal
    #       username?, nickname?

    @commands.group(aliases = ["member"], invoke_without_command = True, case_insensitive = True)
    @checks.not_forbidden()
    async def user(self, ctx):
        '''
        User
        All user subcommands are also commands
        '''
        await ctx.send_help(ctx.command)

    # TODO: Integrate with role command
    @commands.command(aliases = ["addrole"])
    @commands.bot_has_guild_permissions(manage_roles = True)
    @commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner())
    async def add_role(self, ctx, member : discord.Member, *, role : discord.Role):
        '''Gives a user a role'''
        await member.add_roles(role)
        await ctx.embed_reply("I gave the role, {}, to {}".format(role, member))

    @commands.command()
    @checks.not_forbidden()
    async def avatar(self, ctx, *, user: Optional[discord.Member]):
        '''
        See a bigger version of an avatar
        Your own or someone else's avatar
        '''
        if not user:
            await ctx.embed_reply(
                title = "Your avatar",
                image_url = ctx.author.display_avatar.url
            )
        else:
            await ctx.embed_reply(
                title = f"{user}'s avatar",
                image_url = user.display_avatar.url
            )

    @commands.command()
    @checks.not_forbidden()
    async def discriminator(self, ctx, *, user: Optional[discord.Member]):
        '''
        Get a discriminator
        Your own or someone else's discriminator
        '''
        if not user:
            await ctx.embed_reply(
                f"Your discriminator: #{ctx.author.discriminator}"
            )
        else:
            await ctx.embed_reply(
                f"{user.mention}'s discriminator: #{user.discriminator}",
                footer_text = str(user),
                footer_icon_url = user.display_avatar.url
            )

    # TODO: Make general ID command with subcommands
    @commands.command(name = "id")
    @checks.not_forbidden()
    async def id_command(self, ctx, *, user: Optional[discord.Member]):
        '''Get ID of user'''
        if not user:
            await ctx.embed_reply(f"Your ID: {ctx.author.id}")
        else:
            await ctx.embed_reply(
                f"{user.mention}'s ID: {user.id}",
                footer_text = str(user),
                footer_icon_url = user.avatar.url
            )

    # TODO: Make general name command with subcommands
    @commands.command()
    @checks.not_forbidden()
    async def name(self, ctx, *, user: Optional[discord.Member]):
        '''The name of a user'''
        if not user:
            await ctx.embed_reply(ctx.author.mention)
        else:
            await ctx.embed_reply(
                user.mention,
                footer_text = str(user),
                footer_icon_url = user.avatar.url
            )

