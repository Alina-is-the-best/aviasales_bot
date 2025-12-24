"""import pytest
from types import SimpleNamespace

import infra.bot


@pytest.mark.asyncio
async def test_main_registers_all_modules(monkeypatch):
    calls = []

    # ---- FAKE BOT ----
    class FakeBot:
        def __init__(self, *args, **kwargs):
            self.token = kwargs.get("token")

    # ---- FAKE DISPATCHER ----
    class FakeDispatcher:
        def __init__(self, *args, **kwargs):
            self.routers = []

        def include_router(self, router):
            self.routers.append(router)

        def message(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

        async def start_polling(self, bot_instance):
            calls.append("start_polling")

    # ---- patch Bot / Dispatcher ----
    monkeypatch.setattr(infra.bot, "Bot", FakeBot)
    monkeypatch.setattr(infra.bot, "Dispatcher", FakeDispatcher)

    # ---- patch register() функций ----
    def fake_register(dp):
        calls.append("register")

    monkeypatch.setattr(infra.bot.search, "register", fake_register)
    monkeypatch.setattr(infra.bot.hot, "register", fake_register)
    monkeypatch.setattr(infra.bot.tickets, "register", fake_register)
    monkeypatch.setattr(infra.bot.settings, "register", fake_register)
    monkeypatch.setattr(infra.bot.help, "register", fake_register)
    monkeypatch.setattr(infra.bot.complex_search, "register", fake_register)
    monkeypatch.setattr(infra.bot.tracked, "register", fake_register)

    # ---- back router ----
    monkeypatch.setattr(infra.bot.back, "back_router", SimpleNamespace(name="back_router"))

    # ---- RUN ----
    await infra.bot.main()

    # ---- ASSERTS ----
    assert calls.count("register") == 7
    assert "start_polling" in calls

"""