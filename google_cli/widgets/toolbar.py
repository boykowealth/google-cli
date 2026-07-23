"""The navigation toolbar: back/forward/reload, the omnibox and the ⋮ menu."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button

from .omnibox import Omnibox


class Toolbar(Horizontal):
    """Row of navigation controls wrapping the omnibox.

    Bookmarking and open-in-browser live on keyboard shortcuts (Ctrl+D / Ctrl+O)
    and in the menu, so they intentionally have no toolbar buttons.
    """

    #: id -> (glyph, tooltip). Tooltips make each control self-explanatory on hover.
    _LEFT = [
        ("nav-back", "←", "Back  (Alt+←)"),
        ("nav-forward", "→", "Forward  (Alt+→)"),
        ("nav-reload", "↻", "Reload  (Ctrl+R)"),
    ]

    def compose(self) -> ComposeResult:
        for btn_id, glyph, tip in self._LEFT:
            btn = Button(glyph, id=btn_id, classes="icon")
            btn.tooltip = tip
            yield btn
        yield Omnibox()
        menu = Button("⋮", id="nav-menu", classes="icon")
        menu.tooltip = "Menu  (F2)"
        yield menu

    def set_back_enabled(self, enabled: bool) -> None:
        self.query_one("#nav-back", Button).disabled = not enabled

    def set_forward_enabled(self, enabled: bool) -> None:
        self.query_one("#nav-forward", Button).disabled = not enabled
