"""Tiny JSON persistence helper shared by history and bookmarks."""

from __future__ import annotations

import json
from pathlib import Path

from .config import data_dir


def _path(filename: str) -> Path:
    return data_dir() / filename


def load_json(filename: str, default: list | dict) -> list | dict:
    """Load JSON from the data dir, returning ``default`` on any problem."""
    path = _path(filename)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save_json(filename: str, data: list | dict) -> None:
    """Write ``data`` as JSON to the data dir, creating it if needed."""
    path = _path(filename)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        # Persistence is best-effort; never crash the browser over it.
        pass
