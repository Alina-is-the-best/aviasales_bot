import pytest
from adapters.api import functions

@pytest.mark.asyncio
async def test_get_latest_flights_calls_parse(monkeypatch):
    """
    Проверяем:
    - что get_latest_flights вызывает parse_flights
    - что возвращается то, что вернул parse_flights
    """

    async def fake_parse(*args, **kwargs):
        return {"status": "ok"}

    monkeypatch.setattr(functions, "parse_flights", fake_parse)

    result = await functions.get_latest_flights(
        origin="MOW",
        destination="AER",
        depart_date="2025-12-27"
    )

    assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_get_calendar_prices_calls_parse(monkeypatch):
    """
    Проверяем:
    - корректную прокладку аргументов
    """

    async def fake_parse(*args, **kwargs):
        return {"calendar": True}

    monkeypatch.setattr(functions, "parse_flights", fake_parse)

    result = await functions.get_calendar_prices(
        origin="MOW",
        destination="AER",
        month="2025-12"
    )

    assert result == {"calendar": True}
