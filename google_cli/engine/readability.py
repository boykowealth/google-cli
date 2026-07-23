"""Extract the main readable content from a raw HTML document."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Article:
    """Extracted main content plus the document title."""

    title: str
    content_html: str


def extract(html: str, url: str) -> Article:
    """Return the primary article content of ``html``.

    Uses ``readability-lxml`` when available to strip navigation, ads and
    boilerplate. Falls back to the raw document if extraction fails so that no
    page is ever completely unrenderable.
    """
    title = ""
    content_html = html
    try:
        from readability import Document  # type: ignore

        doc = Document(html)
        title = (doc.short_title() or "").strip()
        summary = doc.summary(html_partial=True)
        if summary and summary.strip():
            content_html = summary
    except Exception:
        # Any parsing failure: fall back to the raw HTML; render.py is tolerant.
        pass

    if not title:
        title = _fallback_title(html) or url
    return Article(title=title, content_html=content_html)


def _fallback_title(html: str) -> str:
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        if soup.title and soup.title.string:
            return soup.title.string.strip()
    except Exception:
        pass
    return ""
