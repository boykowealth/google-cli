"""The bottom status bar: current state, hints and the link-follow buffer."""

from __future__ import annotations

from rich.markup import escape
from textual.widgets import Static

DEFAULT_HINT = "Ctrl+L address · Ctrl+T new tab · F6 theme · ? all shortcuts"


class StatusBar(Static):
    """A single-line status/hint bar at the bottom of the window."""

    def on_mount(self) -> None:
        self.show_hint()

    def show_hint(self, text: str = DEFAULT_HINT) -> None:
        self.update(f"[dim]{escape(text)}[/dim]")

    def show_loading(self, target: str) -> None:
        self.update(f"[#FBBC05]●[/] [dim]Loading {escape(target)}…[/dim]")

    def show_message(self, text: str) -> None:
        self.update(escape(text))

    def show_link_buffer(self, buffer: str) -> None:
        self.update(f"Follow link [#4285F4]{escape(buffer)}[/] — Enter to open, Esc to cancel")
