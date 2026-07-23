"""Extract the main readable content from a raw HTML document.

By default we use ``readability-lxml`` for a clean reading view. But readability
strips ``<table>`` elements, so when a page has real data tables that got
dropped, we fall back to the page's semantic main-content node (``<main>`` /
``<article>`` / common content ids) which preserves tables, links and structure.
"""

from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup

# Ordered by specificity: the first that holds real content wins.
_MAIN_SELECTORS = [
    "main",
    "article",
    "[role=main]",
    "#mw-content-text",  # Wikipedia / MediaWiki
    "#content",
    "#main",
    ".article-body",
    ".post-content",
    ".entry-content",
]

# Junk to drop from a semantic main node before rendering.
_JUNK_SELECTORS = (
    "script, style, noscript, nav, footer, header, aside, form, "
    ".navbox, .reflist, .mw-editsection, .mw-jump-link, .toc, "
    ".sidebar, .infobox-below, .noprint"
)


@dataclass(slots=True)
class Article:
    """Extracted main content plus the document title."""

    title: str
    content_html: str


def extract(html: str, url: str) -> Article:
    """Return the primary article content of ``html``.

    Prefers readability's clean summary, but keeps tables: if the summary has no
    table while the page clearly does, use the semantic main node instead.
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
    if _dropped_a_table(summary, html):
        main = _main_content(html)
        if main:
            content_html = main

    if not title:
        title = _fallback_title(html) or url
    return Article(title=title, content_html=content_html)


def _dropped_a_table(summary: str, html: str) -> bool:
    """True if the page has a real data table that the summary doesn't."""
    if "<table" in summary.lower():
        return False
    return _has_data_table(html)


def _has_data_table(html: str) -> bool:
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return False
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        cells = table.find_all(["td", "th"])
        if len(rows) >= 2 and len(cells) >= 4:
            return True
    return False


def _main_content(html: str) -> str | None:
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return None
    for selector in _MAIN_SELECTORS:
        node = soup.select_one(selector)
        if node is None:
            continue
        if len(node.get_text(strip=True)) < 200:
            continue
        for junk in node.select(_JUNK_SELECTORS):
            junk.decompose()
        return str(node)
    return None


def _fallback_title(html: str) -> str:
    try:
        soup = BeautifulSoup(html, "lxml")
        if soup.title and soup.title.string:
            return soup.title.string.strip()
    except Exception:
        pass
    return ""
