"""User profile management service."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from ..storage import db
from . import calc


_PENDING_DATA: dict[int, Dict[str, Any]] = {}


@dataclass(slots=True)
class UserProfile:
    user_id: int
    gender: str
    age: int
    height: float
    weight: float
    goal: str
    activity: str
    norm_kcal: float
    norm_p: float
    norm_f: float
    norm_c: float


@dataclass(slots=True)
class UserState:
    profile: Optional[UserProfile]
    templates: Dict[str, dict]
    recent_meals: list[dict]


def set_step(user_id: int, step: Optional[str]) -> None:
    db.update_step(user_id, step)
    

def get_step(user_id: int) -> Optional[str]:
    row = db.fetch_one("SELECT step FROM users WHERE user_id=?", (user_id,))
    return row["step"] if row else None


def save_profile(user_id: int, data: Dict[str, Any]) -> UserProfile:
    pending = _PENDING_DATA.get(user_id, {})
    pending.update(data)
    data = pending
    targets = calc.calculate_targets(
        weight=data["weight"],
        height=data["height"],
        age=data["age"],
        gender=data["gender"],
        goal=data["goal"],
        activity=data["activity"],
    )
    payload = {
        "gender": data["gender"],
        "age": data["age"],
        "height": data["height"],
        "weight": data["weight"],
        "goal": data["goal"],
        "activity": data["activity"],
        "norm_kcal": targets.kcal,
        "norm_p": targets.protein,
        "norm_f": targets.fat,
        "norm_c": targets.carb,
        "step": None,
    }
    db.upsert_user(user_id, payload)
    _PENDING_DATA.pop(user_id, None)
    return UserProfile(
        user_id=user_id,
        gender=payload["gender"],
        age=payload["age"],
        height=payload["height"],
        weight=payload["weight"],
        goal=payload["goal"],
        activity=payload["activity"],
        norm_kcal=payload["norm_kcal"],
        norm_p=payload["norm_p"],
        norm_f=payload["norm_f"],
        norm_c=payload["norm_c"],
    )


def get_profile(user_id: int) -> Optional[UserProfile]:
    row = db.fetch_one(
        "SELECT user_id, gender, age, height, weight, goal, activity, norm_kcal, norm_p, norm_f, norm_c FROM users WHERE user_id=?",
        (user_id,),
    )
    if not row:
        return None
    return UserProfile(
        user_id=row["user_id"],
        gender=row["gender"],
        age=row["age"],
        height=row["height"],
        weight=row["weight"],
        goal=row["goal"],
        activity=row["activity"],
        norm_kcal=row["norm_kcal"],
        norm_p=row["norm_p"],
        norm_f=row["norm_f"],
        norm_c=row["norm_c"],
    )


def get_state(user_id: int) -> UserState:
    profile = get_profile(user_id)
    templates = db.load_templates(user_id)
    meals = db.list_meals_for_day(user_id, date.today()) if profile else []
    return UserState(profile=profile, templates=templates, recent_meals=meals)


def update_pending(user_id: int, field: str, value: Any) -> None:
    data = _PENDING_DATA.setdefault(user_id, {})
    data[field] = value


def get_pending(user_id: int) -> Dict[str, Any]:
    return dict(_PENDING_DATA.get(user_id, {}))
