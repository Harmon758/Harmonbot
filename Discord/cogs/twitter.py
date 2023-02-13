
import discord
from discord.ext import commands

import asyncio
import html
import logging
import sys
import traceback

from more_itertools import chunked
import tweepy
import tweepy.asynchronous

from utilities import checks


errors_logger = logging.getLogger("errors")

async def setup(bot):
    await bot.add_cog(Twitter(bot))

class Twitter(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.blacklisted_handles = []
        self.stream = TwitterStream(bot)

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
        # Initialize blacklist
        try:
            response = await self.bot.twitter_client.get_me(
                user_fields = ["protected"]
            )
            account = response.data
            if account.protected:
                self.blacklisted_handles.append(
                    account.username.lower()
                )
            # TODO: Handle more than 1000 friends/following
            response = await self.bot.twitter_client.get_users_following(
                account.id, max_results = 1000, user_fields = ["protected"],
                user_auth = True
            )
            following = response.data
            for friend in following:
                if friend.protected:
                    self.blacklisted_handles.append(friend.username.lower())
        except (AttributeError, tweepy.TweepyException) as e:
            self.bot.print(f"Failed to initialize Twitter cog blacklist: {e}")
        # Start stream
        self.task = self.bot.loop.create_task(
            self.start_stream(), name = "Start Twitter Stream"
        )

    def cog_unload(self):
        if self.stream:
            self.stream.disconnect()
        self.task.cancel()

    @commands.hybrid_group(case_insensitive = True)
    @checks.not_forbidden()
    async def twitter(self, ctx):
        '''Twitter'''
        await ctx.send_help(ctx.command)

    @twitter.command(name = "status")
    @checks.not_forbidden()
    async def twitter_status(
        self, ctx, handle: str, replies: bool = False, retweets: bool = False
    ):
        """
        Show a Twitter user's most recent Tweet
        Limited to 3200 most recent Tweets

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
        try:
            response = await self.bot.twitter_client.get_user(
                username = handle.lstrip('@'),
                user_fields = ["profile_image_url"]
            )
        except tweepy.BadRequest as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
            return

        if response.errors:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Error:\n" +
                '\n'.join(error['detail'] for error in response.errors)
            )
            return

        user = response.data

        async for tweet in tweepy.asynchronous.AsyncPaginator(
            self.bot.twitter_client.get_users_tweets,
            user.id,
            exclude = (
                ["replies"] if not replies else [] +
                ["retweets"] if not retweets else []
            ) or None,
            max_results = 100
        ).flatten():
            response = await self.bot.twitter_client.get_tweet(
                tweet.id,
                expansions = ["attachments.media_keys"],
                media_fields = ["url"],
                tweet_fields = ["attachments", "created_at", "entities"]
            )
            break
        else:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Error: Status not found"
            )
            return

        tweet = response.data

        medias = {
            media["media_key"]: media
            for media in response.includes.get("media", ())
        }

        image_url = None
        if tweet.attachments and (
            media_keys := tweet.attachments.get("media_keys")
        ):
            for media_key in media_keys:
                media = medias[media_key]
                if media["type"] == "photo":
                    image_url = media["url"]
                    break

        text = process_tweet_text(tweet.text, tweet.entities)

        if image_url:
            for url in tweet.entities["urls"]:
                if url.get("media_key") == media_key:
                    text = text.replace(url["expanded_url"], "")

        await ctx.embed_reply(
            content = f"<https://twitter.com/{user.username}/status/{tweet.id}>",
            color = self.bot.twitter_color,
            author_icon_url = user.profile_image_url,
            author_name = f"{user.name} (@{user.username})",
            author_url = f"https://twitter.com/{user.username}",
            description = text,
            image_url = image_url,
            footer_text = None,
            timestamp = tweet.created_at
        )

    @twitter.command(
        name = "add", aliases = ["addhandle", "handleadd"],
        with_app_command = False
    )
    @commands.check_any(checks.is_permitted(), checks.is_guild_owner())
    async def twitter_add(self, ctx, handle: str):
        '''
        Add a Twitter handle to a text channel
        A delay of up to 2 min. is possible due to Twitter rate limits
        '''
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
            await ctx.embed_reply(f"{ctx.bot.error_emoji} This text channel is already following that Twitter handle")
            return
        message = await ctx.embed_reply("\N{HOURGLASS} Please wait")
        embed = message.embeds[0]
        try:
            await self.stream.add_feed(ctx.channel, handle)
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
        embed.description = f"Added the Twitter handle, [`{handle}`](https://twitter.com/{handle}), to this text channel"
        await message.edit(embed = embed)

    @twitter.command(name = "remove", aliases = ["delete", "removehandle", "handleremove", "deletehandle", "handledelete"], with_app_command = False)
    @commands.check_any(checks.is_permitted(), checks.is_guild_owner())
    async def twitter_remove(self, ctx, handle: str):
        '''
        Remove a Twitter handle from a text channel
        A delay of up to 2 min. is possible due to Twitter rate limits
        '''
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
            await ctx.embed_reply(f"{ctx.bot.error_emoji} This text channel isn't following that Twitter handle")
            return
        message = await ctx.embed_reply("\N{HOURGLASS} Please wait")
        await self.stream.remove_feed(ctx.channel, handle)
        embed = message.embeds[0]
        embed.description = f"Removed the Twitter handle, [`{handle}`](https://twitter.com/{handle}), from this text channel."
        await message.edit(embed = embed)

    @twitter.command(
        aliases = ["handle", "feeds", "feed", "list"],
        with_app_command = False
    )
    @checks.not_forbidden()
    async def handles(self, ctx):
        '''Show Twitter handles being followed in a text channel'''
        records = await ctx.bot.db.fetch(
            """
            SELECT handle FROM twitter.handles
            WHERE channel_id = $1
            """, 
            ctx.channel.id
        )
        await ctx.embed_reply(
            '\n'.join(sorted(
                [record["handle"] for record in records],
                key = str.casefold
            ))
        )
        # TODO: Add message if none

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
            user_ids = {}
            for usernames_chunk in chunked(usernames, 100):
                response = await self.bot.twitter_client.get_users(
                    usernames = usernames_chunk
                )
                for user in response.data:
                    user_ids[user.id] = usernames[user.username.lower()]
            await self.stream.start_feeds(user_ids = user_ids)
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
    if "user_mentions" in entities:
        for mention in entities["user_mentions"]:
            mentions[text[mention["indices"][0]:mention["indices"][1]]] = (
                mention["screen_name"]
            )
    else:
        for mention in entities.get("mentions", ()):
            mentions[text[mention["start"]:mention["end"]]] = mention["tag"]
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
    if "symbols" in entities:
        for symbol in entities["symbols"]:
            text = text.replace(
                '$' + symbol["text"],
                f"[${symbol['text']}](https://twitter.com/search?q=${symbol['text']})"
            )
    else:
        for cashtag in entities.get("cashtags", ()):
            text = text.replace(
                '$' + cashtag["tag"],
                f"[${cashtag['tag']}](https://twitter.com/search?q=${cashtag['tag']})"
            )
    for url in entities["urls"]:
        text = text.replace(url["url"], url["expanded_url"])
    # Remove Variation Selector-16 characters
    # Unescape HTML entities (&gt;, &lt;, &amp;, etc.)
    return html.unescape(text.replace('\uFE0F', ""))


class TwitterStream(tweepy.asynchronous.AsyncStream):

    def __init__(self, bot):
        super().__init__(
            bot.TWITTER_CONSUMER_KEY, bot.TWITTER_CONSUMER_SECRET,
            bot.TWITTER_ACCESS_TOKEN, bot.TWITTER_ACCESS_TOKEN_SECRET
        )
        self.bot = bot
        self.user_ids = {}
        self.reconnect_ready = asyncio.Event()
        self.reconnect_ready.set()
        self.reconnecting = False

    async def start_feeds(self, *, user_ids = None):
        if self.reconnecting:
            return await self.reconnect_ready.wait()
        self.reconnecting = True
        await self.reconnect_ready.wait()
        self.reconnect_ready.clear()
        if user_ids:
            self.user_ids = user_ids
        if self.task:
            self.disconnect()
            await self.task
        if self.user_ids:
            self.filter(follow = self.user_ids)
        self.bot.loop.call_later(120, self.reconnect_ready.set)
        self.reconnecting = False

    async def add_feed(self, channel, handle):
        response = await self.bot.twitter_client.get_user(username = handle)
        user_id = response.data.id

        if channels := self.user_ids.get(user_id):
            channels.append(channel.id)
        else:
            self.user_ids[user_id] = [channel.id]
            await self.start_feeds()

    async def remove_feed(self, channel, handle):
        response = await self.bot.twitter_client.get_user(username = handle)
        user_id = response.data.id

        channel_ids = self.user_ids[user_id]
        channel_ids.remove(channel.id)
        if not channel_ids:
            del self.user_ids[user_id]

        await self.start_feeds()  # Necessary?

    async def on_status(self, status):
        # Ignore replies
        if status.in_reply_to_status_id:
            return
        # TODO: Settings for including replies, retweets, etc.
        for channel_id in self.user_ids.get(status.user.id, ()):
            channel = self.bot.get_channel(channel_id)
            if not channel:
                # TODO: Handle channel no longer accessible
                continue
            if hasattr(status, "extended_tweet"):
                text = status.extended_tweet["full_text"]
                entities = status.extended_tweet["entities"]
                extended_entities = status.extended_tweet.get(
                    "extended_entities"
                )
            else:
                text = status.text
                entities = status.entities
                extended_entities = getattr(status, "extended_entities", None)
            embed = discord.Embed(
                color = self.bot.twitter_color,
                title = '@' + status.user.screen_name,
                url = f"https://twitter.com/{status.user.screen_name}/status/{status.id}",
                description = process_tweet_text(text, entities),
                timestamp = status.created_at,
            )
            embed.set_author(
                name = status.user.name,
                icon_url = status.user.profile_image_url
            )
            if (
                extended_entities and
                extended_entities["media"][0]["type"] == "photo"
            ):
                embed.set_image(
                    url = extended_entities["media"][0]["media_url_https"]
                )
                embed.description = embed.description.replace(
                    extended_entities["media"][0]["url"], ""
                )
            embed.set_footer(
                icon_url = self.bot.twitter_icon_url,
                text = "Twitter"
            )
            try:
                await channel.send(embed = embed)
            except discord.Forbidden:
                # TODO: Handle unable to send embeds/messages in text channel
                self.bot.print(
                    "Twitter Stream: Missing permissions to send embed in "
                    f"#{channel.name} in {channel.guild.name}"
                )
            except discord.DiscordServerError as e:
                self.bot.print(f"Twitter Stream Discord Server Error: {e}")

    async def on_request_error(self, status_code):
        self.bot.print(f"Twitter Error: {status_code}")

