"""HTTP fetching with sensible defaults and friendly error handling."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 google-cli"
)

DEFAULT_TIMEOUT = 15.0


@dataclass(slots=True)
class FetchResult:
    """The outcome of a fetch: either HTML content or a friendly error message."""

    url: str
    html: str = ""
    content_type: str = ""
    status_code: int = 0
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def is_html(self) -> bool:
        return "html" in self.content_type or self.content_type == ""


async def fetch(url: str, *, timeout: float = DEFAULT_TIMEOUT) -> FetchResult:
    """Fetch ``url`` and return a :class:`FetchResult`.

    Network, DNS, timeout and HTTP-status problems are captured as human-readable
    ``error`` strings rather than raised, so callers never crash the UI.
    """
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=timeout, headers=headers
        ) as client:
            response = await client.get(url)
    except httpx.TimeoutException:
        return FetchResult(url, error=f"Timed out after {timeout:.0f}s while loading this page.")
    except httpx.ConnectError:
        return FetchResult(url, error="Couldn't connect. Check the address or your connection.")
    except httpx.RequestError as exc:
        return FetchResult(url, error=f"Network error: {exc}")

    final_url = str(response.url)
    content_type = response.headers.get("content-type", "").lower()

    if response.status_code >= 400:
        return FetchResult(
            final_url,
            status_code=response.status_code,
            content_type=content_type,
            error=f"HTTP {response.status_code} — {_status_phrase(response.status_code)}.",
        )

    return FetchResult(
        final_url,
        html=response.text,
        content_type=content_type,
        status_code=response.status_code,
    )


def _status_phrase(code: int) -> str:
    phrases = {
        401: "Unauthorized",
        403: "Forbidden",
        404: "Page not found",
        429: "Too many requests",
        500: "Server error",
        502: "Bad gateway",
        503: "Service unavailable",
    }
    return phrases.get(code, "Request failed")
