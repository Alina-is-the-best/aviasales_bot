import pytest
from repo import tickets_repository as repo
from data.db import async_session, Ticket
from sqlalchemy import delete

@pytest.mark.asyncio
async def test_add_and_get_ticket():
    user_id = 123

    # --- очистка перед тестом ---
    async with async_session() as session:
        await session.execute(
            delete(Ticket).where(Ticket.user_id == user_id)
        )
        await session.commit()

    # --- действие ---
    await repo.add_ticket(user_id, "Москва", "Сочи", "12.03.2025")
    tickets = await repo.get_tickets(user_id)

    # --- проверки ---
    assert len(tickets) == 1
    assert tickets[0].from_city == "Москва"
    assert tickets[0].to_city == "Сочи"
    assert tickets[0].date == "12.03.2025"
