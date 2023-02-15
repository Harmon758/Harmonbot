
import discord
from discord.ext import commands

import pycountry

from utilities import checks


async def setup(bot):
    await bot.add_cog(Osu(bot))

class Osu(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.load_emoji()

    @commands.Cog.listener()
    async def on_ready(self):
        self.load_emoji()

    def load_emoji(self):
        # TODO: Check only within Emoji Server emojis?
        self.ssh_emoji = discord.utils.get(self.bot.emojis, name = "osu_ssh") or "SS+"
        self.ss_emoji = discord.utils.get(self.bot.emojis, name = "osu_ss") or "SS"
        self.sh_emoji = discord.utils.get(self.bot.emojis, name = "osu_sh") or "S:"
        self.s_emoji = discord.utils.get(self.bot.emojis, name = "osu_s") or 'S'
        self.a_emoji = discord.utils.get(self.bot.emojis, name = "osu_a") or 'A'

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
        url = "https://osu.ppy.sh/api/get_user"
        params = {'k': ctx.bot.OSU_API_KEY, 'u': user, 'm': mode}
        async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
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
                self.ssh_emoji,
                count_rank_ssh
            ))
        if (count_rank_ss := data["count_rank_ss"]) is not None:
            fields.append((
                self.ss_emoji,
                count_rank_ss
            ))
        if (count_rank_sh := data["count_rank_sh"]) is not None:
            fields.append((
                self.sh_emoji,
                count_rank_sh
            ))
        if (count_rank_s := data["count_rank_s"]) is not None:
            fields.append((
                self.s_emoji,
                count_rank_s
            ))
        if (count_rank_a := data["count_rank_a"]) is not None:
            fields.append((
                self.a_emoji,
                count_rank_a
            ))

        await ctx.embed_reply(
            title = data["username"],
            title_url = f"https://osu.ppy.sh/users/{data['user_id']}",
            fields = fields
        )

