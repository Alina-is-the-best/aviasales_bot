'''import pytest
from unittest.mock import AsyncMock

from commands.search import finish_search_round_trip


@pytest.mark.asyncio
async def test_round_trip_no_dates():
    msg = AsyncMock()
    msg.from_user.id = 1

    state = AsyncMock()
    state.get_data.return_value = {
        "from_city": "Москва",
        "to_city": "Сочи"
    }

    await finish_search_round_trip(msg, state)

    msg.answer.assert_called()
    state.clear.assert_called_once()
'''