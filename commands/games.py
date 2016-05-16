
from discord.ext import commands

import chess
import cleverbot
import random

from modules import utilities
from client import client
from client import wait_time

def setup(bot):
	bot.add_cog(Games())

class Games:
	
	chess_board = chess.Board()
	cleverbot_instance = cleverbot.Cleverbot()

	@commands.command()
	async def chess(self, *option : str):
		'''Play chess'''
		if not option:
			await client.reply("Options: reset, board, undo, standard algebraic notation move")
		elif option[0] == "reset":
			self.chess_board.reset()
			await client.reply("The board has been reset.")
		elif option[0] == "board":
			await client.reply("\n```" + str(self.chess_board) + "```")
		elif option[0] == "undo":
			try:
				self.chess_board.pop()
				await send_client.reply("\n```" + str(board) + "```")
			except IndexError:
				await client.reply("There's no more moves to undo.")
		elif option[0] == "(╯°□°）╯︵":
			self.chess_board.reset()
			await client.say("\n" + message.author.name + " flipped the table over in anger!\nThe board has been reset.")
		else:
			try:
				self.chess_board.push_san(option[0])
				await client.reply("\n```" + str(self.chess_board) + "```")
			except ValueError:
				await client.reply("Invalid move.")
		#await client.send_message(message.channel, message.author.mention + "\n" + "```" + board.__unicode__() + "```")

	@commands.command(aliases = ["talk", "ask"])
	async def cleverbot(self, *message : str):
		'''Talk to Cleverbot'''
		await client.reply(self.cleverbot_instance.ask(' '.join(message)))

	@commands.command(aliases = ["8ball"])
	async def eightball(self):
		'''Let 8ball choose'''
		responses = ["It is certain", "It is decidedly so", "Without a doubt", "Yes, definitely", "You may rely on it", "As I see it, yes", "Most likely",
			"Outlook good", "Yes", "Signs point to yes", "Reply hazy try again", "Ask again later", "Better not tell you now", "Cannot predit now",
			"Concentrate and ask again", "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]
		await client.reply(random.choice(responses))

	@commands.command(pass_context = True)
	async def guess(self, ctx, *options : str):
		'''Guessing game
		
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
