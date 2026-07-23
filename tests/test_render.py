from google_cli.engine.render import render


def test_links_are_numbered_in_order():
    html = """
    <div>
      <p>Intro text with <a href="/a">first</a> and <a href="https://x.com/b">second</a>.</p>
      <p>Then a <a href="/c">third</a> link.</p>
    </div>
    """
    page = render(html, base_url="https://site.test/page", title="T", url="https://site.test/page")

    assert [link.index for link in page.links] == [1, 2, 3]
    assert [link.text for link in page.links] == ["first", "second", "third"]
    # Relative links are resolved against the base url.
    assert page.links[0].url == "https://site.test/a"
    assert page.links[1].url == "https://x.com/b"


def test_javascript_and_anchor_links_are_skipped():
    html = (
        '<p><a href="#top">top</a> '
        '<a href="javascript:void(0)">x</a> '
        '<a href="/real">real</a></p>'
    )
    page = render(html, base_url="https://s.test/", title="T", url="https://s.test/")

    assert len(page.links) == 1
    assert page.links[0].url == "https://s.test/real"


def test_image_alt_placeholder_present():
    html = '<p>Before <img src="x.png" alt="A cat"> after</p>'
    page = render(html, base_url="https://s.test/", title="T", url="https://s.test/")
    body = "\n".join(page.lines)
    assert "image: A cat" in body


def test_table_renders_as_box():
    html = """
    <table>
      <tr><th>Name</th><th>Role</th></tr>
      <tr><td>Ada</td><td>Engineer</td></tr>
      <tr><td>Grace</td><td>Admiral</td></tr>
    </table>
    """
    page = render(html, base_url="https://s.test/", title="T", url="https://s.test/")
    body = "\n".join(page.lines)
    # Box-drawing borders and the cell contents are present.
    assert "┌" in body and "┴" in body and "│" in body
    assert "Name" in body and "Role" in body
    assert "Ada" in body and "Engineer" in body and "Grace" in body


def test_link_lookup_by_number():
    html = '<a href="/one">one</a><a href="/two">two</a>'
    page = render(html, base_url="https://s.test/", title="T", url="https://s.test/")
    assert page.link(2).url == "https://s.test/two"
    assert page.link(3) is None
