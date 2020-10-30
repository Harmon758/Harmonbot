
import telegram
import telegram.ext

import datetime
import os

import dotenv

version = "0.2.2"

# TODO: set up logging and/or make Beta bot for CI

# Load credentials from .env
dotenv.load_dotenv()
token = os.getenv("TELEGRAM_BOT_API_TOKEN")

bot = telegram.Bot(token = token)
updater = telegram.ext.Updater(token = token)

def test(update, context):
	context.bot.sendMessage(chat_id = update.message.chat_id, text = "Hello, World!")

def ping(update, context):
	context.bot.sendMessage(chat_id = update.message.chat_id, text = "pong")

test_handler = telegram.ext.CommandHandler("test", test)
updater.dispatcher.add_handler(test_handler)

ping_handler = telegram.ext.CommandHandler("ping", ping)
updater.dispatcher.add_handler(ping_handler)

def error_handler(update, context):
	if isinstance(context.error, telegram.error.Conflict):
		print(f"Conflict @ {datetime.datetime.now().isoformat()}")  # probably CI
	else:
		raise context.error

updater.dispatcher.add_error_handler(error_handler)

updater.start_polling()

bot_info = bot.getMe()
print(f"Started up Telegram Harmonbot ({bot_info['username']}) ({bot_info['id']})")

if os.getenv("CI") or os.getenv("GITHUB_ACTION"):
	updater.stop()

