import pytest
from infra.handlers import help


class DummyMsg:
    def __init__(self):
        self.answers = []

    async def answer(self, text, reply_markup=None):
        self.answers.append((text, reply_markup))


@pytest.mark.asyncio
async def test_help_menu_sends_text_and_keyboard(monkeypatch):
    msg = DummyMsg()

    monkeypatch.setattr(help.keyboards, "main_menu", lambda: "MAIN_MENU_KB")

    await help.help_menu(msg)

    assert len(msg.answers) == 1
    text, kb = msg.answers[0]
    assert "💡 Я умею" in text
    assert kb == "MAIN_MENU_KB"
