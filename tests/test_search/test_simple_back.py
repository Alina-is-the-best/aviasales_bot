'''import pytest
from unittest.mock import AsyncMock
from commands.search import simple_from, simple_to

@pytest.mark.asyncio
async def test_simple_from_back():
    msg = AsyncMock()
    msg.text = "⬅️ Назад в меню"
    state = AsyncMock()

    await simple_from(msg, state)

    state.clear.assert_called_once()
    msg.answer.assert_called()


@pytest.mark.asyncio
async def test_simple_to_back():
    msg = AsyncMock()
    msg.text = "⬅️ Назад в меню"
    state = AsyncMock()

    await simple_to(msg, state)

    state.clear.assert_called_once()
    msg.answer.assert_called()
'''