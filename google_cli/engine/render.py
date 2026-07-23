"""Turn extracted HTML into styled terminal lines plus an ordered link list.

The output is a :class:`~google_cli.models.Page` whose ``lines`` are Rich markup
strings (rendered by Textual) and whose ``links`` are numbered so the user can
follow ``[n]`` by typing ``n``.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from rich.markup import escape

from ..models import Link, Page

# Chrome blue reads on both light and dark terminals. Headings use the theme's
# own foreground (bold only) so they adapt; code uses a fixed dark chip, which is
# a familiar convention that stays legible in either theme.
LINK_STYLE = "#4285F4"
HEADING_STYLE = "bold"
CODE_STYLE = "#E8EAED on #2B2B2B"

_BLOCK_TAGS = {
    "p",
    "div",
    "section",
    "article",
    "header",
    "footer",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "table",
    "tr",
    "br",
}
_HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_SKIP = {"script", "style", "noscript", "head", "svg", "form", "nav"}


def render(content_html: str, *, base_url: str, title: str, url: str) -> Page:
    """Render ``content_html`` into a :class:`Page`."""
    page = Page(url=url, title=title)
    try:
        soup = BeautifulSoup(content_html, "lxml")
    except Exception:
        page.lines = [escape(re.sub(r"<[^>]+>", "", content_html))]
        return page

    body = soup.body or soup
    builder = _Builder(base_url)
    builder.walk(body)
    builder.flush()

    page.lines = builder.lines or ["[dim]This page has no readable content.[/dim]"]
    page.links = builder.links
    return page


class _Builder:
    """Accumulates rendered lines and links while walking the DOM."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.lines: list[str] = []
        self.links: list[Link] = []
        self._current: list[str] = []
        self._list_depth = 0

    # -- line management ---------------------------------------------------
    def _push(self, markup: str) -> None:
        self._current.append(markup)

    def flush(self) -> None:
        """Commit the in-progress inline run as a finished line."""
        text = "".join(self._current).strip()
        self._current = []
        if text:
            self.lines.append(text)

    def _blank(self) -> None:
        self.flush()
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    # -- traversal ---------------------------------------------------------
    def walk(self, node: Tag) -> None:
        for child in node.children:
            if isinstance(child, NavigableString):
                self._text(str(child))
            elif isinstance(child, Tag):
                self._tag(child)

    def _text(self, raw: str) -> None:
        text = re.sub(r"\s+", " ", raw)
        if text.strip():
            self._push(escape(text))

    def _tag(self, tag: Tag) -> None:
        name = tag.name.lower()
        if name in _SKIP:
            return
        if name == "a":
            self._anchor(tag)
            return
        if name == "img":
            self._image(tag)
            return
        if name in _HEADINGS:
            self._blank()
            level = int(name[1])
            prefix = "#" * level
            self.flush()
            text = tag.get_text(" ", strip=True)
            if text:
                self.lines.append(f"[{HEADING_STYLE}]{prefix} {escape(text)}[/]")
            self._blank()
            return
        if name in {"strong", "b"}:
            self._push(f"[bold]{escape(tag.get_text(' ', strip=True))}[/bold]")
            return
        if name in {"em", "i"}:
            self._push(f"[italic]{escape(tag.get_text(' ', strip=True))}[/italic]")
            return
        if name == "code" and tag.find_parent("pre") is None:
            self._push(f"[{CODE_STYLE}]{escape(tag.get_text())}[/]")
            return
        if name == "pre":
            self._blank()
            self.flush()
            for line in tag.get_text().splitlines():
                self.lines.append(f"[{CODE_STYLE}]  {escape(line)}[/]")
            self._blank()
            return
        if name == "li":
            self.flush()
            indent = "  " * max(self._list_depth, 1)
            self._push(f"{indent}[dim]•[/dim] ")
            self.walk(tag)
            self.flush()
            return
        if name in {"ul", "ol"}:
            self._blank()
            self._list_depth += 1
            self.walk(tag)
            self._list_depth -= 1
            self._blank()
            return
        if name == "table":
            self._table(tag)
            return
        if name == "br":
            self.flush()
            return
        if name in _BLOCK_TAGS:
            self._blank()
            self.walk(tag)
            self._blank()
            return
        # Inline / unknown container: descend inline.
        self.walk(tag)

    def _anchor(self, tag: Tag) -> None:
        href = (tag.get("href") or "").strip()
        text = re.sub(r"\s+", " ", tag.get_text(" ", strip=True))
        if not href or href.startswith(("javascript:", "#", "mailto:")):
            if text:
                self._push(escape(text))
            return
        url = urljoin(self.base_url, href)
        if not text:
            text = url
        index = len(self.links) + 1
        self.links.append(Link(index=index, text=text, url=url))
        # ``@click`` makes the link mouse-clickable in Textual; the escaped
        # ``\[n]`` renders a literal number so links can also be followed by
        # keyboard. Both call the app's ``follow_link`` action.
        self._push(
            f"[@click=app.follow_link({index})]"
            f"[{LINK_STYLE} underline]\\[{index}] {escape(text)}[/][/]"
        )

    def _image(self, tag: Tag) -> None:
        alt = (tag.get("alt") or "").strip()
        label = alt if alt else "image"
        self._push(f"[dim]\\[image: {escape(label)}][/dim]")

    def _table(self, tag: Tag) -> None:
        """Render an HTML table as an aligned, box-drawn text table."""
        header: list[str] | None = None
        rows: list[list[str]] = []
        for tr in tag.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            texts = [re.sub(r"\s+", " ", c.get_text(" ", strip=True)) for c in cells]
            if not texts:
                continue
            if header is None and cells and all(c.name == "th" for c in cells):
                header = texts
            else:
                rows.append(texts)
        if header is None and not rows:
            return

        all_rows = ([header] if header else []) + rows
        ncols = max(len(r) for r in all_rows)
        all_rows = [r + [""] * (ncols - len(r)) for r in all_rows]

        # Keep the whole table within a sensible width by capping column width.
        col_cap = max(8, 64 // ncols)
        widths = [
            min(max((len(r[c]) for r in all_rows), default=3), col_cap)
            for c in range(ncols)
        ]

        def border(left: str, mid: str, right: str) -> str:
            bar = mid.join("─" * (w + 2) for w in widths)
            return f"[dim]{left}{bar}{right}[/dim]"

        def row(cells: list[str], *, bold: bool = False) -> str:
            parts = []
            for c in range(ncols):
                cell = escape(_fit(cells[c], widths[c]))
                parts.append(f"[bold]{cell}[/bold]" if bold else cell)
            inner = " [dim]│[/dim] ".join(parts)
            return f"[dim]│[/dim] {inner} [dim]│[/dim]"

        self._blank()
        self.flush()
        self.lines.append(border("┌", "┬", "┐"))
        if header:
            self.lines.append(row(all_rows[0], bold=True))
            self.lines.append(border("├", "┼", "┤"))
        body = all_rows[1:] if header else all_rows
        for r in body:
            self.lines.append(row(r))
        self.lines.append(border("└", "┴", "┘"))
        self._blank()


def _fit(text: str, width: int) -> str:
    """Truncate with an ellipsis if needed, then pad to exactly ``width``."""
    if len(text) > width:
        return text[: width - 1] + "…"
    return text.ljust(width)
