"""Shared navbar/app-switcher rendering for every Streamlit app in this
household's stack (cgm_abbot_connector, health-gen-ai-chat's dashboard).

Extracted here after the same ~150 lines of CSS/HTML/JS were found
duplicated - and had already drifted - between both apps: a fix for the
app-switcher's icon landed in cgm_abbot_connector but not
health-gen-ai-chat, since there was no single place to fix it once for
both. This package is that place.

Split from the Bootstrap apps' switcher.js/app.css (also in this repo)
because Streamlit can't use either directly: st.html()'s sanitizer strips
<link> tags (so app.css has to be fetched and inlined instead - see
inject_shared_theme()) and <svg>/<script src="..."> content wholesale (so
the switcher toggle below is hand-rolled markup + a small inline <script>,
not Bootstrap's real dropdown component or an <svg> icon - confirmed
empirically by inspecting the rendered DOM, not assumed, after both a real
Bootstrap Icon and an inline SVG silently vanished).

Usage:
    from webapp_theme_streamlit import inject_shared_theme, render_app_switcher

    inject_shared_theme(extra_css=MY_APP_SPECIFIC_CSS)
    with st.container(key="app_navbar"):
        cols = st.columns([4, 3, 2, 1])
        with cols[0]:
            st.html(f'<span class="navbar-brand">{icon} {brand}<span class="brand-accent">{accent}</span></span>')
        with cols[1]:
            render_app_switcher(current_app_id="cgm", user_groups=user["groups"], apps_label=translate(locale, "nav.apps"))
        with cols[2]:
            ...  # this app's own profile popover
        with cols[3]:
            ...  # this app's own logout button
"""
import re
import textwrap

import requests
import streamlit as st

DEFAULT_APP_CSS_URL = "https://cdn.jsdelivr.net/gh/robertobeanuoc/webapp-theme@v1.1.0/app.css"
DEFAULT_APPS_JSON_URL = "https://cdn.jsdelivr.net/gh/robertobeanuoc/webapp-theme@main/apps.json"


def strip_css_comments(css: str) -> str:
    """Removes /* ... */ comments from a CSS string.

    Required before anything reaches st.html(): its sanitizer discards an
    entire <style> block if it contains what looks like a disallowed HTML
    tag ANYWHERE in the text - including plain descriptive text inside a
    CSS comment, since it isn't CSS-aware and can't tell a comment from
    live markup. Every CSS string passed through this module goes through
    this before combining, not just the fetched one, so a future comment
    mentioning an example tag can't silently reintroduce this failure mode.
    """
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


# Navbar shell + app-switcher, shared by every Streamlit app that calls
# inject_shared_theme() - NOT page-content styling like stMetric/stForm/
# stSelectbox, which stays app-specific (pass it via inject_shared_theme's
# extra_css instead of adding it here).
_SHARED_CSS = textwrap.dedent("""\
    [data-testid="stAppViewContainer"] { background-color: var(--ns-surface); }
    [data-testid="stHeader"] { background-color: transparent; }
    [data-testid="stMainBlockContainer"] { padding-top: 5rem; }

    .st-key-app_navbar {
        background-color: var(--ns-navbar);
        border-radius: .75rem;
        padding: .5rem 1.25rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 4px rgba(0,0,0,.3);
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .st-key-app_navbar .navbar-brand {
        font-weight: 700;
        font-size: 1.2rem;
        letter-spacing: -.3px;
        color: #fff;
      }
      .st-key-app_navbar .brand-accent { color: #4ade80; }

      .st-key-logout_btn button {
        background: transparent;
        border: 1px solid transparent;
        color: rgba(255,255,255,.7);
        font-weight: 500;
      }
      .st-key-logout_btn button:hover {
        color: #fff;
        background-color: rgba(255,255,255,.1);
      }

      .st-key-profile_popover button {
        background: transparent;
        border: 1px solid transparent;
        color: rgba(255,255,255,.7);
        font-weight: 500;
      }
      .st-key-profile_popover button:hover {
        color: #fff;
        background-color: rgba(255,255,255,.1);
      }

      .app-switcher-dropdown { position: relative; display: inline-block; }
      .app-switcher-toggle {
        cursor: pointer;
        color: rgba(255,255,255,.7);
        background: transparent;
        border: none;
        font-size: .875rem;
        font-weight: 500;
        text-decoration: none;
        padding: .4rem .75rem;
        border-radius: .375rem;
      }
      .app-switcher-toggle:hover { color: #fff; background-color: rgba(255,255,255,.1); }
      .app-switcher-toggle .grid-icon {
        display: inline-block;
        width: 2px;
        height: 2px;
        margin-right: .5rem;
        vertical-align: middle;
        background: currentColor;
        box-shadow:
          -5px -5px 0 currentColor, 0 -5px 0 currentColor, 5px -5px 0 currentColor,
          -5px 0 0 currentColor, 5px 0 0 currentColor,
          -5px 5px 0 currentColor, 0 5px 0 currentColor, 5px 5px 0 currentColor;
      }
      .app-switcher-toggle::after {
        display: inline-block;
        margin-left: .255em;
        vertical-align: .255em;
        content: "";
        border-top: .3em solid;
        border-right: .3em solid transparent;
        border-bottom: 0;
        border-left: .3em solid transparent;
      }
      .app-switcher-menu {
        position: absolute;
        top: 100%;
        right: 0;
        z-index: 1000;
        display: none;
        min-width: 10rem;
        padding: .5rem 0;
        margin: .25rem 0 0;
        background-color: #fff;
        border: 1px solid #e2e8f0;
        border-radius: .5rem;
        box-shadow: var(--ns-card-shadow);
        list-style: none;
      }
      .app-switcher-menu.show { display: block; }
      .app-switcher-menu a {
        display: block;
        padding: .4rem 1rem;
        color: #0f172a;
        text-decoration: none;
        white-space: nowrap;
        font-size: .875rem;
      }
      .app-switcher-menu a:hover { background-color: #f8fafc; }
    """)


@st.cache_data(ttl=3600)
def _fetch_app_css(url: str) -> str:
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.text


def inject_shared_theme(extra_css: str = "", app_css_url: str = DEFAULT_APP_CSS_URL) -> None:
    """Fetches the shared design tokens (app.css) and combines them with
    the navbar/switcher CSS above plus this app's own extra_css (stMetric,
    stForm, whatever else it needs), then injects the lot via st.html().

    Uses st.html() rather than st.markdown(..., unsafe_allow_html=True):
    the latter runs the string through Streamlit's Markdown sanitizer even
    with unsafe_allow_html, which strips <style> tags. st.html() renders
    raw HTML with no Markdown pass, so the <style> tag survives intact.
    """
    css = (
        strip_css_comments(_fetch_app_css(app_css_url))
        + strip_css_comments(_SHARED_CSS)
        + strip_css_comments(extra_css)
    )
    st.html(f"<style>{css}</style>")


@st.cache_data(ttl=60)  # short: apps.json lives on @main and can change without a tag bump
def fetch_apps_directory(url: str = DEFAULT_APPS_JSON_URL) -> list[dict]:
    """The cross-app navigation directory - see
    https://github.com/robertobeanuoc/webapp-theme's apps.json. `[]` (menu
    just doesn't render) rather than an error if the CDN is briefly
    unreachable - this is a nice-to-have, not core functionality."""
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json().get("apps", [])
    except Exception:
        # Deliberately broad, not just requests.RequestException: this is decorative content
        # (theme/switcher), and a malformed response must never break the actual dashboard below it.
        return []


def render_app_switcher(
    current_app_id: str,
    user_groups: list[str],
    apps_label: str,
    apps_json_url: str = DEFAULT_APPS_JSON_URL,
) -> None:
    """The "Apps" dropdown - only the apps the user actually has access to
    (per their groups), excluding the one they're already on. Renders
    nothing if there's nothing to show, matching the Bootstrap apps'
    switcher.js.

    A hand-rolled open/close toggle, not Bootstrap's real dropdown
    component: Bootstrap's JS bundle builds its Tooltip/Popover markup from
    template strings that read as tag-like text to st.html()'s sanitizer,
    so the whole ~80KB script gets silently dropped the same way a single
    tag-like CSS comment does - confirmed by testing it directly, not
    assumed. The toggle/close behavior below is small enough to guarantee
    has no such text.
    """
    other_apps = [
        app
        for app in fetch_apps_directory(apps_json_url)
        if app["id"] != current_app_id and app["authentik_group"] in user_groups
    ]
    if not other_apps:
        return

    items = "".join(
        f'<a href="{app["url"]}" target="_blank" rel="noopener noreferrer">'
        f'{app["emoji"]} {app["brand"]}{app["accent"]}</a>'
        for app in other_apps
    )
    st.html(
        '<div class="app-switcher-dropdown">'
        '<a class="app-switcher-toggle" href="#" role="button">'
        '<span class="grid-icon"></span>'
        f"{apps_label}</a>"
        f'<div class="app-switcher-menu">{items}</div>'
        "</div>"
    )
    st.html(
        "<script>"
        "document.querySelectorAll('.app-switcher-toggle').forEach(function (toggle) {"
        "  if (toggle.dataset.wired) return;"
        "  toggle.dataset.wired = '1';"
        "  toggle.addEventListener('click', function (e) {"
        "    e.preventDefault();"
        "    var menu = toggle.nextElementSibling;"
        "    var isOpen = menu.classList.contains('show');"
        "    document.querySelectorAll('.app-switcher-menu.show').forEach(function (m) { m.classList.remove('show'); });"
        "    if (!isOpen) menu.classList.add('show');"
        "  });"
        "});"
        "if (!window.__appSwitcherOutsideClickWired) {"
        "  window.__appSwitcherOutsideClickWired = true;"
        "  document.addEventListener('click', function (e) {"
        "    if (!e.target.closest('.app-switcher-dropdown')) {"
        "      document.querySelectorAll('.app-switcher-menu.show').forEach(function (m) { m.classList.remove('show'); });"
        "    }"
        "  });"
        "}"
        "</script>",
        unsafe_allow_javascript=True,
    )
