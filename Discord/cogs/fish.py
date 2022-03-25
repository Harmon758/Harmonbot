
import discord
from discord.ext import commands

import asyncio
import math

import pydealer

from utilities import checks


async def setup(bot):
    await bot.add_cog(Fish())

def card_value(card):
    try:
        return int(card.value)
    except ValueError:
        # Use pattern matching in Python 3.10
        if card.value == "Ace":
            return 1
        elif card.value == "Jack":
            return 11
        elif card.value == "Queen":
            return 12
        elif card.value == "King":
            return 13

def cards_to_string(cards):
    return " | ".join(
        f":{card.suit.lower()}: {card_value(card)}" for card in cards
    )


class Fish(commands.Cog):

    def __init__(self):
        self.matches = {}

    @commands.command(aliases = ["gofish", "go_fish"])
    @checks.not_forbidden()
    async def fish(self, ctx):
        '''Go Fish'''
        if match := self.matches.get(ctx.channel.id):
            return await ctx.embed_reply(
                f"[There's already a Go Fish match in progress here]({match.message.jump_url})"
            )

        self.matches[ctx.channel.id] = GoFishMatch()
        await self.matches[ctx.channel.id].initiate(ctx)
        del self.matches[ctx.channel.id]


class GoFishMatch:

    def __init__(self):
        self.deck = pydealer.Deck()
        self.deck.shuffle()
        self.hands = {}
        self.players = {}
        self.turn = None  # who's turn it is

        self.lines = []  # embed lines

        self.ended = asyncio.Event()

    async def initiate(self, ctx):
        self.bot = ctx.bot
        self.lines = [f"{ctx.author.mention} is initiating a Go Fish match"]
        self.message = await ctx.embed_reply(
            self.lines[0],
            title = '\N{FISH}',
            author_name = discord.Embed.Empty,
            footer_text = discord.Embed.Empty,
            view = GoFishLobby(self)
        )
        self.embed = self.message.embeds[0]
        await self.ended.wait()

    def add_player(self, player):
        self.players[player] = 0

    async def start(self):
        for player in self.players:
            if len(self.players) < 4:
                self.hands[player] = self.deck.deal(7)
            else:
                self.hands[player] = self.deck.deal(5)

        await self.next_turn(next_player = True)

        await self.ended.wait()

        self.lines.pop(-3)  # Remove new line
        self.lines.pop(-2)  # Remove turn line
        self.lines.append("")
        self.lines.append(
            ', '.join(
                f"{player.mention}: {books}"
                for player, books in self.players.items()
            )
        )
        self.embed.description = '\n'.join(self.lines)
        await self.message.edit(embed = self.embed, view = None)

    async def next_turn(self, *, next_player = False):
        if next_player:
            players = list(self.players)
            if self.turn is None or self.turn == players[-1]:
                self.turn = players[0]
            else:
                self.turn = players[players.index(self.turn) + 1]

        if self.hands[self.turn].size:
            self.embed.description = (
                '\n'.join(self.lines) + ('\n' if self.lines[-1] else "") +
                f"\n{self.turn.mention}'s turn: What player would you like to ask for what number?"
            )
        elif not self.deck.size:
            if not any(hand.size for hand in self.hands.values()):
                self.ended.set()
                return
            await self.next_turn(next_player = True)
        else:
            self.hands[self.turn].add(self.deck.deal().cards[0])
            self.embed.description = (
                '\n'.join(self.lines) + ('\n' if self.lines[-1] else "") +
                f"\n{self.turn.mention} was out of cards and drew a card" +
                f"\n{self.turn.mention}'s turn: What player would you like to ask for what number?"
            )
        await self.message.edit(embed = self.embed, view = GoFishTurn(self))

    async def ask(self, asking, target, number):
        if not self.lines[-1]:
            self.lines.append("")

        elif "got all four" in self.lines[-1]:
            if self.lines.count("") > 1:
                self.lines.pop(-3)  # Remove new line
            self.lines.append("")
            self.lines.append(self.lines.pop(-3))  # Move turn line

        cards = {card_value(card): card for card in self.hands[target]}

        if number in cards:
            cards = self.hands[target].get(cards[number].value)
            self.hands[asking].add(cards)

            self.lines[-1] = (
                f"{asking.mention} asked {target.mention} for {number}s: "
                f"{target.mention} had {self.bot.inflect_engine.number_to_words(len(cards))} {number}"
            )
            if len(cards) > 1:
                self.lines[-1] += "s"

            if len(self.hands[asking].find(cards[0].value)) == 4:
                self.hands[asking].get(cards[0].value)
                self.players[asking] += 1
                self.lines.append(f"{asking.mention} got all four {number}s")

            self.embed.description = '\n'.join(self.lines)
            await self.message.edit(embed = self.embed)

        else:
            card = self.deck.deal().cards[0]
            self.hands[asking].add(card)

            self.lines[-1] = f"{asking.mention} asked {target.mention} for {number}s: Go Fish! "
            if card_value(card) == number:
                self.lines[-1] += f"{asking.mention} drew :{card.suit.lower()}: {card_value(card)} and gets to go again"
            else:
                self.lines[-1] += f"{asking.mention} drew a card"

            if len(self.hands[asking].find(card.value)) == 4:
                self.hands[asking].get(card.value)
                self.players[asking] += 1
                self.lines.append(f"{asking.mention} got all four {card_value(card)}s")

            self.embed.description = '\n'.join(self.lines)
            await self.message.edit(embed = self.embed)

            if card_value(card) != number:
                await self.next_turn(next_player = True)

        await self.next_turn()


class GoFishLobby(discord.ui.View):

    def __init__(self, match):
        super().__init__(timeout = None)
        self.match = match
        self.started = False
        self.resending = False

    @discord.ui.button(label = "Join", style = discord.ButtonStyle.green)
    async def join(self, button, interaction):
        if interaction.user in self.match.players:
            return await interaction.response.send_message(
                "You've already joined", ephemeral = True
            )

        if len(self.match.players) == 5:
            return await interaction.response.send_message(
                "Only up to five players can join a Go Fish match",
                ephemeral = True
            )

        if self.started:
            return

        self.match.add_player(interaction.user)

        self.match.lines.append(f"{interaction.user.mention} has joined")
        self.match.embed.description = '\n'.join(self.match.lines)
        await interaction.response.edit_message(
            embed = self.match.embed, view = self
        )

    @discord.ui.button(label = "Start", style = discord.ButtonStyle.green)
    async def start(self, button, interaction):
        if not len(self.match.players):
            return await interaction.response.send_message(
                "Nobody has joined yet", ephemeral = True
            )

        if len(self.match.players) == 1:
            return await interaction.response.send_message(
                "Unfortunately, you can't play Go Fish alone", ephemeral = True
            )
            # TODO: Allow playing against bot

        if self.started:
            return
        self.started = True

        self.match.lines.append(
            f"{interaction.user.mention} has started the match"
        )
        self.match.embed.description = '\n'.join(self.match.lines)
        await interaction.response.edit_message(
            embed = self.match.embed, view = None
        )

        self.match.lines.append("")

        await self.match.start()

        self.stop()

    @discord.ui.button(label = "Resend Message", style = discord.ButtonStyle.blurple)
    async def resend_message(self, button, interaction):
        if self.resending:
            return
        self.resending = True

        self.match.message = await interaction.channel.send(
            interaction.message.content,
            embed = self.match.embed,
            view = self
        )
        await self.match.bot.attempt_delete_message(interaction.message)

        self.resending = False


class GoFishPlayerButton(discord.ui.Button):

    def __init__(self, player):
        super().__init__(
            style = discord.ButtonStyle.green,
            label = str(player),
            row = 1
        )
        self.player = player

    async def callback(self, interaction):
        if interaction.user != self.view.match.turn:
            return await interaction.response.send_message(
                "It's not your turn", ephemeral = True
            )

        if interaction.user == self.player:
            return await interaction.response.send_message(
                "You can't ask yourself for numbers", ephemeral = True
            )

        self.view.player = self.player

        if self.view.number:
            await self.view.match.ask(
                interaction.user, self.view.player, self.view.number
            )
            self.view.stop()

        else:
            self.view.match.embed.description = (
                '\n'.join(self.view.match.lines) + ('\n' if self.view.match.lines[-1] else "") +
                f"\n{interaction.user.mention}'s turn: What number would you like to ask {self.player.mention} for?"
            )
            await interaction.response.edit_message(
                embed = self.view.match.embed
            )


class GoFishNumberButton(discord.ui.Button):

    def __init__(self, number):
        super().__init__(
            style = discord.ButtonStyle.grey,
            label = number,
            row = math.ceil(number / 5) + 1
        )
        self.number = number

    async def callback(self, interaction):
        if interaction.user != self.view.match.turn:
            return await interaction.response.send_message(
                "It's not your turn", ephemeral = True
            )

        if self.number not in [
            card_value(card)
            for card in self.view.match.hands[interaction.user].cards
        ]:
            return await interaction.response.send_message(
                f"You don't have any {self.number}s", ephemeral = True
            )

        self.view.number = self.number

        if self.view.player:
            await self.view.match.ask(
                interaction.user, self.view.player, self.view.number
            )
            self.view.stop()

        else:
            self.view.match.embed.description = (
                '\n'.join(self.view.match.lines) + ('\n' if self.view.match.lines[-1] else "") +
                f"\n{interaction.user.mention}'s turn: Who would you like to ask for that number?"
            )
            await interaction.response.edit_message(
                embed = self.view.match.embed
            )


class GoFishTurn(discord.ui.View):

    def __init__(self, match):
        super().__init__(timeout = None)

        self.match = match
        self.number = None
        self.player = None
        self.resending = False

        for player in self.match.players:
            self.add_item(GoFishPlayerButton(player))

        for number in range(1, 14):
            self.add_item(GoFishNumberButton(number))

    @discord.ui.button(label = "Check Hand", style = discord.ButtonStyle.grey)
    async def check_hand(self, button, interaction):
        if interaction.user not in self.match.players:
            return await interaction.response.send_message(
                "You're not in this match", ephemeral = True
            )

        await interaction.response.send_message(
            f"Your hand: {cards_to_string(sorted(self.match.hands[interaction.user].cards, key = card_value))}",
            ephemeral = True
        )

    @discord.ui.button(label = "Resend Message", style = discord.ButtonStyle.blurple)
    async def resend_message(self, button, interaction):
        if self.resending:
            return
        self.resending = True

        self.match.message = await interaction.channel.send(
            interaction.message.content,
            embed = self.match.embed,
            view = self
        )
        await self.match.bot.attempt_delete_message(interaction.message)

        self.resending = False

