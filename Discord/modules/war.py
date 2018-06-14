
import pydealer

class WarRound:
	
	'''Round of War'''
	
	def __init__(self):
		self.started = False
		self.number_of_players = 0
		self.played = []
		self.hands = {}
		self.cards = {}
		self.cards_played = {}
		self.tied_cards = pydealer.Stack()
		self.tied_players = []
		self.tied_played = {}
	
	def start(self, number):
		'''Start a round of War'''
		self.started = True
		self.number_of_players = number
		self.played = [False] * self.number_of_players
		count = 1
		temp = self.number_of_players
		while temp > 1:
			deck = pydealer.Deck()
			deck.shuffle()
			self.hands[count] = deck.deal(5)
			self.hands[count + 1] = deck.deal(5)
			self.cards[count], self.cards[count + 1] = deck.split()
			count += 2
			temp -= 2
		if temp == 1:
			deck = pydealer.Deck()
			deck.shuffle()
			self.hands[count] = deck.deal(5)
			discard = deck.deal(5)
			self.cards[count], discard = deck.split()
		# hand1.sort()
		# hand2.sort()

	def hand(self, player_number):
		hand_string = ""
		if player_number <= self.number_of_players:
			for card in self.hands[player_number].cards:
				hand_string += card.value + " of " + card.suit + ", "
		else:
			return
		return hand_string[:-2]

	def card_count(self, player_number):
		if player_number <= self.number_of_players:
			return self.cards[player_number].size + self.hands[player_number].size
		else:
			return

	def play(self, player_number, card):
		'''Play a card'''
		if self.tied_cards.size:
			if player_number not in self.tied_players:
				return -3, -1, -1
			if self.tied_played[player_number]:
				return -1, -1, -1
		if self.played[player_number - 1]:
			return -1, -1, -1
		card_played = self.hands[player_number].get(card, limit=1)
		if len(card_played) == 0:
			return -4, -1, -1
		else:
			self.cards_played[player_number - 1] = card_played[0]
		self.hands[player_number].add(self.cards[player_number].deal())
		if self.tied_cards.size:
			self.tied_played[player_number] = True
			if not all(list(self.tied_played.values())):
				return 0, self.cards_played, -1
			list_of_cards_played = []
			for tied_player in self.tied_players:
				list_of_cards_played.append(self.cards_played[tied_player - 1])
		else:
			self.played[player_number - 1] = True
			if not all(self.played):
				return 0, self.cards_played, -1
			self.played = [False for flag in self.played]
			list_of_cards_played = []
			for i in range(self.number_of_players):
				list_of_cards_played.append(self.cards_played[i])
		all_cards_played = pydealer.Stack(cards=list_of_cards_played)
		all_cards_played_sorted = pydealer.Stack(cards=list_of_cards_played)
		all_cards_played_sorted.sort(ranks=pydealer.POKER_RANKS)
		highest_card = all_cards_played_sorted.deal(1)[0]
		highest_players = all_cards_played.find(highest_card.value)
		self.cards_played = {}
		if len(highest_players) == 1 and not self.tied_cards.size:
			self.cards[highest_players[0] + 1].add(all_cards_played, end="bottom")
			return highest_players[0] + 1, all_cards_played, -1
		elif len(highest_players) == 1:
			self.cards[self.tied_players[highest_players[0]]].add(all_cards_played, end="bottom")
			self.cards[self.tied_players[highest_players[0]]].add(self.tied_cards, end="bottom")
			self.tied_cards = pydealer.Stack()
			return self.tied_players[highest_players[0]], all_cards_played, -1
		else:
			if self.tied_cards.size:
				temp = []
				for highest_player in highest_players:
					temp.append(self.tied_players[highest_player])
				self.tied_players = temp
			else:
				self.tied_players = []
				for highest_player in highest_players:
					self.tied_players.append(highest_player + 1)
			self.tied_cards.add(all_cards_played)
			self.tied_played = {}
			for tied_player in self.tied_players:
				self.tied_played[tied_player] = False
			return -2, all_cards_played, self.tied_players

