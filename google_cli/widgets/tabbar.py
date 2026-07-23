"""The tab strip. Rebuilt whenever tabs change; emits click intents."""

from __future__ import annotations

from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Static

from ..state.tabs import TabManager


def _truncate(text: str, width: int = 18) -> str:
    text = text.replace("\n", " ").strip() or "New Tab"
    return text if len(text) <= width else text[: width - 1] + "…"


class TabLabel(Static):
    """A single clickable tab in the strip."""

    def __init__(self, index: int, title: str, active: bool) -> None:
        super().__init__(_truncate(title))
        self._index = index
        if active:
            self.add_class("active")

    def on_click(self) -> None:
        self.post_message(TabBar.Selected(self._index))


class NewTabButton(Static):
    """The ``+`` button that opens a new tab."""

    def __init__(self) -> None:
        super().__init__("+", id="new-tab")

    def on_click(self) -> None:
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

    def compose(self):
        for i, tab in enumerate(self._manager.tabs):
            yield TabLabel(i, tab.title, active=i == self._manager.active_index)
        yield NewTabButton()

    async def refresh_tabs(self) -> None:
        """Re-render the strip after tabs are added, closed or renamed."""
        await self.remove_children()
        for i, tab in enumerate(self._manager.tabs):
            await self.mount(TabLabel(i, tab.title, active=i == self._manager.active_index))
        await self.mount(NewTabButton())
