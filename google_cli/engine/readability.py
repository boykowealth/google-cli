"""Extract the main readable content from a raw HTML document.

We use ``readability-lxml`` for a clean reading view (this is the behaviour that
worked well). readability strips ``<table>`` elements, so — and only so — we
re-attach the page's real data tables to the cleaned content afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup

# Junk to remove from any table we re-attach.
_TABLE_JUNK = "script, style, noscript, .mw-editsection, .reference, sup.reference"

_MAX_TABLES = 8  # don't bloat a page with dozens of tables


@dataclass(slots=True)
class Article:
    """Extracted main content plus the document title."""

    title: str
    content_html: str


def extract(html: str, url: str) -> Article:
    """Return the primary article content of ``html``.

    Clean readability output, with real data tables re-attached (readability
    drops them). Any failure falls back to the raw HTML so nothing is unrenderable.
    """
    title = ""
    summary = ""
    try:
        from readability import Document  # type: ignore

        doc = Document(html)
        title = (doc.short_title() or "").strip()
        summary = doc.summary(html_partial=True) or ""
    except Exception:
        summary = ""

    content_html = summary or html
    # Only re-attach tables when the cleaned content lost them.
    if "<table" not in content_html.lower():
        tables = _data_tables(html)
        if tables:
            content_html = content_html + "\n" + "\n".join(tables)

    if not title:
        title = _fallback_title(html) or url
    return Article(title=title, content_html=content_html)


def _data_tables(html: str) -> list[str]:
    """Return cleaned HTML for the page's real data tables (not layout tables)."""
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return []
    tables: list[str] = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        cells = table.find_all(["td", "th"])
        # Heuristics: a data table has several rows and cells; layout tables
        # tend to have very few rows or a single wide cell.
        if len(rows) < 2 or len(cells) < 4:
            continue
        for junk in table.select(_TABLE_JUNK):
            junk.decompose()
        tables.append(str(table))
        if len(tables) >= _MAX_TABLES:
            break
    return tables


def _fallback_title(html: str) -> str:
    try:
        soup = BeautifulSoup(html, "lxml")
        if soup.title and soup.title.string:
            return soup.title.string.strip()
    except Exception:
        pass
    return ""
