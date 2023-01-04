
import telegram
import telegram.ext

import asyncio
import datetime
import os

import dotenv


version = "0.3.4"

# TODO: set up logging and/or make Beta bot for CI

# Load credentials from .env
dotenv.load_dotenv()
token = os.getenv("TELEGRAM_BOT_API_TOKEN")

async def test(update, context):
    await context.bot.send_message(
        chat_id = update.message.chat_id, text = "Hello, World!"
    )

async def ping(update, context):
    await context.bot.send_message(
        chat_id = update.message.chat_id, text = "pong"
    )

async def error_handler(update, context):
    if isinstance(context.error, telegram.error.Conflict):
        # probably CI
        print(f"Conflict @ {datetime.datetime.now().isoformat()}")
    elif isinstance(context.error, telegram.error.NetworkError):
        print(
            f"Network Error: {context.error} @ {datetime.datetime.now().isoformat()}"
        )
    else:
        raise context.error

async def post_init(application):
    asyncio.create_task(post_start(application), name = "post_start")

async def post_start(application):
    while not application.updater.running:
        await asyncio.sleep(1)

    bot = telegram.Bot(token = token)
    bot_info = await bot.get_me()
    print(
        f"Started up Telegram Harmonbot ({bot_info['username']}) ({bot_info['id']})"
    )

    if os.getenv("CI") or os.getenv("GITHUB_ACTION"):
        asyncio.get_event_loop().stop()

def main():
    application = telegram.ext.Application.builder().token(token).post_init(post_init).build()

    test_handler = telegram.ext.CommandHandler("test", test)
    application.add_handler(test_handler)

    ping_handler = telegram.ext.CommandHandler("ping", ping)
    application.add_handler(ping_handler)

    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == "__main__":
    main()

