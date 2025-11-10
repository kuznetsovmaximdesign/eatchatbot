from __future__ import annotations

from nutrition_bot import product_db


def test_find_product_exact_match():
    macros = product_db.find_product("курица филе")
    assert macros is not None
    assert macros["protein"] > 20


def test_find_product_fuzzy_match():
    macros = product_db.find_product("курица филе запеч")
    assert macros is not None
    assert macros["kcal"] > 0
