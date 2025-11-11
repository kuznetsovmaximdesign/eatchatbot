"""Application configuration helpers for the nutrition tracker bot."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - fallback for environments without python-dotenv
    from dotenv import load_dotenv  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency for tests
    def load_dotenv(*_: object, **__: object) -> bool:
        return False


def _read_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Return a trimmed environment variable value."""

    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


load_dotenv()

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "system_prompt.txt"
SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8") if _PROMPT_PATH.exists() else ""


@dataclass(slots=True)
class Settings:
    """Runtime configuration values loaded from environment/.env."""

    bot_token: str
    tz: str
    openai_api_key: Optional[str]
    openai_model: Optional[str]
    openai_base_url: Optional[str]
    fatsecret_key: Optional[str]
    fatsecret_secret: Optional[str]


@lru_cache(maxsize=1)
def get_settings(validate_bot_token: bool = True) -> Settings:
    """Load settings from environment with optional BOT_TOKEN validation."""

    bot_token = _read_env("BOT_TOKEN", "")
    if validate_bot_token and not bot_token:
        raise RuntimeError(
            "BOT_TOKEN не найден. Создай файл .env с BOT_TOKEN=... или экспортируй переменную окружения."
        )
    return Settings(
        bot_token=bot_token,
        tz=_read_env("TZ", "Europe/Moscow") or "Europe/Moscow",
        openai_api_key=_read_env("OPENAI_API_KEY"),
        openai_model=_read_env("OPENAI_MODEL"),
        openai_base_url=_read_env("OPENAI_BASE_URL"),
        fatsecret_key=_read_env("FATSECRET_KEY"),
        fatsecret_secret=_read_env("FATSECRET_SECRET"),
    )


def require_bot_token() -> str:
    """Return BOT_TOKEN or raise a descriptive error if it is missing."""

    token = get_settings(validate_bot_token=True).bot_token
    if not token:
        raise RuntimeError("BOT_TOKEN не настроен. Добавь его в .env перед запуском бота.")
    return token


def get_timezone() -> str:
    """Return configured timezone (defaults to Europe/Moscow)."""

    settings = get_settings(validate_bot_token=False)
    return settings.tz or "Europe/Moscow"
