"""Search engine interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import SearchResult


class SearchEngine(ABC):
    """A source of web search results.

    Implementations must be safe to call from async code and should never raise
    on network failure — return an empty list instead.
    """

    #: Human-readable name shown in the UI.
    name: str = "search"

    @abstractmethod
    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        """Return up to ``limit`` results for ``query`` (empty list on failure)."""
        raise NotImplementedError
