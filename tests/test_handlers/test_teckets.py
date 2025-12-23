import pytest
from handlers import tickets as tickets_handler


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
async def test_purchased_tickets_empty(monkeypatch):
    msg = DummyMsg(user_id=123)

    monkeypatch.setattr(tickets_handler.repo, "get_tickets", lambda user_id: [])
    # get_tickets у тебя async → делаем async-обёртку
    async def _get_tickets(uid): return []
    monkeypatch.setattr(tickets_handler.repo, "get_tickets", _get_tickets)

    monkeypatch.setattr(tickets_handler.keyboards, "add_ticket_button", lambda: "ADD_BTN")

    await tickets_handler.purchased_tickets(msg)

    assert msg.answers[0][0] == "У вас пока нет купленных билетов."
    assert msg.answers[1][0] == "Добавьте первый билет:"
    assert msg.answers[1][1] == "ADD_BTN"


@pytest.mark.asyncio
async def test_purchased_tickets_non_empty(monkeypatch):
    msg = DummyMsg(user_id=123)

    async def _get_tickets(uid):
        return [
            DummyTicket("Москва", "Сочи", "12.03.2025"),
            DummyTicket("СПб", "Казань", "14.03.2025"),
        ]

    monkeypatch.setattr(tickets_handler.repo, "get_tickets", _get_tickets)
    monkeypatch.setattr(tickets_handler.keyboards, "add_ticket_button", lambda: "ADD_BTN")
    monkeypatch.setattr(tickets_handler.keyboards, "tickets_numbers_kb", lambda n: f"NUM_KB_{n}")

    await tickets_handler.purchased_tickets(msg)

    # 1) сообщение со списком
    text0, kb0 = msg.answers[0]
    assert "Ваши билеты" in text0
    assert "1. Москва – Сочи" in text0
    assert "2. СПб – Казань" in text0
    assert kb0 == "ADD_BTN"

    # 2) сообщение "выберите билет"
    text1, kb1 = msg.answers[1]
    assert text1 == "Выберите билет:"
    assert kb1 == "NUM_KB_2"
