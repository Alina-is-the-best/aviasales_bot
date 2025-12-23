import asyncio
import logging
from typing import Optional, Any, Dict
import aiohttp

from .exceptions import ApiError, RateLimitError, ParseError

logger = logging.getLogger(__name__)

_SESSION: Optional[aiohttp.ClientSession] = None

DEFAULT_TIMEOUT = 10
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.0

def get_session() -> aiohttp.ClientSession:
    global _SESSION
    if _SESSION is None or _SESSION.closed:
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        _SESSION = aiohttp.ClientSession(timeout=timeout)
    return _SESSION

async def close_session() -> None:
    global _SESSION
    if _SESSION and not _SESSION.closed:
        await _SESSION.close()
        _SESSION = None

async def _sleep_backoff(attempt: int, backoff_factor: float = DEFAULT_BACKOFF_FACTOR) -> None:
    delay = backoff_factor * (2 ** (attempt - 1))
    jitter = delay * 0.1
    await asyncio.sleep(delay + (jitter * (0.5 - (asyncio.get_event_loop().time() % 1))))

async def fetch_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    retries: int = DEFAULT_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
) -> Any:
    session = get_session()
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            req_timeout = aiohttp.ClientTimeout(total=timeout) if timeout else session.timeout
            async with session.get(url, params=params, headers=headers, timeout=req_timeout) as resp:
                text = await resp.text()
                status = resp.status

                if status == 429:
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait_seconds = int(retry_after)
                        except Exception:
                            wait_seconds = None
                        if wait_seconds:
                            logger.warning("Rate limited; Retry-After=%s", retry_after)
                            await asyncio.sleep(wait_seconds)
                            raise RateLimitError(f"HTTP 429: Retry-After={retry_after}")
                    logger.warning("HTTP 429 on %s (attempt %d/%d)", url, attempt, retries)
                    raise RateLimitError(f"HTTP 429: {text}")

                if 500 <= status < 600:
                    logger.warning("Server error %d on %s (attempt %d/%d): %s", status, url, attempt, retries, text)
                    raise ApiError(f"{status}: {text}")

                if status >= 400:
                    logger.error("Client error %d on %s: %s", status, url, text)
                    raise ApiError(f"{status}: {text}")

                try:
                    return await resp.json()
                except Exception as e:
                    logger.exception("Failed to parse JSON from %s", url)
                    raise ParseError("Invalid JSON response") from e

        except (aiohttp.ClientError, asyncio.TimeoutError, ApiError, RateLimitError) as e:
            last_exc = e
            should_retry = isinstance(e, (aiohttp.ClientError, asyncio.TimeoutError, ApiError, RateLimitError))
            if attempt >= retries or not should_retry:
                logger.exception("Request failed, no more retries: %s", e)
                raise
            logger.info("Request failed (attempt %d/%d): %s. Backing off...", attempt, retries, e)
            await _sleep_backoff(attempt, backoff_factor)

    raise last_exc or ApiError("Unknown error")