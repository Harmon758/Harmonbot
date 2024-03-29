
from discord import ui
from discord.ext import commands

import asyncio

import pydealer

from utilities import checks


BLACKJACK_VALUES = pydealer.const.DEFAULT_RANKS["values"].copy()
BLACKJACK_VALUES.update({"Ace": 0, "King": 9, "Queen": 9, "Jack": 9})
for value in BLACKJACK_VALUES:
    BLACKJACK_VALUES[value] += 1


async def setup(bot):
    await bot.add_cog(Blackjack())


class Blackjack(commands.Cog):

    @commands.hybrid_command()
    @checks.not_forbidden()
    async def blackjack(self, ctx):
        """Play a game of blackjack"""
        # TODO: S17
        game = BlackjackGame(bot = ctx.bot)

        view = BlackjackView(bot = ctx.bot, game = game, user = ctx.author)
        response = await ctx.embed_reply(
            title = "Blackjack",
            description = (
                f"{ctx.me.mention}:\n"
                f"{game.dealer_string}\n"
                f"(**?**)\n\n"
                f"{ctx.author.mention}:\n"
                f"{game.player_string}\n"
                f"(**{game.player_total}**)\n"
            ),
            footer_text = "Hit or Stay?",
            view = view
        )
        embed = response.embeds[0]

        view.message = response
        ctx.bot.views.append(view)
        await view.wait()

        if game.player_total <= 21:
            game.dealer_turn = True

            embed.description = (
                f"{ctx.me.mention}:\n"
                f"{game.dealer_string}\n"
                f"(**{game.dealer_total}**)\n\n"
                f"{ctx.author.mention}:\n"
                f"{game.player_string}\n"
                f"(**{game.player_total}**)\n"
            )

            if game.dealer_total > game.player_total:
                embed.description += f"\n{ctx.me.mention} beat you"
                embed.set_footer(text = "You lost :(")
                await response.edit(embed = embed)
                return

            embed.set_footer(text = "Dealer's turn..")
            await response.edit(embed = embed)

            while game.dealer_total < 21 and game.dealer_total <= game.player_total:
                await asyncio.sleep(5)

                game.dealer_hit()

                embed.description = (
                    f"{ctx.me.mention}:\n"
                    f"{game.dealer_string}\n"
                    f"(**{game.dealer_total}**)\n\n"
                    f"{ctx.author.mention}:\n"
                    f"{game.player_string}\n"
                    f"(**{game.player_total}**)\n"
                )
                await response.edit(embed = embed)

            if game.dealer_total > 21:
                embed.description += (
                    f"\n\N{COLLISION SYMBOL} {ctx.me.mention} busted"
                )
                embed.set_footer(text = "You won!")
            elif game.dealer_total > game.player_total:
                embed.description += f"\n{ctx.me.mention} beat you"
                embed.set_footer(text = "You lost :(")
            elif game.dealer_total == game.player_total == 21:
                embed.set_footer(text = "It was a push (tie)")

            await response.edit(embed = embed)


class BlackjackGame:

    def __init__(self, bot):
        self.bot = bot

        self.deck = pydealer.Deck()
        self.deck.shuffle()
        self.dealer = self.deck.deal(2)
        self.player = self.deck.deal(2)

        self.dealer_turn = False

    def dealer_hit(self):
        self.dealer.add(self.deck.deal())

    @property
    def dealer_string(self):
        if self.dealer_turn:
            return self.bot.cards_to_string(
                self.dealer.cards, custom_emoji = True
            )
        else:
            return self.bot.cards_to_string(
                self.dealer.cards[1], custom_emoji = True,
                hidden_card_indexes = 0
            )

    @property
    def dealer_total(self):
        return calculate_total(self.dealer.cards)

    def player_hit(self):
        self.player.add(self.deck.deal())

    @property
    def player_string(self):
        return self.bot.cards_to_string(self.player.cards, custom_emoji = True)

    @property
    def player_total(self):
        return calculate_total(self.player.cards)


def calculate_total(cards):
    total = sum(BLACKJACK_VALUES[card.value] for card in cards)

    if pydealer.tools.find_card(
        cards, term = "Ace", limit = 1
    ) and total <= 11:
        total += 10

    return total


class BlackjackView(ui.View):

    def __init__(self, *, bot, game, user):
        super().__init__(timeout = None)

        self.bot = bot
        self.game = game
        self.user = user

        self.message = None

    @ui.button(label = "Hit")
    async def hit(self, interaction, button):
        self.game.player_hit()

        embed = interaction.message.embeds[0]
        embed.description = (
            f"{interaction.client.user.mention}:\n"
            f"{self.game.dealer_string}\n"
            f"(**?**)\n\n"
            f"{interaction.user.mention}:\n"
            f"{self.game.player_string}\n"
            f"(**{self.game.player_total}**)\n"
        )

        if self.game.player_total > 21:
            embed.description += "\n\N{COLLISION SYMBOL} You have busted"
            embed.set_footer(text = "You lost :(")
            await self.stop(interaction = interaction, embed = embed)
        else:
            await interaction.response.edit_message(embed = embed)

    @ui.button(label = "Stay")
    async def stay(self, interaction, button):
        await self.stop(interaction = interaction)

    async def interaction_check(self, interaction):
        if interaction.user.id not in (
            self.user.id, interaction.client.owner_id
        ):
            await interaction.response.send_message(
                "You aren't the one playing this blackjack game.",
                ephemeral = True
            )
            return False
        return True

    async def stop(self, *, interaction = None, embed = None):
        self.hit.disabled = True
        self.stay.disabled = True

        if interaction:
            if embed:
                await interaction.response.edit_message(
                    embed = embed, view = self
                )
            else:
                await interaction.response.edit_message(view = self)
        elif self.message:
            await self.bot.attempt_edit_message(self.message, view = self)

        super().stop()
