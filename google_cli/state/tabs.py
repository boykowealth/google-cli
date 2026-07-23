"""In-memory tab sessions, each with its own back/forward navigation stack."""

from __future__ import annotations

from itertools import count

from ..models import Page
from ..webapps import detect as detect_app

_ids = count(1)


class Tab:
    """A single browser tab: a back/forward URL stack and the loaded page."""

    def __init__(self) -> None:
        self.id = next(_ids)
        self._stack: list[str] = []
        self._pos = -1
        self.page: Page | None = None
        self.loading = False

    # -- navigation stack --------------------------------------------------
    @property
    def url(self) -> str:
        return self._stack[self._pos] if 0 <= self._pos < len(self._stack) else ""

    @property
    def title(self) -> str:
        if self.page and self.page.title:
            return self.page.title
        if self.url:
            return detect_app(self.url) or self.url
        return "New Tab"

    def visit(self, url: str) -> None:
        """Record a new navigation, truncating any forward history."""
        if self.url == url:
            return
        del self._stack[self._pos + 1 :]
        self._stack.append(url)
        self._pos = len(self._stack) - 1

    def can_go_back(self) -> bool:
        return self._pos > 0

    def can_go_forward(self) -> bool:
        return self._pos < len(self._stack) - 1

    def go_back(self) -> str | None:
        if self.can_go_back():
            self._pos -= 1
            return self.url
        return None

    def go_forward(self) -> str | None:
        if self.can_go_forward():
            self._pos += 1
            return self.url
        return None


class TabManager:
    """Owns the ordered list of tabs and which one is active."""

    def __init__(self) -> None:
        self.tabs: list[Tab] = [Tab()]
        self.active_index = 0

    @property
    def active(self) -> Tab:
        return self.tabs[self.active_index]

    def new_tab(self) -> Tab:
        tab = Tab()
        self.tabs.append(tab)
        self.active_index = len(self.tabs) - 1
        return tab

    def close_active(self) -> Tab:
        """Close the active tab. Always keeps at least one tab open."""
        if len(self.tabs) == 1:
            # Replace the last tab with a fresh blank one rather than closing.
            self.tabs[0] = Tab()
            self.active_index = 0
            return self.active
        del self.tabs[self.active_index]
        self.active_index = min(self.active_index, len(self.tabs) - 1)
        return self.active

    def next_tab(self) -> Tab:
        self.active_index = (self.active_index + 1) % len(self.tabs)
        return self.active

    def prev_tab(self) -> Tab:
        self.active_index = (self.active_index - 1) % len(self.tabs)
        return self.active

    def select(self, index: int) -> Tab:
        if 0 <= index < len(self.tabs):
            self.active_index = index
        return self.active
