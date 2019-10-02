
import asyncio
import datetime
import logging
import logging.handlers
import sys

from aiohttp.web_log import AccessLogger

from utilities.database import create_database_connection

sys.path.insert(0, "..")
from units.files import create_folder
sys.path.pop(0)

class ConsoleLogger(object):
	
	'''Console Logger'''
	
	def __init__(self, log, prefix = ""):
		self.log = log
		self.prefix = prefix
		
		self.console = sys.__stdout__
		self.console.reconfigure(encoding = "UTF-8")
	
	def write(self, message):
		self.console.write(message)
		if not message.isspace():
			self.log(self.prefix + message)
	
	def flush(self):
		pass


def initialize_logging(data_path):
	path = data_path + "/logs/"
	
	# Create log folders
	create_folder(path + "aiohttp")
	create_folder(path + "discord")
	
	# Console log
	console_logger = logging.getLogger("console")
	console_logger.setLevel(logging.DEBUG)
	console_logger_handler = logging.FileHandler(filename = path + "console.log", encoding = "UTF-8", mode = 'a')
	console_logger_handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
	console_logger.addHandler(console_logger_handler)
	
	sys.stdout = ConsoleLogger(console_logger.info)
	## sys.stderr = ConsoleLogger(errors_logger.error, "Error")
	## sys.stderr = ConsoleLogger(console_logger.error)
	
	# Errors/Exceptions logs
	# TODO: rename to exceptions?
	errors_logger = logging.getLogger("errors")
	errors_logger.setLevel(logging.DEBUG)
	errors_logger_handler_1 = logging.FileHandler(filename = path + "errors.log", encoding = "UTF-8", mode = 'a')
	errors_logger_handler_1.setFormatter(logging.Formatter("\n\n%(asctime)s\n%(message)s"))
	errors_logger_handler_2 = logging.FileHandler(filename = path + "unresolved_errors.log", encoding = "UTF-8", mode = 'a')
	errors_logger_handler_2.setFormatter(logging.Formatter("\n\n%(asctime)s\n%(message)s"))
	errors_logger.addHandler(errors_logger_handler_1)
	errors_logger.addHandler(errors_logger_handler_2)
	
	def log_exception(exc_type, exc_value, exc_traceback):
		sys.__excepthook__(exc_type, exc_value, exc_traceback)
		errors_logger.error("Uncaught exception\n", exc_info = (exc_type, exc_value, exc_traceback))
	
	sys.excepthook = log_exception
	
	# discord.py log
	discord_logger = logging.getLogger("discord")
	discord_logger.setLevel(logging.INFO)
	discord_handler = logging.handlers.TimedRotatingFileHandler(filename = path + "discord/discord.log", when = "midnight", backupCount = 3650000, encoding = "UTF-8")
	discord_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
	discord_logger.addHandler(discord_handler)
	
	# handler to output to console
	## console_handler = logging.StreamHandler(sys.stdout)
	# not used by aiohttp server log
	
	# aiohttp logs
	
	# aiohttp server access log
	# replaced by AiohttpAccessLogger logging to database
	## TODO: Rotate
	## aiohttp_access_logger = logging.getLogger("aiohttp.access")
	## aiohttp_access_logger.setLevel(logging.DEBUG)
	## aiohttp_access_logger_handler = logging.FileHandler(filename = path + "aiohttp/access.log", 
	##														encoding = "UTF-8", mode = 'a')
	## aiohttp_access_logger_handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
	## aiohttp_access_logger.addHandler(aiohttp_access_logger_handler)
	
	# aiohttp client log
	aiohttp_client_logger = logging.getLogger("aiohttp.client")
	aiohttp_client_logger_handler = logging.FileHandler(filename = path + "aiohttp/client.log", encoding = "UTF-8", mode = 'a')
	aiohttp_client_logger_handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
	aiohttp_client_logger.addHandler(aiohttp_client_logger_handler)
	
	# aiohttp server log
	aiohttp_server_logger = logging.getLogger("aiohttp.server")
	aiohttp_server_logger.setLevel(logging.DEBUG)
	aiohttp_server_logger_handler = logging.FileHandler(filename = path + "aiohttp/server.log", encoding = "UTF-8", mode = 'a')
	aiohttp_server_logger_handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
	aiohttp_server_logger.addHandler(aiohttp_server_logger_handler)
	## aiohttp_server_logger.addHandler(console_handler)
	
	# aiohttp web log
	aiohttp_web_logger = logging.getLogger("aiohttp.web")
	aiohttp_web_logger.setLevel(logging.DEBUG)  # Necessary?
	aiohttp_web_logger_handler = logging.FileHandler(filename = path + "aiohttp/web.log", encoding = "UTF-8", mode = 'a')
	aiohttp_web_logger_handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
	aiohttp_web_logger.addHandler(aiohttp_web_logger_handler)

class AiohttpAccessLogger(AccessLogger):
	
	def log(self, request, response, time):
		# super().log(request, response, time)
		asyncio.create_task(self.log_to_database(request, response, time))
	
	async def log_to_database(self, request, response, time):
		async with create_database_connection() as connection:
			await connection.execute(
				"""
				INSERT INTO aiohttp.access_log
				VALUES ($1, $2, $3, $4, $5, $6, $7)
				""", 
				datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds = time), 
				self._format_a(request, response, time), 
				self._format_r(request, response, time), 
				response.status, response.body_length, 
				self._format_i("Referer", request, response, time), 
				self._format_i("User-Agent", request, response, time).encode("UTF-8", "backslashreplace").decode("UTF-8")
			)


async def initialize_aiohttp_access_logging(database):
	await database.execute("CREATE SCHEMA IF NOT EXISTS aiohttp")
	await database.execute(
		"""
		CREATE TABLE IF NOT EXISTS aiohttp.access_log (
			request_start_timestamp		TIMESTAMPTZ PRIMARY KEY, 
			remote_ip_address			TEXT, 
			request_first_line			TEXT, 
			response_status_code		INT, 
			response_bytes_size			INT, 
			request_referer				TEXT, 
			request_user_agent			TEXT
		)
		"""
	)

