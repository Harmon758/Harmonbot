
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
        """
        Play a game of blackjack
        Manage Messages permission required for message cleanup
        """
        # TODO: S17
        game = BlackjackGame()

        response = await ctx.embed_reply(
            title = "Blackjack",
            description = (
                f"Dealer: {game.dealer_string} (?)"
                f"\n{ctx.author.display_name}: {game.player_string} ({game.player_total})\n"
            ),
            footer_text = "Hit or Stay?"
        )
        embed = response.embeds[0]

        while True:
            action = await ctx.bot.wait_for(
                "message",
                check = (lambda message: (
                    message.author == ctx.author and
                    message.content.lower().strip('!') in ("hit", "stay")
                ))
            )
            await ctx.bot.attempt_delete_message(action)

            if action.content.lower().strip('!') == "hit":
                game.player_hit()

                embed.description = (
                    f"Dealer: {game.dealer_string} (?)\n"
                    f"{ctx.author.display_name}: {game.player_string} ({game.player_total})\n"
                )
                await response.edit(embed = embed)

                if game.player_total > 21:
                    embed.description += ":boom: You have busted"
                    embed.set_footer(text = "You lost :(")
                    break
            else:
                game.dealer_turn = True

                embed.description = (
                    f"Dealer: {game.dealer_string} ({game.dealer_total})\n"
                    f"{ctx.author.display_name}: {game.player_string} ({game.player_total})\n"
                )
                if game.dealer_total > 21:
                    embed.description += ":boom: The dealer busted"
                    embed.set_footer(text = "You win!")
                    break
                elif game.dealer_total > game.player_total:
                    embed.description += "The dealer beat you"
                    embed.set_footer(text = "You lost :(")
                    break
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
                    embed.description += ":boom: The dealer busted"
                    embed.set_footer(text = "You win!")
                elif game.dealer_total > game.player_total:
                    embed.description += "The dealer beat you"
                    embed.set_footer(text = "You lost :(")
                elif game.dealer_total == game.player_total == 21:
                    embed.set_footer(text = "It's a push (tie)")
                break

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
            return f":grey_question: :{self.dealer.cards[1].suit.lower()}: {self.dealer.cards[1].value}"

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
