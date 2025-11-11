"""Service to manage remembered dishes."""
from __future__ import annotations

from typing import Dict, Optional

from ..storage import db


def get_templates(user_id: int) -> Dict[str, dict]:
    return db.load_templates(user_id)


def remember_template(user_id: int, item: dict) -> None:
    if not item.get("name"):
        return
    macros = [item.get("kcal"), item.get("protein"), item.get("fat"), item.get("carb")]
    if not any((value or 0) for value in macros):
        return
    db.upsert_template(user_id, item)


def resolve_template(user_id: int, name: str) -> Optional[dict]:
    templates = get_templates(user_id)
    return templates.get(name.lower())
