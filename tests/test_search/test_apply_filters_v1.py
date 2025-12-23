import pytest
from types import SimpleNamespace

from search import apply_filters_to_flights


@pytest.mark.asyncio
async def test_apply_filters_v1_dict_format():
    """
    Проверяем:
    - старый API формат (dict)
    - перенос destination_code
    """

    flights = {
        "AER": {
            "1": {"price": 5000, "transfers": 0},
            "2": {"price": 20000, "transfers": 0},
        }
    }

    filters = {"price_limit": "10000"}
    user_filters = SimpleNamespace(price_limit="", transfers="")

    result = await apply_filters_to_flights(flights, filters, user_filters)

    assert len(result) == 1
    assert result[0]["destination_code"] == "AER"
