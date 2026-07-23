"""Dropdown menu and the modal list screens it opens (history, bookmarks, help)."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static

from ..markup import escape
from ..models import Bookmark, HistoryEntry

MENU_ITEMS: list[tuple[str, str]] = [
    ("new_tab", "New tab"),
    ("bookmark", "Bookmark this page"),
    ("bookmarks", "Bookmarks"),
    ("history", "History"),
    ("reload", "Reload"),
    ("open_external", "Open in browser  ↗"),
    ("toggle_theme", "Toggle light / dark"),
    ("help", "Keyboard shortcuts"),
    ("about", "About google-cli"),
    ("quit", "Quit"),
]


class MainMenu(ModalScreen[str]):
    """The full-screen, centered menu. Dismisses with the chosen action key."""

    BINDINGS = [("escape", "dismiss", "Close"), ("f2", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical(id="menu-panel"):
            yield Static("Menu", id="menu-title")
            items = [ListItem(Label(label), id=f"m-{key}") for key, label in MENU_ITEMS]
            yield ListView(*items, id="menu-list")
            yield Static("[dim]Esc to close[/dim]", id="menu-hint")

    @on(ListView.Selected)
    def _selected(self, event: ListView.Selected) -> None:
        key = (event.item.id or "").removeprefix("m-")
        self.dismiss(key)

    def action_dismiss(self, result=None) -> None:  # noqa: D401
        self.dismiss(None)


class ChooserScreen(ModalScreen[str]):
    """A modal list of URLs (history or bookmarks). Dismisses with a chosen URL."""

    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, title: str, rows: list[tuple[str, str]]) -> None:
        """``rows`` is a list of ``(url, display_label)`` pairs."""
        super().__init__()
        self._title = title
        self._rows = rows

    def compose(self) -> ComposeResult:
        with Vertical(id="chooser-panel"):
            yield Static(self._title, id="chooser-title")
            if self._rows:
                items = [
                    ListItem(Label(label), id=f"row-{i}")
                    for i, (_url, label) in enumerate(self._rows)
                ]
                yield ListView(*items, id="chooser-list")
            else:
                yield Static("[dim]Nothing here yet.[/dim]", id="chooser-empty")

    @on(ListView.Selected)
    def _selected(self, event: ListView.Selected) -> None:
        idx = int((event.item.id or "row-0").removeprefix("row-"))
        self.dismiss(self._rows[idx][0])

    def action_dismiss(self, result=None) -> None:  # noqa: D401
        self.dismiss(None)


def history_rows(entries: list[HistoryEntry]) -> list[tuple[str, str]]:
    return [(e.url, f"{escape(e.title)}  [dim]{escape(e.url)}[/dim]") for e in entries]


def bookmark_rows(items: list[Bookmark]) -> list[tuple[str, str]]:
    return [(b.url, f"★ {escape(b.title)}  [dim]{escape(b.url)}[/dim]") for b in items]


HELP_TEXT = """[bold]Keyboard shortcuts[/bold]

  [#4285F4]Ctrl+L[/]      Focus the omnibox
  [#4285F4]Enter[/]       Visit URL / search / follow typed link number
  [#4285F4]Ctrl+T[/]      New tab
  [#4285F4]Ctrl+W[/]      Close tab
  [#4285F4]Ctrl+Tab[/]    Next tab
  [#4285F4]Alt+←  Alt+→[/]  Back / forward
  [#4285F4]Ctrl+R[/]      Reload
  [#4285F4]Ctrl+O[/]      Open current page in your real browser ↗
  [#4285F4]Ctrl+D[/]      Bookmark this page
  [#4285F4]Ctrl+H[/]      History
  [#4285F4]Ctrl+B[/]      Bookmarks
  [#4285F4]F6[/]          Toggle light / dark mode
  [#4285F4]F2[/]          Menu
  [#4285F4]digits, Enter[/] Follow link by number  ([#4285F4]Esc[/] cancels)
  [#4285F4]?[/]           This help
  [#4285F4]Ctrl+Q[/]      Quit

[dim]Press Esc to close.[/dim]"""


class HelpScreen(ModalScreen[None]):
    BINDINGS = [("escape", "dismiss", "Close"), ("question_mark", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-panel"):
            yield Static(HELP_TEXT, id="help-text")

    def action_dismiss(self, result=None) -> None:  # noqa: D401
        self.dismiss(None)
