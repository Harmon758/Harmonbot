
import pydealer

started = False

def start(number):
	global started, number_of_players, played, hands, cards, cardsplayed, tiedcards
	started = True
	number_of_players = number
	played = [False] * number_of_players
	cardsplayed = {}
	hands = {}
	cards = {}
	tiedcards = pydealer.Stack()
	count = 1
	temp = number_of_players
	while temp > 1:
		deck = pydealer.Deck()
		deck.shuffle()
		hands[count] = deck.deal(5)
		hands[count + 1] = deck.deal(5)
		cards[count], cards[count + 1] = deck.split()
		count += 2
		temp -= 2
	if temp == 1:
		deck = pydealer.Deck()
		deck.shuffle()
		hands[count] = deck.deal(5)
		discard = deck.deal(5)
		cards[count], discard = deck.split()
	# hand1.sort()
	# hand2.sort()

def hand(player_number):
	hand_string = ""
	if player_number <= number_of_players:
		for card in hands[player_number].cards:
			hand_string += card.value + " of " + card.suit + ", "
	else:
		return
	return hand_string[:-2]

def card_count(player_number):
	if player_number <= number_of_players:
		return cards[player_number].size + hands[player_number].size
	else:
		return

def play(player_number, card):
	global played, cardsplayed, hands, cards, tiedcards, tiedplayers, tiedplayed
	if tiedcards.size:
		if player_number not in tiedplayers:
			return -3, -1, -1
		if tiedplayed[player_number]:
			return -1, -1, -1
	if played[player_number - 1]:
		return -1, -1, -1
	cardplayed = hands[player_number].get(card, limit=1)
	if len(cardplayed) == 0:
		return -4, -1, -1
	else:
		cardsplayed[player_number - 1] = cardplayed[0]
	hands[player_number].add(cards[player_number].deal())
	if tiedcards.size:
		tiedplayed[player_number] = True
		if not all(list(tiedplayed.values())):
			return 0, cardsplayed, -1
		list_of_cards_played = []
		for tiedplayer in tiedplayers:
			list_of_cards_played.append(cardsplayed[tiedplayer - 1])
	else:
		played[player_number - 1] = True
		if not all(played):
			return 0, cardsplayed, -1
		played = [False for flag in played]
		list_of_cards_played = []
		for i in range(number_of_players):
			list_of_cards_played.append(cardsplayed[i])
	allcardsplayed = pydealer.Stack(cards=list_of_cards_played)
	allcardsplayedsorted = pydealer.Stack(cards=list_of_cards_played)
	allcardsplayedsorted.sort(ranks=pydealer.POKER_RANKS)
	highestcard = allcardsplayedsorted.deal(1)[0]
	highestplayers = allcardsplayed.find(highestcard.value)
	cardsplayed = {}
	if len(highestplayers) == 1 and not tiedcards.size:
		cards[highestplayers[0] + 1].add(allcardsplayed, end="bottom")
		return highestplayers[0] + 1, allcardsplayed, -1
	elif len(highestplayers) == 1:
		cards[tiedplayers[highestplayers[0]]].add(allcardsplayed, end="bottom")
		cards[tiedplayers[highestplayers[0]]].add(tiedcards, end="bottom")
		tiedcards = pydealer.Stack()
		return tiedplayers[highestplayers[0]], allcardsplayed, -1
	else:
		if tiedcards.size:
			temp = []
			for highestplayer in highestplayers:
				temp.append(tiedplayers[highestplayer])
			tiedplayers = temp
		else:
			tiedplayers = []
			for highestplayer in highestplayers:
				tiedplayers.append(highestplayer + 1)
		tiedcards.add(allcardsplayed)
		tiedplayed = {}
		for tiedplayer in tiedplayers:
			tiedplayed[tiedplayer] = False
		return -2, allcardsplayed, tiedplayers
