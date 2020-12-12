
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
			self.folded = []
			# reset other
			self.deck = pydealer.Deck()
			self.deck.shuffle()
			self.pot = 0

			self.players = [ctx.author]
			self.hands = {ctx.author.id: self.deck.deal(2)}
			self.initial_message = await ctx.embed_reply(f"{ctx.author.mention} is starting a poker match\n\n"
															f"`{ctx.prefix}poker` to join\n"
															f"`{ctx.prefix}poker` again to start", 
															author_name = discord.Embed.Empty)
			return
		
		if self.status != "started":
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} There's already a poker match in progress")
		
		if ctx.author not in self.players:
			self.players.append(ctx.author)
			self.hands[ctx.author.id] = self.deck.deal(2)
			embed = self.initial_message.embeds[0]
			index = embed.description.find('\n\n') + 1
			embed.description = embed.description[:index] + f"{ctx.author.mention} has joined\n" + embed.description[index:]
			await self.initial_message.edit(embed = embed)
			return await ctx.bot.attempt_delete_message(ctx.message)
		
		self.status = "pre-flop"
		embed = self.initial_message.embeds[0]
		index = embed.description.find('\n\n') + 1
		embed.description = embed.description[:index] + f"{ctx.author.mention} has started the match"
		await self.initial_message.edit(embed = embed)
		await ctx.bot.attempt_delete_message(ctx.message)
		for player in self.players:
			await ctx.bot.send_embed(player, f"Your poker hand: {self.cards_to_string(self.hands[player.id].cards)}")
		
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
	
	async def betting(self, ctx):
		self.status = "betting"
		self.current_bet = 0
		while True:
			for player in self.players:
				if player in self.folded:
					continue
				def check(message):
					if message.author != player:
						return False
					if message.content.lower() in ("call", "check", "fold"):
						return True
					if message.content.lower().startswith("raise "):
						try:
							int(message.content[6:])  # Use .removeprefix in Python 3.9
							return True
						except ValueError:
							return False
					return False
				await ctx.embed_send(f"{player.mention}'s turn")
				while True:
					response = await ctx.bot.wait_for("message", check = check)
					response_ctx = await ctx.bot.get_context(response)
					if response.content.lower() == "call":
						if self.current_bet == 0 or (player.id in self.bets and self.bets[player.id] == self.current_bet):
							await response_ctx.embed_reply("You can't call\nYou have checked instead")
							await response_ctx.embed_reply("has checked")
						else:
							self.bets[player.id] = self.current_bet
							await response_ctx.embed_reply("has called")
						break
					if response.content.lower() == "check":
						if self.current_bet != 0 and (player.id not in self.bets or self.bets[player.id] < self.current_bet):
							await response_ctx.embed_reply(f"{ctx.bot.error_emoji} You can't check")
							continue
						self.bets[player.id] = self.current_bet
						await response_ctx.embed_reply("has checked")
						break
					if response.content.lower() == "fold":
						self.bets[player.id] = -1
						self.folded.append(player)
						await response_ctx.embed_reply("has folded")
						break
					if response.content.lower().startswith("raise "):
						amount = int(response.content[6:])  # Use .removeprefix in Python 3.9
						if amount < self.current_bet:
							await response_ctx.embed_reply("The current bet is more than that")
							continue
						self.bets[player.id] = amount
						if amount > self.current_bet:
							self.current_bet = amount
							await response_ctx.embed_reply(f"{response_ctx.author.display_name} has raised to {amount}")
						else:
							await response_ctx.embed_reply("has called")
						break
			if all([bet == -1 or bet == self.current_bet for bet in self.bets.values()]):
				break
		for bet in self.bets.values():
			if bet != -1:
				self.pot += bet
		self.status = None
	
	# Utility Functions
	
	def cards_to_string(self, cards):
		return "".join(f":{card.suit.lower()}: {card.value} " for card in cards)

