
from discord.ext import commands

import asyncio
import copy

import pydealer

from utilities import checks


async def setup(bot):
    await bot.add_cog(Blackjack(bot))


class Blackjack(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.blackjack_ranks = copy.deepcopy(pydealer.const.DEFAULT_RANKS)
        self.blackjack_ranks["values"].update({"Ace": 0, "King": 9, "Queen": 9, "Jack": 9})
        for value in self.blackjack_ranks["values"]:
            self.blackjack_ranks["values"][value] += 1

    @commands.command()
    @checks.not_forbidden()
    async def blackjack(self, ctx):
        '''
        Play a game of blackjack
        Manage Messages permission required for message cleanup
        '''
        # TODO: S17
        deck = pydealer.Deck()
        deck.shuffle()
        dealer = deck.deal(2)
        player = deck.deal(2)
        dealer_string = f":grey_question: :{dealer.cards[1].suit.lower()}: {dealer.cards[1].value}"
        player_string = self.cards_to_string(player.cards)
        dealer_total = self.blackjack_total(dealer.cards)
        player_total = self.blackjack_total(player.cards)
        response = await ctx.embed_reply(f"Dealer: {dealer_string} (?)\n{ctx.author.display_name}: {player_string} ({player_total})\n", title = "Blackjack", footer_text = "Hit or Stay?")
        embed = response.embeds[0]
        while True:
            action = await self.bot.wait_for("message", check = lambda m: m.author == ctx.author and m.content.lower().strip('!') in ("hit", "stay"))
            await self.bot.attempt_delete_message(action)
            if action.content.lower().strip('!') == "hit":
                player.add(deck.deal())
                player_string = self.cards_to_string(player.cards)
                player_total = self.blackjack_total(player.cards)
                embed.description = f"Dealer: {dealer_string} (?)\n{ctx.author.display_name}: {player_string} ({player_total})\n"
                await response.edit(embed = embed)
                if player_total > 21:
                    embed.description += ":boom: You have busted"
                    embed.set_footer(text = "You lost :(")
                    break
            else:
                dealer_string = self.cards_to_string(dealer.cards)
                embed.description = f"Dealer: {dealer_string} ({dealer_total})\n{ctx.author.display_name}: {player_string} ({player_total})\n"
                if dealer_total > 21:
                    embed.description += ":boom: The dealer busted"
                    embed.set_footer(text = "You win!")
                    break
                elif dealer_total > player_total:
                    embed.description += "The dealer beat you"
                    embed.set_footer(text = "You lost :(")
                    break
                embed.set_footer(text = "Dealer's turn..")
                await response.edit(embed = embed)
                while dealer_total < 21 and dealer_total <= player_total:
                    await asyncio.sleep(5)
                    dealer.add(deck.deal())
                    dealer_string = self.cards_to_string(dealer.cards)
                    dealer_total = self.blackjack_total(dealer.cards)
                    embed.description = f"Dealer: {dealer_string} ({dealer_total})\n{ctx.author.display_name}: {player_string} ({player_total})\n"
                    await response.edit(embed = embed)
                if dealer_total > 21:
                    embed.description += ":boom: The dealer busted"
                    embed.set_footer(text = "You win!")
                elif dealer_total > player_total:
                    embed.description += "The dealer beat you"
                    embed.set_footer(text = "You lost :(")
                elif dealer_total == player_total == 21:
                    embed.set_footer(text = "It's a push (tie)")
                break
        await response.edit(embed = embed)

    def blackjack_total(self, cards):
        total = sum(self.blackjack_ranks["values"][card.value] for card in cards)
        if pydealer.tools.find_card(cards, term = "Ace", limit = 1) and total <= 11: total += 10
        return total

    def cards_to_string(self, cards):
        return "".join(":{}: {} ".format(card.suit.lower(), card.value) for card in cards)
