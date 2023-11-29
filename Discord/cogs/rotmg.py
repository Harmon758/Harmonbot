
import discord
from discord.ext import commands

from utilities import checks


async def setup(bot):
    await bot.add_cog(RotMG())

class RotMG(commands.Cog):

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.group(
        aliases = ["realmofthemadgod"],
        case_insensitive = True, invoke_without_command = True
    )
    async def rotmg(self, ctx, player: str):
        '''Realm of the Mad God player information'''
        # http://webhost.ischool.uw.edu/~joatwood/realmeye_api/0.3/
        async with ctx.bot.aiohttp_session.get(
            "https://nightfirec.at/realmeye-api/",
            params = {"player": player}
        ) as resp:
            data = await resp.json()

        if "error" in data:
            await ctx.embed_reply("Error: " + data["error"])
            return

        fields = [
            ("Characters", data["chars"]),
            ("Total Fame", f"{data['fame']:,}"),
            ("Fame Rank", f"{data['fame_rank']:,}"),
            ("Class Quests Completed", data["rank"]),
            ("Account Fame", f"{data['account_fame']:,}"),
            ("Account Fame Rank", f"{data['account_fame_rank']:,}")
        ]
        if created := data.get("created"):
            fields.append(("Created", created))
        fields.extend((
            ("Total Exp", f"{data['exp']:,}"),
            ("Exp Rank", f"{data['exp_rank']:,}"),
            ("Last Seen", data["player_last_seen"])
        ))
        if guild := data.get("guild"):
            fields.extend((
                ("Guild", guild),
                ("Guild Position", data["guild_rank"])
            ))
        if data["desc1"] or data["desc2"] or data["desc3"]:
            fields.append((
                "Description",
                f"{data['desc1']}\n{data['desc2']}\n{data['desc3']}"
            ))
        await ctx.embed_reply(
            title = data["player"],
            title_url = f"https://www.realmeye.com/player/{player}",
            description = "Donator" if data["donator"] == "true" else None,
            fields = fields
        )

    @rotmg.command(name = "characters")
    async def rotmg_characters(self, ctx, player: str):
        '''Realm of the Mad God player characters information'''
        # http://webhost.ischool.uw.edu/~joatwood/realmeye_api/0.3/
        async with ctx.bot.aiohttp_session.get(
            "https://nightfirec.at/realmeye-api/",
            params = {"player": player}
        ) as resp:
            data = await resp.json()

        if "error" in data:
            await ctx.embed_reply("Error: " + data["error"])
            return

        embed = discord.Embed(
            title = f"{data['player']}'s Characters",
            color = ctx.bot.bot_color
        )
        embed.set_author(
            name = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        )
        for character in data["characters"]:
            stats = character["stats"]
            value = (
                f"Fame: {character['fame']:,}, "
                f"Exp: {character['exp']:,}, "
                f"Rank: {character['place']:,}, "
                f"Class Quests Completed: {character['cqc']}, "
                f"Stats Maxed: {character['stats_maxed']}\n"
                f"HP: {stats['hp']}, "
                f"MP: {stats['mp']}, "
                f"Attack: {stats['attack']}, "
                f"Defense: {stats['defense']}, "
                f"Speed: {stats['speed']}, "
                f"Vitality: {stats['vitality']}, "
                f"Wisdom: {stats['wisdom']}, "
                f"Dexterity: {stats['dexterity']}\n"
            )
            value += ", ".join(
                f"{type.capitalize()}: {equip}"
                for type, equip in character["equips"].items()
            )
            value += (
                f"\nPet: {character['pet']}, "
                f"Clothing Dye: {character['character_dyes']['clothing_dye']}, "
                f"Accessory Dye: {character['character_dyes']['accessory_dye']}, "
                f"Backpack: {character['backpack']}\n"
                f"Last Seen: {character['last_seen']}, "
                f"Last Server: {character['last_server']}"
            )
            embed.add_field(
                name = f"Level {character['level']} {character['class']}",
                value = value,
                inline = False
            )
        await ctx.send(embed = embed)

