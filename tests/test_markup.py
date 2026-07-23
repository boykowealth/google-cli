from google_cli.markup import escape


def test_escapes_every_open_bracket():
    # Both matched and lone brackets must be escaped (rich.escape misses lone ones).
    assert escape("[dubious]") == r"\[dubious]"
    assert escape("[lonely") == r"\[lonely"
    assert escape("a [b [c") == r"a \[b \[c"


def test_escapes_backslash_first():
    assert escape("\\") == "\\\\"


def test_plain_text_unchanged():
    assert escape("hello world") == "hello world"
