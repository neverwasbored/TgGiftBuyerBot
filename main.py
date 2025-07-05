import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import load_config
from bot.handlers import register_handlers
from bot.middlewares.db_session_middleware import DBSessionMiddleware
from db import init_db
from utils.logger import log
from utils.gift_parser import start_gift_parsing_loop
import os

# Load configuration
config = load_config()

# Initialize bot
bot = Bot(token=config["bot_token"])
dp = Dispatcher(storage=MemoryStorage())


async def on_startup():
    """
    Actions to perform when the bot starts, including database initialization.
    """
    log.info("Initializing database...")
    init_db()
    log.info("Database initialized successfully")

    # Start parsing gifts
    log.info("Starting gift parsing loop...")
    asyncio.create_task(start_gift_parsing_loop())


async def main():
    """
    Main entry point for starting the bot.
    """
    log.info("Starting bot...")
    os.makedirs('logs', exist_ok=True)


    await on_startup()

    dp.update.middleware(DBSessionMiddleware())

    # Register handlers
    register_handlers(dp)

    # Start polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        log.exception(f"Bot stopped due to an error: {e}")
