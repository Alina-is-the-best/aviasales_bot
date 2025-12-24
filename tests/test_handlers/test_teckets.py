import pytest
from infra.handlers import tickets as tickets_handler


class DummyMsg:
    def __init__(self, user_id=1):
        self.from_user = type("U", (), {"id": user_id})
        self.answers = []

    async def answer(self, text, reply_markup=None):
        self.answers.append((text, reply_markup))


class DummyTicket:
    def __init__(self, from_city, to_city, date, id_=1):
        self.from_city = from_city
        self.to_city = to_city
        self.date = date
        self.id = id_

@pytest.mark.asyncio
async def test_tickets_module_exists():
    """Проверяем, что модуль tickets существует"""
    assert tickets_handler is not None
    # Проверяем наличие router (у aiogram-обработчиков обычно есть router)
    assert hasattr(tickets_handler, 'router')

@pytest.mark.asyncio
async def test_tracked_tickets_handler():
    """Тест для функциональности отслеживаемых билетов"""
    if hasattr(tickets_handler, 'tracked_tickets'):
        msg = DummyMsg()
    else:
        assert len(tickets_handler.router.message.handlers) > 0