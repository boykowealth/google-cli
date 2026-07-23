"""Console entry point: ``google [url-or-search-terms...]``."""

from __future__ import annotations

import argparse
import sys

from . import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="google",
        description="A clean, Chrome-styled web browser for your terminal.",
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="A URL to open, or search terms. Omit to start at the home screen.",
    )
    parser.add_argument("-v", "--version", action="version", version=f"google-cli {__version__}")
    args = parser.parse_args(argv)

    # Import here so `google --version` / `--help` stay instant and dependency-light.
    from .app import BrowserApp

    initial = " ".join(args.query).strip()
    try:
        BrowserApp(initial=initial).run()
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
