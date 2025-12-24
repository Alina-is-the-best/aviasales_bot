import pytest
from models.repo import filters_repository as repo

@pytest.mark.asyncio
async def test_create_filters_if_not_exists():
    """
    Проверяем:
    - если у пользователя нет записи в БД
    - get_filters создаёт её автоматически
    """
    user_id = 1001

    filters = await repo.get_filters(user_id)

    assert filters.user_id == user_id
    assert filters.from_city == ""
    assert filters.baggage == ""
    assert filters.transfers == ""
    assert filters.price_limit == ""

@pytest.mark.asyncio
async def test_update_filter():
    """
    Проверяем:
    - update_filter реально сохраняет значение
    """
    user_id = 1002

    await repo.update_filter(user_id, "from_city", "Москва")
    filters = await repo.get_filters(user_id)

    assert filters.from_city == "Москва"

@pytest.mark.asyncio
async def test_clear_filter():
    """
    Проверяем:
    - clear_filter очищает поле
    """
    user_id = 1003

    await repo.update_filter(user_id, "baggage", "С багажом")
    await repo.clear_filter(user_id, "baggage")

    filters = await repo.get_filters(user_id)

    assert filters.baggage == ""
