"""Food parsing handler."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..keyboards import main_kb
from ..services import food_service, llm_client, user_service

router = Router()


@router.message(Command(commands=["help", "summary", "close", "start"]))
async def skip_here(_: Message) -> None:
    return


@router.message()
async def handle_food(message: Message) -> None:
    text = (message.text or "").strip()
    user_id = message.from_user.id

    if text == "📊 Текущие итоги":
        from .summary import send_current_summary

        await send_current_summary(message)
        return
    if text == "✅ Подвести итог дня":
        from .summary import close_day_and_send

        await close_day_and_send(message)
        return
    if text == "ℹ️ Справка":
        from .help import send_help

        await send_help(message)
        return

    user_state = user_service.get_state(user_id)
    if not user_state.profile:
        await message.answer("Сначала нужно заполнить профиль через /start.")
        return

    parsed = llm_client.ask_llm(user_state=user_state, message_text=text, mode="parse_food")
    if parsed.get("need_clarify"):
        await message.answer(parsed.get("reply"))
        return

    foods = parsed.get("foods", [])
    if not foods:
        await message.answer("Похоже, это не еда. Напиши, например: 'овсянка 150'.")
        return

    known_templates = {name.lower(): data for name, data in (user_state.templates or {}).items()}
    new_templates: list[str] = []
    additions: list[str] = []
    for item in foods:
        food_service.add_food(user_id, item)
        name = (item.get("name") or "").strip()
        grams = item.get("grams", 0)
        additions.append(
            f"{name} {grams:.0f} г — {item.get('kcal', 0):.0f} ккал, "
            f"Б: {item.get('protein', 0):.0f}, Ж: {item.get('fat', 0):.0f}, У: {item.get('carb', 0):.0f}"
        )
        key = name.lower()
        if key and key not in known_templates and grams:
            known_templates[key] = item
            new_templates.append(name)

    totals = food_service.get_today_totals(user_id)
    reply_lines = [
        "✅ Добавил: " + "; ".join(additions),
        (
            "Итого за сегодня: "
            f"{totals.kcal:.0f} ккал, Б: {totals.protein:.0f}, Ж: {totals.fat:.0f}, У: {totals.carb:.0f}."
        ),
    ]
    if new_templates:
        quoted = ", ".join(f"«{name}»" for name in new_templates)
        reply_lines.append(f"Запомнил {quoted}, в следующий раз посчитаю автоматически 👍")

    await message.answer("\n".join(reply_lines), reply_markup=main_kb)
