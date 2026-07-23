"""Helpers for deciding whether omnibox text is a URL or a search query."""

from __future__ import annotations

import re

# A conservative set of TLD-ish endings and host shapes. We only need to catch
# the common "looks like a domain" cases; everything else becomes a search.
_HAS_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
_DOMAIN = re.compile(
    r"^(localhost|(\d{1,3}\.){3}\d{1,3}|([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})(:\d+)?(/.*)?$"
)


def looks_like_url(text: str) -> bool:
    """Return ``True`` if ``text`` should be treated as an address, not a search.

    Mirrors Chrome's omnibox: an explicit scheme, ``localhost``, an IP, or a
    ``domain.tld`` shape (with no spaces) is a URL; anything else is a query.
    """
    text = text.strip()
    if not text or " " in text:
        return False
    if _HAS_SCHEME.match(text):
        return True
    return bool(_DOMAIN.match(text))


def normalize_url(text: str) -> str:
    """Add a scheme to a bare domain so it can be fetched."""
    text = text.strip()
    if _HAS_SCHEME.match(text):
        return text
    return "https://" + text
