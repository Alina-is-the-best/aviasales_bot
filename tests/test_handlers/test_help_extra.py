import pytest
from handlers import help as help_handler


class DummyMsg:
    def __init__(self):
        self.answers = []

    async def answer(self, text, reply_markup=None):
        self.answers.append(text)


@pytest.mark.asyncio
async def test_help_menu_text_contains_commands(monkeypatch):
    msg = DummyMsg()

    monkeypatch.setattr(
        help_handler.keyboards,
        "main_menu",
        lambda: None
    )

    await help_handler.help_menu(msg)

    text = msg.answers[0]

    assert "билеты" in text.lower()
    assert "поиск" in text.lower()
