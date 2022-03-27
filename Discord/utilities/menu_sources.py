
import discord
from discord.ext import menus

import datetime


class XKCDSource(menus.PageSource):

    def __init__(self, ctx):
        self.bot = ctx.bot

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
        embed = discord.Embed(
            title = page["title"],
            url = f"http://xkcd.com/{page['num']}",
            color = menu.ctx.bot.bot_color
        )
        embed.set_author(
            name = menu.ctx.author.display_name,
            icon_url = menu.ctx.author.avatar.url
        )
        embed.set_image(url = page["img"])
        embed.set_footer(text = page["alt"])
        embed.timestamp = datetime.datetime(
            int(page["year"]), int(page["month"]), int(page["day"])
        )
        return {
            "content": f"In response to: `{menu.ctx.message.clean_content}`",
            "embed": embed
        }

