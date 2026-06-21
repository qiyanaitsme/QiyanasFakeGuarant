from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.connection import create_tables
from handlers import start, menu, profile, deals, stats, withdraw, support, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def main() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(profile.router)
    dp.include_router(deals.router)
    dp.include_router(stats.router)
    dp.include_router(withdraw.router)
    dp.include_router(support.router)
    dp.include_router(admin.router)

    await create_tables()
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await dp.storage.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except SystemExit:
        pass