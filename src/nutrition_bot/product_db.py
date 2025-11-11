"""Local product database lookup utilities."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

from difflib import get_close_matches


_DATA_PATH = Path(__file__).resolve().parent / "data" / "products.json"


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


@lru_cache(maxsize=1)
def load_products() -> Dict[str, Dict[str, float]]:
    """Load the offline product catalogue."""

    if not _DATA_PATH.exists():
        raise FileNotFoundError(f"Не найден файл продуктов: {_DATA_PATH}")
    with _DATA_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {str(name): {k: float(v) for k, v in values.items()} for name, values in data.items()}


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
