
import pydealer

class GoFishRound:
	
	'''Round of Go Fish'''
	
	def __init__(self):
		self.started = False
		self.number_of_players = 0
		self.played = []
		self.hands = {}
		self.deck = pydealer.Deck()
		self.deck.shuffle()
	
	def start(number):
		'''Start a round of Go Fish'''
		self.started = True
		self.number_of_players = number
		self.played = [False] * self.number_of_players
		for i in range(self.number_of_players):
			if self.number_of_players <= 4:
				self.hands[i] = self.deck.deal(7)
			else:
				self.hands[i] = self.deck.deal(5)
			self.hands[i].sort()
	
	def hand(player_number):
		hand_string = ""
		if player_number <= self.number_of_players:
			for card in hands[player_number].cards:
				hand_string += card.value + " of " + card.suit + ", "
		else:
			return
		return hand_string[:-2]

	def ask(player_number, asked_player, card):
		if self.played[player_number - 1]:
			return -1
		if player_number <= self.number_of_players and asked_player <= self.number_of_players:
			if len(self.hands[player_number].get(card)):
				self.played[player_number - 1] = True
			else:
				return -2

