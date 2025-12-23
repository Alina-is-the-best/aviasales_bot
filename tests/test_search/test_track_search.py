import pytest
from unittest.mock import AsyncMock, patch
import search

@pytest.mark.asyncio
async def test_track_search_no_data():
    callback = AsyncMock()

    search.last_search_data = {}

    await search.track_search_result(callback)

    callback.answer.assert_called()

@pytest.mark.asyncio
async def test_track_search_success():
    callback = AsyncMock()
    callback.from_user.id = 1

    search.last_search_data = {
        "trip_type": "one_way",
        "from_city": "Москва",
        "to_city": "Сочи",
        "dates": "01.01.2026"
    }

    with patch("repo.tracked_repository.add_tracked", new=AsyncMock()):
        await search.track_search_result(callback)

    callback.answer.assert_called()
