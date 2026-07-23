"""User configuration loaded from ``~/.config/google-cli/config.toml``."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - py310 fallback
    import tomli as tomllib  # type: ignore

APP_NAME = "google-cli"


def config_dir() -> Path:
    return Path(user_config_dir(APP_NAME))


def data_dir() -> Path:
    return Path(user_data_dir(APP_NAME))


@dataclass(slots=True)
class Config:
    """Resolved user settings.

    Environment variables ``GOOGLE_CLI_API_KEY`` / ``GOOGLE_CLI_CX`` override the
    config file, which is handy for the Google Programmable Search API.
    """

    search_engine: str = "duckduckgo"
    api_key: str = ""
    cx: str = ""
    homepage: str = ""
    theme: str = "light"  # "dark" or "light"; runtime toggle (F6) overrides this
    default_tabs: list[str] = field(
        default_factory=lambda: [
            "https://mail.google.com/",
            "https://calendar.google.com/",
        ]
    )

    @classmethod
    def load(cls) -> Config:
        cfg = cls()
        path = config_dir() / "config.toml"
        if path.exists():
            try:
                data = tomllib.loads(path.read_text(encoding="utf-8"))
            except (OSError, tomllib.TOMLDecodeError):
                data = {}
            search = data.get("search", {})
            cfg.search_engine = search.get("engine", cfg.search_engine)
            cfg.api_key = search.get("api_key", cfg.api_key)
            cfg.cx = search.get("cx", cfg.cx)
            general = data.get("general", {})
            cfg.homepage = general.get("homepage", cfg.homepage)
            cfg.theme = general.get("theme", cfg.theme)
            tabs = general.get("default_tabs")
            if isinstance(tabs, list):
                cfg.default_tabs = [str(t) for t in tabs]

        cfg.api_key = os.environ.get("GOOGLE_CLI_API_KEY", cfg.api_key)
        cfg.cx = os.environ.get("GOOGLE_CLI_CX", cfg.cx)
        return cfg
