"""Calorie and macro calculations plus formatting helpers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class DailyTotals:
    """Aggregate macros for a day."""

    date: date
    kcal: float = 0.0
    protein: float = 0.0
    fat: float = 0.0
    carb: float = 0.0


@dataclass(slots=True)
class DailyTargets:
    """Target macros for a user."""

    kcal: float
    protein: float
    fat: float
    carb: float


def mifflin_st_jeor(weight: float, height: float, age: int, gender: str) -> float:
    gender = gender.lower()
    if gender in {"м", "муж", "male", "m"}:
        offset = 5
    else:
        offset = -161
    return 10 * weight + 6.25 * height - 5 * age + offset


def activity_multiplier(activity: str) -> float:
    activity = activity.lower().strip()
    mapping = {
        "низкая": 1.2,
        "минимальная": 1.2,
        "сидячая": 1.2,
        "умеренная": 1.375,
        "средняя": 1.55,
        "высокая": 1.725,
        "очень высокая": 1.9,
    }
    return mapping.get(activity, 1.375)


def goal_adjustment(goal: str) -> float:
    goal = goal.lower()
    if "похуд" in goal:
        return 0.85
    if "набор" in goal or "масса" in goal:
        return 1.15
    return 1.0


def calculate_targets(*, weight: float, height: float, age: int, gender: str, goal: str, activity: str) -> DailyTargets:
    bmr = mifflin_st_jeor(weight, height, age, gender)
    multiplier = activity_multiplier(activity) * goal_adjustment(goal)
    kcal = bmr * multiplier
    protein = kcal * 0.3 / 4
    fat = kcal * 0.3 / 9
    carb = kcal * 0.4 / 4
    return DailyTargets(kcal=kcal, protein=protein, fat=fat, carb=carb)


def colorize(value: float, norm: float | None, label: str) -> str:
    if not norm:
        return f"{label}: {value:.0f}"
    diff = value - norm
    diff_abs = abs(diff)
    perc = diff_abs / norm if norm else 0
    if perc <= 0.10:
        mark = "🟢"
    elif diff < 0:
        mark = "🟡"
    else:
        mark = "🔴"
    sign = "+" if diff > 0 else "-"
    if diff == 0:
        delta_str = "0"
    else:
        delta_str = f"{sign}{diff_abs:.0f}"
    return f"{mark} <b>{label}:</b> {value:.0f} / {norm:.0f} ({delta_str})"


def format_summary(profile, totals: DailyTotals, *, with_status: bool = False) -> str:
    base = [
        f"Калории: {totals.kcal:.0f} / {profile.norm_kcal:.0f}",
        f"Белки: {totals.protein:.0f} / {profile.norm_p:.0f}",
        f"Жиры: {totals.fat:.0f} / {profile.norm_f:.0f}",
        f"Углеводы: {totals.carb:.0f} / {profile.norm_c:.0f}",
    ]
    if with_status:
        base = [
            colorize(totals.kcal, profile.norm_kcal, "Калории"),
            colorize(totals.protein, profile.norm_p, "Белки"),
            colorize(totals.fat, profile.norm_f, "Жиры"),
            colorize(totals.carb, profile.norm_c, "Углеводы"),
        ]
    return "\n".join(base)


def make_short_advice(profile, totals: DailyTotals) -> str:
    diffs = {
        "белок": totals.protein - profile.norm_p,
        "жиры": totals.fat - profile.norm_f,
        "углеводы": totals.carb - profile.norm_c,
    }
    largest = max(diffs.items(), key=lambda item: abs(item[1]))
    metric, value = largest
    if abs(value) < profile.norm_kcal * 0.05:
        return "Баланс отличный, так держать 👍"
    if value < 0:
        if metric == "белок":
            return "Сегодня не добрал белок — добавь мясо, рыбу или творог.".strip()
        if metric == "жиры":
            return "Немного не хватило жиров — можно добавить орехи или масло.".strip()
        return "Мало углеводов — завтра добавь крупы, фрукты или хлеб.".strip()
    if metric == "жиры":
        return "Чуть перебор по жирам, сократи жирные соусы и выпечку.".strip()
    if metric == "белок":
        return "Перебор по белку — можно уменьшить порции мяса.".strip()
    return "Многовато углеводов, попробуй уменьшить сладкое и хлеб.".strip()


def format_daily_report(profile, totals: DailyTotals) -> str:
    lines = [
        "📅 Итоги за {}".format(totals.date.strftime("%d.%m.%Y")),
        "",
        colorize(totals.kcal, profile.norm_kcal, "Калории"),
        colorize(totals.protein, profile.norm_p, "Белки"),
        colorize(totals.fat, profile.norm_f, "Жиры"),
        colorize(totals.carb, profile.norm_c, "Углеводы"),
        "",
        f"💡 {make_short_advice(profile, totals)}",
    ]
    return "\n".join(lines).strip()
