
from discord.ext import commands

import random

from utilities import checks


async def setup(bot):
    await bot.add_cog(RPS())

class RPS(commands.Cog):

    @commands.command(
        aliases = [
            "rockpaperscissors", "rock-paper-scissors", "rock_paper_scissors"
        ],
        usage = "<object>"
    )
    @checks.not_forbidden()
    async def rps(self, ctx, rps_object: str):
        '''Rock paper scissors'''
        if rps_object.lower() not in (
            'r', 'p', 's', "rock", "paper", "scissors"
        ):
            raise commands.BadArgument("That's not a valid object")
        value = random.choice(("rock", "paper", "scissors"))
        short_shape = rps_object[0].lower()
        resolution = {
            'r': {'s': "crushes"}, 'p': {'r': "covers"}, 's': {'p': "cuts"}
        }
        emotes = {
            'r': f"\N{RAISED FIST}{ctx.bot.emoji_skin_tone}",
            'p': f"\N{RAISED HAND}{ctx.bot.emoji_skin_tone}", 
            's': f"\N{VICTORY HAND}{ctx.bot.emoji_skin_tone}"
        }
        if value[0] == short_shape:
            await ctx.embed_reply(f"I chose `{value}`\nIt's a draw :confused:")
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
        aliases = [
            "rockpaperscissorslizardspock", "rock-paper-scissors-lizard-spock"
        ],
        usage = "<object>"
    )
    @checks.not_forbidden()
    async def rpsls(self, ctx, rpsls_object: str):
        '''
        RPS lizard Spock
        https://upload.wikimedia.org/wikipedia/commons/f/fe/Rock_Paper_Scissors_Lizard_Spock_en.svg
        '''
        if rpsls_object.lower() not in (
            'r', 'p', 's', 'l', "rock", "paper", "scissors", "lizard", "spock"
        ):
            raise commands.BadArgument("That's not a valid object")
        value = random.choice(("rock", "paper", "scissors", "lizard", "Spock"))
        if (
            rpsls_object[0] == 'S' and rpsls_object.lower() != "scissors" or
            rpsls_object.lower() == "spock"
        ):
            short_shape = 'S'
        else:
            short_shape = rpsls_object[0].lower()
        resolution = {
            'r': {'s': "crushes", 'l': "crushes"},
            'p': {'r': "covers", 'S': "disproves"},
            's': {'p': "cuts", 'l': "decapitates"},
            'l': {'p': "eats", 'S': "poisons"},
            'S': {'r': "vaporizes", 's': "smashes"}
        }
        emotes = {
            'r': f"\N{RAISED FIST}{ctx.bot.emoji_skin_tone}",
            'p': f"\N{RAISED HAND}{ctx.bot.emoji_skin_tone}",
            's': f"\N{VICTORY HAND}{ctx.bot.emoji_skin_tone}",
            'l': ":lizard:",
            'S': f"\N{RAISED HAND WITH PART BETWEEN MIDDLE AND RING FINGERS}{ctx.bot.emoji_skin_tone}"
        }
        if value[0] == short_shape:
            await ctx.embed_reply(f"I chose `{value}`\nIt's a draw :confused:")
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
        aliases = [
            "rockpaperscissorslizardspockspidermanbatmanwizardglock",
            "rock-paper-scissors-lizard-spock-spiderman-batman-wizard-glock"
        ],
        usage = "<object>"
    )
    @checks.not_forbidden()
    async def rpslssbwg(self, ctx, rpslssbwg_object: str):
        '''
        RPSLS Spider-Man Batman wizard Glock
        http://i.imgur.com/m9C2UTP.jpg
        '''
        rpslssbwg_object = rpslssbwg_object.lower().replace('-', "")
        if rpslssbwg_object not in (
            "rock", "paper", "scissors", "lizard", "spock", "spiderman",
            "batman", "wizard", "glock"
        ):
            raise commands.BadArgument("That's not a valid object")
        value = random.choice((
            "rock", "paper", "scissors", "lizard", "Spock", "Spider-Man",
            "Batman", "wizard", "Glock"
        ))
        resolution = {
            "rock": {"scissors": "crushes", "lizard": "crushes", "spiderman": "knocks out", "wizard": "interrupts"},
            "paper": {"rock": "covers", "spock": "disproves", "batman": "delays", "glock": "jams"},
            "scissors": {"paper": "cuts", "lizard": "decapitates", "spiderman": "cuts", "wizard": "cuts"},
            "lizard": {"paper": "eats", "spock": "poisons", "batman": "confuses", "glock": "is too small for"},
            "spock": {"rock": "vaporizes", "scissors": "smashes", "spiderman": "befuddles", "wizard": "zaps"},
            "spiderman": {"paper": "rips", "lizard": "defeats", "wizard": "annoys", "glock": "disarms"},
            "batman": {"rock": "explodes", "scissors": "dismantles", "spiderman": "scares", "spock": "hangs"},
            "wizard": {"paper": "burns", "lizard": "transforms", "batman": "stuns", "glock": "melts"},
            "glock": {"rock": "breaks", "scissors": "dents", "batman": "kills parents of", "spock": "shoots"}
        }
        emotes = {
            "rock": f"\N{RAISED FIST}{ctx.bot.emoji_skin_tone}",
            "paper": f"\N{RAISED HAND}{ctx.bot.emoji_skin_tone}", 
            "scissors": f"\N{VICTORY HAND}{ctx.bot.emoji_skin_tone}",
            "lizard": ":lizard:",
            "spock": f"\N{RAISED HAND WITH PART BETWEEN MIDDLE AND RING FINGERS}{ctx.bot.emoji_skin_tone}",
            "spiderman": ":spider:",
            "batman": ":bat:",
            "wizard": ":tophat:",
            "glock": ":gun:"
        }
        standard_value = value.lower().replace('-', "")
        if standard_value == rpslssbwg_object:
            await ctx.embed_reply(
                f"I chose `{value}`\n"
                "It's a draw :confused:"
            )
        elif rpslssbwg_object in resolution[standard_value]:
            await ctx.embed_reply(
                f"I chose `{value}`\n"
                f"{emotes[standard_value]} {resolution[standard_value][rpslssbwg_object]} {emotes[rpslssbwg_object]}\n"
                "You lose :slight_frown:"
            )
        else:
            await ctx.embed_reply(
                f"I chose `{value}`\n"
                f"{emotes[rpslssbwg_object]} {resolution[rpslssbwg_object][standard_value]} {emotes[standard_value]}\n"
                "You win! :tada:"
            )

    @commands.command(
        aliases = ["cockroachfootnuke", "cockroach-foot-nuke"],
        usage = "<object>"
    )
    @checks.not_forbidden()
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
    @checks.not_forbidden()
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

