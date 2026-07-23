"""Persisted bookmarks."""

from __future__ import annotations

from ..models import Bookmark
from .store import load_json, save_json

_FILE = "bookmarks.json"


class Bookmarks:
    """A persisted collection of saved pages, newest first."""

    def __init__(self, items: list[Bookmark] | None = None) -> None:
        self._items: list[Bookmark] = items or []

    @classmethod
    def load(cls) -> Bookmarks:
        raw = load_json(_FILE, [])
        items = [
            Bookmark(
                url=i["url"],
                title=i.get("title", i["url"]),
                created_at=i.get("created_at", 0.0),
            )
            for i in raw
            if isinstance(i, dict) and i.get("url")
        ]
        return cls(items)

    def has(self, url: str) -> bool:
        return any(b.url == url for b in self._items)

    def toggle(self, url: str, title: str) -> bool:
        """Add or remove a bookmark. Returns ``True`` if it is now bookmarked."""
        if self.has(url):
            self._items = [b for b in self._items if b.url != url]
            self.save()
            return False
        self._items.insert(0, Bookmark(url=url, title=title))
        self.save()
        return True

    def items(self) -> list[Bookmark]:
        return list(self._items)

    def save(self) -> None:
        save_json(
            _FILE,
            [{"url": b.url, "title": b.title, "created_at": b.created_at} for b in self._items],
        )
