
import discord
from discord.ext import commands

import asyncio

import pydealer
import treys

from utilities import checks

def setup(bot):
	bot.add_cog(Poker())

class Poker(commands.Cog):
	
	def __init__(self):
		self.status = None
		self.players = []
		self.deck = None
		self.hands = {}
		self.turn = None
		self.bets = {}
		self.current_bet = None
		self.pot = None
		self.community_cards = None
		self.folded = []
		# check default values
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def poker(self, ctx):
		'''WIP'''
		# TODO: Handle folds
		if self.status is None:
			self.status = "started"
			self.players = []
			self.hands = {}
			self.folded = []
			# reset other
			self.deck = pydealer.Deck()
			self.deck.shuffle()
			self.pot = 0
			return await ctx.embed_reply(f"{ctx.author.mention} has started a round of poker\n"
											f"`{ctx.prefix}poker` to join\n"
											f"`{ctx.prefix}poker` again to start", 
											author_name = discord.Embed.Empty)
		if self.status != "started":
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} There's already a round of poker in progress")
		if ctx.author not in self.players:
			self.players.append(ctx.author)
			self.hands[ctx.author.id] = self.deck.deal(2)
			return await ctx.embed_reply("has joined the poker match")
		
		self.status = "pre-flop"
		await ctx.embed_reply("The poker round has started\n"
								f"Players: {' '.join(player.mention for player in self.players)}")
		for player in self.players:
			cards_string = self.cards_to_string(self.hands[player.id].cards)
			await ctx.bot.send_embed(player, f"Your poker hand: {cards_string}")
		await self.betting(ctx)
		self.community_cards = self.deck.deal(3)
		await ctx.embed_send(f"The pot: {self.pot}\n"
								f"The flop: {self.cards_to_string(self.community_cards)}")
		await self.betting(ctx)
		self.community_cards.add(self.deck.deal(1))
		await ctx.embed_send(f"The pot: {self.pot}\n"
								f"The turn: {self.cards_to_string(self.community_cards)}")
		await self.betting(ctx)
		self.community_cards.add(self.deck.deal(1))
		await ctx.embed_send(f"The pot: {self.pot}\n"
								f"The river: {self.cards_to_string(self.community_cards)}")
		await self.betting(ctx)
		await ctx.embed_send(f"The pot: {self.pot}")
		
		evaluator = treys.Evaluator()
		board = []
		for card in self.community_cards.cards:
			abbreviation = pydealer.card.card_abbrev(card.value[0] if card.value != "10" else 'T', card.suit[0].lower())
			board.append(treys.Card.new(abbreviation))
		best_hand_value = evaluator.table.MAX_HIGH_CARD
		best_player = None
		for player, hand in self.hands.items():
			hand_stack = []
			for card in hand:
				abbreviation = pydealer.card.card_abbrev(card.value[0] if card.value != "10" else 'T', card.suit[0].lower())
				hand_stack.append(treys.Card.new(abbreviation))
			value = evaluator.evaluate(board, hand_stack)
			if value < best_hand_value:
				best_hand_value = value
				best_player = player
		player = await ctx.bot.fetch_user(best_player)
		hand_name = evaluator.class_to_string(evaluator.get_rank_class(best_hand_value))
		await ctx.embed_send(f"{player.mention} is the winner with a {hand_name}")
	
	@poker.command(name = "raise")
	async def poker_raise(self, ctx, points: int):
		if not self.turn or self.turn.id == ctx.author.id:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} You can't do that right now")
		if points < self.current_bet:
			return await ctx.embed_reply("The current bet is more than that")
		self.bets[self.turn.id] = points
		if points > self.current_bet:
			self.current_bet = points
			await ctx.embed_reply(f"{ctx.author.display_name} has raised to {points}")
		else:
			await ctx.embed_reply("has called")
		self.turn = None
	
	@poker.command()
	async def call(self, ctx):
		if not self.turn or self.turn.id != ctx.author.id:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} You can't do that right now")
		if self.current_bet == 0 or (self.turn.id in self.bets and self.bets[self.turn.id] == self.current_bet):
			await ctx.embed_reply("You can't call\nYou have checked instead")
			await ctx.embed_reply("has checked")
		else:
			self.bets[self.turn.id] = self.current_bet
			await ctx.embed_reply("has called")
		self.turn = None
	
	@poker.command()
	async def check(self, ctx):
		if not self.turn or self.turn.id != ctx.author.id:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} You can't do that right now")
		if self.current_bet != 0 and (self.turn.id not in self.bets or self.bets[self.turn.id] < self.current_bet):
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} You can't check")
		self.bets[self.turn.id] = self.current_bet
		await ctx.embed_reply("has checked")
		self.turn = None
	
	@poker.command()
	async def fold(self, ctx):
		if not self.turn or self.turn.id != ctx.author.id:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} You can't do that right now")
		self.bets[self.turn.id] = -1
		self.folded.append(self.turn)
		await ctx.embed_reply("has folded")
		self.turn = None
	
	async def betting(self, ctx):
		self.status = "betting"
		self.current_bet = 0
		while True:
			for player in self.players:
				self.turn = player
				if player in self.folded:
					continue
				await ctx.embed_send(f"{player.mention}'s turn")
				while self.turn:
					await asyncio.sleep(1)
			if all([bet == -1 or bet == self.current_bet for bet in self.bets.values()]):
				break
		for bet in self.bets.values():
			if bet != -1:
				self.pot += bet
		self.status = None
	
	# Utility Functions
	
	def cards_to_string(self, cards):
		return "".join(f":{card.suit.lower()}: {card.value} " for card in cards)

