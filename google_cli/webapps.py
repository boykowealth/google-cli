"""Recognise Google (and similar) web apps that a text browser can't render.

These are JavaScript single-page apps behind a sign-in — Gmail, Calendar, etc.
Fetching their HTML yields no readable content, so instead of failing we show a
clean card that hands off to the real browser with one key (Ctrl+O).
"""

from __future__ import annotations

from urllib.parse import urlparse

KNOWN_APPS: dict[str, str] = {
    "mail.google.com": "Gmail",
    "calendar.google.com": "Google Calendar",
    "drive.google.com": "Google Drive",
    "docs.google.com": "Google Docs",
    "sheets.google.com": "Google Sheets",
    "meet.google.com": "Google Meet",
    "keep.google.com": "Google Keep",
    "photos.google.com": "Google Photos",
}


def detect(url: str) -> str | None:
    """Return the friendly app name if ``url`` is a known web app, else ``None``."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return None
    for domain, name in KNOWN_APPS.items():
        if host == domain or host.endswith("." + domain):
            return name
    return None


def card_lines(name: str, url: str) -> list[str]:
    """The rendered body for a web-app hand-off card."""
    return [
        "",
        f"[bold]{name}[/bold]",
        "",
        f"[dim]{name} is an interactive web app — it needs a full browser"
        " (JavaScript and your Google sign-in), so it can't be shown as text here.[/dim]",
        "",
        "[#4285F4]Press [b]Ctrl+O[/b] to open it in your real browser ↗[/]",
        "",
        f"[dim]{url}[/dim]",
    ]
