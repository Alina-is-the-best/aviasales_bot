'''import pytest
from unittest.mock import AsyncMock
from commands.search import choose_route_type

@pytest.mark.asyncio
async def test_choose_route_type():
    msg = AsyncMock()

    await choose_route_type(msg)

    msg.answer.assert_called_once()
'''