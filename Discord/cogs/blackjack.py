
from discord import ui
from discord.ext import commands

import asyncio
import copy

import pydealer

from utilities import checks


BLACKJACK_RANKS = copy.deepcopy(pydealer.const.DEFAULT_RANKS)
BLACKJACK_RANKS["values"].update({"Ace": 0, "King": 9, "Queen": 9, "Jack": 9})
for value in BLACKJACK_RANKS["values"]:
    BLACKJACK_RANKS["values"][value] += 1


async def setup(bot):
    await bot.add_cog(Blackjack())


class Blackjack(commands.Cog):

    @commands.command()
    @checks.not_forbidden()
    async def blackjack(self, ctx):
        """Play a game of blackjack"""
        # TODO: S17
        game = BlackjackGame()

        view = BlackjackView(game = game)
        response = await ctx.embed_reply(
            title = "Blackjack",
            description = (
                f"Dealer: {game.dealer_string} (?)"
                f"\n{ctx.author.display_name}: {game.player_string} ({game.player_total})\n"
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
                f"Dealer: {game.dealer_string} ({game.dealer_total})\n"
                f"{ctx.author.display_name}: {game.player_string} ({game.player_total})\n"
            )

            if game.dealer_total > game.player_total:
                embed.description += "The dealer beat you"
                embed.set_footer(text = "You lost :(")
                await response.edit(embed = embed)
                return

            embed.set_footer(text = "Dealer's turn..")
            await response.edit(embed = embed)

            while game.dealer_total < 21 and game.dealer_total <= game.player_total:
                await asyncio.sleep(5)

                game.dealer_hit()

                embed.description = (
                    f"Dealer: {game.dealer_string} ({game.dealer_total})\n"
                    f"{ctx.author.display_name}: {game.player_string} ({game.player_total})\n"
                )
                await response.edit(embed = embed)

            if game.dealer_total > 21:
                embed.description += "\N{COLLISION SYMBOL} The dealer busted"
                embed.set_footer(text = "You win!")
            elif game.dealer_total > game.player_total:
                embed.description += "The dealer beat you"
                embed.set_footer(text = "You lost :(")
            elif game.dealer_total == game.player_total == 21:
                embed.set_footer(text = "It's a push (tie)")

            await response.edit(embed = embed)


class BlackjackGame:

    def __init__(self):
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
            return cards_to_string(self.dealer.cards)
        else:
            return f"\N{WHITE QUESTION MARK ORNAMENT} :{self.dealer.cards[1].suit.lower()}: {self.dealer.cards[1].value}"

    @property
    def dealer_total(self):
        return calculate_total(self.dealer.cards)

    def player_hit(self):
        self.player.add(self.deck.deal())

    @property
    def player_string(self):
        return cards_to_string(self.player.cards)

    @property
    def player_total(self):
        return calculate_total(self.player.cards)


def calculate_total(cards):
    total = sum(BLACKJACK_RANKS["values"][card.value] for card in cards)
    if pydealer.tools.find_card(cards, term = "Ace", limit = 1) and total <= 11:
        total += 10
    return total

def cards_to_string(cards):
    return "".join(f":{card.suit.lower()}: {card.value} " for card in cards)


class BlackjackView(ui.View):

    def __init__(self, *, game):
        super().__init__(timeout = None)

        self.game = game

        self.message = None

    @ui.button(label = "Hit")
    async def hit(self, interaction, button):
        self.game.player_hit()

        embed = interaction.message.embeds[0]
        embed.description = (
            f"Dealer: {self.game.dealer_string} (?)\n"
            f"{interaction.user.display_name}: {self.game.player_string} ({self.game.player_total})\n"
        )

        if self.game.player_total > 21:
            embed.description += "\N{COLLISION SYMBOL} You have busted"
            embed.set_footer(text = "You lost :(")
            await self.stop(interaction = interaction, embed = embed)
        else:
            await interaction.response.edit_message(embed = embed)

    @ui.button(label = "Stay")
    async def stay(self, interaction, button):
        await self.stop(interaction = interaction)

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
