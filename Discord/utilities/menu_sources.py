
import discord
from discord.ext import commands, menus

import datetime
from math import inf

from more_itertools import chunked


class TextSource(menus.PageSource):

    def __init__(self, text, *, character_limit = inf, embed_title = None):
        self.text = text
        self.character_limit = character_limit
        self.embed_title = embed_title

        self.pages = []

    async def prepare(self):
        lines = self.text.split('\n')
        while lines:
            self.pages.append("")
            while (
                lines and
                len(self.pages[-1]) + len(lines[0]) < self.character_limit
            ):
                self.pages[-1] += '\n' + lines.pop(0)
            self.pages[-1] = self.pages[-1][1:]

    def is_paginating(self):
        return len(self.pages) > 1

    def get_max_pages(self):
        return len(self.pages)

    async def get_page(self, page_number):
        return self.pages[page_number]

    async def format_page(self, menu, page):
        kwargs = {}

        embed = discord.Embed(
            color = menu.ctx.bot.bot_color,
            title = self.embed_title,
            description = page
        )

        if not menu.ctx.interaction:
            kwargs["allowed_mentions"] = discord.AllowedMentions.none()
            kwargs["content"] = (
                f"In response to {menu.ctx.author.mention}: "
                f"`{menu.ctx.message.clean_content}`"
            )

        kwargs["embed"] = embed
        return kwargs


class WolframAlphaSource(menus.ListPageSource):

    def __init__(self, pods, *, didyoumean = None, timedout = None):
        self.didyoumean = didyoumean
        self.timedout = timedout.replace(',', ", ")
        super().__init__(
            [
                (pod, subpods)
                for pod in pods
                for subpods in chunked(
                    pod.subpods,
                    10 - (bool(didyoumean) or bool(timedout))
                )
            ],
            per_page = 1
        )

    async def format_page(self, menu, pods):
        embeds = []
        kwargs = {}
        pod, subpods = pods

        description = ""
        if self.didyoumean:
            description += (
                "Using closest Wolfram|Alpha interpretation: "
                f"`{self.didyoumean}`\n"
            )
        if self.timedout:
            description += f"Some results timed out: {self.timedout}"
        if description:
            embeds.append(
                discord.Embed(
                    description = description, color = menu.bot.bot_color
                )
            )

        embeds.append(
            discord.Embed(
                title = pod.title, color = menu.bot.bot_color
            ).set_image(url = subpods[0].img.src)
        )

        if isinstance(menu.ctx_or_interaction, commands.Context):
            embeds[0].set_author(
                name = menu.ctx_or_interaction.author.display_name,
                icon_url = menu.ctx_or_interaction.author.avatar.url
            )
            kwargs["content"] = (
                "In response to: "
                f"`{menu.ctx_or_interaction.message.clean_content}`"
            )
        elif not isinstance(menu.ctx_or_interaction, discord.Interaction):
            raise RuntimeError(
                "WolframAlphaSource using neither Context nor Interaction"
            )

        for subpod in subpods[1:]:
            embeds.append(
                discord.Embed(
                    color = menu.bot.bot_color
                ).set_image(url = subpod.img.src)
            )

        kwargs["embeds"] = embeds
        return kwargs


class XKCDSource(menus.PageSource):

    def __init__(self, ctx):
        self.ctx = ctx
        self.bot = ctx.bot

    async def prepare(self):
        async with self.bot.aiohttp_session.get(
            "http://xkcd.com/info.0.json"
        ) as response:
            self.max_pages = (await response.json())["num"]

    def is_paginating(self):
        return True

    def get_max_pages(self):
        return self.max_pages

    async def get_page(self, page_number):
        async with self.bot.aiohttp_session.get(
            f"http://xkcd.com/{page_number + 1}/info.0.json"
        ) as response:
            return await response.json()

    async def format_page(self, menu, page):
        kwargs = {}

        embed = discord.Embed(
            title = page["title"],
            url = f"http://xkcd.com/{page['num']}",
            color = self.bot.bot_color
        )

        if not self.ctx.interaction:
            embed.set_author(
                name = self.ctx.author.display_name,
                icon_url = self.ctx.author.avatar.url
            )
            kwargs["content"] = (
                "In response to: "
                f"`{self.ctx.message.clean_content}`"
            )

        embed.set_image(url = page["img"])
        embed.set_footer(text = page["alt"])
        embed.timestamp = datetime.datetime(
            int(page["year"]), int(page["month"]), int(page["day"])
        )

        kwargs["embed"] = embed
        return kwargs

