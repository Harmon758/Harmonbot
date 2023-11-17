
import discord
from discord import ui
from discord.ext import commands, menus

import re
import textwrap

from bs4 import BeautifulSoup
import dateutil
from markdownify import MarkdownConverter
import sphobjinv

from utilities.paginators import ButtonPaginator


DISCORD_INVITE_REGEX_PATTERN = re.compile(
    r"(?:https?://)?discord(?:app)?\.(?:com/invite|gg)/[a-zA-Z0-9]+/?"
)

PYTHON_GUILD_ID = 267624335836053506
TWEEPY_GUILD_ADMIN_ROLE_ID = 432751422673649666
TWEEPY_GUILD_ID = 432685901596852224
TWEEPY_GUILD_MODERATOR_ONLY_CHANNEL_ID = 758188869941985321

markdown_converter = MarkdownConverter(
    bullets = '•',
    escape_underscores = False,
    heading_style = "ATX_CLOSED"
)

ANCHOR_LINK_REGEX_PATTERN = re.compile(r"\[\uF0C1\]\(.+\)")

def remove_anchor_links(text):
    return ANCHOR_LINK_REGEX_PATTERN.sub("", text)

NEWLINES_REGEX_PATTERN = re.compile(r"\n\s*\n")

def remove_extra_newlines(text):
    return NEWLINES_REGEX_PATTERN.sub("\n\n", text)


async def setup(bot):
    await bot.add_cog(Tweepy(bot))


class Tweepy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        url = "https://readthedocs.org/api/v3/projects/tweepy/versions/"
        headers = {
            "Authorization": "Token " + self.bot.READ_THE_DOCS_API_TOKEN
        }
        async with self.bot.aiohttp_session.get(
            url, headers = headers
        ) as resp:
            data = await resp.json()

        highest_id = 0
        for result in data["results"]:
            if result["id"] > highest_id:
                self.rtd_version = result["slug"]
                highest_id = result["id"]

        url = (
            f"https://tweepy.readthedocs.io/en/{self.rtd_version}/objects.inv"
        )
        async with self.bot.aiohttp_session.get(url) as resp:
            data = await resp.read()
        self.sphinx_inventory = sphobjinv.Inventory(data)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return
        if message.guild.id != TWEEPY_GUILD_ID:
            return
        if not isinstance(message.author, discord.Member):
            return
        if message.author.get_role(TWEEPY_GUILD_ADMIN_ROLE_ID):
            return
        for match in DISCORD_INVITE_REGEX_PATTERN.finditer(
            message.content
        ):
            invite = await self.bot.fetch_invite(match.group())
            if invite.guild.id not in (TWEEPY_GUILD_ID, PYTHON_GUILD_ID):
                ctx = await self.bot.get_context(message)
                await ctx.embed_reply(
                    author_name = None,
                    description = (
                        ctx.author.mention +
                        ": Please don't send Discord invites here"
                    ),
                    in_response_to = False
                )
                await self.bot.get_channel(
                    TWEEPY_GUILD_MODERATOR_ONLY_CHANNEL_ID
                ).send(
                    embed = discord.Embed(
                        description = (
                            "Deleted message with invite "
                            f"from {ctx.author.mention} "
                            f"in {message.channel.mention}:"
                            f"\n{message.content}"
                        ),
                        color = self.bot.bot_color
                    )
                )
                return

    @commands.hybrid_group(case_insensitive = True)
    async def tweepy(self, ctx):
        """
        Tweepy Python library
        https://github.com/tweepy/tweepy
        """
        await ctx.send_help(ctx.command)

    @tweepy.command(aliases = ["docs", "rtd"])
    async def documentation(self, ctx, *, query: str):
        """
        Search Tweepy documentation on Read the Docs

        Parameters
        ----------
        query
            The query to search
        """
        await ctx.defer()

        suggestions = self.sphinx_inventory.suggest(
            query, thresh = 64, with_index = True
        )

        if not suggestions:
            await ctx.embed_reply("\N{NO ENTRY SIGN} No results found")
            return

        if len(suggestions) == 1:
            object = self.sphinx_inventory.objects[suggestions[0][1]]
            embed = await format_documentation_section(
                object,
                bot = ctx.bot,
                rtd_version = self.rtd_version
            )
            if ctx.interaction:
                await ctx.send(embed = embed)
            else:
                embed.set_author(
                    name = ctx.author.display_name,
                    icon_url = ctx.author.display_avatar.url
                )
                embed.set_footer(
                    text = f"In response to: {ctx.message.clean_content}"
                )
                await ctx.send(embed = embed)
                await ctx.bot.attempt_delete_message(ctx.message)
        else:
            objects = [
                self.sphinx_inventory.objects[index]
                for rst, index in suggestions[:5]
            ]
            view = TweepyDocumentationView(
                objects,
                bot = ctx.bot,
                rtd_version = self.rtd_version,
                user = ctx.author
            )
            message = await ctx.embed_reply(
                '\n'.join(
                    f"[{object.dispname_expanded}]"
                    f"(https://tweepy.readthedocs.io/en/{self.rtd_version}/{object.uri_expanded})"
                    for object in objects
                ),
                view = view
            )
            view.message = message
            ctx.bot.views.append(view)

    @tweepy.command()
    async def issue(self, ctx, *, query: str):
        """
        Search Tweepy GitHub issues

        Parameters
        ----------
        query
            The query to search
        """
        await ctx.defer()
        data = ctx.bot.github_api.getiter(
            "/search/issues?q={q}", {'q': "repo:tweepy/tweepy " + query}
        )
        paginator = ButtonPaginator(ctx, TweepyIssuesSource(ctx, query, data))
        # TODO: Button to switch to pagination by issue number
        await paginator.start()
        ctx.bot.views.append(paginator)


async def format_documentation_section(
    object, *, bot, rtd_version, embed = None
):
        if embed:
            embed.clear_fields()
        else:
            embed = discord.Embed(color = bot.bot_color)

        embed.title = object.dispname_expanded
        embed.url = (
            f"https://tweepy.readthedocs.io/en/{rtd_version}/{object.uri_expanded}"
        )

        url = "https://readthedocs.org/api/v3/embed/"
        params = {"url": embed.url, "doctool": "sphinx"}
        async with bot.aiohttp_session.get(url, params = params) as resp:
            data = await resp.json()

        content = BeautifulSoup(data["content"], "lxml")

        if next(content.body.children).name == "dl":
            embed.description = bot.PY_CODE_BLOCK.format(
                content.find("dt").get_text().rstrip('\uF0C1')
            )

            for description_list in content.dl.dd.find_all(
                "dl", recursive = False
            ):
                for term, description in zip(
                    *[iter(
                        description_list.find_all(
                            ["dt", "dd"], recursive = False
                        )
                    )] * 2
                ):
                    if (
                        description.get_text().strip() and
                        len(embed) < bot.EMBED_TOTAL_CHARACTER_LIMIT
                    ):
                        description_text = remove_extra_newlines(
                            markdown_converter.convert_soup(description)
                        )
                        if len(description_text) > bot.EFVCL:
                            # EFVCL: Embed Field Value Character Limit
                            description_text = (
                                description_text[:bot.EFVCL - 4].rsplit(
                                    maxsplit = 1
                                )[0] + "\n..."
                            )
                        embed.add_field(
                            name = term.get_text().rstrip('\uF0C1'),
                            value = description_text,
                            inline = False
                        )
                description_list.extract()

            if references_heading := content.find(
                'p', class_ = "rubric", string = "References"
            ):
                embed.add_field(
                    name = "References",
                    value = '\n'.join(
                        reference.extract().get_text()
                        for reference in references_heading.find_all_next(
                            'a', class_ = "reference external"
                        )
                    ),
                    inline = False
                )
                references_heading.extract()

            embed.description += (
                '\n' + remove_extra_newlines(
                    markdown_converter.convert_soup(content.find("dd"))
                )
            )

            while len(embed) > bot.EMBED_TOTAL_CHARACTER_LIMIT:
                if embed.fields[-1].name == "...":
                    embed.remove_field(-2)
                elif embed.fields[-2].name == "...":
                    embed.remove_field(-3)
                elif embed.fields[-1].name == "References":
                    embed.remove_field(-2)
                    embed.insert_field_at(
                        -1,
                        name = "...",
                        value = bot.ZERO_WIDTH_SPACE,
                        inline = False
                    )
                else:
                    embed.remove_field(-1)
                    embed.add_field(
                        name = "...",
                        value = bot.ZERO_WIDTH_SPACE,
                        inline = False
                    )
        else:
            embed.description = remove_extra_newlines(
                remove_anchor_links(
                    markdown_converter.convert_soup(content)
                )
            ).strip()

            # pylint: disable-next=unused-variable
            first_line, newline, subsequent_lines = (
                embed.description.partition('\n')
            )
            if first_line.strip("# `") == embed.title:
                embed.description = subsequent_lines.lstrip()

            if len(embed.description) > bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
                embed.description = (
                    embed.description[:bot.EDCL - 4].rsplit(
                        maxsplit = 1
                    )[0] + " ..."
                )

        return embed


class TweepyDocumentationView(ui.View):

    def __init__(self, objects, *, bot, rtd_version, user):
        super().__init__(timeout = 600)

        self.bot = bot
        self.user = user

        self.add_item(
            TweepyDocumentationSelect(objects, rtd_version = rtd_version)
        )

        self.message = None

    async def interaction_check(self, interaction):
        if interaction.user.id not in (
            self.user.id, interaction.client.owner_id
        ):
            await interaction.response.send_message(
                "This isn't your search.", ephemeral = True
            )
            return False
        return True

    async def stop(self):
        self.children[0].disabled = True

        if self.message:
            await self.bot.attempt_edit_message(self.message, view = self)

        super().stop()

    async def on_timeout(self):
        await self.stop()


class TweepyDocumentationSelect(ui.Select):

    def __init__(self, objects, *, rtd_version):
        self.objects = {}
        options = []
        for object in objects:
            if object.dispname_expanded not in self.objects:
                self.objects[object.dispname_expanded] = object
                options.append(
                    discord.SelectOption(label = object.dispname_expanded)
                )
        self.rtd_version = rtd_version

        super().__init__(
            options = options,
            placeholder = "Select a documentation section to view"
        )

    async def callback(self, interaction):
        embed = interaction.message.embeds[0]
        object = self.objects[self.values[0]]
        embed = await format_documentation_section(
            object,
            bot = interaction.client,
            embed = embed,
            rtd_version = self.rtd_version
        )

        for option in self.options:
            option.default = option.label == self.values[0]
        await interaction.response.edit_message(
            embed = embed, view = self.view
        )


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
