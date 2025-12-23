import pytest
from api.aviasales_api import parse_flights


@pytest.mark.asyncio
async def test_parse_flights_returns_dict():
    result = await parse_flights(
        origin="MOW",
        destination="AER",
        depart_date="2025-12-27",
        currency="RUB",
        endpoint="cheap"
    )

    assert isinstance(result, dict)
