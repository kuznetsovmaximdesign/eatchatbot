from types import SimpleNamespace

from nutrition_bot.services import llm_client


class DummyProfile(SimpleNamespace):
    pass


def test_llm_parses_simple_food(monkeypatch):
    profile = DummyProfile(user_id=1)
    state = SimpleNamespace(profile=profile, templates={}, recent_meals=[])

    result = llm_client.ask_llm(user_state=state, message_text="курица 150, рис 100")

    assert len(result["foods"]) == 2
    assert not result["need_clarify"]
    assert "курица" in result["reply"].lower()


def test_llm_requires_text():
    profile = DummyProfile(user_id=1)
    state = SimpleNamespace(profile=profile, templates={}, recent_meals=[])

    result = llm_client.ask_llm(user_state=state, message_text="")

    assert result["foods"] == []
    assert "Нужен текст" in result["reply"]
