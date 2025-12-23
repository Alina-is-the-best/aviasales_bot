import pytest
from repo import tracked_repository as repo

@pytest.mark.asyncio
async def test_add_and_get_tracked_ticket_oneway():
    """
    Проверяем:
    - добавление one-way билета
    """
    user_id = 2001

    await repo.add_tracked(
        user_id=user_id,
        from_city="Москва",
        to_city="Сочи",
        date_from="12.03.2025",
        date_to="",
        baggage="С багажом",
        transfers="Только прямой",
        price_limit="10000"
    )

    tickets = await repo.get_tracked(user_id)

    assert len(tickets) == 1
    assert tickets[0].date_to == ""
