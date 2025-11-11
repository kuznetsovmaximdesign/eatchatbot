"""/start command and onboarding flow."""
from __future__ import annotations

from aiogram import F
from aiogram import Router


from ..keyboards import main_kb
from ..services import user_service

router = Router()





def _parse_value(field: str, text: str):
    text = text.strip()
    if field in {"age"}:
        return int(text)
    if field in {"height", "weight"}:
        return float(text.replace(",", "."))
    return text.lower()


@router.message(F.text == "/start")

    await message.answer(
        "Привет! Я помогу тебе считать питание и КБЖУ.\n"
        "Давай настроим профиль.\n"
        "Укажи, пожалуйста, пол (м/ж)."
    )



