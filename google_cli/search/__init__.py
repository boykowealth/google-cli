"""Pluggable search engines.

The no-key default is a :class:`MultiEngine` that tries DuckDuckGo then Bing, so
a search still works when one provider blocks automated requests. A configured
Google Programmable Search API key takes precedence when present.
"""

from __future__ import annotations

from .base import SearchEngine
from .bing import BingEngine
from .duckduckgo import DuckDuckGoEngine
from .google_api import GoogleApiEngine
from .multi import MultiEngine


def get_engine(name: str, *, api_key: str = "", cx: str = "") -> SearchEngine:
    """Return a search engine by name.

    ``google`` (with credentials) uses the official API; ``bing`` uses Bing only;
    everything else uses the robust multi-provider default.
    """
    name = (name or "").lower().strip()
    if name in {"google", "google_api"} and api_key and cx:
        return GoogleApiEngine(api_key=api_key, cx=cx)
    if name == "bing":
        return BingEngine()
    if name == "duckduckgo":
        return DuckDuckGoEngine()
    return MultiEngine([DuckDuckGoEngine(), BingEngine()])


__all__ = [
    "SearchEngine",
    "DuckDuckGoEngine",
    "BingEngine",
    "GoogleApiEngine",
    "MultiEngine",
    "get_engine",
]
