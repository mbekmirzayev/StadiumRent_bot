import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from services import start, stadium, booking, search_by_time
import logging

from utils import time_slots

logging.basicConfig(level=logging.DEBUG)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(stadium.router)
    dp.include_router(search_by_time.router)
    dp.include_router(time_slots.router)

    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi")