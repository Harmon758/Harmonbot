
import pydealer

class PokerRound:
	
	'''Round of poker'''
	
	def __init__(self):
		self.status = None
		self.players = []
		self.deck = None
		self.hands = {}
		self.turn = None
		self.pot = None
	
	