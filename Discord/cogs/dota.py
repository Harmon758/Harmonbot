
import discord
from discord.ext import commands

import io

import pycountry
from wordcloud import WordCloud

from units.dota import get_player, get_player_wl
from utilities import checks
from utilities.converters import SteamID32

async def setup(bot):
    await bot.add_cog(DotA())

class DotA(commands.Cog):

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.group(
        aliases = ["dota2"],
        case_insensitive = True, invoke_without_command = True
    )
    async def dota(self, ctx):
        '''Defense of the Ancients 2'''
        await ctx.send_help(ctx.command)

    # TODO: Add dota buff subcommand alias
    @commands.command()
    async def dotabuff(self, ctx, account: SteamID32):
        '''Get Dotabuff link'''
        await ctx.embed_reply(f"https://www.dotabuff.com/players/{account}")

    @dota.group(case_insensitive = True, invoke_without_command = True)
    async def player(self, ctx, account: SteamID32):
        '''DotA 2 player'''
        try:
            player = await get_player(
                account, aiohttp_session = ctx.bot.aiohttp_session
            )
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
            return

        player_wl = await get_player_wl(
            account, aiohttp_session = ctx.bot.aiohttp_session
        )

        fields = [("Wins", player_wl.win), ("Losses", player_wl.lose)]
        if player_wl.win or player_wl.lose:
            fields.append(
                (
                    "Wins/Losses",
                    f"{player_wl.win / (player_wl.win + player_wl.lose) * 100:.2f}%"
                )
            )
        if player.rank_tier:
            fields.append(("Rank Tier", player.rank_tier))
        if player.profile.loccountrycode:
            fields.append(
                (
                    "Country",
                    pycountry.countries.get(alpha_2 = player.profile.loccountrycode).name
                )
            )

        await ctx.embed_reply(
            title = player.profile.personaname,
            title_url = player.profile.profileurl,
            thumbnail_url = player.profile.avatarfull,
            fields = fields
        )

    @player.group(
        name = "words", case_insensitive = True, invoke_without_command = True
    )
    async def player_words(self, ctx):
        '''Words said or read in all chat'''
        await ctx.send_help(ctx.command)

    @player_words.command(
        name = "said", case_insensitive = True, invoke_without_command = True
    )
    async def player_words_said(self, ctx, account: SteamID32):
        '''Word cloud of words said in all chat'''
        async with ctx.bot.aiohttp_session.get(
            f"https://api.opendota.com/api/players/{account}/wordcloud"
        ) as resp:
            data = await resp.json()

        if not data["my_word_counts"]:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Error: No words found"
            )
            return

        word_cloud = WordCloud()
        word_cloud.fit_words(data["my_word_counts"])
        buffer = io.BytesIO()
        word_cloud.to_image().save(buffer, "PNG")
        buffer.seek(0)

        await ctx.embed_reply(
            file = discord.File(buffer, filename = "word_cloud.png"),
            image_url = "attachment://word_cloud.png"
        )

    @player_words.command(
        name = "read", case_insensitive = True, invoke_without_command = True
    )
    async def player_words_read(self, ctx, account: SteamID32):
        '''Word cloud of words read in all chat'''
        async with ctx.bot.aiohttp_session.get(
            f"https://api.opendota.com/api/players/{account}/wordcloud"
        ) as resp:
            data = await resp.json()

        if not data["all_word_counts"]:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Error: No words found"
            )
            return

        word_cloud = WordCloud()
        word_cloud.fit_words(data["all_word_counts"])
        buffer = io.BytesIO()
        word_cloud.to_image().save(buffer, "PNG")
        buffer.seek(0)

        await ctx.embed_reply(
            file = discord.File(buffer, filename = "word_cloud.png"),
            image_url = "attachment://word_cloud.png"
        )

