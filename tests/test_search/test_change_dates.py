'''import pytest
from unittest.mock import AsyncMock
from commands.search import change_dates_callback

@pytest.mark.asyncio
async def test_change_dates_callback():
    callback = AsyncMock()
    callback.message.answer = AsyncMock()
    state = AsyncMock()

    await change_dates_callback(callback, state)

    callback.answer.assert_called()
    state.clear.assert_called_once()
    callback.message.answer.assert_called()
'''