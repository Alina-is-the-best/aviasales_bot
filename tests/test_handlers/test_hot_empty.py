import pytest
from infra.handlers import hot


class DummyState:
    def __init__(self):
        self.cleared = False

    async def clear(self):
        self.cleared = True


class DummyMsg:
    def __init__(self, text="Москва"):
        self.text = text
        self.answers = []

    async def answer(self, text, reply_markup=None):
        self.answers.append(text)


@pytest.mark.asyncio
async def test_hot_when_no_deals(monkeypatch):
    msg = DummyMsg("Москва")
    state = DummyState()

    # подменяем city code
    monkeypatch.setattr(hot, "get_city_code", lambda city: "MOW")

    # API всегда возвращает пустые данные
    async def fake_parse(*args, **kwargs):
        return {"data": {}}

    monkeypatch.setattr(hot, "parse_flights", fake_parse)

    # 🔥 ВАЖНО: вызываем РЕАЛЬНЫЙ handler
    await hot.hot_city_received(msg, state)

    assert state.cleared is True
    assert any("не найдены" in t.lower() for t in msg.answers)