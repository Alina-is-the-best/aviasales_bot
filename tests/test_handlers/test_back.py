import pytest
from types import SimpleNamespace

from infra.handlers import back


class DummyMsg:
    def __init__(self):
        self.answers = []

    async def answer(self, text, reply_markup=None):
        self.answers.append((text, reply_markup))


class DummyState:
    def __init__(self, value):
        self.value = value

    async def get_state(self):
        return self.value


@pytest.mark.asyncio
async def test_back_does_nothing_when_state_active(monkeypatch):
    msg = DummyMsg()
    state = DummyState("some_state")

    await back.back_to_main(msg, state)

    assert msg.answers == []  # ничего не отправили


@pytest.mark.asyncio
async def test_back_sends_main_menu_when_state_none(monkeypatch):
    msg = DummyMsg()
    state = DummyState(None)

    # чтобы не зависеть от реальной клавиатуры
    monkeypatch.setattr(back.keyboards, "main_menu", lambda: "MAIN_MENU_KB")

    await back.back_to_main(msg, state)

    assert msg.answers == [("Главное меню:", "MAIN_MENU_KB")]
