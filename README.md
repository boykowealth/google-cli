<div align="center">

# 🔵🔴🟡🟢 &nbsp;google

### A clean, Chrome-styled web browser that lives entirely in your terminal.

Type **`google`**, and browse the web — omnibox, tabs, history, bookmarks and
readable pages, all without leaving the command line.

[![Python](https://img.shields.io/badge/python-3.10%2B-4285F4?logo=python&logoColor=white)](https://www.python.org)
[![Textual](https://img.shields.io/badge/TUI-Textual-34A853)](https://textual.textualize.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-FBBC05)](#license)

</div>

---

```
┌──────────────────────────────────────────────────────────────────────┐
│ ◑ google   Welcome  ·  Python.org ×   +                                │
├──────────────────────────────────────────────────────────────────────┤
│  ←  →  ↻   [ https://www.python.org                       ]   ↗  ☆  ⋮  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  # Welcome to Python                                                   │
│                                                                        │
│  Python is a programming language that lets you work quickly and       │
│  integrate systems more effectively.                                   │
│                                                                        │
│  [1] Download Python      [2] Documentation      [3] Community         │
│                                                                        │
├──────────────────────────────────────────────────────────────────────┤
│ Loaded · 34 links                              Ctrl+L address · ? help │
└──────────────────────────────────────────────────────────────────────┘
```

## ✨ Features

- **Omnibox** — type a URL to visit, or plain text to search (just like Chrome).
- **Tabs** — open, close and switch between multiple pages.
- **Back / forward & history** — a per-tab navigation stack plus persistent, browsable history.
- **Bookmarks** — star pages and reopen them anytime; saved to disk.
- **Readable rendering** — pages are distilled to their main content, with **numbered links**
  you follow by typing a number or clicking.
- **Hand off to your real browser** — press `Ctrl+O` (or the ↗ button) to open the current
  page in your system's GUI browser at any time.
- **Pluggable search** — DuckDuckGo out of the box (no API key), or plug in the Google
  Programmable Search API.
- **Clean, subtle branding** — Chrome's four colours used sparingly; light- and dark-terminal aware.
- **Unbreakable** — timeouts, dead links and bad addresses show a friendly message, never a crash.

## 🚀 Quick Start

The recommended way puts a `google` command on your `PATH` in an isolated environment:

```bash
# Install pipx once (if you don't have it)
python3 -m pip install --user pipx && python3 -m pipx ensurepath

# Install google-cli
pipx install git+https://github.com/boykowealth/google-cli.git

# …or from a local clone
git clone https://github.com/boykowealth/google-cli.git
pipx install ./google-cli
```

Then just:

```bash
google                 # start at the home screen
google github.com      # open a page directly
google "best pizza"    # jump straight into search results
```

<details>
<summary>Prefer plain <code>pip</code>?</summary>

```bash
pip install --user git+https://github.com/boykowealth/google-cli.git
# make sure your user scripts dir is on PATH, then run `google`
```
</details>

## ⌨️ Usage

Everything is keyboard-first (and mouse-clickable where it helps).

| Key | Action |
| --- | --- |
| `Ctrl+L` | Focus the omnibox |
| `Enter` | Visit URL / search / follow a typed link number |
| *digits* then `Enter` | Follow link `[n]` on the page (`Esc` cancels) |
| `Ctrl+T` / `Ctrl+W` | New tab / close tab |
| `Ctrl+Tab` | Next tab |
| `Alt+←` / `Alt+→` | Back / forward |
| `Ctrl+R` | Reload |
| `Ctrl+O` | **Open the current page in your real GUI browser** ↗ |
| `Ctrl+D` | Bookmark this page |
| `Ctrl+H` / `Ctrl+B` | History / bookmarks |
| `F2` | Open the ⋮ menu |
| `?` | Keyboard shortcuts |
| `Ctrl+Q` | Quit |

## ⚙️ Configuration

Settings live in a TOML file at `~/.config/google-cli/config.toml` (all fields optional):

```toml
[general]
homepage = "https://news.ycombinator.com"

[search]
# "duckduckgo" (default, no key) or "google"
engine = "duckduckgo"

# Only needed for engine = "google" (Google Programmable Search API)
api_key = "YOUR_API_KEY"
cx = "YOUR_SEARCH_ENGINE_ID"
```

You can also supply the Google API credentials via environment variables, which
override the file:

```bash
export GOOGLE_CLI_API_KEY="…"
export GOOGLE_CLI_CX="…"
```

History and bookmarks are stored as JSON under `~/.local/share/google-cli/`.

## 🧠 How it works

`google` is intentionally lightweight — there's no embedded browser engine:

1. **Fetch** the page over HTTP (`httpx`), following redirects.
2. **Extract** the main article content (`readability-lxml`), stripping nav, ads and clutter.
3. **Render** the result into styled terminal lines with ordered, followable links.

This makes it fast, dependency-light and installable with a single `pip`/`pipx`
command anywhere. The trade-off: JavaScript-heavy apps that build their content
client-side won't render fully.

## 🛠️ Development

```bash
git clone https://github.com/boykowealth/google-cli.git
cd google-cli
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest            # run the test suite
ruff check .      # lint
python -m google_cli   # run from source
```

## 🗺️ Roadmap

- Optional headless-Chrome rendering for JavaScript-heavy sites
- Inline images via terminal graphics (Kitty / iTerm / sixel)
- Tab session restore
- Find-in-page

## License

MIT © Brayden Boyko
