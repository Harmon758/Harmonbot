
import pydealer

started = False

def start(number):
	global started, number_of_players, played, hands, deck
	started = True
	number_of_players = number
	played = [False] * number_of_players
	deck = pydealer.Deck()
	deck.shuffle()
	hands = {}
	for i in range(number_of_players):
		if number_of_players <= 4:
			hands[i] = deck.deal(7)
		else:
			hands[i] = deck.deal(5)
		hands[i].sort()

def hand(player_number):
	hand_string = ""
	if player_number <= number_of_players:
		for card in hands[player_number].cards:
			hand_string += card.value + " of " + card.suit + ", "
	else:
		return
	return hand_string[:-2]

def ask(player_number, asked_player, card):
	if played[player_number - 1]:
		return -1
	if player_number <= number_of_players and asked_player <= number_of_players:
		if len(hands[player_number].get(card)):
			played[player_number - 1] = True
		else:
			return -2
