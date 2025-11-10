"""Daily summary handlers."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from ..services import calc, food_service, user_service

router = Router()


@router.message(Command("summary"))
@router.message(F.text.casefold() == "📊 текущие итоги".casefold())
async def summary_command(message: Message) -> None:
    await send_current_summary(message)


async def send_current_summary(message: Message) -> None:
    user_id = message.from_user.id
    profile = user_service.get_profile(user_id)
    if not profile:
        await message.answer("Сначала заполни профиль через /start.")
        return
    totals = food_service.get_today_totals(user_id)
    text = calc.format_summary(profile, totals, with_status=True)
    await message.answer(text, parse_mode="HTML")


async def close_day_and_send(message: Message) -> None:
    user_id = message.from_user.id
    profile = user_service.get_profile(user_id)
    if not profile:
        await message.answer("Сначала заполни профиль через /start.")
        return
    totals = food_service.get_today_totals(user_id)
    food_service.close_today(user_id)
    text = calc.format_daily_report(profile, totals)
    await message.answer(text, parse_mode="HTML")


@router.message(Command("close"))
@router.message(F.text.casefold() == "✅ подвести итог дня".casefold())
async def close_command(message: Message) -> None:
    await close_day_and_send(message)
