"""Auto-summary scheduler."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from ..storage import db
from . import calc, food_service, user_service


async def send_daily_reports(bot: Bot, tz: str) -> None:
    """Send daily reports for the previous day to all active users."""

    tzinfo = pytz.timezone(tz)
    today = datetime.now(tzinfo).date()
    target_date = today - timedelta(days=1)
    users = db.get_all_users()
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


def setup_scheduler(*, bot: Bot, tz: str) -> AsyncIOScheduler:
    """Configure and return scheduler instance bound to bot and timezone."""

    scheduler = AsyncIOScheduler(timezone=tz)
    scheduler.add_job(send_daily_reports, "cron", hour=3, minute=0, args=(bot, tz))
    return scheduler
