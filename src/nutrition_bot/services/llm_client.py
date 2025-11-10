"""Wrapper around the LLM API. For now uses heuristic parsing."""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from ..config import LLM_API_KEY, SYSTEM_PROMPT
from .templates import resolve_template

_NUMBER_RE = re.compile(r"(?P<name>[\wёЁа-яА-Я\s]+?)\s*(?P<grams>\d+(?:[.,]\d+)?)\b")


class LLMError(RuntimeError):
    pass


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).lower()


def ask_llm(*, user_state, message_text: Optional[str] = None, ocr_text: Optional[str] = None, mode: str = "parse_food") -> Dict[str, Any]:
    _ = LLM_API_KEY  # placeholders for future real API usage
    _ = SYSTEM_PROMPT
    text = (message_text or "").strip()
    if mode != "parse_food":
        return {"reply": "Пока умею только разбирать еду.", "foods": []}
    if not text:
        return {"reply": "Нужен текст с описанием блюда.", "foods": []}

    templates = getattr(user_state, "templates", {}) or {}
    foods: list[dict[str, Any]] = []
    for match in _NUMBER_RE.finditer(text):
        name = _normalize_name(match.group("name"))
        grams = float(match.group("grams").replace(",", "."))
        template = templates.get(name)
        if not template and getattr(user_state, "profile", None):
            template = resolve_template(user_state.profile.user_id, name)
        if template:
            ratio = grams / template["grams"] if template.get("grams") else 0
            foods.append(
                {
                    "name": template["name"],
                    "grams": grams,
                    "kcal": template["kcal"] * ratio,
                    "protein": template["protein"] * ratio,
                    "fat": template["fat"] * ratio,
                    "carb": template["carb"] * ratio,
                }
            )
        else:
            foods.append(
                {
                    "name": name,
                    "grams": grams,
                    "kcal": grams * 1.2,
                    "protein": grams * 0.05,
                    "fat": grams * 0.04,
                    "carb": grams * 0.1,
                }
            )

    need_clarify = False
    reply: Optional[str] = None
    if not foods:
        need_clarify = True
        reply = "Не понял блюдо, укажи название и граммы, например: 'курица 150'."
    else:
        total_kcal = sum(item["kcal"] for item in foods)
        total_p = sum(item["protein"] for item in foods)
        total_f = sum(item["fat"] for item in foods)
        total_c = sum(item["carb"] for item in foods)
        reply = (
            "Добавил: "
            + ", ".join(f"{item['name']} {item['grams']:.0f} г" for item in foods)
            + f" — {total_kcal:.0f} ккал, Б: {total_p:.0f}, Ж: {total_f:.0f}, У: {total_c:.0f}."
        )
    return {"foods": foods, "reply": reply, "need_clarify": need_clarify}
