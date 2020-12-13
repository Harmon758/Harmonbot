
import discord
from discord.ext import commands

import pydealer
import treys

from utilities import checks

def setup(bot):
	bot.add_cog(Poker())

class Poker(commands.Cog):
	
	def __init__(self):
		self.poker_hands = {}
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def poker(self, ctx):
		'''WIP'''
		if not (poker_hand := self.poker_hands.get(ctx.channel.id)):
			self.poker_hands[ctx.channel.id] = PokerHand()
			await self.poker_hands[ctx.channel.id].initiate(ctx)
		elif poker_hand.started:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} There's already a poker match in progress here")
		elif ctx.author not in poker_hand.hands:
			await poker_hand.add_player(ctx)
		else:
			await poker_hand.start(ctx)
			del self.poker_hands[ctx.channel.id]

def cards_to_string(cards):
	return " | ".join(f":{card.suit.lower()}: {card.value}" for card in cards)

class PokerHand:
	
	# TODO: Handle folds
	
	def __init__(self):
		self.deck = pydealer.Deck()
		self.deck.shuffle()
		self.community_cards = self.deck.deal(3)
		self.folded = []
		self.pot = 0
		self.started = False
	
	async def initiate(self, ctx):
		self.hands = {ctx.author: self.deck.deal(2)}
		self.initial_message = await ctx.embed_reply(f"{ctx.author.mention} is initiating a poker match\n\n"
														f"`{ctx.prefix}poker` to join\n"
														f"`{ctx.prefix}poker` again to start", 
														author_name = discord.Embed.Empty)
	
	async def add_player(self, ctx):
		self.hands[ctx.author] = self.deck.deal(2)
		embed = self.initial_message.embeds[0]
		index = embed.description.find('\n\n') + 1
		embed.description = embed.description[:index] + f"{ctx.author.mention} has joined\n" + embed.description[index:]
		await self.initial_message.edit(embed = embed)
		await ctx.bot.attempt_delete_message(ctx.message)
	
	async def start(self, ctx):
		self.started = True

		embed = self.initial_message.embeds[0]
		index = embed.description.find('\n\n') + 1
		embed.description = embed.description[:index] + f"{ctx.author.mention} has started the match"
		await self.initial_message.edit(embed = embed)
		await ctx.bot.attempt_delete_message(ctx.message)

		for player, hand in self.hands.items():
			await ctx.bot.send_embed(player, f"Your poker hand: {cards_to_string(hand.cards)}")
		
		await self.betting(ctx)
		round_message = await ctx.embed_send(f"The pot: {self.pot}\n"
												f"The flop: {cards_to_string(self.community_cards)}")
		await self.betting(ctx, round_message)
		self.community_cards.add(self.deck.deal(1))
		round_message = await ctx.embed_send(f"The pot: {self.pot}\n"
												f"The turn: {cards_to_string(self.community_cards)}")
		await self.betting(ctx, round_message)
		self.community_cards.add(self.deck.deal(1))
		round_message = await ctx.embed_send(f"The pot: {self.pot}\n"
												f"The river: {cards_to_string(self.community_cards)}")
		await self.betting(ctx, round_message)
		final_message = await ctx.embed_send(f"The pot: {self.pot}")
		
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
		
		hand_name = evaluator.class_to_string(evaluator.get_rank_class(best_hand_value))
		embed = final_message.embeds[0]
		embed.description = f"{best_player.mention} is the winner of {self.pot} with a {hand_name}"
		await final_message.edit(embed = embed)
	
	async def betting(self, ctx, message = None):
		bets = {}
		current_bet = 0
		while True:
			for player in self.hands:
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
				turn_message = (f"{player.mention}'s turn\n"
								"Respond with `call`, `check`, `fold`, or `raise ` and the amount")
				if not message:
					initial_embed = discord.Embed(color = ctx.bot.bot_color)
					initial_embed.description = ""
					message = await ctx.embed_send(turn_message)
					embed = message.embeds[0]
				else:
					embed = message.embeds[0]
					initial_embed = embed.copy()
					embed.description += '\n' + turn_message
					await message.edit(embed = embed)
				while True:
					response = await ctx.bot.wait_for("message", check = check)
					if response.content.lower() == "call":
						if current_bet == 0 or (player.id in bets and bets[player.id] == current_bet):
							initial_embed.description += (f"\n{player.mention} attempted to call\n"
															f"Since there's nothing to call, {player.mention} has checked instead")
						else:
							initial_embed.description += f"\n{player.mention} has called"
						bets[player.id] = current_bet
					elif response.content.lower() == "check":
						if current_bet != 0 and (player.id not in bets or bets[player.id] < current_bet):
							embed_copy = embed.copy()
							embed_copy.description += f"\n{player.mention} attempted to check, but there is a bet to call"
							await message.edit(embed = embed_copy)
							await ctx.bot.attempt_delete_message(response)
							continue
						bets[player.id] = current_bet
						initial_embed.description += f"\n{player.mention} has checked"
					elif response.content.lower() == "fold":
						bets[player.id] = -1
						self.folded.append(player)
						initial_embed.description += f"\n{player.mention} has folded"
					elif response.content.lower().startswith("raise "):
						amount = int(response.content[6:])  # Use .removeprefix in Python 3.9
						if amount < current_bet:
							embed_copy = embed.copy()
							embed_copy.description += f"\n{player.mention} attempted to raise to {amount}, but the current bet is more than that"
							await message.edit(embed = embed_copy)
							await ctx.bot.attempt_delete_message(response)
							continue
						bets[player.id] = amount
						if amount > current_bet:
							current_bet = amount
							initial_embed.description += f"\n{player.mention} has raised to {amount}"
						else:
							initial_embed.description += f"\n{player.mention} has called"
					await message.edit(embed = initial_embed)
					await ctx.bot.attempt_delete_message(response)
					break
			if all([bet == -1 or bet == current_bet for bet in bets.values()]):
				break
		for bet in bets.values():
			if bet != -1:
				self.pot += bet

