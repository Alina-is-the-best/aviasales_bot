'''import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from commands.search import finish_search_one_way


@pytest.mark.asyncio
async def test_finish_search_no_date():
    """
    Проверяем:
    - отсутствие даты → ранний выход
    """

    msg = AsyncMock()
    msg.from_user.id = 1

    state = AsyncMock()
    state.get_data.return_value = {
        "from_city": "Москва",
        "to_city": "Сочи"
    }

    await finish_search_one_way(msg, state)

    msg.answer.assert_called()
    state.clear.assert_called_once()

@pytest.mark.asyncio
async def test_finish_search_api_error():
    """
    Проверяем:
    - API вернул error
    """

    msg = AsyncMock()
    msg.from_user.id = 1

    state = AsyncMock()
    state.get_data.return_value = {
        "from_city": "Москва",
        "to_city": "Сочи",
        "dates": "02.01.2026"
    }

    with patch("search.parse_flights", return_value={"error": "API DOWN"}), \
         patch("search.filters_repo.get_filters", return_value=SimpleNamespace(price_limit="", transfers="")), \
         patch("search.get_city_code", side_effect=["MOW", "AER"]):

        await finish_search_one_way(msg, state)

    msg.answer.assert_called()
    state.clear.assert_called_once()
'''