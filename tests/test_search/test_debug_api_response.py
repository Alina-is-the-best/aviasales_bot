import pytest
from search import debug_api_response

@pytest.mark.asyncio
async def test_debug_api_response_with_empty_data(capsys):
    result = {"data": {}, "error": None}

    await debug_api_response(result)

    captured = capsys.readouterr()
    assert "DEBUG API RESPONSE" in captured.out


@pytest.mark.asyncio
async def test_debug_api_response_with_data(capsys):
    result = {
        "data": {
            "MOW": {"price": 1000}
        },
        "error": None
    }

    await debug_api_response(result)

    captured = capsys.readouterr()
    assert "Data keys" in captured.out
