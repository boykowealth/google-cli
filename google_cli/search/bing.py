"""Bing HTML search — no API key. Used as a fallback when DuckDuckGo blocks."""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from ..engine.fetch import DEFAULT_HEADERS
from ..models import SearchPage, SearchResult
from .base import SearchEngine

ENDPOINT = "https://www.bing.com/search"


class BingEngine(SearchEngine):
    name = "Bing"

    async def search(
        self, query: str, *, limit: int = 20, cursor: object | None = None
    ) -> SearchPage:
        first = cursor if isinstance(cursor, int) else 1  # 1-based result offset
        params = {"q": query, "first": first, "count": limit, "setlang": "en"}
        headers = dict(DEFAULT_HEADERS)
        headers["Referer"] = "https://www.bing.com/"
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=15.0, headers=headers
            ) as client:
                response = await client.get(ENDPOINT, params=params)
                response.raise_for_status()
                html = response.text
        except httpx.HTTPError:
            return SearchPage([], None)
        results = parse_results(html, limit=limit)
        next_cursor = first + len(results) if results else None
        return SearchPage(results, next_cursor)


def parse_results(html: str, *, limit: int = 20) -> list[SearchResult]:
    """Parse a Bing results page. Pure function for easy testing."""
    soup = BeautifulSoup(html, "lxml")
    results: list[SearchResult] = []
    seen: set[str] = set()
    for li in soup.select("li.b_algo"):
        anchor = li.select_one("h2 a") or li.select_one("a[href^=http]")
        if anchor is None:
            continue
        url = anchor.get("href", "")
        if not url.startswith("http") or url in seen:
            continue
        title = anchor.get_text(" ", strip=True)
        if not title:
            continue
        snippet_el = li.select_one(".b_caption p") or li.select_one("p")
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
        results.append(SearchResult(title=title, url=url, snippet=snippet))
        seen.add(url)
        if len(results) >= limit:
            break
    return results
