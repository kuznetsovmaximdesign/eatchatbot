"""/start command and onboarding flow."""
from __future__ import annotations

from aiogram import F
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..keyboards import main_kb
from ..services import user_service

router = Router()


class ProfileStates(StatesGroup):
    gender = State()
    age = State()
    height = State()
    weight = State()
    goal = State()
    activity = State()


def _parse_value(field: str, text: str):
    text = text.strip()
    if field in {"age"}:
        return int(text)
    if field in {"height", "weight"}:
        return float(text.replace(",", "."))
    return text.lower()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext) -> None:
    user_service.set_step(message.from_user.id, "gender")
    await state.set_state(ProfileStates.gender)
    await message.answer(
        "Привет! Я помогу тебе считать питание и КБЖУ.\n"
        "Давай настроим профиль.\n"
        "Укажи, пожалуйста, пол (м/ж)."
    )


@router.message(ProfileStates.gender)
async def handle_gender(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    if not text:
        await message.answer("Не совсем понял, повтори, пожалуйста.")
        return

    try:
        value = _parse_value("gender", text)
    except Exception:
        await message.answer("Не совсем понял, повтори, пожалуйста.")
        return

    user_service.update_pending(user_id, "gender", value)
    user_service.set_step(user_id, "age")
    await state.set_state(ProfileStates.age)
    await message.answer("Теперь укажи свой возраст:")


@router.message(ProfileStates.age)
async def handle_age(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    try:
        value = _parse_value("age", text)
    except Exception:
        await message.answer("Укажи возраст числом, пожалуйста.")
        return

    user_service.update_pending(user_id, "age", value)
    user_service.set_step(user_id, "height")
    await state.set_state(ProfileStates.height)
    await message.answer("Какой у тебя рост в сантиметрах?")


@router.message(ProfileStates.height)
async def handle_height(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    try:
        value = _parse_value("height", text)
    except Exception:
        await message.answer("Напиши рост числом, пожалуйста.")
        return

    user_service.update_pending(user_id, "height", value)
    user_service.set_step(user_id, "weight")
    await state.set_state(ProfileStates.weight)
    await message.answer("Какой у тебя вес в килограммах?")


@router.message(ProfileStates.weight)
async def handle_weight(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    try:
        value = _parse_value("weight", text)
    except Exception:
        await message.answer("Укажи вес числом, пожалуйста.")
        return

    user_service.update_pending(user_id, "weight", value)
    user_service.set_step(user_id, "goal")
    await state.set_state(ProfileStates.goal)
    await message.answer("Какова цель: похудение, поддержание или набор?")


@router.message(ProfileStates.goal)
async def handle_goal(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    if not text:
        await message.answer("Повтори, пожалуйста, цель: похудение, поддержание или набор.")
        return

    value = _parse_value("goal", text)
    user_service.update_pending(user_id, "goal", value)
    user_service.set_step(user_id, "activity")
    await state.set_state(ProfileStates.activity)
    await message.answer("Какой уровень активности (низкая, умеренная, высокая)?")


@router.message(ProfileStates.activity)
async def handle_activity(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    if not text:
        await message.answer("Напиши уровень активности, пожалуйста.")
        return

    value = _parse_value("activity", text)
    user_service.update_pending(user_id, "activity", value)
    profile = user_service.save_profile(user_id, {"activity": value})

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
    await state.clear()
