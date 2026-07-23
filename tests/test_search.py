from google_cli.search.duckduckgo import parse_next_cursor
from google_cli.search.duckduckgo import parse_results as ddg_parse
from google_cli.search.google_api import parse_results as google_parse

DDG_HTML = """
<div class="result">
  <a class="result__a" href="/l/?uddg=https%3A%2F%2Fexample.com%2Fpage">Example Page</a>
  <a class="result__snippet">A useful snippet.</a>
</div>
<div class="result">
  <a class="result__a" href="https://direct.test/x">Direct Result</a>
</div>
"""


def test_ddg_unwraps_redirect_and_parses():
    results = ddg_parse(DDG_HTML)
    assert len(results) == 2
    assert results[0].title == "Example Page"
    assert results[0].url == "https://example.com/page"
    assert results[0].snippet == "A useful snippet."
    assert results[1].url == "https://direct.test/x"


def test_ddg_respects_limit():
    assert len(ddg_parse(DDG_HTML, limit=1)) == 1


def test_ddg_skips_ads():
    html = """
    <div class="result result--ad">
      <a class="result__a" href="https://duckduckgo.com/y.js?ad_domain=x">Sponsored</a>
    </div>
    <div class="result">
      <a class="result__a" href="https://real.test/page">Real</a>
    </div>
    """
    results = ddg_parse(html)
    assert len(results) == 1
    assert results[0].url == "https://real.test/page"


def test_google_api_parses_items():
    data = {
        "items": [
            {"title": "One", "link": "https://one.test", "snippet": "s1"},
            {"title": "Two", "link": "https://two.test", "snippet": "s2"},
        ]
    }
    results = google_parse(data)
    assert [r.url for r in results] == ["https://one.test", "https://two.test"]
    assert results[0].title == "One"


def test_google_api_empty_on_no_items():
    assert google_parse({}) == []


def test_ddg_next_cursor_captures_form_fields():
    html = """
    <div class="nav-link">
      <form action="/html/" method="post">
        <input type="hidden" name="q" value="cats">
        <input type="hidden" name="s" value="30">
        <input type="hidden" name="nextParams" value="xyz">
        <input type="hidden" name="vqd" value="4-abc">
        <input type="submit" value="Next">
      </form>
    </div>
    """
    cursor = parse_next_cursor(html, "cats")
    assert cursor == {"q": "cats", "s": "30", "nextParams": "xyz", "vqd": "4-abc"}


def test_ddg_next_cursor_none_when_no_next_form():
    html = '<div class="result"><a class="result__a" href="https://x.test">X</a></div>'
    assert parse_next_cursor(html, "cats") is None
