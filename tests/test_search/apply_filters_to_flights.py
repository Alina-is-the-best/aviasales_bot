import pytest
from commands.search import apply_filters_to_flights

class DummyFilters:
    price_limit = ""
    transfers = ""

@pytest.mark.asyncio
async def test_apply_filters_unknown_format():
    result = await apply_filters_to_flights(
        flights_data="wrong_format",
        filters={},
        user_filters=DummyFilters()
    )
    assert result == []


@pytest.mark.asyncio
async def test_apply_filters_dict_with_data_list_is_not_supported():
    """
    Сейчас dict с ключом 'data' НЕ распознаётся как "обёртка",
    потому что ветка isinstance(dict) срабатывает раньше.
    Поэтому ожидаем пустой результат.
    """
    flights = {
        "data": [
            {"price": 1000, "transfers": 0}
        ]
    }

    result = await apply_filters_to_flights(
        flights_data=flights,
        filters={},
        user_filters=DummyFilters()
    )

    assert result == []
