import pytest
from types import SimpleNamespace

from search import apply_filters_to_flights


@pytest.mark.asyncio
async def test_apply_filters_v3_price_and_transfers():
    """
    Проверяем:
    - обработку v3 API (список)
    - фильтр по цене
    - фильтр по пересадкам
    """

    flights = [
        {"value": 5000, "transfers": 0},
        {"value": 15000, "transfers": 0},
        {"value": 4000, "transfers": 1},
    ]

    search_filters = {"price_limit": "10000", "transfers": "Только прямой"}
    user_filters = SimpleNamespace(price_limit="", transfers="")

    result = await apply_filters_to_flights(flights, search_filters, user_filters)

    assert len(result) == 1
    assert result[0]["value"] == 5000
