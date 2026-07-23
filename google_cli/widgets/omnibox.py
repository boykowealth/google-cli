"""The address/search bar. Emits a single ``Submitted`` intent."""

from __future__ import annotations

from textual import on
from textual.message import Message
from textual.widgets import Input

from ..urls import looks_like_url, normalize_url


class Omnibox(Input):
    """Chrome-style omnibox: type a URL to visit, or text to search."""

    class Navigate(Message):
        """User wants to open ``url`` (already normalized)."""

        def __init__(self, url: str) -> None:
            self.url = url
            super().__init__()

    class Search(Message):
        """User wants to search for ``query``."""

        def __init__(self, query: str) -> None:
            self.query = query
            super().__init__()

    def __init__(self, **kwargs) -> None:
        super().__init__(
            placeholder="Search Google or type a URL",
            id="omnibox",
            **kwargs,
        )

    @on(Input.Submitted)
    def _handle_submit(self, event: Input.Submitted) -> None:
        event.stop()
        text = self.value.strip()
        if not text:
            return
        if looks_like_url(text):
            self.post_message(self.Navigate(normalize_url(text)))
        else:
            self.post_message(self.Search(text))

    def set_url(self, url: str) -> None:
        """Reflect the current page's URL without emitting a message."""
        self.value = url
