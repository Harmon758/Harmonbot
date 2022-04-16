
import discord
from discord.ext import commands, menus

import textwrap

import dateutil

from utilities.paginator import ButtonPaginator


async def setup(bot):
    await bot.add_cog(Tweepy())


class Tweepy(commands.Cog):

    @commands.hybrid_group(
        case_insensitive = True, invoke_without_command = True
    )
    async def tweepy(self, ctx):
        """
        Tweepy Python library
        https://github.com/tweepy/tweepy
        """
        await ctx.send_help(ctx.command)

    @tweepy.command()
    async def issue(self, ctx, *, query: str):
        """
        Search Tweepy GitHub issues

        Parameters
        ----------
        query
            The query to search
        """
        data = ctx.bot.github_api.getiter(
            "/search/issues?q={q}", {'q': "repo:tweepy/tweepy " + query}
        )
        paginator = ButtonPaginator(ctx, TweepyIssuesSource(ctx, query, data))
        # TODO: Button to switch to pagination by issue number
        await paginator.start()
        ctx.bot.views.append(paginator)


class TweepyIssuesSource(menus.AsyncIteratorPageSource):

    def __init__(self, ctx, query, data):
        self.ctx = ctx
        self.query = query

        self.bot = ctx.bot

        super().__init__(data, per_page = 1)

    async def prepare(self):
        data = await self.bot.github_api.getitem(
            "/search/issues?q={q}&per_page=1",
            {'q': "repo:tweepy/tweepy " + self.query}
        )
        self.max_pages = data["total_count"]

        await super().prepare()

    def is_paginating(self):
        return True

    def get_max_pages(self):
        return self.max_pages

    async def format_page(self, menu, page):
        kwargs = {}

        if "issues" in page["html_url"]:
            issue_type = "Issue"
        elif "pull" in page["html_url"]:
            issue_type = "Pull Request"

        embed = discord.Embed(
            title = f"{page['title']} · {issue_type} #{page['number']}",
            url = page["html_url"],
            description = textwrap.shorten(
                page["body"], 200, placeholder = " ..."
            ),
            color = self.bot.bot_color
        )

        if not self.ctx.interaction:
            embed.set_author(
                name = self.ctx.author.display_name,
                icon_url = self.ctx.author.avatar.url
            )
            kwargs["content"] = (
                f"In response to: `{self.ctx.message.clean_content}`"
            )

        if page["labels"]:
            embed.add_field(
                name = "Labels",
                value = ", ".join(
                    sorted(label["name"] for label in page["labels"])
                )
            )
        embed.add_field(name = "State", value = page["state"].capitalize())
        embed.set_image(
            url = page["html_url"].replace(
                "github.com",
                f"opengraph.githubassets.com/{self.ctx.message.id}"
            )
        )
        embed.set_footer(text = "Created")
        embed.timestamp = dateutil.parser.parse(page["created_at"])

        kwargs["embed"] = embed
        return kwargs
