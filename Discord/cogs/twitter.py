
import discord
from discord.ext import commands

import asyncio
import datetime
import functools
import io
import logging
import re
import sys
import traceback
import urllib.parse

import aiohttp
from more_itertools import chunked
import feedparser

from units import nitter
from utilities import checks, tasks


errors_logger = logging.getLogger("errors")

MAX_AGE_REGEX_PATTERN = re.compile(r"max-age=(\d+)")

async def setup(bot):
    await bot.add_cog(Twitter(bot))

class Twitter(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.check_tweets.start().set_name("Twitter")

    async def cog_load(self):
        # Initialize database
        await self.bot.connect_to_database()
        await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS twitter")
        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS twitter.handles (
                channel_id    BIGINT,
                handle        TEXT,
                replies       BOOL,
                retweets      BOOL,
                last_checked  TIMESTAMPTZ,
                ttl           INT,
                max_age       INT,
                etag          TEXT,
                PRIMARY KEY   (channel_id, handle)
            )
            """
        )
        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS twitter.tweets (
                link         TEXT,
                handle       TEXT,
                PRIMARY KEY  (link, handle)
            )
            """
        )
        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS twitter.errors (
                timestamp  TIMESTAMPTZ PRIMARY KEY DEFAULT NOW(), 
                handle     TEXT, 
                type       TEXT, 
                message	   TEXT
            )
            """
        )

    def cog_unload(self):
        self.check_tweets.cancel()

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

        nitter_instance_url = await nitter.get_best_healthy_rss_instance_url()

        async with ctx.bot.aiohttp_session.get(
            f"{nitter_instance_url}/{username}/rss"
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
                entry.author.lstrip('@').lower() != username.lower()
            ):
                continue

            if not replies and entry.title.startswith("R to @"):
                # TODO: Handle false positives
                continue

            await ctx.reply(
                urllib.parse.urlparse(entry.link)._replace(
                    scheme = "https",
                    netloc = "twitter.com",
                    fragment = ""
                ).geturl()
            )
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

        record = await ctx.bot.db.fetchrow(
            """
            SELECT * FROM twitter.handles
            WHERE handle = $1
            LIMIT 1
            """,
            handle
        )

        if record:  # Following elsewhere
            await self.bot.db.execute(
                """
                INSERT INTO twitter.handles (channel_id, handle, last_checked, ttl, max_age, etag)
                VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                ctx.channel.id, handle, record["last_checked"], record["ttl"],
                record["max_age"], record["etag"]
            )
        else:
            nitter_instance_url = (
                await nitter.get_random_healthy_rss_instance_url()
            )
            async with self.bot.aiohttp_session.get(
                f"{nitter_instance_url}/{handle}/rss"
            ) as resp:
                # TODO: Use structural pattern matching with Python 3.10
                if resp.status == 400:
                    await ctx.embed_reply(
                        f"{ctx.bot.error_emoji} User not found:\n"
                        f"> `{handle}` doesn't appear to be a valid Twitter "
                        f"user at https://twitter.com/{handle}\n"
                        "> If the user existed before, they may have been "
                        "suspended or banned."
                    )
                    return
                elif resp.status == 404:
                    await ctx.embed_reply(
                        f"{ctx.bot.error_emoji} User not found:\n"
                        f"> The page at https://twitter.com/{handle} is "
                        "either invalid, private, requires login, or doesn't "
                        "exist"
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

            ttl = None
            if "ttl" in feed_info.feed:
                ttl = int(feed_info.feed.ttl)
            await self.bot.db.execute(
                """
                INSERT INTO twitter.handles (channel_id, handle, last_checked, ttl)
                VALUES ($1, $2, NOW(), $3)
                """, 
                ctx.channel.id, handle, ttl
            )

            for entry in feed_info.entries:
                if not (link := entry.get("link")):
                    # TODO: Handle?
                    continue

                link = urllib.parse.urlparse(link)._replace(
                    scheme = "https",
                    netloc = "twitter.com",
                    fragment = ""
                ).geturl()

                await self.bot.db.execute(
                    """
                    INSERT INTO twitter.tweets (link, handle)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                    """,
                    link, handle
                )

        await ctx.embed_reply(
            "Added the Twitter handle, "
            f"[`{handle}`](https://twitter.com/{handle}), "
            "to this text channel"
        )

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
        await ctx.embed_reply(
            "Removed the Twitter handle, "
            f"[`{handle}`](https://twitter.com/{handle}), "
            "from this text channel."
        )

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
                    await ctx.bot.last_resort_notices_channel.send(
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
                    await ctx.bot.last_resort_notices_channel.send(notice)
                else:
                    try:
                        await channel.send(notice)
                    except discord.Forbidden:
                        await ctx.bot.last_resort_notices_channel.send(notice)

        await ctx.embed_reply("Purge complete")

    # R/PT60S
    @tasks.loop(seconds = 60)
    async def check_tweets(self):
        # TODO: Handle case-sensitivity
        # TODO: Optimize
        records = await self.bot.db.fetch(
            """
            SELECT DISTINCT ON (handle, last_checked) handle, last_checked, ttl
            FROM twitter.handles
            ORDER BY last_checked
            """
        )

        for record in records:
            handle = record["handle"]

            if record["ttl"] and datetime.datetime.now(
                datetime.timezone.utc
            ) < record["last_checked"] + datetime.timedelta(
                minutes = record["ttl"]
            ):
                continue

            nitter_instance_url = (
                await nitter.get_random_healthy_rss_instance_url()
            )

            try:
                # TODO: Handle connection errors?
                async with self.bot.aiohttp_session.get(
                    f"{nitter_instance_url}/{handle}/rss"
                ) as resp:
                    # TODO: Use structural pattern matching with Python 3.10
                    if resp.status == 404:
                        async with self.bot.aiohttp_session.get(
                            f"{nitter_instance_url}/{self.bot.twitter_test_handle}/rss"
                        ) as resp:
                            if resp.status == 200:
                                deleted = await self.bot.db.fetch(
                                    """
                                    DELETE FROM twitter.handles
                                    WHERE handle = $1
                                    RETURNING *
                                    """,
                                    handle
                                )
                                for record in deleted:
                                    notice = (
                                        f"`{record['handle']}` doesn't appear "
                                        "to be a valid Twitter user at "
                                        f"https://twitter.com/{record['handle']} "
                                        "anymore, so "
                                        f"<#{record['channel_id']}> is no "
                                        "longer following that handle\n"
                                        "(Their account may have been "
                                        "suspended or restricted / made "
                                        "unavailable, their Tweets may be "
                                        "private/protected now, or they may "
                                        "have changed their handle/username "
                                        "or deactived their account)"
                                    )
                                    self.bot.print(notice)
                                    try:
                                        channel = (
                                            self.bot.get_channel(
                                                record["channel_id"]
                                            ) or (
                                                await self.bot.fetch_channel(
                                                    record["channel_id"]
                                                )
                                            )
                                        )
                                        await channel.send(notice)
                                    except (
                                        discord.Forbidden, discord.NotFound
                                    ):
                                        await self.bot.last_resort_notices_channel.send(
                                            notice
                                        )
                                continue

                    elif resp.status in (
                        500, 502, 503, 504, 520, 521, 522, 524
                    ):
                        # TODO: Log
                        await asyncio.sleep(1)
                        continue

                    if resp.status != 200:
                        self.bot.print(
                            f"Twitter feed returned {resp.status} "
                            f"status with handle, {handle}, and "
                            f"Nitter instance, {nitter_instance_url}"
                        )
                        continue

                    feed_text = await resp.text()

                feed_info = await self.bot.loop.run_in_executor(
                    None,
                    functools.partial(
                        feedparser.parse,
                        io.BytesIO(feed_text.encode("UTF-8"))
                    )
                )
                # Necessary to run in executor?

                ttl = None
                if "ttl" in feed_info.feed:
                    ttl = int(feed_info.feed.ttl)
                await self.bot.db.execute(
                    """
                    UPDATE twitter.handles
                    SET last_checked = NOW(),
                        ttl = $1,
                        max_age = NULL,
                        etag = NULL
                    WHERE handle = $2
                    """, 
                    ttl, handle
                )

                for entry in reversed(feed_info.entries):
                    if not (link := entry.get("link")):
                        # TODO: Handle?
                        continue

                    link = urllib.parse.urlparse(link)._replace(
                        scheme = "https",
                        netloc = "twitter.com",
                        fragment = ""
                    ).geturl()

                    inserted = await self.bot.db.fetchrow(
                        """
                        INSERT INTO twitter.tweets (link, handle)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                        RETURNING *
                        """,
                        link, handle
                    )
                    if not inserted:
                        continue

                    if entry.title.startswith("R to @"):
                        # TODO: Handle false positives
                        continue

                    if entry.title.startswith('@'):
                        continue

                    if entry.author.lstrip('@').lower() != handle.lower():
                        user = (
                            discord.utils.escape_mentions(
                                feed_info.feed.title
                            ).replace(
                                "/ ", '('
                            ) + ')'
                        )
                        user_link = (
                            urllib.parse.urlparse(
                                feed_info.feed.link
                            )._replace(
                                scheme = "https",
                                netloc = "twitter.com",
                                fragment = ""
                            ).geturl()
                        )
                        content = f"[{user}]({user_link}) Retweeted:\n{link}"
                    else:
                        content = link

                    # TODO: Settings for including replies, retweets, etc.

                    # Send message
                    channel_records = await self.bot.db.fetch(
                        """
                        SELECT channel_id
                        FROM twitter.handles
                        WHERE handle = $1
                        """,
                        handle
                    )
                    for record in channel_records:
                        text_channel = self.bot.get_channel(record["channel_id"])
                        if not text_channel:
                            # TODO: Handle channel no longer accessible
                            continue
                        try:
                            await text_channel.send(content)
                        except discord.Forbidden:
                            if not text_channel.permissions_for(text_channel.guild.me).send_messages:
                                deleted = await self.bot.db.fetch(
                                    """
                                    DELETE FROM twitter.handles
                                    WHERE channel_id = $1
                                    RETURNING *
                                    """,
                                    record["channel_id"]
                                )
                                for record in deleted:
                                    await self.bot.last_resort_notices_channel.send(
                                        f"{text_channel.mention} is no longer "
                                        f"following `{record['handle']}` as a "
                                        "Twitter handle, as I no longer have "
                                        "permission to send messages in that "
                                        "channel."
                                    )
                                continue
                            self.bot.print(
                                "Twitter Task: Missing permissions to send message "
                                f"in #{text_channel.name} in {text_channel.guild.name}"
                            )
            except discord.DiscordServerError as e:
                self.bot.print(f"Twitter Task Discord Server Error: {e}")
                await asyncio.sleep(60)
            except (
                aiohttp.ClientConnectionError, aiohttp.TooManyRedirects,
                asyncio.TimeoutError
            ):
                # TODO: Log
                await asyncio.sleep(1)
            except Exception as e:
                print("Exception in Twitter Task", file = sys.stderr)
                traceback.print_exception(
                    type(e), e, e.__traceback__, file = sys.stderr
                )
                errors_logger.error(
                    "Uncaught Twitter Task exception\n",
                    exc_info = (type(e), e, e.__traceback__)
                )
                print(f" (handle: {handle})")
                await asyncio.sleep(60)

    @check_tweets.before_loop
    async def before_check_tweets(self):
        await self.bot.wait_until_ready()

    @check_tweets.after_loop
    async def after_check_tweets(self):
        self.bot.print("Twitter task cancelled")

