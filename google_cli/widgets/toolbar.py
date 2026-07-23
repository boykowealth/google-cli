"""The navigation toolbar: back/forward/reload, omnibox and bookmark/menu."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button

from .omnibox import Omnibox


class Toolbar(Horizontal):
    """Row of navigation controls wrapping the omnibox."""

    #: id -> (glyph, tooltip). Tooltips make each control self-explanatory on hover.
    _BUTTONS = [
        ("nav-back", "←", "Back  (Alt+←)"),
        ("nav-forward", "→", "Forward  (Alt+→)"),
        ("nav-reload", "↻", "Reload  (Ctrl+R)"),
    ]
    _BUTTONS_RIGHT = [
        ("nav-external", "↗", "Open in browser  (Ctrl+O)"),
        ("nav-bookmark", "☆", "Bookmark  (Ctrl+D)"),
        ("nav-menu", "⋮", "Menu  (F2)"),
    ]

    def compose(self) -> ComposeResult:
        for btn_id, glyph, tip in self._BUTTONS:
            btn = Button(glyph, id=btn_id, classes="icon")
            btn.tooltip = tip
            yield btn
        yield Omnibox()
        for btn_id, glyph, tip in self._BUTTONS_RIGHT:
            btn = Button(glyph, id=btn_id, classes="icon")
            btn.tooltip = tip
            yield btn

    def set_back_enabled(self, enabled: bool) -> None:
        self.query_one("#nav-back", Button).disabled = not enabled

    def set_forward_enabled(self, enabled: bool) -> None:
        self.query_one("#nav-forward", Button).disabled = not enabled

    def set_bookmarked(self, bookmarked: bool) -> None:
        btn = self.query_one("#nav-bookmark", Button)
        btn.label = "★" if bookmarked else "☆"
        btn.set_class(bookmarked, "starred")
