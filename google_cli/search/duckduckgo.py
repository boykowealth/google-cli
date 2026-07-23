"""DuckDuckGo HTML search — works with no API key.

Pagination follows DuckDuckGo's own "Next" form: the results page embeds a form
with hidden fields (``s``, ``nextParams``, ``vqd``, …). We capture those and
resubmit them to get the next page, which is the only reliable way to page the
HTML endpoint.
"""

from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from ..engine.fetch import USER_AGENT
from ..models import SearchPage, SearchResult
from .base import SearchEngine

ENDPOINT = "https://html.duckduckgo.com/html/"


class DuckDuckGoEngine(SearchEngine):
    name = "DuckDuckGo"

    async def search(
        self, query: str, *, limit: int = 20, cursor: object | None = None
    ) -> SearchPage:
        headers = {"User-Agent": USER_AGENT}
        data = cursor if isinstance(cursor, dict) else {"q": query}
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=15.0, headers=headers
            ) as client:
                response = await client.post(ENDPOINT, data=data)
                response.raise_for_status()
                html = response.text
        except httpx.HTTPError:
            return SearchPage([], None)
        results = parse_results(html, limit=limit)
        next_cursor = parse_next_cursor(html, query)
        return SearchPage(results, next_cursor)


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


def parse_next_cursor(html: str, query: str) -> dict | None:
    """Return the hidden fields of the "Next" form, or ``None`` if there's none.

    Pure function for easy testing. The returned dict is POSTed as-is to fetch
    the following page.
    """
    soup = BeautifulSoup(html, "lxml")
    for form in soup.select("form.nav-link, div.nav-link form, form"):
        inputs = form.select("input[type=hidden]")
        names = {i.get("name") for i in inputs}
        # The next-page form is the one carrying pagination state.
        if "s" not in names and "nextParams" not in names:
            continue
        fields = {
            i.get("name"): i.get("value", "")
            for i in inputs
            if i.get("name")
        }
        fields.setdefault("q", query)
        return fields
    return None


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
