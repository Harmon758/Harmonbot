
from telegram.error import Conflict, NetworkError
from telegram.ext import Application, CommandHandler

import asyncio
import datetime
import os

import dotenv


version = "0.3.8"

# TODO: Set up logging and/or make Beta bot for CI

# Load credentials from .env
dotenv.load_dotenv()
token = os.getenv("TELEGRAM_BOT_API_TOKEN")

async def ping(update, context):
    await context.bot.send_message(
        chat_id = update.message.chat_id,
        text = "pong"
    )

async def test(update, context):
    await context.bot.send_message(
        chat_id = update.message.chat_id,
        text = "Hello, World!"
    )

async def error_handler(update, context):
    if isinstance(context.error, Conflict):
        # Probably due to CI
        print(f"Conflict @ {datetime.datetime.now().isoformat()}")
    elif isinstance(context.error, NetworkError):
        print(
            f"Network Error: {context.error}"
            f" @ {datetime.datetime.now().isoformat()}"
        )
    else:
        raise context.error

async def post_init(application):
    asyncio.create_task(
        post_start(application),
        name = "post_start"
    )

async def post_start(application):
    while not application.updater.running:
        await asyncio.sleep(1)

    bot_info = await application.bot.get_me()
    print(
        "Started up Telegram Harmonbot "
        f"({bot_info['username']}) ({bot_info['id']})"
    )

    if os.getenv("CI") or os.getenv("GITHUB_ACTION"):
        asyncio.get_event_loop().stop()

def main():
    builder = Application.builder()
    builder.token(token)
    builder.post_init(post_init)
    application = builder.build()

    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("test", test))

    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == "__main__":
    main()

