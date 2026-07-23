"""The tab strip. Keyboard-first: Tab focuses each tab, Enter activates it.

Tabs are also mouse-clickable, but the primary interaction is the keyboard —
Ctrl+T / Ctrl+W / Ctrl+Tab to open, close and cycle.
"""

from __future__ import annotations

import asyncio

from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Static

from ..state.tabs import TabManager


def _truncate(text: str, width: int = 20) -> str:
    text = text.replace("\n", " ").strip() or "New Tab"
    return text if len(text) <= width else text[: width - 1] + "…"


class TabLabel(Static):
    """A single tab. Focusable so it can be reached with the Tab key."""

    can_focus = True

    def __init__(self, index: int, title: str, active: bool) -> None:
        super().__init__(_truncate(title))
        self._index = index
        if active:
            self.add_class("active")

    def on_click(self) -> None:
        self.post_message(TabBar.Selected(self._index))

    def on_key(self, event) -> None:
        if event.key == "enter":
            event.stop()
            self.post_message(TabBar.Selected(self._index))


class NewTabButton(Static):
    """Opens a new tab. Focusable (Tab key) and also bound to Ctrl+T globally."""

    can_focus = True

    def __init__(self) -> None:
        super().__init__("+", id="new-tab")
        self.tooltip = "New tab  (Ctrl+T)"

    def on_click(self) -> None:
        self.post_message(TabBar.NewTab())

    def on_key(self, event) -> None:
        if event.key == "enter":
            event.stop()
            self.post_message(TabBar.NewTab())


class TabBar(Horizontal):
    """Displays all open tabs and the new-tab button."""

    class Selected(Message):
        def __init__(self, index: int) -> None:
            self.index = index
            super().__init__()

    class NewTab(Message):
        pass

    def __init__(self, manager: TabManager) -> None:
        super().__init__(id="tabbar")
        self._manager = manager
        self._lock = asyncio.Lock()

    def compose(self):
        for i, tab in enumerate(self._manager.tabs):
            yield TabLabel(i, tab.title, active=i == self._manager.active_index)
        yield NewTabButton()

    async def refresh_tabs(self) -> None:
        """Re-render the strip after tabs are added, closed or renamed.

        The lock serialises overlapping refreshes so we never mount a second
        ``new-tab`` (or duplicate tab) before the previous strip is removed.
        """
        async with self._lock:
            await self.remove_children()
            widgets = [
                TabLabel(i, tab.title, active=i == self._manager.active_index)
                for i, tab in enumerate(self._manager.tabs)
            ]
            widgets.append(NewTabButton())
            await self.mount_all(widgets)
