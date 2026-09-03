from webapp_theme_streamlit import fetch_apps_directory, strip_css_comments


def test_strip_css_comments_removes_block_comments():
    css = "a { color: red; } /* a comment mentioning <a-tag> */ b { color: blue; }"
    assert strip_css_comments(css) == "a { color: red; }  b { color: blue; }"


def test_strip_css_comments_handles_multiline_comments():
    css = "a { color: red; }\n/* line one\n   line two */\nb { color: blue; }"
    assert strip_css_comments(css) == "a { color: red; }\n\nb { color: blue; }"


def test_fetch_apps_directory_returns_empty_list_on_failure(monkeypatch):
    import requests

    def _raise(*args, **kwargs):
        raise requests.RequestException("boom")

    monkeypatch.setattr(requests, "get", _raise)
    fetch_apps_directory.clear()
    assert fetch_apps_directory("https://example.invalid/apps.json") == []
