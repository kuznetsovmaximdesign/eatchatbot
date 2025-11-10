"""Food parsing handler with offline DB and LLM fallback."""
from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Iterable, List, Tuple

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from .. import llm_client, product_db
from ..keyboards import main_kb
from ..services import food_service, user_service
from ..services.templates import resolve_template

router = Router()


_FOOD_RE = re.compile(
    r"(?P<name>[\wёЁа-яА-Я\s\-,'"]+?)\s*(?P<grams>\d+(?:[.,]\d+)?)\s*(?:г|гр|грамм|ml|мл|кг|kg)?\b",
    re.IGNORECASE,
)


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).lower()


def _format_food_line(item: dict) -> str:
    grams = item.get("grams", 0)
    return (
        f"{item.get('name', 'блюдо')} {grams:.0f} г — {item.get('kcal', 0):.0f} ккал, "
        f"Б: {item.get('protein', 0):.0f}, Ж: {item.get('fat', 0):.0f}, У: {item.get('carb', 0):.0f}"
    )


def _item_from_product(name: str, grams: float, macros: dict) -> dict:
    factor = grams / 100.0
    return {
        "name": name,
        "grams": grams,
        "kcal": macros.get("kcal", 0) * factor,
        "protein": macros.get("protein", 0) * factor,
        "fat": macros.get("fat", 0) * factor,
        "carb": macros.get("carb", 0) * factor,
    }


def _item_from_template(template: dict, grams: float | None) -> dict | None:
    base_grams = template.get("grams") or grams
    if not base_grams:
        return None
    grams = grams or base_grams
    ratio = grams / base_grams if base_grams else 1.0
    return {
        "name": template.get("name") or "блюдо",
        "grams": grams,
        "kcal": (template.get("kcal") or 0) * ratio,
        "protein": (template.get("protein") or 0) * ratio,
        "fat": (template.get("fat") or 0) * ratio,
        "carb": (template.get("carb") or 0) * ratio,
    }


def _parse_segments(text: str) -> list[Tuple[str, float]]:
    segments: list[Tuple[str, float]] = []
    for match in _FOOD_RE.finditer(text):
        name = (match.group("name") or "").strip()
        grams_str = match.group("grams") or "0"
        try:
            grams = float(grams_str.replace(",", "."))
        except ValueError:
            continue
        if grams <= 0:
            continue
        cleaned = re.sub(r"[+,:;]+$", "", name).strip()
        if cleaned:
            segments.append((cleaned, grams))
    return segments


async def _persist_and_reply(message: Message, foods: List[dict]) -> None:
    if not foods:
        await message.answer("Похоже, это не еда. Напиши, например: 'овсянка 150'.")
        return

    user_id = message.from_user.id
    for item in foods:
        food_service.add_food(user_id, item)

    totals = food_service.get_today_totals(user_id)
    reply_lines = [
        "✅ Добавил: " + "; ".join(_format_food_line(item) for item in foods),
        (
            "Итого за сегодня: "
            f"{totals.kcal:.0f} ккал, Б: {totals.protein:.0f}, Ж: {totals.fat:.0f}, У: {totals.carb:.0f}."
        ),
    ]
    await message.answer("\n".join(reply_lines), reply_markup=main_kb)


@router.message(Command(commands=["help", "summary", "close", "start"]))
async def skip_here(_: Message) -> None:
    return


async def _process_segments(
    segments: Iterable[Tuple[str, float]],
    templates_cache: dict[str, dict],
) -> tuple[list[dict], bool, str]:
    foods: list[dict] = []
    for name, grams in segments:
        normalized = _normalize_name(name)
        template = templates_cache.get(normalized)
        if template:
            item = _item_from_template(template, grams)
            if item:
                foods.append(item)
                continue

        product = product_db.find_product(name)
        if product:
            foods.append(_item_from_product(name, grams, product))
            continue

        llm_text = f"{name} {grams:.0f}".strip()
        result = llm_client.estimate_foods(llm_text, grams_hint=int(grams))
        if result.get("need_clarify"):
            question = result.get("clarify_question") or "Уточни, пожалуйста, состав и массу блюда."
            return [], True, question
        foods.extend(result.get("foods", []))
    return foods, False, ""


@router.message(F.photo)
async def handle_photo(message: Message) -> None:
    user_id = message.from_user.id
    user_state = user_service.get_state(user_id)
    if not user_state.profile:
        await message.answer("Сначала нужно заполнить профиль через /start.")
        return

    photo = message.photo[-1]
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / f"{photo.file_unique_id}.jpg"
        await photo.download(destination=temp_path)
        caption = (message.caption or "").strip() or "Фото продукта"
        result = llm_client.estimate_foods(caption, image_path=temp_path)

    if result.get("need_clarify"):
        question = result.get("clarify_question") or "Сфотографируй таблицу КБЖУ ближе, пожалуйста."
        await message.answer(question)
        return

    foods = result.get("foods", [])
    await _persist_and_reply(message, foods)


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

    templates_cache = {name: data for name, data in (user_state.templates or {}).items()}
    segments = _parse_segments(text)

    if segments:
        foods, need_clarify, question = await _process_segments(segments, templates_cache)
        if need_clarify:
            await message.answer(question)
            return
    else:
        template = resolve_template(user_id, _normalize_name(text)) if text else None
        if template:
            item = _item_from_template(template, None)
            foods = [item] if item else []
        else:
            result = llm_client.estimate_foods(text)
            if result.get("need_clarify"):
                question = result.get("clarify_question") or "Напиши название блюда и массу порции."
                await message.answer(question)
                return
            foods = result.get("foods", [])

    await _persist_and_reply(message, foods)
