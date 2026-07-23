"""Google Programmable Search Engine (JSON API) — optional, needs a key + cx."""

from __future__ import annotations

import httpx

from ..models import SearchPage, SearchResult
from .base import SearchEngine

ENDPOINT = "https://www.googleapis.com/customsearch/v1"
_MAX_START = 91  # Custom Search API caps start at 91 (results 1-100).


class GoogleApiEngine(SearchEngine):
    name = "Google"

    def __init__(self, api_key: str, cx: str) -> None:
        self.api_key = api_key
        self.cx = cx

    async def search(
        self, query: str, *, limit: int = 20, cursor: object | None = None
    ) -> SearchPage:
        num = min(limit, 10)  # API max per request.
        start = cursor if isinstance(cursor, int) else 1
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": num,
            "start": start,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(ENDPOINT, params=params)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            return SearchPage([], None)
        results = parse_results(data, limit=limit)
        next_start = start + num
        next_cursor = next_start if results and next_start <= _MAX_START else None
        return SearchPage(results, next_cursor)


def parse_results(data: dict, *, limit: int = 20) -> list[SearchResult]:
    """Parse the Custom Search JSON payload. Pure function for easy testing."""
    results: list[SearchResult] = []
    for item in data.get("items", []):
        url = item.get("link")
        if not url:
            continue
        results.append(
            SearchResult(
                title=item.get("title", url),
                url=url,
                snippet=item.get("snippet", ""),
            )
        )
        if len(results) >= limit:
            break
    return results
