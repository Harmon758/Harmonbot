
from discord import app_commands
from discord.ext import commands

import random
from typing import Literal, Optional

from utilities import checks


EMOJI = {
    "rock": '\N{RAISED FIST}',
    "paper": '\N{RAISED HAND}',
    "scissors": '\N{VICTORY HAND}',
    "lizard": '🫳',  # Replace with '\N{PALM DOWN HAND}' in Python 3.11
    "Spock": '\N{RAISED HAND WITH PART BETWEEN MIDDLE AND RING FINGERS}',
    "Spider-Man": ":spider:",
    "Batman": ":bat:",
    "wizard": ":tophat:",
    "Glock": ":gun:"
}

RPS_OBJECTS = ("rock", "paper", "scissors")
RPSLS_OBJECTS = RPS_OBJECTS + ("lizard", "Spock")
RPSLSSBWG_OBJECTS = RPSLS_OBJECTS + ("Spider-Man", "Batman", "wizard", "Glock")

OBJECTS = {
    "RPS": RPS_OBJECTS, "RPSLS": RPSLS_OBJECTS, "RPSLSSBWG": RPSLSSBWG_OBJECTS
}

RESOLUTION = {
    "rock": {
        "scissors": "crushes", "lizard": "crushes",
        "Spider-Man": "knocks out", "wizard": "interrupts"
    },
    "paper": {
        "rock": "covers", "Spock": "disproves", "Batman": "delays",
        "Glock": "jams"
    },
    "scissors": {
        "paper": "cuts", "lizard": "decapitates", "Spider-Man": "cuts",
        "wizard": "cuts"
    },
    "lizard": {
        "paper": "eats", "Spock": "poisons", "Batman": "confuses",
        "Glock": "is too small for"
    },
    "Spock": {
        "rock": "vaporizes", "scissors": "smashes", "Spider-Man": "befuddles",
        "wizard": "zaps"
    },
    "Spider-Man": {
        "paper": "rips", "lizard": "defeats", "wizard": "annoys",
        "Glock": "disarms"
    },
    "Batman": {
        "rock": "explodes", "scissors": "dismantles", "Spider-Man": "scares",
        "Spock": "hangs"
    },
    "wizard": {
        "paper": "burns", "lizard": "transforms", "Batman": "stuns",
        "Glock": "melts"
    },
    "Glock": {
        "rock": "breaks", "scissors": "dents", "Batman": "kills parents of",
        "Spock": "shoots"
    }
}


async def setup(bot):
    for object_name in EMOJI:
        EMOJI[object_name] += bot.emoji_skin_tone

    await bot.add_cog(RPS())

class RPS(commands.Cog):

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.hybrid_command(
        aliases = [
            "rockpaperscissors", "rock-paper-scissors", "rock_paper_scissors"
        ],
        usage = "<object>"
    )
    @app_commands.rename(rps_object = "object")
    async def rps(
        self, ctx,
        rps_object: str,
        variant: Optional[Literal["RPS", "RPSLS", "RPSLSSBWG"]] = "RPS"  # noqa: UP007 (non-pep604-annotation)
    ):
        '''
        Rock Paper Scissors

        RPSLS — RPS lizard Spock
        https://upload.wikimedia.org/wikipedia/commons/f/fe/Rock_Paper_Scissors_Lizard_Spock_en.svg

        RPSLSSBWG — RPSLS Spider-Man Batman wizard Glock
        http://i.imgur.com/m9C2UTP.jpg

        Parameters
        ----------
        rps_object
            Object of your choice
        variant
            Variant of RPS to play
            (Defaults to None / RPS)
        '''
        if rps_object not in OBJECTS[variant]:
            raise commands.BadArgument("That's not a valid object")
        value = random.choice(OBJECTS[variant])
        if value == rps_object:
            await ctx.embed_reply(
                f"I chose `{value}`\n"
                "It's a draw :confused:"
            )
        elif rps_object in RESOLUTION[value]:
            await ctx.embed_reply(
                f"I chose `{value}`\n"
                f"{EMOJI[value]} {RESOLUTION[value][rps_object]} {EMOJI[rps_object]}\n"
                "You lose :slight_frown:"
            )
        else:
            await ctx.embed_reply(
                f"I chose `{value}`\n"
                f"{EMOJI[rps_object]} {RESOLUTION[rps_object][value]} {EMOJI[value]}\n"
                "You win! :tada:"
            )

    @rps.autocomplete("rps_object")
    async def rps_autocomplete(self, interaction, current):
        variant = interaction.namespace.variant or "RPS"
        return [
            app_commands.Choice(name = rps_object, value = rps_object)
            for rps_object in OBJECTS[variant]
            if current.lower() in rps_object.lower()
        ]

    @commands.command(
        aliases = [
            "rockpaperscissorslizardspock", "rock-paper-scissors-lizard-spock"
        ],
        usage = "<object>"
    )
    async def rpsls(self, ctx, rpsls_object: str):
        '''
        RPS lizard Spock
        https://upload.wikimedia.org/wikipedia/commons/f/fe/Rock_Paper_Scissors_Lizard_Spock_en.svg
        '''
        if command := ctx.bot.get_command("rps"):
            await ctx.invoke(
                command, rps_object = rpsls_object, variant = "RPSLS"
            )
        else:
            raise RuntimeError(
                "rps command not found when rpsls command invoked"
            )

    @commands.command(
        aliases = [
            "rockpaperscissorslizardspockspidermanbatmanwizardglock",
            "rock-paper-scissors-lizard-spock-spiderman-batman-wizard-glock"
        ],
        usage = "<object>"
    )
    async def rpslssbwg(self, ctx, rpslssbwg_object: str):
        '''
        RPSLS Spider-Man Batman wizard Glock
        http://i.imgur.com/m9C2UTP.jpg
        '''
        if command := ctx.bot.get_command("rps"):
            await ctx.invoke(
                command, rps_object = rpslssbwg_object, variant = "RPSLSSBWG"
            )
        else:
            raise RuntimeError(
                "rps command not found when rpslssbwg command invoked"
            )

    @commands.command(
        aliases = ["cockroachfootnuke", "cockroach-foot-nuke"],
        usage = "<object>"
    )
    async def cfn(self, ctx, cfn_object: str):
        '''
        Cockroach foot nuke
        https://www.youtube.com/watch?v=wRi2j8k0vjo
        '''
        if cfn_object.lower() not in (
            'c', 'f', 'n', "cockroach", "foot", "nuke"
        ):
            raise commands.BadArgument("That's not a valid object")
        value = random.choice(("cockroach", "foot", "nuke"))
        short_shape = cfn_object[0].lower()
        resolution = {
            'c': {'n': "survives"}, 'f': {'c': "squashes"},
            'n': {'f': "blows up"}
        }
        emotes = {'c': ":bug:", 'f': ":footprints:", 'n': ":bomb:"}
        if value[0] == short_shape:
            await ctx.embed_reply(
                f"I chose `{value}`\n"
                "It's a draw :confused:"
            )
        elif short_shape in resolution[value[0]]:
            await ctx.embed_reply(
                f"I chose `{value}`\n"
                f"{emotes[value[0]]} {resolution[value[0]][short_shape]} {emotes[short_shape]}\n"
                "You lose :slight_frown:"
            )
        else:
            await ctx.embed_reply(
                f"I chose `{value}`\n"
                f"{emotes[short_shape]} {resolution[short_shape][value[0]]} {emotes[value[0]]}\n"
                "You win! :tada:"
            )

    @commands.command(
        aliases = ["extremerps", "rps-101", "rps101"],
        usage = "<object>"
    )
    async def erps(self, ctx, erps_object: str):
        '''
        Extreme rock paper scissors
        http://www.umop.com/rps101.htm
        http://www.umop.com/rps101/alloutcomes.htm
        http://www.umop.com/rps101/rps101chart.html
        '''
        # TODO: Harmonbot option
        erps_object = (
            erps_object.lower().replace('.', "").replace("video game", "game")
        )
        # dynamite: outwits gun
        # tornado: sweeps away -> blows away, fills pit, ruins camera
        emotes = {
            "dynamite": ":boom:", "tornado": ":cloud_tornado:", "quicksand": "quicksand",
            "pit": ":black_circle:", "chain": ":chains:", "gun": ":gun:", "law": ":scales:", "whip": "whip",
            "sword": ":crossed_swords:", "rock": f"\N{RAISED FIST}{ctx.bot.emoji_skin_tone}", "death": ":skull:",
            "wall": "wall", "sun": ":sunny:", "camera": ":camera:", "fire": ":fire:", "chainsaw": "chainsaw",
            "school": ":school:", "scissors": ":scissors:", "poison": "poison", "cage": "cage", "axe": "axe",
            "peace": ":peace:", "computer": ":computer:", "castle": ":european_castle:", "snake": ":snake:",
            "blood": "blood", "porcupine": "porcupine", "vulture": "vulture", "monkey": ":monkey:", "king": "king",
            "queen": "queen", "prince": "prince", "princess": "princess", "police": ":police_car:",
            "woman": f"\N{WOMAN}{ctx.bot.emoji_skin_tone}", "baby": f"\N{BABY}{ctx.bot.emoji_skin_tone}",
            "man": f"\N{MAN}{ctx.bot.emoji_skin_tone}", "home": ":homes:", "train": ":train:", "car": ":red_car:",
            "noise": "noise", "bicycle": f"\N{BICYCLIST}{ctx.bot.emoji_skin_tone}", "tree": ":evergreen_tree:",
            "turnip": "turnip", "duck": ":duck:", "wolf": ":wolf:", "cat": ":cat:", "bird": ":bird:",
            "fish": ":fish:", "spider": ":spider:", "cockroach": "cockroach", "brain": "brain",
            "community": "community", "cross": ":cross:", "money": ":moneybag:", "vampire": "vampire",
            "sponge": "sponge", "church": ":church:", "butter": "butter", "book": ":book:",
            "paper": f"\N{RAISED HAND}{ctx.bot.emoji_skin_tone}", "cloud": ":cloud:", "airplane": ":airplane:",
            "moon": ":full_moon:", "grass": "grass", "film": ":film_frames:", "toilet": ":toilet:", "air": "air",
            "planet": "planet", "guitar": ":guitar:", "bowl": "bowl", "cup": "cup", "beer": ":beer:",
            "rain": ":cloud_rain:", "water": ":potable_water:", "tv": ":tv:", "rainbow": ":rainbow:", "ufo": "ufo",
            "alien": ":alien:", "prayer": f"\N{PERSON WITH FOLDED HANDS}{ctx.bot.emoji_skin_tone}",
            "mountain": ":mountain:", "satan": "satan", "dragon": ":dragon:", "diamond": "diamond",
            "platinum": "platinum", "gold": "gold", "devil": "devil", "fence": "fence", "game": ":video_game:",
            "math": "math", "robot": ":robot:", "heart": ":heart:", "electricity": ":zap:",
            "lightning": ":cloud_lightning:", "medusa": "medusa", "power": ":electric_plug:", "laser": "laser",
            "nuke": ":bomb:", "sky": "sky", "tank": "tank", "helicopter": ":helicopter:"
        }
        '''
        for key, emote in emotes.ites():
            if key == emote
                print(key)
        '''
        value = random.choice(list(emotes.keys()))
        if erps_object not in emotes:
            raise commands.BadArgument("That's not a valid object")
        standard_value = (
            value.lower().replace('.', "").replace("video game", "game")
        )
        if standard_value == erps_object:
            await ctx.embed_reply(
                f"I chose `{value}`\n"
                "It's a draw :confused:"
            )
            return
        action = await ctx.bot.db.fetchval(
            """
            SELECT action FROM games.erps
            WHERE object = $1 AND against = $2
            """,
            standard_value, erps_object
        )
        if action:
            await ctx.embed_reply(
                f"I chose `{value}`\n"
                f"{emotes[standard_value]} {action} {emotes[erps_object]}\n"
                "You lose :slight_frown:"
            )
            return
        action = await ctx.bot.db.fetchval(
            """
            SELECT action FROM games.erps
            WHERE object = $1 AND against = $2
            """,
            erps_object, standard_value
        )
        if action:
            await ctx.embed_reply(
                f"I chose `{value}`\n"
                f"{emotes[erps_object]} {action} {emotes[standard_value]}\n"
                "You win! :tada:"
            )
            return
        await ctx.embed_reply(
            ":no_entry: Error: I don't know the relationship between "
            f"{emotes[erps_object]} and {emotes[standard_value]}, the object that I chose"
        )

