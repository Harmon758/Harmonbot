
import logging
import logging.handlers

# TODO: Create folders

# TwitchIO log
twitchio_logger = logging.getLogger("twitchio")
twitchio_logger.setLevel(logging.DEBUG)
twitchio_logger_handler = logging.handlers.TimedRotatingFileHandler(filename = "data/logs/twitchio/twitchio.log", 
																	when = "midnight", backupCount = 3650000, encoding = "UTF-8")
twitchio_logger_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
twitchio_logger.addHandler(twitchio_logger_handler)

# raw data log
raw_data_logger = logging.getLogger("raw data")
raw_data_logger.setLevel(logging.DEBUG)
raw_data_handler = logging.handlers.TimedRotatingFileHandler(filename = "data/logs/raw_data/raw_data.log", 
																when = "midnight", backupCount = 3650000, encoding = "UTF-8")
raw_data_handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
raw_data_logger.addHandler(raw_data_handler)

