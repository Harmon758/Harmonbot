
from discord.ext import commands

import asyncio
import datetime

import dateutil
import pycountry

from utilities import checks


# Commit prior to removal in https://github.com/ppy/osu-web/commit/151e9bb989a851f4f34b9878ad9756d426316f75
EMOJIS_COMMIT = "33f98cf12eb25b4e6648126ba85c94ab24eb4081"

EMOJIS_URL_BASE = f"https://raw.githubusercontent.com/ppy/osu-web/{EMOJIS_COMMIT}/public/images/badges/score-ranks-v2/"

EMOJIS = {
    "ssh": f"{EMOJIS_URL_BASE}SS%2B%402x.png",
    "ss": f"{EMOJIS_URL_BASE}SS%402x.png",
    "sh": f"{EMOJIS_URL_BASE}S%2B%402x.png",
    's': f"{EMOJIS_URL_BASE}S%402x.png",
    'a': f"{EMOJIS_URL_BASE}A%402x.png",
}

# TODO: Update to https://github.com/ppy/osu-web/tree/master/public/images/badges/score-ranks-v2019 ?


async def setup(bot):
    await bot.add_cog(Osu(bot))

class Osu(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        asyncio.create_task(
            self.initialize_application_emojis(),
            name = "Initialize osu! application emojis"
        )

    async def initialize_application_emojis(self):
        for name, url in EMOJIS.items():
            if f"osu_{name}" not in self.bot.application_emojis:
                async with self.bot.aiohttp_session.get(url) as resp:
                    self.bot.application_emojis[f"osu_{name}"] = (
                        await self.bot.create_application_emoji(
                            name = f"osu_{name}",
                            image = await resp.read()
                        )
                )

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.hybrid_group(aliases = ["osu!"], case_insensitive = True)
    async def osu(self, ctx):
        """osu!"""
        await ctx.send_help(ctx.command)

    @osu.group(case_insensitive = True)
    async def taiko(self, ctx):
        """osu!taiko"""
        await ctx.send_help(ctx.command)

    @osu.group(case_insensitive = True)
    async def catch(self, ctx):
        """osu!catch"""
        await ctx.send_help(ctx.command)

    @osu.group(case_insensitive = True)
    async def mania(self, ctx):
        """osu!mania"""
        await ctx.send_help(ctx.command)

    @osu.command()
    async def user(self, ctx, *, user: str):
        """
        General osu! user information

        Parameters
        ----------
        user
            User to retrieve osu! information about
        """
        await ctx.defer()
        await self.get_user(ctx, user)

    @taiko.command(name = "user")
    async def taiko_user(self, ctx, *, user: str):
        """
        General osu!taiko user information

        Parameters
        ----------
        user
            User to retrieve osu!taiko information about
        """
        await ctx.defer()
        await self.get_user(ctx, user, 1)

    @catch.command(name = "user")
    async def catch_user(self, ctx, *, user: str):
        """
        General osu!catch user information

        Parameters
        ----------
        user
            User to retrieve osu!catch information about
        """
        await ctx.defer()
        await self.get_user(ctx, user, 2)

    @mania.command(name = "user")
    async def mania_user(self, ctx, *, user: str):
        """
        General osu!mania user information

        Parameters
        ----------
        user
            User to retrieve osu!mania information about
        """
        await ctx.defer()
        await self.get_user(ctx, user, 3)

    async def get_user(self, ctx, user, mode = 0):
        async with ctx.bot.aiohttp_session.get(
            "https://osu.ppy.sh/api/get_user",
            params = {'k': ctx.bot.OSU_API_KEY, 'u': user, 'm': mode}
        ) as resp:
            data = await resp.json()

        if not data:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Error: User not found"
            )
            return

        data = data[0]
        fields = []
        if (ranked_score := data["ranked_score"]) is not None:
            fields.append((
                "Ranked Score",
                f"{int(ranked_score):,}"
            ))
        if (accuracy := data["accuracy"]) is not None:
            fields.append((
                "Hit Accuracy",
                f"{float(accuracy):6g}%"
            ))
        if (playcount := data["playcount"]) is not None:
            fields.append((
                "Play Count",
                playcount
            ))
        if (total_score := data["total_score"]) is not None:
            fields.append((
                "Total Score",
                f"{int(total_score):,}"
            ))
        if (pp_raw := data["pp_raw"]) is not None:
            fields.append((
                "Performance",
                f"{float(pp_raw):,}pp"
            ))
        if (pp_rank := data["pp_rank"]) is not None:
            fields.append((
                "Rank",
                f"#{int(pp_rank):,}"
            ))
        if (level := data["level"]) is not None:
            fields.append((
                "Level",
                level
            ))
        if (pp_country_rank := data["pp_country_rank"]) is not None:
            country_name = pycountry.countries.get(
                alpha_2 = data["country"]
            ).name
            fields.append((
                "Country Rank",
                f"{country_name} #{int(pp_country_rank):,}"
            ))
        if (count300 := data["count300"]) is not None:
            count300 = int(count300)
        if (count100 := data["count100"]) is not None:
            count100 = int(count100)
        if (count50 := data["count50"]) is not None:
            count50 = int(count50)
        total_hits = (count300 or 0) + (count100 or 0) + (count50 or 0)
        if count300 is not None or count100 is not None or count50 is not None:
            fields.append((
                "Total Hits",
                f"{total_hits:,}"
            ))
        if count300 is not None:
            fields.append((
                "300 Hits",
                f"{count300:,}"
            ))
        if count100 is not None:
            fields.append((
                "100 Hits",
                f"{count100:,}"
            ))
        if count50 is not None:
            fields.append((
                "50 Hits",
                f"{count50:,}"
            ))
        if (count_rank_ssh := data["count_rank_ssh"]) is not None:
            fields.append((
                str(ctx.bot.application_emojis.get("osu_ssh", "SS+")),
                count_rank_ssh
            ))
        if (count_rank_ss := data["count_rank_ss"]) is not None:
            fields.append((
                str(ctx.bot.application_emojis.get("osu_ss", "SS")),
                count_rank_ss
            ))
        if (count_rank_sh := data["count_rank_sh"]) is not None:
            fields.append((
                str(ctx.bot.application_emojis.get("osu_sh", "S+")),
                count_rank_sh
            ))
        if (count_rank_s := data["count_rank_s"]) is not None:
            fields.append((
                str(ctx.bot.application_emojis.get("osu_s", 'S')),
                count_rank_s
            ))
        if (count_rank_a := data["count_rank_a"]) is not None:
            fields.append((
                str(ctx.bot.application_emojis.get("osu_a", 'A')),
                count_rank_a
            ))

        await ctx.embed_reply(
            title = data["username"],
            title_url = f"https://osu.ppy.sh/users/{data['user_id']}",
            fields = fields,
            footer_text = "Joined",
            timestamp = dateutil.parser.parse(
                data["join_date"]
            ).replace(tzinfo = datetime.UTC)
        )

