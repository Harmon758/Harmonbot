
from __future__ import annotations

from discord import Attachment  # noqa: TC001 (typing-only-first-party-import)
from discord.ext import commands

import inspect
import re
from typing import Optional, TYPE_CHECKING

import imgurpython

from units import clarifai
from units import google
from utilities import checks

if TYPE_CHECKING:
    from utilities.context import Context


async def setup(bot):
    await bot.add_cog(Images(bot))


class Images(commands.Cog):

    '''
    All image subcommands are also commands
    '''

    def __init__(self, bot):
        self.bot = bot
        # Add commands as image subcommands
        for name, command in inspect.getmembers(self):
            if isinstance(command, commands.Command) and command.parent is None and name != "image":
                self.bot.add_command(command)
                self.image.add_command(command)

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.group(
        aliases = ["images", "photo", "photos"],
        case_insensitive = True, invoke_without_command = True
    )
    async def image(self, ctx, *, query):
        '''Images/Photos'''
        async with ctx.bot.aiohttp_session.get(
            "https://api.unsplash.com/search/photos",
            headers = {
                "Accept-Version": "v1",
                "Authorization": f"Client-ID {ctx.bot.UNSPLASH_ACCESS_KEY}"
            },
            params = {"query": query, "per_page": 1}
        ) as resp:
            data = await resp.json()

        if not data["results"]:
            await ctx.embed_reply("No photo results found")
            return

        photo = data["results"][0]

        await ctx.embed_reply(
            photo["description"] or "",
            author_name = f"{photo['user']['name']} on Unsplash",
            author_url = f"{photo['user']['links']['html']}?utm_source=Harmonbot&utm_medium=referral",
            author_icon_url = photo["user"]["profile_image"]["small"],
            image_url = photo["urls"]["full"]
        )

    @image.command(name = "color", aliases = ["colour"])
    async def image_color(
        self, ctx: Context,
        image: Optional[Attachment],  # noqa: UP045 (non-pep604-annotation-optional)
        image_url: Optional[str]  # noqa: UP045 (non-pep604-annotation-optional)
    ):
        """
        Image color density values
        and the closest W3C color name for each identified color
        """
        if image:
            image_url = image.url
        elif not image_url:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Please input an image and/or url"
            )
            return

        try:
            colors = clarifai.image_color(image_url)
        except Exception as e:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Error: {e}"
            )
            return

        fields = [
            (
                color.raw_hex.upper(),
                (
                    f"{color.value * 100:.2f}%\n"
                    f"{re.sub(r'(?!^)(?=[A-Z])', ' ', color.w3c_name)}\n"
                    f"({color.w3c_hex.upper()})"
                )
            )
            for color in sorted(
                colors, key = lambda c: c.value, reverse = True
            )
        ]
        await ctx.embed_reply(
            title = "Color Density", fields = fields, thumbnail_url = image_url
        )

    # TODO: add as search subcommand
    @commands.group(case_insensitive = True, invoke_without_command = True)
    async def giphy(self, ctx: Context, *, search: str):
        """Find an image on Giphy"""
        async with ctx.bot.aiohttp_session.get(
            "http://api.giphy.com/v1/gifs/search",
            params = {
                "api_key": ctx.bot.GIPHY_API_KEY, 'q': search, "limit": 1
            }
        ) as resp:
            data = await resp.json()

        await ctx.embed_reply(
            image_url = data["data"][0]["images"]["original"]["url"]
        )

    @giphy.command(name = "random")
    async def giphy_random(self, ctx: Context):
        """Random GIF from Giphy"""
        # Note: random giphy command invokes this command
        async with ctx.bot.aiohttp_session.get(
            "http://api.giphy.com/v1/gifs/random",
            params = {"api_key": ctx.bot.GIPHY_API_KEY}
        ) as resp:
            data = await resp.json()

        await ctx.embed_reply(
            image_url = data["data"]["images"]["original"]["url"]
        )

    @giphy.command(name = "trending")
    async def giphy_trending(self, ctx: Context):
        """Trending GIF from Giphy"""
        async with ctx.bot.aiohttp_session.get(
            "http://api.giphy.com/v1/gifs/trending",
            params = {"api_key": ctx.bot.GIPHY_API_KEY}
        ) as resp:
            data = await resp.json()

        await ctx.embed_reply(
            image_url = data["data"][0]["images"]["original"]["url"]
        )

    @image.command(aliases = ["search"])
    async def google(self, ctx: Context, *, search: str):
        '''Google image search something'''
        # Note: google images command invokes this command
        # Note: search google images command invokes this command
        # TODO: Option to disable SafeSearch
        async with ctx.bot.aiohttp_session.get(
            "https://www.googleapis.com/customsearch/v1",
            params = {
                "key": ctx.bot.GOOGLE_API_KEY,
                "cx": ctx.bot.GOOGLE_CUSTOM_SEARCH_ENGINE_ID,
                "searchType": "image", 'q': search, "num": 1, "safe": "active"
            }
        ) as resp:
            if resp.status == 403:
                await ctx.embed_reply(
                    f"{ctx.bot.error_emoji} Daily limit exceeded"
                )
                return

            data = await resp.json()

        if "items" not in data:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} No images with that search found"
            )
            return

        await ctx.embed_reply(
            title = f"Image of {search}",
            title_url = data["items"][0]["link"],
            image_url = data["items"][0]["link"]
        )
        # TODO: Handle 403 daily limit exceeded error

    @commands.group(case_insensitive = True, invoke_without_command = True)
    async def imgur(self, ctx: Context):
        """Imgur"""
        await ctx.send_help(ctx.command)

    @imgur.command(name = "search")
    async def imgur_search(self, ctx: Context, *, search: str):
        """Search images on Imgur"""
        # Note: search imgur command invokes this command
        if not (
            result := ctx.bot.imgur_client.gallery_search(search, sort = "top")
        ):
            await ctx.embed_reply(f"{ctx.bot.error_emoji} No results found")
            return

        result = result[0]

        if result.is_album:
            result = ctx.bot.imgur_client.get_album(result.id).images[0]
            await ctx.embed_reply(image_url = result["link"])
        else:
            await ctx.embed_reply(image_url = result.link)

    @imgur.command(name = "upload")
    async def imgur_upload(
        self, ctx: Context,
        image: Optional[Attachment],  # noqa: UP045 (non-pep604-annotation-optional)
        image_url: Optional[str]  # noqa: UP045 (non-pep604-annotation-optional)
    ):
        """Upload images to Imgur"""
        if image:
            image_url = image.url
        elif not image_url:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Please input an image and/or url"
            )
            return

        try:
            await ctx.embed_reply(
                ctx.bot.imgur_client.upload_from_url(image_url)["link"]
            )
        except imgurpython.helpers.error.ImgurClientError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")

    @image.command(name = "random")
    async def image_random(self, ctx: Context, *, query = ""):
        '''Random photo from Unsplash'''
        # Note: random photo command invokes this command
        async with ctx.bot.aiohttp_session.get(
            "https://api.unsplash.com/photos/random",
            headers = {
                "Accept-Version": "v1",
                "Authorization": f"Client-ID {ctx.bot.UNSPLASH_ACCESS_KEY}"
            },
            params = {"query": query}
        ) as resp:
            data = await resp.json()

        if "errors" in data:
            errors = '\n'.join(data["errors"])
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Error:\n{errors}")
            return

        await ctx.embed_reply(
            data["description"] or "",
            author_name = f"{data['user']['name']} on Unsplash",
            author_url = f"{data['user']['links']['html']}?utm_source=Harmonbot&utm_medium=referral",
            author_icon_url = data["user"]["profile_image"]["small"],
            image_url = data["urls"]["full"]
        )

    @image.command(name = "recognition")
    async def image_recognition(
        self, ctx: Context,
        image: Optional[Attachment],  # noqa: UP045 (non-pep604-annotation-optional)
        image_url: Optional[str]  # noqa: UP045 (non-pep604-annotation-optional)
    ):
        """Image recognition"""
        if image:
            image_url = image.url
        elif not image_url:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Please input an image and/or url"
            )
            return

        labels = google.cloud.vision.detect_labels(image_url)

        await ctx.embed_reply(
            ", ".join(
                f"**{label.description}**: {label.score * 100:.2f}%"
                for label in sorted(
                    labels, key = lambda l: l.score, reverse = True
                )
            ),
            thumbnail_url = image_url
        )

    @commands.command()
    async def nsfw(
        self, ctx: Context,
        image: Optional[Attachment],  # noqa: UP045 (non-pep604-annotation-optional)
        image_url: Optional[str]  # noqa: UP045 (non-pep604-annotation-optional)
    ):
        """NSFW recognition"""
        if image:
            image_url = image.url
        elif not image_url:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Please input an image and/or url"
            )
            return

        try:
            percentage = clarifai.image_nsfw(image_url) * 100
        except Exception as e:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Error: {e}"
            )
            return

        await ctx.embed_reply(
            f"NSFW: {percentage:.2f}%", thumbnail_url = image_url
        )

