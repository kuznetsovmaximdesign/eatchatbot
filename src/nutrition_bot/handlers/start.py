"""/start command and onboarding flow."""
from __future__ import annotations

from aiogram import F
from aiogram import Router
from aiogram.exceptions import SkipHandler
from aiogram.types import Message

from ..keyboards import main_kb
from ..services import user_service

router = Router()


PROFILE_FIELDS = [
    ("gender", "Укажи, пожалуйста, пол (м/ж)."),
    ("age", "Сколько тебе лет?"),
    ("height", "Какой у тебя рост в сантиметрах?"),
    ("weight", "Какой вес в килограммах?"),
    ("goal", "Какова цель: похудение, поддержание или набор?"),
    ("activity", "Какой уровень активности (низкая, умеренная, высокая)?"),
]


def _parse_value(field: str, text: str):
    text = text.strip()
    if field in {"age"}:
        return int(text)
    if field in {"height", "weight"}:
        return float(text.replace(",", "."))
    return text.lower()


@router.message(F.text == "/start")
async def cmd_start(message: Message) -> None:
    user_service.set_step(message.from_user.id, "gender")
    await message.answer(
        "Привет! Я помогу тебе считать питание и КБЖУ.\n"
        "Давай настроим профиль.\n"
        "Укажи, пожалуйста, пол (м/ж)."
    )


@router.message()
async def fill_profile(message: Message) -> None:
    user_id = message.from_user.id
    step = user_service.get_step(user_id)
    if not step:
        raise SkipHandler()
    text = (message.text or "").strip()
    try:
        value = _parse_value(step, text)
    except Exception:
        await message.answer("Не совсем понял, повтори, пожалуйста.")
        return

    user_service.update_pending(user_id, step, value)
    pending = user_service.get_pending(user_id)

    next_index = next((i for i, (field, _) in enumerate(PROFILE_FIELDS) if field == step), len(PROFILE_FIELDS) - 1)
    if step == "activity":
        profile = user_service.save_profile(user_id, pending)
        summary = (
            f"Готово! Вот твои ориентиры:\n"
            f"Калории: {profile.norm_kcal:.0f}\n"
            f"Белки: {profile.norm_p:.0f} г\n"
            f"Жиры: {profile.norm_f:.0f} г\n"
            f"Углеводы: {profile.norm_c:.0f} г\n"
            "Это ориентировочные значения, не медицинские рекомендации."
        )
        await message.answer(summary, reply_markup=main_kb)
        user_service.set_step(user_id, None)
        return

    next_field, prompt = PROFILE_FIELDS[next_index + 1]
    user_service.set_step(user_id, next_field)
    await message.answer(prompt)
