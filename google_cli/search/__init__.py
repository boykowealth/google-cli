"""Pluggable search engines. DuckDuckGo is the no-key default."""

from __future__ import annotations

from .base import SearchEngine
from .duckduckgo import DuckDuckGoEngine
from .google_api import GoogleApiEngine


def get_engine(name: str, *, api_key: str = "", cx: str = "") -> SearchEngine:
    """Return a search engine by name, falling back to DuckDuckGo."""
    name = (name or "").lower().strip()
    if name in {"google", "google_api"} and api_key and cx:
        return GoogleApiEngine(api_key=api_key, cx=cx)
    return DuckDuckGoEngine()


__all__ = ["SearchEngine", "DuckDuckGoEngine", "GoogleApiEngine", "get_engine"]
