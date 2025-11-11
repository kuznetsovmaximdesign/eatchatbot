import importlib


def reload_fatsecret(monkeypatch):
    module = importlib.import_module("nutrition_bot.fatsecret_client")
    return importlib.reload(module)


def reset_config_cache():
    import nutrition_bot.config as config

    config.get_settings.cache_clear()  # type: ignore[attr-defined]


def test_get_macros_without_credentials(monkeypatch):
    monkeypatch.delenv("FATSECRET_KEY", raising=False)
    monkeypatch.delenv("FATSECRET_SECRET", raising=False)
    reset_config_cache()
    module = reload_fatsecret(monkeypatch)
    assert module.get_macros_for_product("яблоко") is None


def test_get_macros_success(monkeypatch):
    monkeypatch.setenv("FATSECRET_KEY", "demo-key")
    monkeypatch.setenv("FATSECRET_SECRET", "demo-secret")
    reset_config_cache()
    module = reload_fatsecret(monkeypatch)

    class DummyResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):  # pragma: no cover - nothing to do in dummy
            return

        def json(self):
            return self.payload

    def fake_post(url, data, auth, timeout):
        assert "connect/token" in url
        assert auth == ("demo-key", "demo-secret")
        return DummyResponse({"access_token": "abc", "expires_in": 3600})

    calls = {"search": 0, "get": 0}

    def fake_get(url, params, headers, timeout):
        assert headers["Authorization"] == "Bearer abc"
        if params["method"] == "foods.search":
            calls["search"] += 1
            return DummyResponse({"foods": {"food": [{"food_id": "42"}]}})
        if params["method"] == "food.get":
            calls["get"] += 1
            return DummyResponse(
                {
                    "food": {
                        "servings": {
                            "serving": {
                                "metric_serving_amount": "100",
                                "metric_serving_unit": "g",
                                "calories": "200",
                                "protein": "10",
                                "fat": "5",
                                "carbohydrate": "20",
                            }
                        }
                    }
                }
            )
        raise AssertionError(f"Unexpected method {params['method']}")

    monkeypatch.setattr(module.requests, "post", fake_post)
    monkeypatch.setattr(module.requests, "get", fake_get)

    macros = module.get_macros_for_product("тест")
    assert macros == {"kcal": 200.0, "protein": 10.0, "fat": 5.0, "carb": 20.0}
    assert calls == {"search": 1, "get": 1}
