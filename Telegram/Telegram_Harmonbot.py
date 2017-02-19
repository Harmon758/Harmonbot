
import telegram
import telegram.ext

import credentials

version = "0.1.1"

bot = telegram.Bot(token = credentials.telegram_harmonbot_token)
updater = telegram.ext.Updater(token = credentials.telegram_harmonbot_token)

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
print("Started up Telegram Harmonbot ({0[username]}) ({0[id]})".format(bot_info))

