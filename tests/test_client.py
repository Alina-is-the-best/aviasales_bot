"""import pytest
from aioresponses import aioresponses

import adapters.api.client as client
from adapters.api.exceptions import RateLimitError, ParseError

@pytest.mark.asyncio
async def test_fetch_retry_and_success():
    url = "https://example.test/ok"
    with aioresponses() as m:
        m.get(url, status=500, body="err1")
        m.get(url, status=200, payload={"ok": True})
        res = await client.fetch_json(url, retries=3, backoff_factor=0.01)
        assert res["ok"] is True

@pytest.mark.asyncio
async def test_fetch_429_raises_after_retries():
    url = "https://example.test/ratelimit"
    with aioresponses() as m:
        m.get(url, status=429, headers={"Retry-After": "0"})
        m.get(url, status=429, headers={"Retry-After": "0"})
        with pytest.raises(RateLimitError):
            await client.fetch_json(url, retries=2, backoff_factor=0.01)

@pytest.mark.asyncio
async def test_parse_error_on_non_json():
    url = "https://example.test/notjson"
    with aioresponses() as m:
        m.get(url, status=200, body="not json")
        with pytest.raises(ParseError):
            await client.fetch_json(url, retries=1)"""