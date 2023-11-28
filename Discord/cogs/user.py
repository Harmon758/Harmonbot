
import discord
from discord.ext import commands

import io
from typing import Optional

from PIL import Image, ImageOps

from utilities import checks


async def setup(bot):
    await bot.add_cog(User(bot))


class User(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    # TODO: Add commands
    #       ban, role removal
    #       username?, nickname?

    @commands.hybrid_group(aliases = ["member"], case_insensitive = True)
    async def user(self, ctx):
        """
        User
        All user subcommands are also commands
        """
        await ctx.send_help(ctx.command)

    # TODO: Integrate with role command
    @user.command(
        name = "add_role", aliases = ["addrole"], with_app_command = False
    )
    @commands.bot_has_guild_permissions(manage_roles = True)
    @commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner())
    async def user_add_role(self, ctx, member: discord.Member, *, role: discord.Role):
        '''Gives a user a role'''
        await member.add_roles(role)
        await ctx.embed_reply(f"I gave the role, {role}, to {member}")

    @commands.command(aliases = ["addrole"])
    @commands.bot_has_guild_permissions(manage_roles = True)
    @commands.check_any(
        commands.has_guild_permissions(manage_roles = True),
        commands.is_owner()
    )
    async def add_role(
        self, ctx, member: discord.Member, *, role: discord.Role
    ):
        """Gives a user a role"""
        await ctx.invoke(self.user_add_role, member = member, role = role)

    @user.command(name = "avatar")
    async def user_avatar(
        self, ctx,
        flip: Optional[bool] = False,  # noqa: UP007 (non-pep604-annotation)
        mirror: Optional[bool] = False,  # noqa: UP007 (non-pep604-annotation)
        *, user: discord.User = commands.Author
    ):
        """
        Show the avatar of a user

        Parameters
        ----------
        flip
            Whether or not to flip the avatar vertically
            (Defaults to False)
        mirror
            Whether or not to mirror the avatar horizontally
            (Defaults to False)
        user
            User to show avatar of
            (Defaults to command invoker)
        """
        # Note avatar command invokes this command
        await ctx.defer()

        description = f"{user.mention}**'s "
        file = None
        image_url = user.display_avatar.url

        if flip or mirror:
            buffer = io.BytesIO()
            await user.display_avatar.save(buffer, seek_begin = True)
            avatar = Image.open(buffer)

            if flip:
                avatar = ImageOps.flip(avatar)
                description += "(flipped) "

            if mirror:
                avatar = ImageOps.mirror(avatar)
                description += "(mirrored) "

            buffer = io.BytesIO()
            avatar.save(fp = buffer, format = "PNG")
            buffer.seek(0)

            file = discord.File(buffer, filename = "avatar.png")
            image_url = "attachment://avatar.png"

        description += f"[avatar]({user.display_avatar.url}):**"

        await ctx.embed_reply(
            author_name = None,
            description = description,
            image_url = image_url,
            file = file
        )

    @commands.command()
    async def avatar(
        self, ctx,
        flip: Optional[bool] = False,  # noqa: UP007 (non-pep604-annotation)
        mirror: Optional[bool] = False,  # noqa: UP007 (non-pep604-annotation)
        *, user: discord.User = commands.Author
    ):
        """
        Show the avatar of a user

        Parameters
        ----------
        flip
            Whether or not to flip the avatar vertically
            (Defaults to False)
        mirror
            Whether or not to mirror the avatar horizontally
            (Defaults to False)
        user
            User to show avatar of
            (Defaults to command invoker)
        """
        if command := ctx.bot.get_command("user avatar"):
            await ctx.invoke(
                command, flip = flip, mirror = mirror, user = user
            )
        else:
            raise RuntimeError(
                "user avatar command not found when avatar command invoked"
            )

    @user.command(name = "discriminator", with_app_command = False)
    async def user_discriminator(
        self, ctx, *,
        user: Optional[discord.Member]  # noqa: UP007 (non-pep604-annotation)
    ):
        '''
        Get a discriminator
        Your own or someone else's discriminator
        '''
        # Note: discriminator command invokes this command
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

    @commands.command()
    async def discriminator(self, ctx, *, user: Optional[discord.Member]):
        """
        Get a discriminator
        Your own or someone else's discriminator
        """
        if command := ctx.bot.get_command("user discriminator"):
            await ctx.invoke(command, user = user)
        else:
            raise RuntimeError(
                "user discriminator command not found "
                "when discriminator command invoked"
            )

    @user.command(name = "id")
    async def user_id(
        self, ctx, *, user: discord.User = commands.Author
    ):
        """
        Show the ID of a user

        Parameters
        ----------
        user
            User to show ID of
            (Defaults to command invoker)
        """
        # Note: id command invokes this command
        await ctx.embed_reply(
            description = f"{user.mention}'s ID: {user.id}",
            footer_icon_url = user.display_avatar.url,
            footer_text = str(user)
        )

    # TODO: Make general ID command with subcommands
    @commands.command()
    async def id(self, ctx, *, user: discord.User = commands.Author):
        """
        Show the ID of a user

        Parameters
        ----------
        user
            User to show ID of
            (Defaults to command invoker)
        """
        await ctx.invoke(self.user_id, user = user)

    @user.command(aliases = ["info"], with_app_command = False)
    async def information(
        self, ctx, *, user: discord.Member = commands.Author
    ):
        """Information about a user"""
        if command := ctx.bot.get_command("information user"):
            await ctx.invoke(command, user = user)
        else:
            raise RuntimeError(
                "information user command not found "
                "when user information command invoked"
            )

    # TODO: Make general name command with subcommands
    @user.command(name = "name", with_app_command = False)
    async def user_name(self, ctx, *, user: Optional[discord.Member]):
        '''The name of a user'''
        if not user:
            await ctx.embed_reply(ctx.author.mention)
        else:
            await ctx.embed_reply(
                user.mention,
                footer_text = str(user),
                footer_icon_url = user.avatar.url
            )

    @commands.command()
    async def name(self, ctx, *, user: Optional[discord.Member]):
        """The name of a user"""
        await ctx.invoke(self.user_name, user = user)

    @user.command(with_app_command = False)
    async def random(self, ctx):
        """Random user/member"""
        if command := ctx.bot.get_command("random user"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "random user command not found "
                "when user random command invoked"
            )

