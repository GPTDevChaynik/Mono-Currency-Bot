import asyncio
import logging
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.handlers.start import router as start_router
from app.handlers.rates import router as rates_router
from app.handlers.converter import router as converter_router
from app.handlers.home import router as home_router
from app.handlers.about import router as about_router

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Add it to .env")

bot = Bot(
    TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
    ),
)

dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(rates_router)
dp.include_router(converter_router)
dp.include_router(about_router)
dp.include_router(home_router)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
