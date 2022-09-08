
import discord
from discord.ext import commands, menus

import datetime


class WolframAlphaSource(menus.ListPageSource):

    def __init__(self, subpods):
        super().__init__(subpods, per_page = 1)

    async def format_page(self, menu, subpod):
        kwargs = {}
        pod, subpod = subpod
        embed = discord.Embed(title = pod.title, color = menu.bot.bot_color)

        if isinstance(menu.ctx_or_interaction, commands.Context):
            embed.set_author(
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

        embed.set_image(url = subpod.img.src)

        kwargs["embed"] = embed
        return kwargs


class XKCDSource(menus.PageSource):

    def __init__(self, ctx_or_interaction):
        self.ctx_or_interaction = ctx_or_interaction

        if isinstance(ctx_or_interaction, commands.Context):
            self.bot = ctx_or_interaction.bot
        elif isinstance(ctx_or_interaction, discord.Interaction):
            self.bot = ctx_or_interaction.client
        else:
            raise RuntimeError(
                "XKCDSource passed neither Context nor Interaction"
            )

    async def prepare(self):
        url = "http://xkcd.com/info.0.json"
        async with self.bot.aiohttp_session.get(url) as resp:
            data = await resp.json()
        self.max_pages = data["num"]

    def is_paginating(self):
        return True

    def get_max_pages(self):
        return self.max_pages

    async def get_page(self, page_number):
        url = f"http://xkcd.com/{page_number + 1}/info.0.json"
        async with self.bot.aiohttp_session.get(url) as resp:
            return await resp.json()

    async def format_page(self, menu, page):
        kwargs = {}

        embed = discord.Embed(
            title = page["title"],
            url = f"http://xkcd.com/{page['num']}",
            color = self.bot.bot_color
        )

        if isinstance(self.ctx_or_interaction, commands.Context):
            embed.set_author(
                name = self.ctx_or_interaction.author.display_name,
                icon_url = self.ctx_or_interaction.author.avatar.url
            )
            kwargs["content"] = (
                "In response to: "
                f"`{self.ctx_or_interaction.message.clean_content}`"
            )
        elif not isinstance(self.ctx_or_interaction, discord.Interaction):
            raise RuntimeError(
                "XKCDSource using neither Context nor Interaction"
            )

        embed.set_image(url = page["img"])
        embed.set_footer(text = page["alt"])
        embed.timestamp = datetime.datetime(
            int(page["year"]), int(page["month"]), int(page["day"])
        )

        kwargs["embed"] = embed
        return kwargs

