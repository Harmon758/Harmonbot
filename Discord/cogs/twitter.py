
import discord
from discord.ext import commands

import functools
import html
import io
import logging
import sys
import traceback

from more_itertools import chunked
import feedparser
import tweepy
import tweepy.asynchronous

from utilities import checks


errors_logger = logging.getLogger("errors")

async def setup(bot):
    await bot.add_cog(Twitter(bot))

class Twitter(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.streaming_client = TwitterStreamingClient(bot)

    async def cog_load(self):
        # Initialize database
        await self.bot.connect_to_database()
        await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS twitter")
        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS twitter.handles (
                channel_id   BIGINT,
                handle       TEXT,
                replies      BOOL,
                retweets     BOOL,
                PRIMARY KEY  (channel_id, handle)
            )
            """
        )
        # Start stream
        self.task = self.bot.loop.create_task(
            self.start_stream(), name = "Start Twitter Stream"
        )

    def cog_unload(self):
        if self.streaming_client:
            self.streaming_client.disconnect()
        self.task.cancel()

    @commands.hybrid_group(case_insensitive = True)
    @checks.not_forbidden()
    async def twitter(self, ctx):
        """Twitter"""
        await ctx.send_help(ctx.command)

    @twitter.command(name = "status")
    @checks.not_forbidden()
    async def twitter_status(
        self, ctx, handle: str, replies: bool = False, retweets: bool = False
    ):
        """
        Show a Twitter user's most recent Tweet

        Parameters
        ----------
        handle
            Handle/Username of Twitter user for which to show most recent Tweet
        replies
            Whether or not to include replies
            (Defaults to False)
        retweets
            Whether or not to include retweets
            (Defaults to False)
        """
        await ctx.defer()

        username = handle.lstrip('@')

        async with ctx.bot.aiohttp_session.get(
            "https://openrss.org/twitter.com/" + username
        ) as resp:
            if resp.status == 404:
                await ctx.embed_reply(
                    f"{ctx.bot.error_emoji} Error: User not found"
                )
                return
            feed_text = await resp.text()

        feed_info = await self.bot.loop.run_in_executor(
            None,
            functools.partial(
                feedparser.parse,
                io.BytesIO(feed_text.encode("UTF-8"))
            )
        )
        # Necessary to run in executor?

        # TODO: Change to pagination
        for entry in feed_info.entries:
            if not retweets and (
                entry.title[
                    :len(username) + 13  # 13 == len("@ retweeted: ")
                ].lower() == f"@{username.lower()} retweeted: "
            ):
                continue

            if not replies and (
                entry.title[
                    :len(username) + 14  #14 == len("@ replied to: ")
                ].lower() == f"@{username.lower()} replied to: "
            ):
                continue

            await ctx.reply(entry.link)
            return

        await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Status not found")

    @twitter.command(
        name = "add", aliases = ["addhandle", "handleadd"],
        with_app_command = False
    )
    @commands.check_any(checks.is_permitted(), checks.is_guild_owner())
    async def twitter_add(self, ctx, handle: str):
        """
        Add a Twitter handle to a text channel
        A delay of up to 2 min. is possible due to Twitter rate limits
        """
        handle = handle.lstrip('@')
        following = await ctx.bot.db.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM twitter.handles
                WHERE channel_id = $1 AND handle = $2
            )
            """,
            ctx.channel.id, handle
        )
        if following:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} This text channel "
                "is already following that Twitter handle"
            )
            return
        message = await ctx.embed_reply("\N{HOURGLASS} Please wait")
        embed = message.embeds[0]
        try:
            await self.streaming_client.add_feed(ctx.channel, handle)
        except tweepy.TweepyException as e:
            embed.description = f"{ctx.bot.error_emoji} Error: {e}"
            await message.edit(embed = embed)
            return
        await ctx.bot.db.execute(
            """
            INSERT INTO twitter.handles (channel_id, handle)
            VALUES ($1, $2)
            """,
            ctx.channel.id, handle
        )
        embed.description = (
            "Added the Twitter handle, "
            f"[`{handle}`](https://twitter.com/{handle}), "
            "to this text channel"
        )
        await message.edit(embed = embed)

    @twitter.command(
        name = "remove",
        aliases = [
            "delete", "removehandle", "handleremove", "deletehandle",
            "handledelete"
        ],
        with_app_command = False
    )
    @commands.check_any(checks.is_permitted(), checks.is_guild_owner())
    async def twitter_remove(self, ctx, handle: str):
        """
        Remove a Twitter handle from a text channel
        A delay of up to 2 min. is possible due to Twitter rate limits
        """
        handle = handle.lstrip('@')
        deleted = await ctx.bot.db.fetchval(
            """
            DELETE FROM twitter.handles
            WHERE channel_id = $1 AND handle = $2
            RETURNING *
            """,
            ctx.channel.id, handle
        )
        if not deleted:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} This text channel "
                "isn't following that Twitter handle"
            )
            return
        message = await ctx.embed_reply("\N{HOURGLASS} Please wait")
        await self.streaming_client.remove_feed(ctx.channel, handle)
        embed = message.embeds[0]
        embed.description = (
            "Removed the Twitter handle, "
            f"[`{handle}`](https://twitter.com/{handle}), "
            "from this text channel."
        )
        await message.edit(embed = embed)

    @twitter.command(
        aliases = ["handle", "feeds", "feed", "list"],
        with_app_command = False
    )
    @checks.not_forbidden()
    async def handles(self, ctx):
        """Show Twitter handles being followed in a text channel"""
        records = await ctx.bot.db.fetch(
            """
            SELECT handle FROM twitter.handles
            WHERE channel_id = $1
            """, 
            ctx.channel.id
        )
        await ctx.embed_reply(
            title = "Twitter handles being followed in this channel",
            description = '\n'.join(sorted(
                [record["handle"] for record in records],
                key = str.casefold
            ))
        )
        # TODO: Add message if none

    @twitter.command(aliases = ["maintenance"], with_app_command = False)
    @commands.is_owner()
    async def purge(self, ctx):
        last_resort_notices_channel = ctx.bot.get_channel(
            ctx.bot.last_resort_notices_channel_id
        )

        records = await ctx.bot.db.fetch("SELECT * FROM twitter.handles")
        channel_ids = set(record["channel_id"] for record in records)
        for channel_id in channel_ids:
            try:
                await ctx.bot.fetch_channel(channel_id)
            except discord.NotFound:
                deleted = await ctx.bot.db.fetch(
                    """
                    DELETE FROM twitter.handles
                    WHERE channel_id = $1
                    RETURNING *
                    """,
                    channel_id
                )
                for record in deleted:
                    await last_resort_notices_channel.send(
                        f"<#{record['channel_id']}> is no longer following "
                        f"`{record['handle']}` as a Twitter handle, "
                        "as the channel can no longer be found "
                        "(i.e. was deleted)."
                    )
            except discord.Forbidden:
                ctx.bot.print(f"Forbidden: {channel_id}")

        usernames = set(record["handle"] for record in records)
        usernames_not_found = []
        for usernames_chunk in chunked(usernames, 100):
            response = await self.bot.twitter_client.get_users(
                usernames = usernames_chunk
            )
            for error in response.errors:
                if error["title"] == "Not Found Error":
                    usernames_not_found.append(error["value"])
        for username in usernames_not_found:
            deleted = await ctx.bot.db.fetch(
                """
                DELETE FROM twitter.handles
                WHERE handle = $1
                RETURNING *
                """,
                username
            )
            for record in deleted:
                notice = (
                    f"<#{record['channel_id']}> is no longer following"
                    f"`{record['handle']}` as a Twitter handle, "
                    "as the handle can no longer be found "
                    "(i.e. no longer exists)."
                )
                ctx.bot.print(notice)
                try:
                    channel = ctx.bot.get_channel(record["channel_id"]) or (
                        await ctx.bot.fetch_channel(record["channel_id"])
                    )
                except discord.Forbidden:
                    await last_resort_notices_channel.send(notice)
                else:
                    try:
                        await channel.send(notice)
                    except discord.Forbidden:
                        await last_resort_notices_channel.send(notice)

        await ctx.embed_reply("Purge complete")

    async def start_stream(self):
        await self.bot.wait_until_ready()
        try:
            records = await self.bot.db.fetch("SELECT * FROM twitter.handles")
            usernames = {}
            for record in records:
                usernames[record["handle"].lower()] = (
                    usernames.get(record["handle"].lower(), []) +
                    [record["channel_id"]]
                )
            await self.streaming_client.start_feeds(usernames = usernames)
        except Exception as e:
            print("Exception in Twitter Task", file = sys.stderr)
            traceback.print_exception(
                type(e), e, e.__traceback__, file = sys.stderr
            )
            errors_logger.error(
                "Uncaught Twitter Task exception\n",
                exc_info = (type(e), e, e.__traceback__)
            )
            return


def process_tweet_text(text, entities):
    mentions = {}
    for mention in entities.get("mentions", ()):
        mentions[text[mention["start"]:mention["end"]]] = mention["username"]
    for mention, screen_name in mentions.items():
        text = text.replace(
            mention,
            f"[{mention}](https://twitter.com/{screen_name})"
        )
    for hashtag in entities.get("hashtags", ()):
        tag = hashtag.get("text") or hashtag.get("tag")
        text = text.replace(
            '#' + tag,
            f"[#{tag}](https://twitter.com/hashtag/{tag})"
        )
    for cashtag in entities.get("cashtags", ()):
        text = text.replace(
            '$' + cashtag["tag"],
            f"[${cashtag['tag']}](https://twitter.com/search?q=${cashtag['tag']})"
        )
    for url in entities.get("urls", ()):
        text = text.replace(url["url"], url["expanded_url"])
    # Remove Variation Selector-16 characters
    # Unescape HTML entities (&gt;, &lt;, &amp;, etc.)
    return html.unescape(text.replace('\uFE0F', ""))


class TwitterStreamingClient(tweepy.asynchronous.AsyncStreamingClient):

    def __init__(self, bot):
        super().__init__(bot.TWITTER_BEARER_TOKEN)
        self.bot = bot
        self.usernames = {}

    async def start_feeds(self, *, usernames = None):
        if usernames:
            self.usernames = usernames

        if self.session and self.session.closed:
            self.session = None

        response = await self.get_rules()
        if rules := response.data:
            await self.delete_rules([rule.id for rule in rules])

        rule = ""
        rules = []
        for username in self.usernames:
            if len(rule) + len(username) + 5 > 512:  # 5 == len("from:")
                rules.append(tweepy.StreamRule(rule[:-4]))  # 4 == len(" OR ")
                rule = ""
            rule += f"from:{username} OR "
        rules.append(tweepy.StreamRule(rule[:-4]))  # 4 == len(" OR ")
        await self.add_rules(rules)

        if self.task is None or self.task.done():
            self.filter(
                expansions = ["attachments.media_keys", "author_id"],
                media_fields = ["url"],
                tweet_fields = [
                    "attachments", "created_at", "entities",
                    "in_reply_to_user_id"
                ],
                user_fields = ["profile_image_url"]
            )

    async def add_feed(self, channel, handle):
        if channels := self.usernames.get(handle):
            channels.append(channel.id)
        else:
            self.usernames[handle] = [channel.id]
            await self.start_feeds()

    async def remove_feed(self, channel, handle):
        channel_ids = self.usernames[handle]
        channel_ids.remove(channel.id)
        if not channel_ids:
            del self.usernames[handle]

        await self.start_feeds()  # Necessary?

    async def on_response(self, response):
        if response.errors and not response.data:
            return

        tweet = response.data
        author = response.includes["users"][0]
        # Ignore replies
        if tweet.in_reply_to_user_id:
            return
        # TODO: Settings for including replies, retweets, etc.
        for channel_id in self.usernames.get(author.username.lower(), ()):
            channel = self.bot.get_channel(channel_id)
            if not channel:
                # TODO: Handle channel no longer accessible
                continue
            embeds = [
                discord.Embed(
                    color = self.bot.twitter_color,
                    description = process_tweet_text(tweet.text, tweet.entities),
                    timestamp = tweet.created_at,
                ).set_author(
                    name = f"{author.name} (@{author.username})",
                    icon_url = author.profile_image_url,
                    url = f"https://twitter.com/{author.username}"
                ).set_footer(
                    icon_url = self.bot.twitter_icon_url,
                    text = "Twitter"
                )
            ]
            medias = {
                media["media_key"]: media
                for media in response.includes.get("media", ())
            }
            tweet_url = f"https://twitter.com/{author.username}/status/{tweet.id}"
            for media_key in (tweet.attachments or {}).get("media_keys", ()):
                media = medias[media_key]
                if media["type"] != "photo":
                    continue
                if not embeds[0].image:
                    embeds[0].set_image(url = media["url"])
                    for url in tweet.entities["urls"]:
                        if url.get("media_key") == media_key:
                            embeds[0].description = embeds[0].description.replace(
                                url["expanded_url"], ""
                            )
                    embeds[0].url = tweet_url
                else:
                    embeds.append(
                        discord.Embed(
                            url = tweet_url
                        ).set_image(url = media["url"])
                    )
            try:
                await channel.send(
                    content = f"<{tweet_url}>",
                    embeds = embeds
                )
            except discord.Forbidden:
                try:
                    await channel.send(content = tweet_url)
                except discord.Forbidden:
                    # TODO: Handle unable to send messages in text channel
                    self.bot.print(
                        "Twitter Stream: Missing permissions to send message "
                        f"in #{channel.name} in {channel.guild.name}"
                    )
            except discord.DiscordServerError as e:
                self.bot.print(f"Twitter Stream Discord Server Error: {e}")

    async def on_errors(self, errors):
        for error in errors:
            if (
                error.get("title") == "operational-disconnect" or
                error.get("disconnect_type") == "OperationalDisconnect"
            ):
                self.bot.print(
                    "Twitter stream reconnecting from operational disconnect"
                )
                self.bot.loop.create_task(
                    self.reconnect(), name = "Reconnect Twitter Stream"
                )
            else:
                self.bot.print(f"Twitter Stream received error: {error}")

    async def reconnect(self):
        self.disconnect()
        await self.task
        await self.start_feeds()

    async def on_request_error(self, status_code):
        self.bot.print(f"Twitter Error: {status_code}")

