from google_cli.models import SearchPage, SearchResult
from google_cli.search.base import SearchEngine
from google_cli.search.bing import parse_results as bing_parse
from google_cli.search.duckduckgo import parse_next_cursor
from google_cli.search.duckduckgo import parse_results as ddg_parse
from google_cli.search.google_api import parse_results as google_parse
from google_cli.search.multi import MultiEngine

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


BING_HTML = """
<ol id="b_results">
  <li class="b_algo">
    <h2><a href="https://a.test/page">Title A</a></h2>
    <div class="b_caption"><p>Snippet A</p></div>
  </li>
  <li class="b_algo"><h2><a href="https://b.test">Title B</a></h2></li>
  <li class="b_algo"><h2><a href="/relative-ignored">No scheme</a></h2></li>
</ol>
"""


def test_bing_parses_results_and_skips_relative():
    results = bing_parse(BING_HTML)
    assert [r.url for r in results] == ["https://a.test/page", "https://b.test"]
    assert results[0].title == "Title A"
    assert results[0].snippet == "Snippet A"


class _Empty(SearchEngine):
    async def search(self, query, *, limit=20, cursor=None):
        return SearchPage([], None)


class _Full(SearchEngine):
    async def search(self, query, *, limit=20, cursor=None):
        return SearchPage([SearchResult("t", "https://u.test")], next_cursor=5)


async def test_multi_engine_falls_through_to_a_working_provider():
    engine = MultiEngine([_Empty(), _Full()])
    sp = await engine.search("q")
    assert len(sp.results) == 1
    # Cursor remembers which provider (index 1) answered, plus its sub-cursor.
    assert sp.next_cursor == (1, 5)
    # Paging reuses that provider directly.
    sp2 = await engine.search("q", cursor=sp.next_cursor)
    assert len(sp2.results) == 1


async def test_multi_engine_empty_when_all_block():
    engine = MultiEngine([_Empty(), _Empty()])
    sp = await engine.search("q")
    assert sp.results == [] and sp.next_cursor is None
