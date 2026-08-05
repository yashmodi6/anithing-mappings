import time
import asyncio
import httpx
from typing import Callable, Optional, Dict, Any, List
from config import ANILIST_URL, PER_PAGE, CHUNK_PAGE_QUERY, INCREMENTAL_PAGE_QUERY, MAX_ID_QUERY


def _parse_retry_after(headers: Any, default: int = 60) -> int:
    raw = headers.get("Retry-After")
    try:
        val = int(float(raw)) if raw else default
    except (ValueError, TypeError):
        val = default
    return max(1, min(val + 2, 300))


class AsyncRateLimiter:
    def __init__(self, requests_per_minute: int = 30) -> None:
        self.interval = 60.0 / requests_per_minute
        self.lock = asyncio.Lock()
        self.last_request_time = 0.0

    async def acquire(self) -> None:
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_request_time
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
            self.last_request_time = time.time()


async def get_max_id_async() -> int:
    async with httpx.AsyncClient(timeout=15.0) as client:
        rate_limit_retries = error_retries = 0
        while True:
            try:
                res = await client.post(ANILIST_URL, json={"query": MAX_ID_QUERY})
                if res.status_code == 429:
                    rate_limit_retries += 1
                    if rate_limit_retries > 8:
                        break
                    await asyncio.sleep(_parse_retry_after(res.headers, 60))
                    continue
                res.raise_for_status()
                media = res.json().get("data", {}).get("Page", {}).get("media", [])
                if media:
                    return media[0]["id"]
                break
            except Exception:
                error_retries += 1
                if error_retries >= 3:
                    break
                await asyncio.sleep(error_retries * 3)
    raise RuntimeError("Failed to fetch maximum AniList ID from GraphQL API")


async def _fetch_graphql_page(
    client: httpx.AsyncClient,
    query: str,
    variables: Dict[str, Any],
    progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    rate_limiter: Optional[AsyncRateLimiter] = None
) -> Dict[str, Any]:
    rate_limit_attempts = error_attempts = 0
    while True:
        try:
            if rate_limiter:
                await rate_limiter.acquire()
            res = await client.post(ANILIST_URL, json={"query": query, "variables": variables}, timeout=15.0)
            if res.status_code == 429:
                rate_limit_attempts += 1
                if rate_limit_attempts > 10:
                    if progress_callback:
                        progress_callback("error", {"message": f"Exceeded 429 retries on query.", "attempt": rate_limit_attempts})
                    return {}
                retry_sec = _parse_retry_after(res.headers, 60)
                if progress_callback:
                    for sec in range(retry_sec, 0, -1):
                        progress_callback("rate_limit", {"seconds_remaining": sec})
                        await asyncio.sleep(1)
                else:
                    await asyncio.sleep(retry_sec)
                continue
            res.raise_for_status()
            rem = res.headers.get("X-RateLimit-Remaining")
            if rem is not None:
                try:
                    r = int(rem)
                    if r <= 5:
                        await asyncio.sleep(1.2)
                    elif r <= 12:
                        await asyncio.sleep(0.4)
                except ValueError:
                    pass
            return res.json().get("data", {}).get("Page", {})
        except Exception as e:
            error_attempts += 1
            if error_attempts >= 3:
                if progress_callback:
                    progress_callback("error", {"message": str(e), "attempt": error_attempts})
                return {}
            await asyncio.sleep(3 * error_attempts)


async def fetch_page_async(
    client: httpx.AsyncClient,
    page: int,
    id_list: List[int],
    progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    rate_limiter: Optional[AsyncRateLimiter] = None
) -> Dict[str, Any]:
    return await _fetch_graphql_page(
        client, CHUNK_PAGE_QUERY, {"page": page, "perPage": PER_PAGE, "idIn": id_list},
        progress_callback=progress_callback, rate_limiter=rate_limiter
    )


async def fetch_incremental_page_async(
    client: httpx.AsyncClient,
    page: int,
    progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    rate_limiter: Optional[AsyncRateLimiter] = None
) -> Dict[str, Any]:
    return await _fetch_graphql_page(
        client, INCREMENTAL_PAGE_QUERY, {"page": page, "perPage": PER_PAGE},
        progress_callback=progress_callback, rate_limiter=rate_limiter
    )
