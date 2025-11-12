"""Client for the nutrition LLM fallback."""
from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from types import SimpleNamespace

try:  # pragma: no cover - exercised implicitly when dependency present
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for test envs without requests
    def _missing_post(*_: Any, **__: Any) -> None:
        raise RuntimeError(
            "Библиотека 'requests' не установлена. Добавь её в окружение или установи пакет."
        )

    requests = SimpleNamespace(post=_missing_post)  # type: ignore

try:  # pragma: no cover - fallback mirrors python-dotenv interface
    from dotenv import load_dotenv  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency in some envs
    def load_dotenv(*_: Any, **__: Any) -> bool:
        """Stubbed loader when python-dotenv отсутствует."""

        return False


logger = logging.getLogger(__name__)


load_dotenv()


_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "system_prompt.txt"
_SYSTEM_PROMPT = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Укажи желаемую модель в .env через OPENAI_MODEL, например: gpt-4o-mini или gpt-4.1
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")


def _default_response() -> Dict[str, Any]:
    return {
        "foods": [],
        "need_clarify": True,
        "clarify_question": "Не понял блюдо, напиши название и граммы, например: 'курица 150'.",
        "templates_to_update": [],
    }


def _headers() -> Dict[str, str]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY не задан. Укажи его в .env")
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }


def _build_user_content(message_text: Optional[str], grams_hint: Optional[int], image_path: Optional[Path]) -> list[dict]:
    content: list[dict[str, Any]] = []
    if message_text:
        hint_text = message_text.strip()
        if grams_hint:
            hint_text += f"\nПодсказка по массе: {grams_hint} г."
        content.append({"type": "text", "text": hint_text})
    if image_path:
        image_bytes = image_path.read_bytes()
        content.append(
            {
                "type": "input_image",
                "image_base64": base64.b64encode(image_bytes).decode("ascii"),
            }
        )
    return content


def _extract_text(payload: Dict[str, Any]) -> str:
    if "output_text" in payload:
        return str(payload["output_text"]).strip()
    output = payload.get("output", [])
    for block in output:
        for chunk in block.get("content", []):
            text = chunk.get("text")
            if text:
                return str(text).strip()
    choices = payload.get("choices")
    if choices:
        for choice in choices:
            message = choice.get("message")
            if message and isinstance(message.get("content"), str):
                return message["content"].strip()
    return ""


def estimate_foods(
    message_text: Optional[str],
    grams_hint: Optional[int] = None,
    *,
    image_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Call the LLM to estimate foods when local DB is insufficient."""

    try:
        headers = _headers()
    except RuntimeError as exc:
        logger.warning("LLM disabled: %s", exc)
        response = _default_response()
        response["clarify_question"] = "Нужно настроить ключ LLM, сейчас не могу распознать блюдо."
        return response

    content = _build_user_content(message_text, grams_hint, image_path)
    if not content:
        return _default_response()

    body = {
        "model": OPENAI_MODEL,
        "input": [
            {"role": "system", "content": [{"type": "text", "text": _SYSTEM_PROMPT}]},
            {"role": "user", "content": content},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }

    url = f"{OPENAI_BASE_URL}/responses"
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        text = _extract_text(payload)
        if not text:
            logger.warning("LLM вернул пустой ответ: %s", payload)
            return _default_response()
        data = json.loads(text)
    except requests.RequestException as exc:
        logger.error("Ошибка вызова LLM: %s", exc)
        return _default_response()
    except json.JSONDecodeError as exc:
        logger.error("Не удалось распарсить ответ LLM: %s", exc)
        logger.debug("RAW LLM response: %s", text if 'text' in locals() else "<empty>")
        return _default_response()

    data.setdefault("foods", [])
    data.setdefault("need_clarify", False)
    data.setdefault("clarify_question", "")
    data.setdefault("templates_to_update", [])
    return data
