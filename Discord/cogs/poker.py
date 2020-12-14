
import discord
from discord.ext import commands

import asyncio
import contextlib

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
		'''Texas hold'em'''
		if not (poker_hand := self.poker_hands.get(ctx.channel.id)):
			self.poker_hands[ctx.channel.id] = PokerHand()
			await self.poker_hands[ctx.channel.id].initiate(ctx)
		elif poker_hand.started:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} There's already a poker match in progress here")
		elif ctx.author not in poker_hand.hands:
			await poker_hand.add_player(ctx)
		elif len(poker_hand.hands) == 1:
			await ctx.embed_reply("Unfortunately, you can't play poker alone")
			# TODO: Allow playing against bot
		else:
			await poker_hand.start(ctx)
			del self.poker_hands[ctx.channel.id]

def cards_to_string(cards):
	return " | ".join(f":{card.suit.lower()}: {card.value}" for card in cards)

class PokerHand:
	
	def __init__(self):
		self.deck = pydealer.Deck()
		self.deck.shuffle()
		self.community_cards = self.deck.deal(5)
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
		
		round_message = None
		for stage, number_of_cards in zip(("flop", "turn", "river", "showdown"), (3, 4, 5, 5)):
			await self.betting(ctx, round_message)
			if len(self.hands) == 1:
				return await ctx.embed_send(f"{next(iter(self.hands.keys())).mention} is the winner of {self.pot}")
			round_message = await ctx.embed_send(f"The pot: {self.pot}\n"
													f"The {stage}: {cards_to_string(self.community_cards[:number_of_cards])}")
		
		evaluator = treys.Evaluator()
		board = []
		for card in self.community_cards.cards:
			abbreviation = pydealer.card.card_abbrev(card.value[0] if card.value != "10" else 'T', card.suit[0].lower())
			board.append(treys.Card.new(abbreviation))
		best_hand_value = evaluator.table.MAX_HIGH_CARD
		for player, hand in self.hands.items():
			hand_stack = []
			for card in hand:
				abbreviation = pydealer.card.card_abbrev(card.value[0] if card.value != "10" else 'T', card.suit[0].lower())
				hand_stack.append(treys.Card.new(abbreviation))
			value = evaluator.evaluate(board, hand_stack)
			if value < best_hand_value:
				best_hand_value = value
				winner = player
		
		hand_name = evaluator.class_to_string(evaluator.get_rank_class(best_hand_value))
		embed = round_message.embeds[0]
		embed.description += (f"\n\n{winner.mention} is the winner of {self.pot} with a {hand_name}\n"
								f"{winner.mention}'s hand: {cards_to_string(self.hands.pop(winner))}\n")
		for player, hand in self.hands.items():
			embed.description += f"\n{player.mention}'s hand: {cards_to_string(hand)}"
			# TODO: Allow mucking
		await round_message.edit(embed = embed)
	
	async def betting(self, ctx, message = None):
		bets = {}
		current_bet = 0
		first_player_turn = True
		while (not bets and len(self.hands) != 1) or not all(bet == current_bet for bet in bets.values()):
			for player in self.hands.copy():
				def check(message):
					if message.author != player:
						return False
					if message.content.lower() in ("call", "check", "fold"):
						return True
					if message.content.lower().startswith("raise "):
						try:
							return int(message.content[6:]) >= 0  # Use .removeprefix in Python 3.9
						except ValueError:
							return False
					return False
				can_check = bets.get(player, 0) == current_bet
				turn_message = (f"{player.mention}'s turn\n"
								f"{player.mention}: Would you like to `{'check' if can_check else 'call'}`, `fold`, or `raise ` an amount?")
				if not message:
					initial_embed = discord.Embed(color = ctx.bot.bot_color)
					initial_embed.description = ""
					message = await ctx.embed_send(turn_message)
					embed = message.embeds[0]
					first_player_turn = False
				else:
					embed = message.embeds[0]
					initial_embed = embed.copy()
					if first_player_turn:
						initial_embed.description += '\n'
						first_player_turn = False
					embed.description += "\n\n" + turn_message
					await message.edit(embed = embed)
				while (response := await ctx.bot.wait_for("message", check = check)).content.lower() == "check" and not can_check:
					embed_copy = embed.copy()
					embed_copy.description += f"\n{player.mention} attempted to check, but there is a bet to call"
					await message.edit(embed = embed_copy)
					await ctx.bot.attempt_delete_message(response)
				if response.content.lower() == "call":
					if can_check:
						initial_embed.description += (f"\n{player.mention} attempted to call\n"
														f"Since there's nothing to call, {player.mention} has checked instead")
					else:
						initial_embed.description += f"\n{player.mention} has called"
					bets[player] = current_bet
				elif response.content.lower() == "check":
					initial_embed.description += f"\n{player.mention} has checked"
					bets[player] = current_bet
				elif response.content.lower() == "fold":
					self.pot += bets.pop(player, 0)
					hand = self.hands.pop(player)
					initial_embed.description += f"\n{player.mention} has folded"
					prompt = await ctx.embed_send(f"\n{player.mention}: Would you like to show your hand?")
					with contextlib.suppress(asyncio.TimeoutError):
						if (await ctx.bot.wait_for_yes_or_no(channel = ctx.channel, message = prompt, user = player, 
																timeout = 10, use_reactions = True)):
							initial_embed.description += f"\n{player.mention}'s hand was {cards_to_string(hand)}"
					await ctx.bot.attempt_delete_message(prompt)
				elif response.content.lower().startswith("raise "):
					amount = int(response.content[6:])  # Use .removeprefix in Python 3.9
					if not amount:
						if can_check:
							initial_embed.description += f"\n{player.mention} has checked"
						else:
							initial_embed.description += f"\n{player.mention} has called"
					else:
						current_bet += amount
						initial_embed.description += f"\n{player.mention} has raised to {current_bet}"
					bets[player] = current_bet
				await message.edit(embed = initial_embed)
				await ctx.bot.attempt_delete_message(response)
				if len(self.hands) == 1 or (len(self.hands) == len(bets) and all(bet == current_bet for bet in bets.values())):
					break
		self.pot += sum(bets.values())

