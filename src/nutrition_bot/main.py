"""Bot entrypoint."""
from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher

from .config import BOT_TOKEN
from .handlers import food, help, start, summary
from .services.scheduler import setup_scheduler
from .storage import db


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(food.router)
    dp.include_router(summary.router)
    dp.include_router(help.router)
    return dp


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан")
    db.init_db()
    bot = Bot(BOT_TOKEN, parse_mode="HTML")
    dp = build_dispatcher()
    scheduler = setup_scheduler()
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
