"""A search engine that tries several providers until one returns results.

Search endpoints block automated requests unpredictably (rate limits, bot
challenges). Rather than fail when one provider blocks, we fall through to the
next, so a search succeeds as long as *any* provider answers.
"""

from __future__ import annotations

from ..models import SearchPage
from .base import SearchEngine


class MultiEngine(SearchEngine):
    name = "Web"

    def __init__(self, engines: list[SearchEngine]) -> None:
        self._engines = engines

    async def search(
        self, query: str, *, limit: int = 20, cursor: object | None = None
    ) -> SearchPage:
        # Paging: the cursor remembers which provider answered, so we keep using
        # it for subsequent pages.
        if isinstance(cursor, tuple):
            idx, sub = cursor
            if 0 <= idx < len(self._engines):
                sp = await self._safe(self._engines[idx], query, limit, sub)
                return self._wrap(idx, sp)
            return SearchPage([], None)

        for idx, engine in enumerate(self._engines):
            sp = await self._safe(engine, query, limit, None)
            if sp.results:
                return self._wrap(idx, sp)
        return SearchPage([], None)

    @staticmethod
    async def _safe(engine, query, limit, sub) -> SearchPage:
        try:
            return await engine.search(query, limit=limit, cursor=sub)
        except Exception:
            return SearchPage([], None)

    @staticmethod
    def _wrap(idx: int, sp: SearchPage) -> SearchPage:
        next_cursor = (idx, sp.next_cursor) if sp.next_cursor is not None else None
        return SearchPage(sp.results, next_cursor)
