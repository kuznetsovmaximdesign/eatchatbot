"""Lightweight smoke test ensuring imports and wiring succeed."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from nutrition_bot.__main__ import build_dispatcher
from nutrition_bot.config import get_settings
from nutrition_bot.services.scheduler import setup_scheduler


async def main() -> None:
    settings = get_settings(validate_bot_token=False)
    dp = build_dispatcher()
    routers = getattr(dp, "sub_routers", ())
    print(f"✅ Dispatcher создан, роутеров: {len(list(routers))}")

    token = settings.bot_token
    if not token:
        print("⚠️ BOT_TOKEN не найден — пропускаю создание бота. Укажи токен в .env для полной проверки.")
        return

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    scheduler = setup_scheduler(bot=bot, tz=settings.tz)
    print("✅ Планировщик настроен (не запущен)")
    scheduler.shutdown(wait=False)

    await bot.session.close()
    await dp.storage.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
