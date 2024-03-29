
import discord
from discord.ext import commands

from utilities import checks


async def setup(bot):
    await bot.add_cog(Channel(bot))

class Channel(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        guild_only = await commands.guild_only().predicate(ctx)
        not_forbidden = await checks.not_forbidden().predicate(ctx)
        return guild_only and not_forbidden

    @commands.hybrid_group(case_insensitive = True)
    async def channel(self, ctx):
        '''Channel'''
        await ctx.send_help(ctx.command)

    @channel.command(name = "id")
    async def channel_id(
        self, ctx, *,
        channel: discord.abc.GuildChannel = commands.CurrentChannel
    ):
        """
        Show the ID of a channel

        Parameters
        ----------
        channel
            Channel to show the ID of
            (Defaults to the current text channel)
        """
        await ctx.embed_reply(channel.id)

    # TODO: help - filter subcommands list

    # TODO: commands/parameters; reason options?
    # TODO: default channel?: text, voice, category

    @channel.group(case_insensitive = True, with_app_command = False)
    async def category(self, ctx):
        '''Category'''
        await ctx.send_help(ctx.command)

    @category.command(name = "create", aliases = ["make", "new"], with_app_command = False)
    @commands.bot_has_guild_permissions(manage_channels = True)
    @commands.check_any(commands.has_guild_permissions(manage_channels = True), commands.is_owner())
    async def category_create(self, ctx, *, name : str):
        '''Create category'''
        channel = await ctx.guild.create_category_channel(name)
        await ctx.embed_reply(channel.mention + " created")

    @category.command(name = "name", with_app_command = False)
    async def category_name(self, ctx, channel : discord.CategoryChannel, *, name : str = ""):
        '''Name of a category'''
        if name:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await channel.edit(name = name)
            await ctx.embed_reply(channel.mention + " has been renamed")
        else:
            await ctx.embed_reply(channel)

    @category.command(name = "nsfw", with_app_command = False)
    async def category_nsfw(self, ctx, channel : discord.CategoryChannel, nsfw : bool = None):
        '''Whether a category is NSFW or not'''
        if nsfw is not None:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await channel.edit(nsfw = nsfw)
            await ctx.embed_reply(channel.mention + " has been set to {}NSFW".format("" if nsfw else "not "))
        else:
            await ctx.embed_reply(channel.mention + " is {}NSFW".format("" if channel.is_nsfw() else "not "))

    @category.command(name = "position", with_app_command = False)
    async def category_position(self, ctx, channel : discord.CategoryChannel, position : int = None):
        '''
        The position in the category list
        This is a number that starts at 0
        e.g. the top category is position 0
        '''
        if position is not None:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await channel.edit(position = position)
            await ctx.embed_reply(f"{channel.mention}'s position has been set to {position}")
        else:
            await ctx.embed_reply(f"{channel.mention}'s position is {channel.position}")

    # TODO: Alias text channel subcommands as channel subcommands
    @channel.group(case_insensitive = True, with_app_command = False)
    async def text(self, ctx):
        '''Text Channel'''
        await ctx.send_help(ctx.command)

    @text.command(name = "category", with_app_command = False)
    async def text_category(self, ctx, channel : discord.TextChannel, *, category : discord.CategoryChannel = None):
        '''Category the text channel belongs to'''
        if category:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await channel.edit(category = category)
            await ctx.embed_reply(channel.mention + " is now under " + category.mention)
        else:
            await ctx.embed_reply(channel.category.mention if channel.category else channel.mention + " is not under a category")

    @text.command(name = "create", aliases = ["make", "new"], with_app_command = False)
    @commands.bot_has_guild_permissions(manage_channels = True)
    @commands.check_any(commands.has_guild_permissions(manage_channels = True), commands.is_owner())
    async def text_create(self, ctx, name : str):
        '''Create text channel'''
        channel = await ctx.guild.create_text_channel(name)
        await ctx.embed_reply(channel.mention + " created")

    @text.command(name = "name", with_app_command = False)
    async def text_name(self, ctx, channel : discord.TextChannel, *, name : str = ""):
        '''Name of a text channel'''
        if name:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await channel.edit(name = name)
            await ctx.embed_reply(channel.mention + " has been renamed")
        else:
            await ctx.embed_reply(channel)

    @text.command(name = "nsfw", with_app_command = False)
    async def text_nsfw(self, ctx, channel : discord.TextChannel, nsfw : bool = None):
        '''Whether a text channel is NSFW or not'''
        if nsfw is not None:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await channel.edit(nsfw = nsfw)
            await ctx.embed_reply(channel.mention + " has been set to {}NSFW".format("" if nsfw else "not "))
        else:
            await ctx.embed_reply(channel.mention + " is {}NSFW".format("" if channel.is_nsfw() else "not "))

    @text.command(name = "position", with_app_command = False)
    async def text_position(self, ctx, channel : discord.TextChannel, position : int = None):
        '''
        The position in the channel list
        This is a number that starts at 0
        e.g. the top category is position 0
        '''
        if position is not None:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await channel.edit(position = position)
            await ctx.embed_reply(f"{channel.mention}'s position has been set to {position}")
        else:
            await ctx.embed_reply(f"{channel.mention}'s position is {channel.position}")

    @text.command(name = "slowmode", with_app_command = False)
    async def text_slowmode(self, ctx, channel : discord.TextChannel, slowmode_delay : int = None):
        '''
        Slowmode setting
        Slowmode delay must be between 0 and 120 inclusive
        Set slowmode delay to 0 to disable slowmode
        '''
        if slowmode_delay is not None:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            if slowmode_delay < 0:
                return await ctx.embed_reply("Slowmode delay must be greater than 0")
            elif slowmode_delay > 120:
                return await ctx.embed_reply("Slowmode dealy must be less than 120")
            await channel.edit(slowmode_delay = slowmode_delay)
            if slowmode_delay == 0:
                await ctx.embed_reply(f"Slowmode has been turned off for {channel.mention}")
            else:
                await ctx.embed_reply(f"Slowmode has been set to {slowmode_delay}s for {channel.mention}")
        elif channel.slowmode_delay:
            await ctx.embed_reply(f"Slowmode is set to {channel.slowmode_delay}s for {channel.mention}")
        else:
            await ctx.embed_reply(f"Slowmode is off for {channel.mention}")

    @text.command(name = "sync", with_app_command = False)
    @commands.bot_has_permissions(manage_channels = True, manage_permissions = True)
    @commands.check_any(commands.has_permissions(manage_channels = True, manage_permissions = True), commands.is_owner())
    async def text_sync(self, ctx, *, channel : discord.TextChannel):
        '''Sync permissions with category the text channel belongs to'''
        await channel.edit(sync_permissions = True)
        await ctx.embed_reply("Permissions synced with: " + channel.category.mention)

    @text.command(name = "topic", with_app_command = False)
    async def text_topic(self, ctx, channel : discord.TextChannel, *, topic : str = ""):
        '''Name of a text channel'''
        if topic:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await channel.edit(topic = topic)
            await ctx.embed_reply(channel.mention + "'s topic has been changed")
        else:
            await ctx.embed_reply(channel.topic)

    @text.command(name = "webhooks", aliases = ["webhook"], with_app_command = False)
    @commands.bot_has_permissions(manage_webhooks = True)
    @commands.check_any(
        commands.has_permissions(manage_webhooks = True), commands.is_owner()
    )
    async def text_webhooks(self, ctx):
        '''This text channel's webhooks'''
        webhooks = await ctx.channel.webhooks()
        await ctx.embed_reply(
            '\n'.join(webhook.name for webhook in webhooks),
            title = "This Channel's Webhooks"
        )

    # TODO: following command?
    # TODO: webhooks menu command

    @channel.group(case_insensitive = True, with_app_command = False)
    async def voice(self, ctx):
        '''Voice Channel'''
        await ctx.send_help(ctx.command)

    @voice.command(name = "bitrate", with_app_command = False)
    async def voice_bitrate(self, ctx, channel : discord.VoiceChannel, bitrate : int = None):
        '''Voice channel’s preferred audio bitrate in bits per second'''
        if bitrate is not None:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await channel.edit(bitrate = bitrate)
            await ctx.embed_reply(f"{channel.mention}'s bitrate has been set to {bitrate}")
        else:
            await ctx.embed_reply(f"{channel.mention}'s bitrate is {channel.bitrate}")

    @voice.command(name = "category", with_app_command = False)
    async def voice_category(self, ctx, channel : discord.VoiceChannel, *, category : discord.CategoryChannel = None):
        '''Category the voice channel belongs to'''
        if category:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await channel.edit(category = category)
            await ctx.embed_reply(channel.mention + " is now under " + category.mention)
        else:
            await ctx.embed_reply(channel.category.mention if channel.category else channel.mention + " is not under a category")

    @voice.command(name = "create", aliases = ["make", "new"], with_app_command = False)
    @commands.bot_has_guild_permissions(manage_channels = True)
    @commands.check_any(commands.has_guild_permissions(manage_channels = True), commands.is_owner())
    async def voice_create(self, ctx, *, name : str):
        '''Create voice channel'''
        channel = await ctx.guild.create_voice_channel(name)
        await ctx.embed_reply(channel.mention + " created")

    @voice.command(name = "name", with_app_command = False)
    async def voice_name(self, ctx, channel : discord.VoiceChannel, *, name : str = ""):
        '''Name of a voice channel'''
        if name:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await channel.edit(name = name)
            await ctx.embed_reply(channel.mention + " has been renamed")
        else:
            await ctx.embed_reply(channel)

    @voice.command(name = "position", with_app_command = False)
    async def voice_position(self, ctx, channel : discord.VoiceChannel, position : int = None):
        '''
        The position in the channel list
        This is a number that starts at 0
        e.g. the top category is position 0
        '''
        if position is not None:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await channel.edit(position = position)
            await ctx.embed_reply(f"{channel.mention}'s position has been set to {position}")
        else:
            await ctx.embed_reply(f"{channel.mention}'s position is {channel.position}")

    @voice.command(name = "sync", with_app_command = False)
    @commands.bot_has_permissions(manage_channels = True, manage_permissions = True)
    @commands.check_any(commands.has_permissions(manage_channels = True, manage_permissions = True), commands.is_owner())
    async def voice_sync(self, ctx, *, channel : discord.VoiceChannel):
        '''Sync permissions with category the voice channel belongs to'''
        await channel.edit(sync_permissions = True)
        await ctx.embed_reply("Permissions synced with: " + channel.category.mention)

    @voice.command(name = "user_limit", aliases = ["userlimit"], with_app_command = False)
    async def voice_user_limit(self, ctx, channel : discord.VoiceChannel, user_limit : int = None):
        '''Limit for number of members that can be in the voice channel'''
        if user_limit is not None:
            await checks.has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await checks.bot_has_permissions_for(channel, manage_channels = True).predicate(ctx)
            await channel.edit(user_limit = user_limit)
            await ctx.embed_reply(f"{channel.mention}'s user limit has been set to {user_limit}")
        else:
            await ctx.embed_reply(f"{channel.mention}'s user limit is {channel.user_limit}")

