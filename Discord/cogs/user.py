
import discord
from discord.ext import commands

from typing import Optional

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

    @commands.group(
        aliases = ["member"],
        case_insensitive = True, invoke_without_command = True
    )
    async def user(self, ctx):
        '''
        User
        All user subcommands are also commands
        '''
        await ctx.send_help(ctx.command)

    # TODO: Integrate with role command
    @user.command(name = "add_role", aliases = ["addrole"])
    @commands.bot_has_guild_permissions(manage_roles = True)
    @commands.check_any(commands.has_guild_permissions(manage_roles = True), commands.is_owner())
    async def user_add_role(self, ctx, member : discord.Member, *, role : discord.Role):
        '''Gives a user a role'''
        await member.add_roles(role)
        await ctx.embed_reply("I gave the role, {}, to {}".format(role, member))

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
    async def user_avatar(self, ctx, *, user: Optional[discord.Member]):
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
    async def avatar(self, ctx, *, user: Optional[discord.Member]):
        """
        See a bigger version of an avatar
        Your own or someone else's avatar
        """
        await ctx.invoke(self.user_avatar, user = user)

    @user.command(name = "discriminator")
    async def user_discriminator(self, ctx, *, user: Optional[discord.Member]):
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

    @commands.command()
    async def discriminator(self, ctx, *, user: Optional[discord.Member]):
        """
        Get a discriminator
        Your own or someone else's discriminator
        """
        await ctx.invoke(self.user_discriminator, user = user)

    # TODO: Make general ID command with subcommands
    @user.command(name = "id")
    async def user_id(self, ctx, *, user: Optional[discord.Member]):
        '''Get ID of user'''
        if not user:
            await ctx.embed_reply(f"Your ID: {ctx.author.id}")
        else:
            await ctx.embed_reply(
                f"{user.mention}'s ID: {user.id}",
                footer_text = str(user),
                footer_icon_url = user.avatar.url
            )

    @commands.command()
    async def id(self, ctx, *, user: Optional[discord.Member]):
        """Get ID of user"""
        await ctx.invoke(self.user_id, user = user)

    # TODO: Make general name command with subcommands
    @user.command(name = "name")
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

