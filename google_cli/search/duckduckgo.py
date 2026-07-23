"""DuckDuckGo HTML search — works with no API key."""

from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from ..engine.fetch import USER_AGENT
from ..models import SearchResult
from .base import SearchEngine

ENDPOINT = "https://html.duckduckgo.com/html/"


class DuckDuckGoEngine(SearchEngine):
    name = "DuckDuckGo"

    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        headers = {"User-Agent": USER_AGENT}
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=15.0, headers=headers
            ) as client:
                response = await client.post(ENDPOINT, data={"q": query})
                response.raise_for_status()
                html = response.text
        except httpx.HTTPError:
            return []
        return parse_results(html, limit=limit)


def parse_results(html: str, *, limit: int = 20) -> list[SearchResult]:
    """Parse DuckDuckGo's HTML results page. Pure function for easy testing."""
    soup = BeautifulSoup(html, "lxml")
    results: list[SearchResult] = []
    for node in soup.select(".result"):
        classes = node.get("class", [])
        if "result--ad" in classes or "result--ad-v2" in classes:
            continue  # skip sponsored/ad results
        anchor = node.select_one("a.result__a")
        if anchor is None:
            continue
        href = anchor.get("href", "")
        url = _unwrap(href)
        if not url or "duckduckgo.com/y.js" in url:
            continue
        title = anchor.get_text(" ", strip=True)
        snippet_el = node.select_one(".result__snippet")
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
        results.append(SearchResult(title=title, url=url, snippet=snippet))
        if len(results) >= limit:
            break
    return results


def _unwrap(href: str) -> str:
    """DuckDuckGo wraps links as ``/l/?uddg=<encoded>``; unwrap to the real URL."""
    if not href:
        return ""
    parsed = urlparse(href)
    if parsed.path.endswith("/l/") or "uddg" in (parsed.query or ""):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            return unquote(target)
    if href.startswith("//"):
        return "https:" + href
    return href
