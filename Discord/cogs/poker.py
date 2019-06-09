
from discord.ext import commands

import asyncio

import treys
import pydealer

from utilities import checks

def setup(bot):
	bot.add_cog(Poker(bot))

class Poker(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
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
		await ctx.send_help(ctx.command)
	
	@poker.command()
	async def start(self, ctx):
		if self.status not in (None, "started"):
			await ctx.embed_reply("There's already a round of poker in progress")
		elif self.status is None:
			self.status = "started"
			self.players = []
			self.hands = {}
			# reset other
			self.deck = pydealer.Deck()
			self.deck.shuffle()
			self.pot = 0
			await ctx.embed_say(f"{ctx.author.display_name} has started a round of poker\n`{ctx.prefix}poker join` to join\n`{1}poker start` again to start")
		else:
			self.status = "pre-flop"
			await ctx.embed_say(f"The poker round has started\nPlayers: {' '.join(player.mention for player in self.players)}")
			for player in self.players:
				cards_string = self.cards_to_string(self.hands[player.id].cards)
				await self.bot.send_embed(player, f"Your poker hand: {cards_string}")
			await self.betting(ctx)
			while self.status:
				await asyncio.sleep(1)
			await ctx.embed_say(f"The pot: {self.pot}")
			self.community_cards = self.deck.deal(3)
			await ctx.embed_say(f"The flop: {self.cards_to_string(self.community_cards)}")
			await self.betting(ctx)
			while self.status:
				await asyncio.sleep(1)
			await ctx.embed_say(f"The pot: {self.pot}")
			self.community_cards.add(self.deck.deal(1))
			await ctx.embed_say(f"The turn: {self.cards_to_string(self.community_cards)}")
			await self.betting(ctx)
			while self.status:
				await asyncio.sleep(1)
			await ctx.embed_say(f"The pot: {self.pot}")
			self.community_cards.add(self.deck.deal(1))
			await ctx.embed_say(f"The river: {self.cards_to_string(self.community_cards)}")
			await self.betting(ctx)
			while self.status:
				await asyncio.sleep(1)
			await ctx.embed_say(f"The pot: {self.pot}")
			
			evaluator = treys.Evaluator()
			board = []
			for card in self.community_cards.cards:
				abbreviation = pydealer.card.card_abbrev(card.value[0] if card.value != "10" else 'T', card.suit[0].lower())
				board.append(treys.Card.new(abbreviation))
			best_hand_value = 7462
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
			player = await self.bot.fetch_user(player)
			type = evaluator.class_to_string(evaluator.get_rank_class(best_hand_value))
			await ctx.embed_say(f"{player.mention} is the winner with a {type}")
	
	@poker.command()
	async def join(self, ctx):
		if self.status == "started":
			self.players.append(ctx.author)
			self.hands[ctx.author.id] = self.deck.deal(2)
			await ctx.embed_say(f"{ctx.author.display_name} has joined the poker match")
		elif self.status is None:
			await ctx.embed_reply(f"There's not currently a round of poker going on\nUse `{ctx.prefix}poker start` to start one")
		else:
			await ctx.embed_reply(":no_entry: The current round of poker already started")
	
	@poker.command(name = "raise")
	async def poker_raise(self, ctx, points : int):
		if self.turn and self.turn.id == ctx.author.id:
			if points > self.current_bet:
				self.bets[self.turn.id] = points
				self.current_bet = points
				await ctx.embed_reply(f"{ctx.author.display_name} has raised to {points}")
				self.turn = None
			elif points == self.current_bet:
				self.bets[self.turn.id] = points
				await ctx.embed_say(f"{ctx.author.display_name} has called")
				self.turn = None
			else:
				await ctx.embed_reply("The current bet is more than that")
		else:
			await ctx.embed_reply(":no_entry: You can't do that right now")
	
	@poker.command()
	async def call(self, ctx):
		if self.turn and self.turn.id == ctx.author.id:
			if self.current_bet == 0 or (self.turn.id in self.bets and self.bets[self.turn.id] == self.current_bet):
				await ctx.embed_reply("You can't call\nYou have checked instead")
				await ctx.embed_say(f"{ctx.author.display_name} has checked")
			else:
				self.bets[self.turn.id] = self.current_bet
				await ctx.embed_say(f"{ctx.author.display_name} has called")
			self.turn = None
		else:
			await ctx.embed_reply(":no_entry: You can't do that right now")
	
	@poker.command()
	async def check(self, ctx):
		if self.turn and self.turn.id == ctx.author.id:
			if self.current_bet != 0 and (self.turn.id not in self.bets or self.bets[self.turn.id] < self.current_bet):
				await ctx.embed_reply(":no_entry: You can't check")
			else:
				self.bets[self.turn.id] = self.current_bet
				await ctx.embed_say(f"{ctx.author.display_name} has checked")
				self.turn = None
		else:
			await ctx.embed_reply(":no_entry: You can't do that right now.")
	
	@poker.command()
	async def fold(self, ctx):
		if self.turn and self.turn.id == ctx.author.id:
			self.bets[self.turn.id] = -1
			self.folded.append(self.turn)
			self.turn = None
		else:
			await ctx.embed_reply(":no_entry: You can't do that right now")
	
	async def betting(self, ctx):
		self.status = "betting"
		self.current_bet = 0
		while True:
			for player in self.players:
				self.turn = player
				if player in self.folded:
					continue
				await ctx.embed_say("{}'s turn".format(player.mention))
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
		return "".join(":{}: {} ".format(card.suit.lower(), card.value) for card in cards)

