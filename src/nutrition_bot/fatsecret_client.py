"""FatSecret API client for fetching nutrition data."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from types import SimpleNamespace

try:  # pragma: no cover - allow running without requests in minimal environments
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for tests without dependency
    def _missing_request(*_: object, **__: object) -> None:
        raise RuntimeError("Библиотека 'requests' не установлена. Установи зависимости проекта.")

    requests = SimpleNamespace(post=_missing_request, get=_missing_request)  # type: ignore

from .config import get_settings


logger = logging.getLogger(__name__)

TOKEN_URL = "https://oauth.fatsecret.com/connect/token"
API_URL = "https://platform.fatsecret.com/rest/server.api"

_token_cache: dict[str, Any] | None = None


def _get_credentials() -> Optional[tuple[str, str]]:
    settings = get_settings(validate_bot_token=False)
    if not settings.fatsecret_key or not settings.fatsecret_secret:
        return None
    return settings.fatsecret_key, settings.fatsecret_secret


def _obtain_token() -> Optional[dict[str, Any]]:
    creds = _get_credentials()
    if not creds:
        logger.debug("FatSecret credentials are not configured; skipping API call")
        return None

    key, secret = creds
    data = {"grant_type": "client_credentials", "scope": "basic"}
    try:
        resp = requests.post(TOKEN_URL, data=data, auth=(key, secret), timeout=30)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as exc:  # pragma: no cover - network failure path
        logger.error("Не удалось получить токен FatSecret: %s", exc)
        return None

    payload["obtained_at"] = time.time()
    return payload


def _get_token() -> Optional[str]:
    global _token_cache
    if _token_cache:
        expires_in = float(_token_cache.get("expires_in", 0))
        obtained_at = float(_token_cache.get("obtained_at", 0))
        if time.time() < obtained_at + max(expires_in - 60, 0):
            return _token_cache.get("access_token")

    _token_cache = _obtain_token()
    if not _token_cache:
        return None
    return _token_cache.get("access_token")


def _api_request(params: Dict[str, Any]) -> Optional[dict[str, Any]]:
    token = _get_token()
    if not token:
        return None

    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(API_URL, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:  # pragma: no cover - network failure path
        logger.error("Ошибка FatSecret API (%s): %s", params.get("method"), exc)
        return None


def _choose_serving(servings: Any) -> Optional[dict[str, Any]]:
    if isinstance(servings, dict) and "serving" in servings:
        servings = servings["serving"]
    if isinstance(servings, dict):
        candidates = [servings]
    else:
        candidates = list(servings or [])
    for serving in candidates:
        unit = str(serving.get("metric_serving_unit", "")).lower()
        amount = float(serving.get("metric_serving_amount", 0) or 0)
        if unit in {"g", "ml"} and amount > 0:
            return serving
    return candidates[0] if candidates else None


def _macros_from_serving(serving: dict[str, Any]) -> Optional[dict[str, float]]:
    try:
        amount = float(serving.get("metric_serving_amount", 0) or 0)
    except (TypeError, ValueError):
        amount = 0.0
    unit = str(serving.get("metric_serving_unit", "")).lower()

    if amount <= 0:
        try:
            amount = float(serving.get("serving_weight_grams", 0) or 0)
            unit = "g"
        except (TypeError, ValueError):
            amount = 0.0

    if amount <= 0:
        return None

    factor = 100.0 / amount

    def _to_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    return {
        "kcal": _to_float(serving.get("calories")) * factor,
        "protein": _to_float(serving.get("protein")) * factor,
        "fat": _to_float(serving.get("fat")) * factor,
        "carb": _to_float(serving.get("carbohydrate")) * factor,
    }


def get_macros_for_product(name: str) -> Optional[dict[str, float]]:
    """Fetch macros for a product name from FatSecret API."""

    if not name:
        return None

    search_params = {
        "method": "foods.search",
        "format": "json",
        "search_expression": name,
        "max_results": 1,
    }
    search_data = _api_request(search_params)
    if not search_data:
        return None

    foods = search_data.get("foods", {})
    food = foods.get("food") if isinstance(foods, dict) else None
    if isinstance(food, list):
        food = food[0] if food else None
    if not food:
        return None

    food_id = food.get("food_id")
    if not food_id:
        return None

    detail_params = {
        "method": "food.get",
        "format": "json",
        "food_id": food_id,
    }
    detail_data = _api_request(detail_params)
    if not detail_data:
        return None

    servings = detail_data.get("food", {}).get("servings")
    serving = _choose_serving(servings)
    if not serving:
        return None

    macros = _macros_from_serving(serving)
    if not macros:
        return None

    logger.debug("FatSecret matched '%s' -> %s", name, macros)
    return macros
