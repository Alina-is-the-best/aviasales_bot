import pytest
from infra.handlers import settings as settings_handler


class DummyMsg:
    def __init__(self):
        self.answers = []

    async def answer(self, text, reply_markup=None):
        self.answers.append((text, reply_markup))


@pytest.mark.asyncio
async def test_settings_root(monkeypatch):
    msg = DummyMsg()
    monkeypatch.setattr(settings_handler.keyboards, "settings_menu", lambda: "SETTINGS_MENU")

    await settings_handler.settings_root(msg)

    assert msg.answers == [("Раздел настроек:", "SETTINGS_MENU")]


@pytest.mark.asyncio
async def test_currency_setting(monkeypatch):
    msg = DummyMsg()
    monkeypatch.setattr(settings_handler.keyboards, "settings_menu", lambda: "SETTINGS_MENU")

    await settings_handler.currency_setting(msg)

    text, kb = msg.answers[0]
    assert "скоро" in text.lower()
    assert kb == "SETTINGS_MENU"
