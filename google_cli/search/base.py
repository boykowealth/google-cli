"""Search engine interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import SearchPage


class SearchEngine(ABC):
    """A source of web search results.

    Implementations must be safe to call from async code and should never raise
    on network failure — return an empty :class:`SearchPage` instead.
    """

    #: Human-readable name shown in the UI.
    name: str = "search"

    @abstractmethod
    async def search(
        self, query: str, *, limit: int = 20, cursor: object | None = None
    ) -> SearchPage:
        """Return a :class:`SearchPage` for ``query``.

        ``cursor`` is ``None`` for the first page; pass a page's
        ``next_cursor`` back to fetch the following page.
        """
        raise NotImplementedError
