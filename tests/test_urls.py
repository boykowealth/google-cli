from google_cli.urls import looks_like_url, normalize_url


def test_scheme_is_url():
    assert looks_like_url("https://example.com")
    assert looks_like_url("http://localhost:8000/path")


def test_bare_domain_is_url():
    assert looks_like_url("example.com")
    assert looks_like_url("news.ycombinator.com/newest")
    assert looks_like_url("192.168.0.1")
    assert looks_like_url("localhost")


def test_plain_text_is_search():
    assert not looks_like_url("best pizza near me")
    assert not looks_like_url("python")  # single word, no dot
    assert not looks_like_url("what is a domain.tld thing")  # has spaces


def test_normalize_adds_scheme():
    assert normalize_url("example.com") == "https://example.com"
    assert normalize_url("http://x.com") == "http://x.com"
