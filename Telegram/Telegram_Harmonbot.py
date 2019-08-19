
import telegram
import telegram.ext

import os

import dotenv

version = "0.1.4"

# Load credentials from .env
dotenv.load_dotenv()
token = os.getenv("TELEGRAM_BOT_API_TOKEN")

bot = telegram.Bot(token = token)
updater = telegram.ext.Updater(token = token)

def test(bot, update):
	bot.sendMessage(chat_id = update.message.chat_id, text = "Hello, World!")

def ping(bot, update):
	bot.sendMessage(chat_id = update.message.chat_id, text = "pong")

test_handler = telegram.ext.CommandHandler("test", test)
updater.dispatcher.add_handler(test_handler)

ping_handler = telegram.ext.CommandHandler("ping", ping)
updater.dispatcher.add_handler(ping_handler)

updater.start_polling()

bot_info = bot.getMe()
print(f"Started up Telegram Harmonbot ({bot_info['username']}) ({bot_info['id']})")

if os.getenv("CI") or os.getenv("GITHUB_ACTION"):
	updater.stop()

