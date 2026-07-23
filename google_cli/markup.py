"""Robust escaping of arbitrary text for Textual/Rich markup.

``rich.markup.escape`` only escapes ``[`` that begins a well-formed ``[...]``
token, so a lone ``[`` in web text (e.g. Wikipedia's "[dubious – discuss]", or a
truncated table cell) slips through and breaks Textual's stricter parser —
taking the whole page down with a MarkupError. We escape *every* ``[`` so no
page content can ever be mistaken for markup.
"""

from __future__ import annotations


def escape(text: str) -> str:
    """Escape ``text`` so it renders literally inside markup."""
    return text.replace("\\", "\\\\").replace("[", r"\[")
