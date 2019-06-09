
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
		self.poker_status, self.poker_players, self.poker_deck, self.poker_hands, self.poker_turn, self.poker_bets, self.poker_current_bet, self.poker_pot, self.poker_community_cards, self.poker_folded = None, [], None, {}, None, {}, None, None, None, []
		# check default values
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def poker(self, ctx):
		'''WIP'''
		await ctx.send_help(ctx.command)
	
	@poker.command(name = "start")
	async def poker_start(self, ctx):
		if self.poker_status not in (None, "started"):
			await ctx.embed_reply("There's already a round of poker in progress")
		elif self.poker_status is None:
			self.poker_status = "started"
			self.poker_players = []
			self.poker_hands = {}
			# reset other
			self.poker_deck = pydealer.Deck()
			self.poker_deck.shuffle()
			self.poker_pot = 0
			await ctx.embed_say("{0} has started a round of poker\n`{1}poker join` to join\n`{1}poker start` again to start".format(ctx.author.display_name, ctx.prefix))
		else:
			self.poker_status = "pre-flop"
			await ctx.embed_say("The poker round has started\nPlayers: {}".format(" ".join([player.mention for player in self.poker_players])))
			for player in self.poker_players:
				cards_string = self.cards_to_string(self.poker_hands[player.id].cards)
				await self.bot.send_embed(player, "Your poker hand: {}".format(cards_string))
			await self.poker_betting(ctx)
			while self.poker_status:
				await asyncio.sleep(1)
			await ctx.embed_say("The pot: {}".format(self.poker_pot))
			self.poker_community_cards = self.poker_deck.deal(3)
			await ctx.embed_say("The flop: {}".format(self.cards_to_string(self.poker_community_cards)))
			await self.poker_betting(ctx)
			while self.poker_status:
				await asyncio.sleep(1)
			await ctx.embed_say("The pot: {}".format(self.poker_pot))
			self.poker_community_cards.add(self.poker_deck.deal(1))
			await ctx.embed_say("The turn: {}".format(self.cards_to_string(self.poker_community_cards)))
			await self.poker_betting(ctx)
			while self.poker_status:
				await asyncio.sleep(1)
			await ctx.embed_say("The pot: {}".format(self.poker_pot))
			self.poker_community_cards.add(self.poker_deck.deal(1))
			await ctx.embed_say("The river: {}".format(self.cards_to_string(self.poker_community_cards)))
			await self.poker_betting(ctx)
			while self.poker_status:
				await asyncio.sleep(1)
			await ctx.embed_say("The pot: {}".format(self.poker_pot))
			
			evaluator = treys.Evaluator()
			board = []
			for card in self.poker_community_cards.cards:
				abbreviation = pydealer.card.card_abbrev(card.value[0] if card.value != "10" else 'T', card.suit[0].lower())
				board.append(treys.Card.new(abbreviation))
			best_hand_value = 7462
			best_player = None
			for player, hand in self.poker_hands.items():
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
			await ctx.embed_say("{} is the winner with a {}".format(player.mention, type))
	
	@poker.command(name = "join")
	async def poker_join(self, ctx):
		if self.poker_status == "started":
			self.poker_players.append(ctx.author)
			self.poker_hands[ctx.author.id] = self.poker_deck.deal(2)
			await ctx.embed_say("{} has joined the poker match".format(ctx.author.display_name))
		elif self.poker_status is None:
			await ctx.embed_reply("There's not currently a round of poker going on\nUse `{}poker start` to start one".format(ctx.prefix))
		else:
			await ctx.embed_reply(":no_entry: The current round of poker already started")
	
	@poker.command(name = "raise")
	async def poker_raise(self, ctx, points : int):
		if self.poker_turn and self.poker_turn.id == ctx.author.id:
			if points > self.poker_current_bet:
				self.poker_bets[self.poker_turn.id] = points
				self.poker_current_bet = points
				await ctx.embed_reply("{} has raised to {}".format(ctx.author.display_name, points))
				self.poker_turn = None
			elif points == self.poker_current_bet:
				self.poker_bets[self.poker_turn.id] = points
				await ctx.embed_say("{} has called".format(ctx.author.display_name))
				self.poker_turn = None
			else:
				await ctx.embed_reply("The current bet is more than that")
		else:
			await ctx.embed_reply(":no_entry: You can't do that right now")
	
	@poker.command(name = "call")
	async def poker_call(self, ctx):
		if self.poker_turn and self.poker_turn.id == ctx.author.id:
			if self.poker_current_bet == 0 or (self.poker_turn.id in self.poker_bets and self.poker_bets[self.poker_turn.id] == self.poker_current_bet):
				await ctx.embed_reply("You can't call\nYou have checked instead")
				await ctx.embed_say("{} has checked".format(ctx.author.display_name))
			else:
				self.poker_bets[self.poker_turn.id] = self.poker_current_bet
				await ctx.embed_say("{} has called".format(ctx.author.display_name))
			self.poker_turn = None
		else:
			await ctx.embed_reply(":no_entry: You can't do that right now")
	
	@poker.command(name = "check")
	async def poker_check(self, ctx):
		if self.poker_turn and self.poker_turn.id == ctx.author.id:
			if self.poker_current_bet != 0 and (self.poker_turn.id not in self.poker_bets or self.poker_bets[self.poker_turn.id] < self.poker_current_bet):
				await ctx.embed_reply(":no_entry: You can't check")
			else:
				self.poker_bets[self.poker_turn.id] = self.poker_current_bet
				await ctx.embed_say("{} has checked".format(ctx.author.display_name))
				self.poker_turn = None
		else:
			await ctx.embed_reply(":no_entry: You can't do that right now.")
	
	@poker.command(name = "fold")
	async def poker_fold(self, ctx):
		if self.poker_turn and self.poker_turn.id == ctx.author.id:
			self.poker_bets[self.poker_turn.id] = -1
			self.poker_folded.append(self.poker_turn)
			self.poker_turn = None
		else:
			await ctx.embed_reply(":no_entry: You can't do that right now")
	
	async def poker_betting(self, ctx):
		self.poker_status = "betting"
		self.poker_current_bet = 0
		while True:
			for player in self.poker_players:
				self.poker_turn = player
				if player in self.poker_folded:
					continue
				await ctx.embed_say("{}'s turn".format(player.mention))
				while self.poker_turn:
					await asyncio.sleep(1)
			if all([bet == -1 or bet == self.poker_current_bet for bet in self.poker_bets.values()]):
				break
		for bet in self.poker_bets.values():
			if bet != -1:
				self.poker_pot += bet
		self.poker_status = None
	
	# Utility Functions
	
	def cards_to_string(self, cards):
		return "".join(":{}: {} ".format(card.suit.lower(), card.value) for card in cards)

