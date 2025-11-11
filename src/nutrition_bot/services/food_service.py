"""Food logging service."""
from __future__ import annotations

from datetime import date
from typing import Dict, Optional

from ..storage import db
from . import calc
from .templates import remember_template


def add_food(user_id: int, item: Dict[str, float]) -> None:
    db.store_meal(user_id, item)
    remember_template(user_id, item)


def get_today_totals(user_id: int) -> calc.DailyTotals:
    today = date.today()
    data = db.get_totals(user_id, today)
    totals = calc.DailyTotals(date=today)
    if data:
        totals.kcal = data.get("kcal", 0.0) or 0.0
        totals.protein = data.get("protein", 0.0) or 0.0
        totals.fat = data.get("fat", 0.0) or 0.0
        totals.carb = data.get("carb", 0.0) or 0.0
    return totals


def get_totals_for_date(user_id: int, day: date) -> Optional[calc.DailyTotals]:
    data = db.get_totals(user_id, day)
    if not data:
        return None
    totals = calc.DailyTotals(date=day)
    totals.kcal = data.get("kcal", 0.0) or 0.0
    totals.protein = data.get("protein", 0.0) or 0.0
    totals.fat = data.get("fat", 0.0) or 0.0
    totals.carb = data.get("carb", 0.0) or 0.0
    return totals


def close_today(user_id: int) -> None:
    today = date.today()
    db.mark_day_closed(user_id, today)


def mark_day_closed(user_id: int, day: date) -> None:
    db.mark_day_closed(user_id, day)


def is_day_closed(user_id: int, day: date) -> bool:
    return db.is_day_closed(user_id, day)
