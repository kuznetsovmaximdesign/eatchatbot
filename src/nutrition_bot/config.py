"""Application configuration for the nutrition tracker bot."""
from __future__ import annotations

import os
from pathlib import Path

BOT_TOKEN: str | None = os.getenv("BOT_TOKEN")
LLM_API_KEY: str | None = os.getenv("LLM_API_KEY")
TZ: str = os.getenv("BOT_TZ", "Europe/Moscow")

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "system_prompt.txt"

if _PROMPT_PATH.exists():
    SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")
else:
    SYSTEM_PROMPT = ""
