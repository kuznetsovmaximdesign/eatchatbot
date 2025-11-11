from __future__ import annotations

from nutrition_bot import product_db


def teardown_function() -> None:
    product_db.load_products.cache_clear()
    product_db._normalized_index.cache_clear()  # type: ignore[attr-defined]


def test_find_product_exact_match():
    macros = product_db.find_product("курица филе")
    assert macros is not None
    assert macros["protein"] > 20


def test_find_product_fuzzy_match():
    macros = product_db.find_product("курица филе запеч")
    assert macros is not None
    assert macros["kcal"] > 0


def test_cache_product(tmp_path, monkeypatch):
    base_path = tmp_path / "products.json"
    base_path.write_text("{}", encoding="utf-8")
    custom_path = tmp_path / "products_custom.json"
    monkeypatch.setattr(product_db, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(product_db, "_DATA_PATH", base_path)
    monkeypatch.setattr(product_db, "_CUSTOM_DATA_PATH", custom_path)
    product_db.cache_product("тестовый продукт", {"kcal": 200, "protein": 10, "fat": 5, "carb": 20})
    macros = product_db.find_product("тестовый продукт")
    assert macros is not None
    assert macros["kcal"] == 200
