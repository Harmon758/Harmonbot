
from discord.ext import commands

import asyncio
import chess
import cleverbot
import pydealer
import random

from modules import utilities
#from modules import gofish
from modules.maze import maze
from modules import war
from utilities import checks
from client import client
from client import wait_time
from client import cleverbot_instance

def setup(bot):
	bot.add_cog(Games())

class Games:
	
	#init
	_chess_board = chess.Board()
	war_channel, war_players = None, []
	gofish_channel, gofish_players = None, []
	taboo_players = []
	maze_started, maze_maze = False, None
	
	@commands.command(pass_context = True)
	async def blackjack(self, ctx):
		'''Play a game of blackjack'''
		deck = pydealer.Deck()
		deck.shuffle()
		dealer = deck.deal(2)
		hand = deck.deal(2)
		dealer_string = ""
		hand_string = ""
		for card in dealer.cards:
			dealer_string += card.value + " :" + card.suit.lower() + ": "
		for card in hand.cards:
			hand_string += card.value + " :" + card.suit.lower() + ": "
		dealer_total = sum([pydealer.const.DEFAULT_RANKS["values"][card.value] + 1 for card in dealer.cards])
		hand_total = sum([pydealer.const.DEFAULT_RANKS["values"][card.value] + 1 for card in hand.cards])
		await client.say("Dealer: " + dealer_string + '(' + str(dealer_total) + ')\n' + ctx.message.author.mention + ": " + hand_string + '(' + str(hand_total) + ')\n' )
		while True:
			action = await client.wait_for_message(author = ctx.message.author, check = lambda msg: msg.content in ["hit", "stay"])
			if action.content == "hit":
				hand_string = ""
				hand.add(deck.deal())
				for card in hand.cards:
					hand_string += card.value + " :" + card.suit.lower() + ": "
				hand_total = sum([pydealer.const.DEFAULT_RANKS["values"][card.value] + 1 for card in hand.cards])
				await client.say("Dealer: " + dealer_string + '(' + str(dealer_total) + ')\n' + ctx.message.author.mention + ": " + hand_string + '(' + str(hand_total) + ')\n' )
				if hand_total > 21:
					await client.reply("You have busted. You lost :(")
					return
			else:
				if dealer_total > 21:
					await client.reply("The dealer busted. You win!")
					return
				elif dealer_total > hand_total:
					await client.reply("The dealer beat you. You lost :(")
					return
				while True:
					dealer_string = ""
					dealer.add(deck.deal())
					for card in dealer.cards:
						dealer_string += card.value + " :" + card.suit.lower() + ": "
					dealer_total = sum([pydealer.const.DEFAULT_RANKS["values"][card.value] + 1 for card in dealer.cards])
					await client.say("Dealer: " + dealer_string + '(' + str(dealer_total) + ')\n' + ctx.message.author.mention + ": " + hand_string + '(' + str(hand_total) + ')\n' )
					if dealer_total > 21:
						await client.reply("The dealer busted. You win!")
						return
					elif dealer_total > hand_total:
						await client.reply("The dealer beat you. You lost :(")
						return
					await asyncio.sleep(5)
	
	@commands.group(invoke_without_command = True)
	async def chess(self, *option : str):
		'''
		Play chess
		standard algebraic notation
		'''
		if not option:
			await client.reply("Options: reset, board, undo, standard algebraic notation move")
		else:
			try:
				self._chess_board.push_san(option[0])
				await client.reply("\n```" + str(self._chess_board) + "```")
			except ValueError:
				await client.reply("Invalid move.")
		#await client.send_message(message.channel, message.author.mention + "\n" + "```" + board.__unicode__() + "```")
	
	@chess.command(name = "reset")
	async def chess_reset(self):
		'''Reset the board'''
		self._chess_board.reset()
		await client.reply("The board has been reset.")
	
	@chess.command(name = "board")
	async def chess_board(self):
		'''Display the current board'''
		await client.reply("\n```" + str(self._chess_board) + "```")
	
	@chess.command(name = "undo")
	async def chess_undo(self):
		'''Undo the last move'''
		try:
			self._chess_board.pop()
			await send_client.reply("\n```" + str(board) + "```")
		except IndexError:
			await client.reply("There's no more moves to undo.")
	
	@chess.command(name = "(╯°□°）╯︵", pass_context = True)
	async def chess_flip(self, ctx):
		'''Flip the table over'''
		self._chess_board.reset()
		await client.say(ctx.message.author.name + " flipped the table over in anger!\nThe board has been reset.")
	
	@commands.command(aliases = ["talk", "ask"])
	async def cleverbot(self, *, message : str):
		'''Talk to Cleverbot'''
		await client.reply(cleverbot_instance.ask(message))
	
	@commands.command(name = "8ball", aliases = ["eightball"])
	async def eightball(self):
		'''Ask 8ball a yes or no question'''
		responses = ["It is certain", "It is decidedly so", "Without a doubt", "Yes, definitely", "You may rely on it", "As I see it, yes", "Most likely",
			"Outlook good", "Yes", "Signs point to yes", "Reply hazy try again", "Ask again later", "Better not tell you now", "Cannot predit now",
			"Concentrate and ask again", "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]
		await client.reply(":8ball: {}".format(random.choice(responses)))
	
	@commands.group(hidden = True, pass_context = True)
	async def gofish(self, ctx): #WIP
		'''WIP'''
		return
	
	@gofish.command(hidden = True, name = "start", pass_context = True, no_pm = True)
	@checks.is_owner()
	async def gofish_start(self, ctx, *players : str): #WIP
		'''WIP'''
		self.gofish_channel = ctx.message.channel
		if ctx.message.server:
			for member in ctx.message.server.members:
				if member.name in players:
					self.gofish_players.append(member)
					break
		else:
			await client.reply("Please use that command in a server.")
			pass
		gofish.start(len(players))
		gofish_players_string = ""
		for player in self.gofish_players:
			gofish_players_string += player.name + " and "
		await client.reply(message.author.name + " has started a game of Go Fish between " + gofish_players_string[:-5] + "!")
	
	@gofish.command(hidden = True, name = "hand", pass_context = True)
	async def gofish_hand(self, ctx): #WIP
		'''WIP'''
		if ctx.message.author in gofish_players:
			await client.whisper("Your hand: " + gofish.hand(gofish_players.index(ctx.message.author) + 1))
	
	@gofish.command(hidden = True, name = "ask", pass_context = True)
	async def gofish_ask(self, ctx): #WIP
		'''WIP'''
		if ctx.message.author in gofish_players:
			pass
	
	@commands.command(pass_context = True)
	async def guess(self, ctx, *options : str):
		'''
		Guessing game
		Guess <max> <tries>
		'''
		tries = False
		if len(options) >= 2 and utilities.is_digit_gtz(options[1]):
			tries = int(options[1])
		if len(options) >= 1 and utilities.is_digit_gtz(options[0]):
			max_value = int(options[0])
		else:
			await client.reply("What range of numbers would you like to guess to? 1 to _")
			max_value = await client.wait_for_message(timeout = wait_time, author = ctx.message.author, check = utilities.message_is_digit_gtz)
			if max_value is None:
				max_value = 10
			else:
				max_value = int(max_value.content)
		answer = random.randint(1, max_value)
		if not tries:
			await client.reply("How many tries would you like?")
			tries = await client.wait_for_message(timeout = wait_time, author = ctx.message.author, check = utilities.message_is_digit_gtz)
			if tries is None:
				tries = 1
			else:
				tries = int(tries.content)
		await client.reply("Guess a number between 1 to " + str(max_value))
		while tries != 0:
			guess = await client.wait_for_message(timeout = wait_time, author = ctx.message.author, check = utilities.message_is_digit_gtz)
			if guess is None:
				await client.reply("Sorry, you took too long. It was " + str(answer))
				return
			if int(guess.content) == answer:
				await client.reply("You are right!")
				return
			elif tries != 1 and int(guess.content) > answer:
				await client.reply("It's less than " + guess.content)
				tries -= 1
			elif tries != 1 and int(guess.content) < answer:
				await client.reply("It's greater than " + guess.content)
				tries -= 1
			else:
				await client.reply("Sorry, it was actually " + str(answer))
				return
	
	@commands.command(pass_context = True)
	async def maze(self, ctx, *options : str):
		'''
		Maze game
		options: start <width> <height>, current, [w, a, s, d] to move
		'''
		if not options:
			await client.reply("Please enter an option (start/current)")
		elif options[0] == "start":
			if self.maze_started:
				await client.reply("There's already a maze game going on.")
			elif len(options) >= 3 and options[1].isdigit() and options[2].isdigit():
				self.maze_started = True
				self.maze_maze = maze(int(options[1]), int(options[2]))
				await utilities.send_mention_code(ctx.message, self.maze_maze.print_visible())
				'''
				maze_print = ""
				for r in maze_maze.test_print():
					row_print = ""
					for cell in r:
						row_print += cell + ' '
					maze_print += row_print + "\n"
				await send_mention_code(message, maze_print)
				'''
				# await send_mention_code(message, repr(maze_maze))
				convert_move = {'w' : 'n', 'a' : 'w', 's' : 's', 'd' : 'e'}
				while not self.maze_maze.reached_end():
					moved = False
					move = await client.wait_for_message(check = lambda message: message.content.lower() in ['w', 'a', 's', 'd']) # author = ctx.message.author
					moved = self.maze_maze.move(convert_move[move.content.lower()])
					await utilities.send_mention_code(ctx.message, self.maze_maze.print_visible())
					if not moved:
						await client.reply("You can't go that way.")
				await client.reply("Congratulations! You reached the end of the maze.")
				self.maze_started = False
			else:
				await client.reply("Please enter a valid maze size. (e.g. !maze start 2 2)")
		elif options[0] == "current":
			if self.maze_started:
				await utilities.send_mention_code(ctx.message, self.maze_maze.print_visible())
			else:
				await client.reply("There's no maze game currently going on.")
		else:
			await client.reply("Please enter a valid option (start/current).")
	
	@commands.group(hidden = True)
	async def taboo(self): #WIP
		'''WIP'''
		return
	
	@taboo.command(hidden = True, name = "start", pass_context = True, no_pm = True)
	async def taboo_start(self, ctx, player : str): #WIP
		'''WIP'''
		self.taboo_players.append(ctx.message.author)
		for member in self.message.server.members:
			if member.name == player:
				self.taboo_players.append(member)
				break
		await client.reply(" has started a game of Taboo with " + taboo_players[1].mention)
		await client.whisper("You have started a game of Taboo with " + taboo_players[1].name)
		await client.send_message(taboo_players[1], ctx.message.author.name + " has started a game of Taboo with you.")
	
	@taboo.command(hidden = True, name = "nextround") # no_pm = True ?
	async def taboo_nextround(self): #WIP
		'''WIP'''
		if message.server:
			pass
	
	@commands.group(pass_context = True)
	async def war(self, ctx):
		'''Based on the War card game'''
		return
	
	@war.command(name = "start", pass_context = True, no_pm = True)
	@checks.is_owner()
	async def war_start(self, ctx, *players : str):
		'''Start a game of War'''
		self.war_players = []
		for member in ctx.message.server.members:
			if member.name in players:
				self.war_players.append(member)
				break
		war.start(len(players))
		self.war_channel = ctx.message.channel
		war_players_string = ""
		for player in self.war_players:
			war_players_string += player.name + " and "
		await client.reply(message.author.name + " has started a game of War between " + war_players_string[:-5] + "!")
	
	@war.command(name = "hand", pass_context = True)
	async def war_hand(self, ctx):
		'''See your current hand'''
		if ctx.message.author in self.war_players:
			await client.whisper("Your hand: " + war.hand(self.war_players.index(ctx.message.author) + 1))
	
	@war.command(name = "left", pass_context = True)
	async def war_left(self, ctx):
		'''See how many cards you have left'''
		if ctx.message.author in self.war_players:
			await client.reply("You have " + str(war.card_count(self.war_players.index(ctx.message.author) + 1)) + " cards left.")
	
	@war.command(name = "play", pass_context = True)
	async def war_play(self, ctx, *card : str):
		'''Play a card'''
		if ctx.message.author in self.war_players:
			player_number = self.war_players.index(message.author) + 1
			winner, cardsplayed, tiedplayers = war.play(player_number, ' '.join(card))
			if winner == -1:
				await client.reply("You have already chosen your card for this battle.")
			elif winner == -3:
				await client.reply("You are not in this battle.")
			elif winner == -4:
				await client.reply("Card not found in your hand.")
			else:
				await client.reply("You chose the " + cardsplayed[player_number - 1].value + " of " + cardsplayed[player_number - 1].suit)
				await client.whisper("Your hand: " + war.hand(player_number))
			if winner > 0:
				winner_name = self.war_players[winner - 1].name
				cards_played_print = ""
				for i in range(len(self.war_players)):
					cards_played_print += self.war_players[i].name + " played " + cardsplayed[i].value + " of " + cardsplayed[i].suit + " and "
				cards_played_print = cards_played_print[:-5] + "."
				await client.send_message(self.war_channel, winner_name + " wins the battle.\n" + cards_played_print)
				for war_player in self.war_players:
					await client.send_message(war_player, winner_name + " wins the battle.\n" + cards_played_print)
			if winner == -2:
				cards_played_print = ""
				for i in range(len(self.war_players)):
					cards_played_print += self.war_players[i].name + " played " + cardsplayed[i].value + " of " + cardsplayed[i].suit + " and "
				cards_played_print = cards_played_print[:-5] + "."
				tiedplayers_print = ""
				for tiedplayer in tiedplayers:
					tiedplayers_print += self.war_players[tiedplayer - 1].name + " and "
				tiedplayers_print = tiedplayers_print[:-5] + " tied.\n"
				await client.send_message(self.war_channel, tiedplayers_print + cards_played_print)
				for war_player in self.war_players:
					await client.send_message(war_player, tiedplayers_print + cards_played_print)
				pass

