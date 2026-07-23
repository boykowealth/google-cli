"""The BrowserApp — layout, navigation, tabs and all user actions."""

from __future__ import annotations

import webbrowser
from urllib.parse import quote_plus

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.theme import Theme
from textual.widgets import Button, Static

from . import webapps
from .engine import readability, render
from .engine.fetch import fetch
from .models import Link, Page
from .search import get_engine
from .state.bookmarks import Bookmarks
from .state.config import Config
from .state.history import History
from .state.store import load_json, save_json
from .state.tabs import TabManager
from .urls import looks_like_url, normalize_url
from .widgets.menu import (
    ChooserScreen,
    HelpScreen,
    MainMenu,
    bookmark_rows,
    history_rows,
)
from .widgets.omnibox import Omnibox
from .widgets.page_view import PageView
from .widgets.statusbar import StatusBar
from .widgets.tabbar import TabBar
from .widgets.toolbar import Toolbar

DARK_THEME = "google-dark"
LIGHT_THEME = "google-light"
_PREFS_FILE = "prefs.json"

# Timeless off-black / off-white palette. A single blue accent; the four brand
# colours appear only in the small wordmark. Neutral greys do the rest, so the
# UI reads as calm and current rather than trend-driven.
_GOOGLE_DARK = Theme(
    name=DARK_THEME,
    dark=True,
    primary="#4285F4",
    accent="#4285F4",
    foreground="#E6E6E6",
    background="#121212",
    surface="#161616",
    panel="#202020",
    success="#34A853",
    warning="#FBBC05",
    error="#EA4335",
)
_GOOGLE_LIGHT = Theme(
    name=LIGHT_THEME,
    dark=False,
    primary="#1A73E8",
    accent="#1A73E8",
    foreground="#1F1F1F",
    background="#FAFAFA",
    surface="#FFFFFF",
    panel="#EFEFEF",
    success="#188038",
    warning="#B06000",
    error="#C5221F",
)


class Logo(Static):
    """The four-colour google wordmark shown top-left."""

    def render(self) -> str:
        return (
            "[b]◑ [#4285F4]g[#EA4335]o[#FBBC05]o[#4285F4]g[#34A853]l[#EA4335]e[/][/b]"
        )


class BrowserApp(App):
    CSS_PATH = "app.tcss"
    TITLE = "google"

    BINDINGS = [
        ("ctrl+l", "focus_omnibox", "Address"),
        ("ctrl+t", "new_tab", "New tab"),
        ("ctrl+w", "close_tab", "Close tab"),
        ("ctrl+tab", "next_tab", "Next tab"),
        ("shift+ctrl+tab", "prev_tab", "Prev tab"),
        ("alt+left", "back", "Back"),
        ("alt+right", "forward", "Forward"),
        ("ctrl+r", "reload", "Reload"),
        ("ctrl+o", "open_external", "Open in browser"),
        ("ctrl+d", "bookmark", "Bookmark"),
        ("ctrl+h", "history", "History"),
        ("ctrl+b", "bookmarks", "Bookmarks"),
        ("f2", "menu", "Menu"),
        ("f6", "toggle_theme", "Light/Dark"),
        ("question_mark", "help", "Help"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, initial: str = "") -> None:
        super().__init__()
        self.config = Config.load()
        self.history = History.load()
        self.bookmarks = Bookmarks.load()
        self.tabs = TabManager()
        self.engine = get_engine(
            self.config.search_engine, api_key=self.config.api_key, cx=self.config.cx
        )
        self._initial = initial.strip()
        self._link_buffer = ""
        # Search pagination state (n / p keys).
        self._search_query = ""
        self._search_page = 0
        self._page_cursor: dict[int, object | None] = {0: None}
        self._next_cursor: dict[int, object | None] = {}

    # -- composition -------------------------------------------------------
    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            yield Logo(id="logo")
            yield TabBar(self.tabs)
        yield Toolbar()
        yield PageView(id="page")
        yield StatusBar(id="status")

    async def on_mount(self) -> None:
        self.register_theme(_GOOGLE_DARK)
        self.register_theme(_GOOGLE_LIGHT)
        self._apply_saved_theme()
        self._page_view.show_welcome()
        self._sync_chrome()
        if self._initial:
            if looks_like_url(self._initial):
                self._load(normalize_url(self._initial))
            else:
                self._search(self._initial)
        elif self.config.homepage:
            self._load(normalize_url(self.config.homepage))
        else:
            await self._seed_default_tabs()

    async def _seed_default_tabs(self) -> None:
        """Open the configured default tabs (e.g. Gmail, Calendar) on startup.

        Tabs are created but their content is loaded lazily when first viewed,
        so startup stays instant and no network hit happens until you switch.
        """
        for url in self.config.default_tabs:
            url = url.strip()
            if not url:
                continue
            tab = self.tabs.new_tab()
            tab.visit(normalize_url(url))
        self.tabs.select(0)
        await self._activate_tab()
        self.set_focus(self._omnibox)

    # -- convenient handles ------------------------------------------------
    @property
    def _omnibox(self) -> Omnibox:
        return self.query_one(Omnibox)

    @property
    def _page_view(self) -> PageView:
        return self.query_one(PageView)

    @property
    def _status(self) -> StatusBar:
        return self.query_one(StatusBar)

    @property
    def _toolbar(self) -> Toolbar:
        return self.query_one(Toolbar)

    @property
    def _tabbar(self) -> TabBar:
        return self.query_one(TabBar)

    # -- omnibox / tab messages -------------------------------------------
    @on(Omnibox.Navigate)
    def _on_navigate(self, event: Omnibox.Navigate) -> None:
        self._load(event.url)

    @on(Omnibox.Search)
    def _on_search(self, event: Omnibox.Search) -> None:
        self._search(event.query)

    @on(TabBar.Selected)
    async def _on_tab_selected(self, event: TabBar.Selected) -> None:
        self.tabs.select(event.index)
        await self._activate_tab()

    @on(TabBar.NewTab)
    async def _on_new_tab(self, event: TabBar.NewTab) -> None:
        await self.action_new_tab()

    @on(Button.Pressed)
    def _on_button(self, event: Button.Pressed) -> None:
        actions = {
            "nav-back": self.action_back,
            "nav-forward": self.action_forward,
            "nav-reload": self.action_reload,
            "nav-menu": self.action_menu,
        }
        action = actions.get(event.button.id or "")
        if action:
            action()

    # -- navigation core ---------------------------------------------------
    def _load(self, url: str, *, record: bool = True) -> None:
        tab = self.tabs.active
        if record:
            tab.visit(url)
        self._omnibox.set_url(url)
        # Known JS web apps (Gmail, Calendar, …) can't render as text — show a
        # hand-off card instead of fetching, so they're instant and never "blocked".
        app_name = webapps.detect(url)
        if app_name:
            page = Page(url=url, title=app_name, lines=webapps.card_lines(app_name, url))
            tab.page = page
            self._page_view.loading = False
            self._page_view.show_page(page)
            # Selecting a web-app tab opens it in the real browser automatically
            # (once per tab), so the user never has to reach for Ctrl+O.
            if not tab.app_opened:
                tab.app_opened = True
                if self._open_in_browser(url):
                    self._status.show_message(f"Opening {app_name} in your browser…")
                else:
                    self._status.show_message(f"{app_name} · press Ctrl+O to open it")
            else:
                self._status.show_message(f"{app_name} · press Ctrl+O to reopen")
            self._sync_chrome()
            self.call_later(self._tabbar.refresh_tabs)
            return
        self._page_view.show_loading(url)
        self._status.show_loading(url)
        self._sync_chrome()
        self._fetch_worker(url)

    @work(exclusive=True, group="load")
    async def _fetch_worker(self, url: str) -> None:
        self._page_view.loading = True
        try:
            result = await fetch(url)
            tab = self.tabs.active
            if result.url != url:  # followed a redirect
                self._omnibox.set_url(result.url)

            if not result.ok:
                tab.page = Page(url=result.url, title="Problem loading page", is_error=True)
                self._page_view.show_error(result.error or "Unknown error.")
                self._status.show_hint()
                await self._after_load(record_history=False)
                return

            if not result.is_html:
                page = Page(url=result.url, title=result.url)
                page.lines = [
                    "[dim]This content isn't a web page "
                    f"({result.content_type or 'unknown type'}) "
                    "and can't be rendered as text.[/dim]"
                ]
                tab.page = page
                self._page_view.show_page(page)
                self._status.show_hint()
                await self._after_load()
                return

            article = readability.extract(result.html, result.url)
            page = render.render(
                article.content_html,
                base_url=result.url,
                title=article.title,
                url=result.url,
            )
            tab.page = page
            self._page_view.show_page(page)
            self._status.show_message(f"Loaded · {len(page.links)} links")
            await self._after_load()
        except Exception as exc:
            # Never leave the spinner stuck — surface any unexpected failure.
            self.tabs.active.page = Page(url=url, title="Problem loading page", is_error=True)
            self._page_view.show_error(f"Couldn't display this page. ({type(exc).__name__})")
            self._status.show_hint()
            await self._after_load(record_history=False)

    def _search(self, query: str, *, record: bool = True) -> None:
        tab = self.tabs.active
        if record:
            tab.visit(f"search:{query}")
        # Reset pagination for a fresh query.
        self._search_query = query
        self._search_page = 0
        self._page_cursor = {0: None}
        self._next_cursor = {}
        self._omnibox.set_url(query)
        self._page_view.show_loading(f"search · {query}")
        self._status.show_loading(f"searching {self.engine.name}")
        self._sync_chrome()
        self._search_worker(query, 0, None)

    @work(exclusive=True, group="load")
    async def _search_worker(self, query: str, page: int, cursor: object | None) -> None:
        self._page_view.loading = True
        try:
            sp = await self.engine.search(query, limit=20, cursor=cursor)
            tab = self.tabs.active
            if not sp.results and page > 0:
                # Ran past the last page — keep the current one on screen.
                self._page_view.loading = False
                self._status.show_message("No more results")
                return
            self._search_page = page
            self._next_cursor[page] = sp.next_cursor
            page_obj = Page(url=f"search:{query}", title=f"{query} — {self.engine.name}")
            page_obj.links = [
                Link(index=i, text=r.title, url=r.url) for i, r in enumerate(sp.results, 1)
            ]
            tab.page = page_obj
            self._page_view.show_search(
                query, sp.results, page=page, has_next=sp.next_cursor is not None
            )
            self._status.show_message(
                f"{len(sp.results)} results · page {page + 1} · {self.engine.name}"
            )
            await self._after_load(record_history=False)
        except Exception as exc:
            self._page_view.show_error(f"Search failed. ({type(exc).__name__})")
            self._status.show_hint()
            self._page_view.loading = False

    def _is_search_view(self) -> bool:
        page = self.tabs.active.page
        return bool(page and page.url.startswith("search:"))

    def _paginate(self, delta: int) -> None:
        """Load the next (delta>0) or previous (delta<0) page of results."""
        if not self._is_search_view():
            return
        cur = self._search_page
        if delta > 0:
            nxt = self._next_cursor.get(cur)
            if nxt is None:
                self._status.show_message("No more results")
                return
            self._page_cursor[cur + 1] = nxt
            self._search_worker(self._search_query, cur + 1, nxt)
        else:
            if cur <= 0:
                self._status.show_message("Already at the first page")
                return
            self._search_worker(self._search_query, cur - 1, self._page_cursor.get(cur - 1))

    async def _after_load(self, *, record_history: bool = True) -> None:
        tab = self.tabs.active
        self._page_view.loading = False
        if record_history and tab.page and not tab.page.is_error and tab.url:
            self.history.add(tab.url, tab.page.title)
        self._sync_chrome()
        await self._tabbar.refresh_tabs()
        # Land the user in the scrollable page so they can read/scroll at once.
        self._page_view.focus()

    async def _activate_tab(self) -> None:
        """Redraw the page area for the newly-active tab."""
        tab = self.tabs.active
        page = tab.page
        if page is None:
            if tab.url:
                # Unloaded tab (e.g. a default tab): load it now, lazily.
                # _load handles the tab-strip refresh, so return to avoid a
                # second, overlapping refresh.
                self._load(tab.url, record=False)
                return
            self._page_view.show_welcome()
            self._omnibox.set_url("")
        elif page.is_error:
            self._omnibox.set_url(tab.url)
            self._page_view.show_error("This page failed to load.")
        elif page.url.startswith("search:"):
            self._omnibox.set_url(page.url.removeprefix("search:"))
            self._page_view.show_page(page)
        else:
            self._omnibox.set_url(tab.url)
            self._page_view.show_page(page)
        self._sync_chrome()
        await self._tabbar.refresh_tabs()

    def _sync_chrome(self) -> None:
        """Keep toolbar button states in sync with the active tab."""
        tab = self.tabs.active
        self._toolbar.set_back_enabled(tab.can_go_back())
        self._toolbar.set_forward_enabled(tab.can_go_forward())

    # -- actions -----------------------------------------------------------
    def action_focus_omnibox(self) -> None:
        self._omnibox.focus()
        self._omnibox.cursor_position = len(self._omnibox.value)

    async def action_new_tab(self) -> None:
        self.tabs.new_tab()
        await self._activate_tab()
        self.action_focus_omnibox()

    async def action_close_tab(self) -> None:
        self.tabs.close_active()
        await self._activate_tab()

    async def action_next_tab(self) -> None:
        self.tabs.next_tab()
        await self._activate_tab()

    async def action_prev_tab(self) -> None:
        self.tabs.prev_tab()
        await self._activate_tab()

    def action_back(self) -> None:
        url = self.tabs.active.go_back()
        if url is not None:
            self._reopen(url)

    def action_forward(self) -> None:
        url = self.tabs.active.go_forward()
        if url is not None:
            self._reopen(url)

    def _reopen(self, url: str) -> None:
        """Re-open a URL from the nav stack without pushing a new entry."""
        if url.startswith("search:"):
            self._search(url.removeprefix("search:"), record=False)
        else:
            self._load(url, record=False)

    def action_reload(self) -> None:
        tab = self.tabs.active
        if tab.url.startswith("search:"):
            self._search(tab.url.removeprefix("search:"), record=False)
        elif tab.url:
            self._load(tab.url, record=False)

    def _open_in_browser(self, url: str) -> bool:
        """Open ``url`` in the system browser. Returns ``True`` on success."""
        try:
            return webbrowser.open(url)
        except Exception:
            return False

    def action_open_external(self) -> None:
        """Open the current page (or search) in the system's real GUI browser."""
        tab = self.tabs.active
        url = tab.url
        if not url:
            self._status.show_message("Nothing to open yet.")
            return
        if url.startswith("search:"):
            query = url.removeprefix("search:")
            url = f"https://www.google.com/search?q={quote_plus(query)}"
        if self._open_in_browser(url):
            self._status.show_message(f"Opened in your browser · {url}")
        else:
            self.notify(
                f"Couldn't launch a browser here. URL:\n{url}",
                title="Open in browser",
                severity="warning",
                timeout=8,
            )

    def action_bookmark(self) -> None:
        tab = self.tabs.active
        if not tab.url or tab.url.startswith("search:"):
            self._status.show_message("Nothing to bookmark yet.")
            return
        title = tab.page.title if tab.page else tab.url
        now_saved = self.bookmarks.toggle(tab.url, title)
        self._status.show_message("Bookmarked ★" if now_saved else "Bookmark removed")

    def action_history(self) -> None:
        rows = history_rows(self.history.entries())
        self.push_screen(ChooserScreen("History", rows), self._open_from_chooser)

    def action_bookmarks(self) -> None:
        rows = bookmark_rows(self.bookmarks.items())
        self.push_screen(ChooserScreen("Bookmarks", rows), self._open_from_chooser)

    def _open_from_chooser(self, url: str | None) -> None:
        if url:
            self.action_focus_omnibox()
            self._load(url)

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_menu(self) -> None:
        self.push_screen(MainMenu(), self._handle_menu)

    # Menu keys map directly to action names; run_action handles sync + async.
    _MENU_ACTIONS = {
        "new_tab",
        "bookmark",
        "bookmarks",
        "history",
        "reload",
        "open_external",
        "toggle_theme",
        "help",
        "about",
        "quit",
    }

    def _handle_menu(self, key: str | None) -> None:
        if key in self._MENU_ACTIONS:
            self.call_next(self.run_action, key)

    # -- theme -------------------------------------------------------------
    def _apply_saved_theme(self) -> None:
        prefs = load_json(_PREFS_FILE, {})
        pref = prefs.get("theme") if isinstance(prefs, dict) else None
        pref = pref or self.config.theme
        self.theme = LIGHT_THEME if pref == "light" else DARK_THEME

    def action_toggle_theme(self) -> None:
        to_dark = self.theme != DARK_THEME
        self.theme = DARK_THEME if to_dark else LIGHT_THEME
        save_json(_PREFS_FILE, {"theme": "dark" if to_dark else "light"})
        self._status.show_message("Dark mode" if to_dark else "Light mode")

    def action_about(self) -> None:
        self.notify(
            "A lightweight, keyboard-first web browser for your terminal.\n"
            "Fetch + readability rendering · pluggable search.",
            title="google-cli · v0.1.0",
            timeout=6,
        )

    def action_follow_link(self, number: int) -> None:
        """Follow link ``[number]`` on the current page (from markup or keyboard)."""
        tab = self.tabs.active
        if tab.page is None:
            return
        link = tab.page.link(number)
        if link is None:
            self._status.show_message(f"No link [{number}] on this page.")
            return
        self._clear_link_buffer()
        self._load(link.url)

    # -- keyboard link-following buffer -----------------------------------
    def on_key(self, event) -> None:
        if isinstance(self.focused, Omnibox):
            return
        char = event.character or ""
        # n / p page through search results.
        if char in ("n", "p") and not self._link_buffer and self._is_search_view():
            self._paginate(1 if char == "n" else -1)
            event.stop()
            return
        if char.isdigit():
            self._link_buffer += char
            self._status.show_link_buffer(self._link_buffer)
            event.stop()
        elif event.key == "enter" and self._link_buffer:
            number = int(self._link_buffer)
            self._clear_link_buffer()
            self.action_follow_link(number)
            event.stop()
        elif event.key == "escape" and self._link_buffer:
            self._clear_link_buffer()
            self._status.show_hint()
            event.stop()

    def _clear_link_buffer(self) -> None:
        self._link_buffer = ""


def run(initial: str = "") -> None:
    BrowserApp(initial=initial).run()
