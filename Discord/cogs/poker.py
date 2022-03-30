
import discord
from discord.ext import commands

import asyncio

import pydealer
import treys

from utilities import checks


async def setup(bot):
    await bot.add_cog(Poker())

def cards_to_string(cards):
    return " | ".join(f":{card.suit.lower()}: {card.value}" for card in cards)


class Poker(commands.Cog):

    def __init__(self):
        self.poker_hands = {}

    @commands.command()
    @checks.not_forbidden()
    async def poker(self, ctx):
        '''Texas Hold'em'''
        if poker_hand := self.poker_hands.get(ctx.channel.id):
            return await ctx.embed_reply(
                f"[There's already a poker match in progress here]({poker_hand.message.jump_url})"
            )

        self.poker_hands[ctx.channel.id] = PokerHand(ctx)
        await self.poker_hands[ctx.channel.id].start(ctx)
        del self.poker_hands[ctx.channel.id]


class PokerHand:

    STAGES = {1: "flop", 2: "turn", 3: "river", 4: "showdown"}

    def __init__(self, ctx):
        self.bot = ctx.bot
        self.channel = ctx.channel
        self.ctx = ctx

        self.deck = pydealer.Deck()
        self.deck.shuffle()
        self.community_cards = self.deck.deal(5)
        self.hands = {}

        self.bets = {}
        self.current_bet = 0
        self.pot = 0
        self.stage = -1
        self.turn = None  # who's turn it is

        self.lines = []  # embed lines

        self.ended = asyncio.Event()

    async def start(self, ctx):
        self.lines = [f"{ctx.author.mention} is initiating a poker match"]
        self.message = await ctx.embed_reply(
            self.lines[0],
            author_name = None,
            footer_text = None,
            view = PokerLobby(self)
        )
        self.embed = self.message.embeds[0]
        await self.ended.wait()

    def add_player(self, player):
        self.hands[player] = self.deck.deal(2)

    async def bet(self, amount):
        self.current_bet += amount
        self.bets[self.turn] = self.current_bet
        await self.next_turn()

    async def call(self):
        self.bets[self.turn] = self.current_bet
        await self.next_turn()

    async def fold(self):
        self.pot += self.bets.pop(self.turn, 0)

        index = list(self.hands).index(self.turn)
        del self.hands[self.turn]

        if len(self.hands) == 1:
            return await self.last_remaining_end()

        await self.next_turn(index = index)

    async def next_turn(self, *, index = None):
        if (
            len(self.hands) == len(self.bets) and
            all(bet == self.current_bet for bet in self.bets.values())
        ):
            self.pot += sum(self.bets.values())
            return await self.new_round()

        players = list(self.hands)
        if index is not None:
            try:
                self.turn = players[index]
            except IndexError:
                self.turn = players[0]
        elif self.turn is None or self.turn == players[-1]:
            self.turn = players[0]
        else:
            self.turn = players[players.index(self.turn) + 1]

        self.embed.description = (
            '\n'.join(self.lines) + ('\n' if self.lines[-1] else "") +
            f"\n{self.turn.mention}'s turn:"
        )
        await self.message.edit(
            embed = self.embed,
            view = PokerRound(
                self, call = self.current_bet - self.bets.get(self.turn, 0)
            )
        )

    async def new_round(self):
        self.bets = {}
        self.current_bet = 0

        self.stage += 1

        if self.stage:
            number_of_cards = min(self.stage + 2, 5)
            self.lines.append("")
            self.lines.append(f"The pot: {self.pot}")
            self.lines.append(
                f"The {self.STAGES[self.stage]}: {cards_to_string(self.community_cards[:number_of_cards])}"
            )
            await self.message.edit(embed = self.embed)

        if self.stage == 4:
            return await self.showdown_end()

        self.lines.append("")

        await self.next_turn()

    async def last_remaining_end(self):
        winner, hand = next(iter(self.hands.items()))

        self.lines.append("")
        self.lines.append(f"{winner.mention} is the winner of {self.pot}")
        self.embed.description = (
            '\n'.join(self.lines) +
            f"\n{winner.mention}: Would you like to show your hand?"
        )
        await self.message.edit(
            embed = self.embed, view = PokerMuck(self, winner)
        )

        self.ended.set()

    async def showdown_end(self):
        evaluator = treys.Evaluator()
        board = [
            treys.Card.new(
                (card.value[0] if card.value != "10" else 'T') + card.suit[0].lower()
            )
            for card in self.community_cards.cards
        ]
        best_hand_value = evaluator.table.MAX_HIGH_CARD
        for player, hand in self.hands.items():
            hand_stack = [
                treys.Card.new(
                    (card.value[0] if card.value != "10" else 'T') + card.suit[0].lower()
                )
                for card in hand
            ]
            value = evaluator.evaluate(board, hand_stack)
            if value < best_hand_value:
                best_hand_value = value
                winner = player
                # TODO: Handle multiple winners

        hand_name = evaluator.class_to_string(evaluator.get_rank_class(best_hand_value))
        self.lines.append("")
        self.lines.append(f"{winner.mention} is the winner of {self.pot} with a {hand_name}")
        self.lines.append(f"{winner.mention}'s hand: {cards_to_string(self.hands.pop(winner))}")

        for player, hand in self.hands.items():
            self.embed.description = (
                '\n'.join(self.lines) +
                f"\n\n{player.mention}: Would you like to show your hand?"
            )
            view = PokerMuck(self, player)
            await self.message.edit(embed = self.embed, view = view)
            await view.wait()

        await self.message.edit(view = None)

        self.ended.set()


class PokerLobby(discord.ui.View):

    def __init__(self, poker_hand):
        super().__init__(timeout = None)

        self.poker_hand = poker_hand
        self.resending = False
        self.started = False

    @discord.ui.button(label = "Join", style = discord.ButtonStyle.green)
    async def join(self, interaction, button):
        if interaction.user in self.poker_hand.hands:
            return await interaction.response.send_message(
                "You've already joined", ephemeral = True
            )

        if self.started:
            return

        self.poker_hand.add_player(interaction.user)
        self.poker_hand.lines.append(f"{interaction.user.mention} has joined")
        self.poker_hand.embed.description = '\n'.join(self.poker_hand.lines)
        await interaction.response.edit_message(
            embed = self.poker_hand.embed, view = self
        )

    @discord.ui.button(label = "Start", style = discord.ButtonStyle.green)
    async def start(self, interaction, button):
        if not len(self.poker_hand.hands):
            return await interaction.response.send_message(
                "Nobody has joined yet", ephemeral = True
            )

        if len(self.poker_hand.hands) == 1:
            return await interaction.response.send_message(
                "Unfortunately, you can't play poker alone", ephemeral = True
            )
            # TODO: Allow playing against bot

        if self.started:
            return
        self.started = True

        self.poker_hand.lines.append(
            f"{interaction.user.mention} has started the match"
        )
        self.poker_hand.embed.description = '\n'.join(self.poker_hand.lines)
        await interaction.response.edit_message(
            embed = self.poker_hand.embed, view = None
        )

        await self.poker_hand.new_round()

        self.stop()

    @discord.ui.button(label = "Resend Message", style = discord.ButtonStyle.blurple)
    async def resend_message(self, interaction, button):
        if self.resending:
            return
        self.resending = True

        self.poker_hand.message = await interaction.channel.send(
            interaction.message.content,
            embed = self.poker_hand.embed,
            view = self
        )
        await self.poker_hand.bot.attempt_delete_message(interaction.message)

        self.resending = False


class PokerRound(discord.ui.View):

    def __init__(self, poker_hand, *, call):
        super().__init__(timeout = 20)

        self.bot = poker_hand.bot
        self.poker_hand = poker_hand
        self.resending = False

        if call:
            self.call.label = f"Call {call}"
        else:
            self.call.label = "Check"

        if self.poker_hand.current_bet:
            self.bet.label = "Raise"
        else:
            self.bet.label = "Bet"

    async def on_timeout(self):
        self.poker_hand.lines.append(
            f"{self.poker_hand.turn.mention} has folded"
        )
        await self.poker_hand.fold()

    @discord.ui.button(label = "Check Hand", style = discord.ButtonStyle.grey)
    async def check_hand(self, interaction, button):
        if interaction.user not in self.poker_hand.hands:
            return await interaction.response.send_message(
                "You're not in this match", ephemeral = True
            )

        await interaction.response.send_message(
            f"Your poker hand: {cards_to_string(self.poker_hand.hands[interaction.user].cards)}",
            ephemeral = True
        )

    @discord.ui.button(label = "Check / Call", style = discord.ButtonStyle.green)
    async def call(self, interaction, button):
        if interaction.user != self.poker_hand.turn:
            return await interaction.response.send_message(
                "It's not your turn", ephemeral = True
            )

        self.poker_hand.lines.append(
            f"{interaction.user.mention} has {button.label.split()[0].lower()}ed"
        )
        self.poker_hand.embed.description = '\n'.join(self.poker_hand.lines)
        await interaction.response.edit_message(embed = self.poker_hand.embed)

        self.stop()

        await self.poker_hand.call()

    @discord.ui.button(label = "Bet / Raise", style = discord.ButtonStyle.blurple)
    async def bet(self, interaction, button):
        if interaction.user != self.poker_hand.turn:
            return await interaction.response.send_message(
                "It's not your turn", ephemeral = True
            )

        self.poker_hand.embed.description = (
            '\n'.join(self.poker_hand.lines) + ('\n' if self.poker_hand.lines[-1] else "") +
            f"\n{interaction.user.mention}: How much would you like to {button.label.lower()}?"
        )
        await interaction.response.edit_message(embed = self.poker_hand.embed)

        try:
            message = await self.bot.wait_for(
                "message", check = self.bet_check, timeout = self.timeout
            )
        except asyncio.TimeoutError:
            return

        if self.is_finished():
            return

        amount = int(message.content)

        if not amount:
            if self.poker_hand.bets.get(interaction.user, 0) == self.poker_hand.current_bet:
                self.poker_hand.lines.append(f"{interaction.user.mention} has checked")
            else:
                self.poker_hand.lines.append(f"{interaction.user.mention} has called")
        else:
            self.poker_hand.lines.append(
                f"{interaction.user.mention} has raised {amount}; current bet: {self.poker_hand.current_bet + amount}"
            )
        self.poker_hand.embed.description = '\n'.join(self.poker_hand.lines)
        await self.poker_hand.message.edit(embed = self.poker_hand.embed)
        await self.bot.attempt_delete_message(message)

        self.stop()

        await self.poker_hand.bet(amount)

    def bet_check(self, message):
        if message.author != self.poker_hand.turn:
            return False
        try:
            return 10 ** 76 > int(message.content) >= 0
            # max of 80 characters for button - 5 for "Call "
        except ValueError:
            return False

    @discord.ui.button(label = "Fold", style = discord.ButtonStyle.red)
    async def fold(self, interaction, button):
        if interaction.user != self.poker_hand.turn:
            return await interaction.response.send_message(
                "It's not your turn", ephemeral = True
            )

        self.poker_hand.lines.append(f"{interaction.user.mention} has folded")
        self.poker_hand.embed.description = (
            '\n'.join(self.poker_hand.lines) +
            f"\n{interaction.user.mention}: Would you like to show your hand?"
        )
        view = PokerMuck(self.poker_hand, interaction.user)
        await interaction.response.edit_message(
            embed = self.poker_hand.embed, view = view
        )
        await view.wait()

        self.stop()

        await self.poker_hand.fold()

    @discord.ui.button(label = "Resend Message", style = discord.ButtonStyle.blurple)
    async def resend_message(self, interaction, button):
        if self.resending:
            return
        self.resending = True

        self.poker_hand.message = await interaction.channel.send(
            interaction.message.content,
            embed = self.poker_hand.embed,
            view = self
        )
        await self.poker_hand.bot.attempt_delete_message(interaction.message)

        self.resending = False


class PokerMuck(discord.ui.View):

    def __init__(self, poker_hand, user):
        super().__init__(timeout = 10)
        self.poker_hand = poker_hand
        self.user = user

    async def interaction_check(self, interaction):
        if not_user := interaction.user != self.user:
            await interaction.response.send_message(
                "You're not the one being asked whether or not to show your hand",
                ephemeral = True
            )

        return not not_user

    @discord.ui.button(label = "Yes", style = discord.ButtonStyle.green)
    async def yes(self, interaction, button):
        self.poker_hand.lines.append(
            f"{interaction.user.mention}'s hand was {cards_to_string(self.poker_hand.hands[interaction.user])}"
        )
        self.poker_hand.embed.description = '\n'.join(self.poker_hand.lines)
        await interaction.response.edit_message(
            embed = self.poker_hand.embed, view = None
        )

        self.stop()

    @discord.ui.button(label = "No", style = discord.ButtonStyle.red)
    async def no(self, interaction, button):
        self.poker_hand.embed.description = '\n'.join(self.poker_hand.lines)
        await interaction.response.edit_message(
            embed = self.poker_hand.embed, view = None
        )

        self.stop()

    async def on_timeout(self):
        self.poker_hand.embed.description = '\n'.join(self.poker_hand.lines)
        await self.poker_hand.message.edit(
            embed = self.poker_hand.embed, view = None
        )

        self.stop()

