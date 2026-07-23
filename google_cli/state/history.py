"""Global, persisted browsing history."""

from __future__ import annotations

from ..models import HistoryEntry
from .store import load_json, save_json

_FILE = "history.json"
_MAX = 500


class History:
    """A capped, most-recent-first list of visited pages, persisted to disk."""

    def __init__(self, entries: list[HistoryEntry] | None = None) -> None:
        self._entries: list[HistoryEntry] = entries or []

    @classmethod
    def load(cls) -> History:
        raw = load_json(_FILE, [])
        entries = [
            HistoryEntry(
                url=i["url"],
                title=i.get("title", i["url"]),
                visited_at=i.get("visited_at", 0.0),
            )
            for i in raw
            if isinstance(i, dict) and i.get("url")
        ]
        return cls(entries)

    def add(self, url: str, title: str) -> None:
        # Drop any existing entry for this url so it floats to the top.
        self._entries = [e for e in self._entries if e.url != url]
        self._entries.insert(0, HistoryEntry(url=url, title=title))
        del self._entries[_MAX:]
        self.save()

    def clear(self) -> None:
        self._entries = []
        self.save()

    def entries(self) -> list[HistoryEntry]:
        return list(self._entries)

    def save(self) -> None:
        save_json(
            _FILE,
            [{"url": e.url, "title": e.title, "visited_at": e.visited_at} for e in self._entries],
        )
