"""Auto-summary scheduler."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from ..config import BOT_TOKEN, TZ
from ..storage import db
from . import food_service, user_service, calc


async def send_daily_reports() -> None:
    tz = pytz.timezone(TZ)
    today = datetime.now(tz).date()
    target_date = today - timedelta(days=1)
    users = db.get_all_users()
    if not BOT_TOKEN:
        return
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    for user_id in users:
        if food_service.is_day_closed(user_id, target_date):
            continue
        profile = user_service.get_profile(user_id)
        if not profile:
            continue
        totals = food_service.get_totals_for_date(user_id, target_date)
        if not totals:
            continue
        text = calc.format_daily_report(profile, totals)
        await bot.send_message(chat_id=user_id, text=text)
        food_service.mark_day_closed(user_id, target_date)
    await bot.session.close()


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TZ)
    scheduler.add_job(send_daily_reports, "cron", hour=3, minute=0)
    return scheduler
