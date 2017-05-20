
import logging
import logging.handlers
import sys

import clients

path = clients.data_path + "/logs/"
clients.create_folder(path + "chat")
clients.create_folder(path + "discord")

console_logger = logging.getLogger("console")
console_logger.setLevel(logging.DEBUG)
console_logger_handler = logging.FileHandler(filename = path + "console.log", encoding = "utf-8", mode = 'a')
console_logger_handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
console_logger.addHandler(console_logger_handler)

class Logger(object):
	
	'''Logger'''
	
	def __init__(self, log, prefix = ""):
		self.console = sys.__stdout__
		self.log = log
		self.prefix = prefix
	
	def write(self, message):
		self.console.write(message)
		if not message.isspace():
			self.log(self.prefix + message)
	
	def flush(self):
		pass

sys.stdout = Logger(console_logger.info)
# sys.stderr = Logger(errors_logger.error, "Error")
# sys.stderr = Logger(console_logger.error)

# rename to exceptions?
errors_logger = logging.getLogger("errors")
errors_logger.setLevel(logging.DEBUG)
errors_logger_handler_1 = logging.FileHandler(filename = path + "errors.log", encoding = "utf-8", mode = 'a')
errors_logger_handler_1.setFormatter(logging.Formatter("\n\n%(asctime)s\n%(message)s"))
errors_logger_handler_2 = logging.FileHandler(filename = path + "unresolved_errors.log", encoding = "utf-8", mode = 'a')
errors_logger_handler_2.setFormatter(logging.Formatter("\n\n%(asctime)s\n%(message)s"))
errors_logger.addHandler(errors_logger_handler_1)
errors_logger.addHandler(errors_logger_handler_2)
def log_exception(exc_type, exc_value, exc_traceback):
	sys.__excepthook__(exc_type, exc_value, exc_traceback)
	errors_logger.error("Uncaught exception\n", exc_info = (exc_type, exc_value, exc_traceback))
sys.excepthook = log_exception

discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.INFO)
discord_handler = logging.handlers.TimedRotatingFileHandler(filename = path + "discord/discord.log", when = "midnight", backupCount = 3650000, encoding = "utf-8")
discord_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
discord_logger.addHandler(discord_handler)

chat_logger = logging.getLogger("chat")
chat_logger.setLevel(logging.DEBUG)
chat_logger_handler = logging.handlers.TimedRotatingFileHandler(filename = path + "chat/chat.log", when = "midnight", backupCount = 3650000, encoding = "utf-8")
chat_logger.addHandler(chat_logger_handler)

aiohttp_client_logger = logging.getLogger("aiohttp.client")
aiohttp_client_logger_handler = logging.FileHandler(filename = path + "aiohttp/client.log", encoding = "utf-8", mode = 'a')
aiohttp_client_logger_handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
aiohttp_client_logger.addHandler(aiohttp_client_logger_handler)

