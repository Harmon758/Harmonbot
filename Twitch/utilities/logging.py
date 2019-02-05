
import logging
import logging.handlers

# TwitchIO log
twitchio_logger = logging.getLogger("twitchio")
twitchio_logger.setLevel(logging.DEBUG)
twitchio_logger_handler = logging.handlers.TimedRotatingFileHandler(filename = "data/logs/twitchio/twitchio.log", 
																	when = "midnight", backupCount = 3650000, encoding = "UTF-8")
twitchio_logger_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
twitchio_logger.addHandler(twitchio_logger_handler)

