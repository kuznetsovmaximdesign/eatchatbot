"""Executable entrypoint for launching the nutrition bot."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import get_timezone, require_bot_token
from .handlers import food, help, start, summary
from .services.scheduler import setup_scheduler
from .storage import db


def build_dispatcher() -> Dispatcher:
    """Register all routers in a dispatcher instance."""

    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(food.router)
    dp.include_router(summary.router)
    dp.include_router(help.router)
    return dp


async def main() -> None:
    """Initialise storage, bot, scheduler and start polling."""

    token = require_bot_token()
    tz = get_timezone()
    db.init_db()

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = build_dispatcher()

    scheduler = setup_scheduler(bot=bot, tz=tz)
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
