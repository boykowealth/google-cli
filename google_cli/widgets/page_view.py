"""The scrollable page content area."""

from __future__ import annotations

from rich.markup import escape
from textual.containers import VerticalScroll
from textual.widgets import Static

from ..models import Page, SearchResult

WELCOME = [
    "",
    "[bold]Welcome to [#4285F4]g[#EA4335]o[#FBBC05]o[#4285F4]g[#34A853]l[#EA4335]e[/][/]"
    " — your terminal browser.[/bold]",
    "",
    "[dim]Type a URL or a search in the omnibox above and press Enter.[/dim]",
    "[dim]Follow a link by typing its [#4285F4]number[/dim][dim] then Enter, or click it.[/dim]",
    "[dim]Press [#4285F4]Ctrl+O[/dim][dim] anytime to open the current page"
    " in your real browser ↗.[/dim]",
    "[dim]Press [b]?[/b] any time for keyboard shortcuts.[/dim]",
    "",
]


class PageView(VerticalScroll):
    """Displays rendered page content or search results."""

    def compose(self):
        yield Static("", id="page-content", markup=True)

    @property
    def _content(self) -> Static:
        return self.query_one("#page-content", Static)

    def show_welcome(self) -> None:
        self._content.update("\n".join(WELCOME))
        self.scroll_home(animate=False)

    def show_loading(self, target: str) -> None:
        self._content.update(f"\n[dim]Loading [#4285F4]{escape(target)}[/]…[/dim]")

    def show_page(self, page: Page) -> None:
        self._content.update("\n".join(page.lines))
        self.scroll_home(animate=False)

    def show_error(self, message: str) -> None:
        self._content.update(
            f"\n[#EA4335]⚠  {escape(message)}[/]\n\n"
            "[dim]Press [b]Ctrl+L[/b] to try another address.[/dim]"
        )
        self.scroll_home(animate=False)

    def show_search(self, query: str, results: list[SearchResult]) -> None:
        lines = [f"[dim]Results for[/dim] [bold]{escape(query)}[/bold]", ""]
        if not results:
            lines.append("[dim]No results found (or the search service was unreachable).[/dim]")
        for i, r in enumerate(results, start=1):
            lines.append(
                f"[@click=app.follow_link({i})]"
                f"[#4285F4 underline]\\[{i}] {escape(r.title)}[/][/]"
            )
            lines.append(f"[#34A853]{escape(r.url)}[/]")
            if r.snippet:
                lines.append(f"[dim]{escape(r.snippet)}[/dim]")
            lines.append("")
        self._content.update("\n".join(lines))
        self.scroll_home(animate=False)
