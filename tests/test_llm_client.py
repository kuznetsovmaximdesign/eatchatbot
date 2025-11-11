from __future__ import annotations

import importlib
import json
from types import SimpleNamespace


def reload_llm(monkeypatch) -> SimpleNamespace:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    module = importlib.import_module("nutrition_bot.llm_client")
    return importlib.reload(module)


def test_estimate_foods_success(monkeypatch):
    llm = reload_llm(monkeypatch)

    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self) -> None:  # pragma: no cover - nothing to do
            return

        def json(self) -> dict:
            return self._payload

    payload = {
        "output": [
            {
                "content": [
                    {
                        "text": json.dumps(
                            {
                                "foods": [
                                    {
                                        "name": "курица",
                                        "grams": 150,
                                        "kcal": 250,
                                        "protein": 32,
                                        "fat": 9,
                                        "carb": 0,
                                    }
                                ],
                                "need_clarify": False,
                            }
                        )
                    }
                ]
            }
        ]
    }

    def fake_post(url, headers, json, timeout):  # noqa: D401 - patched in tests
        assert "responses" in url
        assert json["model"] == "gpt-test"
        return DummyResponse(payload)

    monkeypatch.setattr(llm.requests, "post", fake_post)

    result = llm.estimate_foods("курица 150")
    assert not result["need_clarify"]
    assert result["foods"][0]["kcal"] == 250


def test_estimate_foods_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    module = importlib.import_module("nutrition_bot.llm_client")
    llm = importlib.reload(module)

    result = llm.estimate_foods("овсянка 100")
    assert result["need_clarify"]
    assert "ключ" in result["clarify_question"].lower()
