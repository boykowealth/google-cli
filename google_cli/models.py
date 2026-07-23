"""Core data structures shared across the browser."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(slots=True)
class Link:
    """A followable link discovered while rendering a page.

    ``index`` is the 1-based number shown to the user (e.g. ``[3]``) so links can
    be followed by typing their number.
    """

    index: int
    text: str
    url: str


@dataclass(slots=True)
class Page:
    """A rendered page: the display body plus its ordered links.

    ``lines`` holds Textual/Rich markup, one entry per visual line. ``links`` is
    ordered by ``Link.index`` so ``links[i - 1]`` is link ``[i]``.
    """

    url: str
    title: str
    lines: list[str] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    is_error: bool = False

    def link(self, number: int) -> Link | None:
        """Return the link shown as ``[number]``, or ``None`` if out of range."""
        if 1 <= number <= len(self.links):
            return self.links[number - 1]
        return None


@dataclass(slots=True)
class HistoryEntry:
    """A single visited page recorded in global history."""

    url: str
    title: str
    visited_at: float = field(default_factory=time.time)


@dataclass(slots=True)
class Bookmark:
    """A saved page."""

    url: str
    title: str
    created_at: float = field(default_factory=time.time)


@dataclass(slots=True)
class SearchResult:
    """One result returned by a search engine."""

    title: str
    url: str
    snippet: str = ""
