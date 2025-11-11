"""Local product database lookup utilities."""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

from difflib import get_close_matches


logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent / "data"
_DATA_PATH = _DATA_DIR / "products.json"
_CUSTOM_DATA_PATH = _DATA_DIR / "products_custom.json"


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _load_json(path: Path) -> Dict[str, Dict[str, float]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {str(name): {k: float(v) for k, v in values.items()} for name, values in data.items()}


@lru_cache(maxsize=1)
def load_products() -> Dict[str, Dict[str, float]]:
    """Load the offline product catalogue."""

    if not _DATA_PATH.exists():
        raise FileNotFoundError(f"Не найден файл продуктов: {_DATA_PATH}")
    data = _load_json(_DATA_PATH)
    custom = _load_json(_CUSTOM_DATA_PATH)
    merged = {**data, **custom}
    return merged


@lru_cache(maxsize=1)
def _normalized_index() -> Dict[str, str]:
    products = load_products()
    return {_normalize(name): name for name in products}


def find_product(name: str) -> Optional[Dict[str, float]]:
    """Try to match a product name against the offline catalogue."""

    if not name:
        return None
    products = load_products()
    index = _normalized_index()
    normalized = _normalize(name)

    canonical = index.get(normalized)
    if canonical:
        return products[canonical]

    # substring / prefix search
    for key, canonical_name in index.items():
        if normalized in key or key in normalized:
            return products[canonical_name]

    # fuzzy match as last resort
    matches = get_close_matches(normalized, list(index.keys()), n=1, cutoff=0.72)
    if matches:
        return products[index[matches[0]]]
    return None


def cache_product(name: str, macros: Dict[str, float]) -> None:
    """Store a custom product entry for future lookups."""

    cleaned_name = name.strip()
    if not cleaned_name:
        return
    if not macros:
        return

    normalized_macros = {
        key: float(macros.get(key, 0.0) or 0.0)
        for key in ("kcal", "protein", "fat", "carb")
    }

    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    if _CUSTOM_DATA_PATH.exists():
        try:
            data = _load_json(_CUSTOM_DATA_PATH)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            logger.warning("Не удалось прочитать пользовательскую базу продуктов: %s", exc)
            data = {}

    data[cleaned_name] = normalized_macros
    with _CUSTOM_DATA_PATH.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)

    load_products.cache_clear()
    _normalized_index.cache_clear()
