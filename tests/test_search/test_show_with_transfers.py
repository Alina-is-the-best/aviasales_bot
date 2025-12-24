import pytest
from unittest.mock import AsyncMock
from commands.search import show_flights_with_transfers

@pytest.mark.asyncio
async def test_show_with_transfers_no_data():
    callback = AsyncMock()
    state = AsyncMock()
    state.get_data.return_value = {}

    await show_flights_with_transfers(callback, state)

    callback.answer.assert_called()
    state.clear.assert_not_called()


@pytest.mark.asyncio
async def test_show_with_transfers_success():
    callback = AsyncMock()
    callback.message.answer = AsyncMock()

    state = AsyncMock()
    state.get_data.return_value = {
        "cheapest_there": [{"price": 1000, "transfers": 1}],
        "cheapest_back": [{"price": 1200, "transfers": 1}],
        "depart_date": "01.01.2026",
        "return_date": "10.01.2026"
    }

    await show_flights_with_transfers(callback, state)

    callback.message.answer.assert_called()
    state.clear.assert_called_once()
