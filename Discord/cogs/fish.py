
import discord
from discord.ext import commands

import asyncio

import pydealer

from utilities import checks


def setup(bot):
    bot.add_cog(Fish())

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

def remove_mention(message):
    mention = message.mentions[0].mention
    content = message.content.replace(mention, "")
    if '!' in mention:
        content = content.replace(mention.replace('!', ""), "")
    else:
        content = content.replace(mention.replace('@', "@!"), "")
    return content.strip()


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

        await self.message.edit(view = GoFishTurn(self))

        while self.deck.size or any(hand.size for hand in self.hands.values()):
            for player in self.players:
                self.turn = player
                while True:
                    if self.hands[player].size:
                        self.embed.description = (
                            '\n'.join(self.lines) + ('\n' if self.lines[-1] else "") +
                            f"\n{player.mention}'s turn: mention another player with the number to ask them for"
                        )
                    elif not self.deck.size:
                        break
                    else:
                        self.hands[player].add(self.deck.deal().cards[0])
                        self.embed.description = (
                            '\n'.join(self.lines) + ('\n' if self.lines[-1] else "") +
                            f"\n{player.mention} was out of cards and drew a card" +
                            f"\n{player.mention}'s turn: mention another player with the number to ask them for"
                        )
                    await self.message.edit(embed = self.embed)

                    message = await self.bot.wait_for("message", check = self.check)
                    number = int(remove_mention(message))
                    cards = {card_value(card): card for card in self.hands[message.mentions[0]]}

                    if not self.lines[-1]:
                        self.lines.append("")

                    elif "got all four" in self.lines[-1]:
                        if self.lines.count("") > 1:
                            self.lines.pop(-3)  # Remove new line
                        self.lines.append("")
                        self.lines.append(self.lines.pop(-3))  # Move turn line

                    if number in cards:
                        cards = self.hands[message.mentions[0]].get(cards[number].value)
                        self.hands[player].add(cards)

                        self.lines[-1] = (
                            f"{player.mention} asked {message.mentions[0].mention} for {number}s: "
                            f"{message.mentions[0].mention} had {self.bot.inflect_engine.number_to_words(len(cards))} {number}"
                        )
                        if len(cards) > 1:
                            self.lines[-1] += "s"

                        if len(self.hands[player].find(cards[0].value)) == 4:
                            self.hands[player].get(cards[0].value)
                            self.players[player] += 1
                            self.lines.append(f"{player.mention} got all four {number}s")

                        self.embed.description = '\n'.join(self.lines)
                        await self.message.edit(embed = self.embed)
                        await self.bot.attempt_delete_message(message)

                    else:
                        card = self.deck.deal().cards[0]
                        self.hands[player].add(card)

                        self.lines[-1] = f"{player.mention} asked {message.mentions[0].mention} for {number}s: Go Fish! "
                        if card_value(card) == number:
                            self.lines[-1] += f"{player.mention} drew :{card.suit.lower()}: {card_value(card)} and gets to go again"
                        else:
                            self.lines[-1] += f"{player.mention} drew a card"

                        if len(self.hands[player].find(card.value)) == 4:
                            self.hands[player].get(card.value)
                            self.players[player] += 1
                            self.lines.append(f"{player.mention} got all four {card_value(card)}s")

                        self.embed.description = '\n'.join(self.lines)
                        await self.message.edit(embed = self.embed)
                        await self.bot.attempt_delete_message(message)

                        if card_value(card) != number:
                            break

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

        self.ended.set()

    def check(self, message):
        if message.author != self.turn:
            return False
        if len(message.mentions) != 1:
            return False
        if message.mentions[0] == message.author:
            return False
        if message.mentions[0] not in self.players:
            return False
        try:
            return int(remove_mention(message)) in [card_value(card) for card in self.hands[message.author].cards]
        except ValueError:
            return False

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

        for child in self.children:
            child.disabled = True
        self.stop()

    @discord.ui.button(label = "Resend Message", style = discord.ButtonStyle.blurple)
    async def resend_message(self, button, interaction):
        if self.resending:
            return
        self.resending = True

        self.match.message = await interaction.channel.send(
            interaction.message.content, embed = self.match.embed, view = self
        )
        await self.match.bot.attempt_delete_message(interaction.message)

        self.resending = False


class GoFishTurn(discord.ui.View):

    def __init__(self, match):
        super().__init__(timeout = None)

        self.match = match
        self.resending = False

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
            interaction.message.content, embed = self.match.embed, view = self
        )
        await self.match.bot.attempt_delete_message(interaction.message)

        self.resending = False

