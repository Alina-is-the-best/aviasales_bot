import pytest
from infra.handlers import settings


class DummyMsg:
    def __init__(self):
        self.answers = []

    async def answer(self, text, reply_markup=None):
        self.answers.append((text, reply_markup))


@pytest.mark.asyncio
async def test_settings_root_menu(monkeypatch):
    msg = DummyMsg()

    monkeypatch.setattr(
        settings.keyboards,
        "settings_menu",
        lambda: "SETTINGS_MENU_KB"
    )

    await settings.settings_root(msg)

    assert msg.answers == [
        ("Раздел настроек:", "SETTINGS_MENU_KB")
    ]


@pytest.mark.asyncio
async def test_currency_setting_placeholder(monkeypatch):
    msg = DummyMsg()

    monkeypatch.setattr(
        settings.keyboards,
        "settings_menu",
        lambda: "SETTINGS_MENU_KB"
    )

    await settings.currency_setting(msg)

    text, kb = msg.answers[0]

    assert "скоро" in text.lower()
    assert kb == "SETTINGS_MENU_KB"
