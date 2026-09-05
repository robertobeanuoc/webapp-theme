# webapp-theme-streamlit

Shared navbar + app-switcher rendering for every Streamlit app in this household's stack (`datacarebot-cgm`, `datacarebot-chat`'s dashboard) - the Streamlit-side equivalent of this repo's `app.css`/`switcher.js` for the Bootstrap apps, which Streamlit can't use directly (see the module docstring in `src/webapp_theme_streamlit/__init__.py` for why).

## Install

```toml
# pyproject.toml
dependencies = [
    "webapp-theme-streamlit @ git+https://github.com/robertobeanuoc/datacarebot-theme.git@main#subdirectory=python",
]
```

Pinned to `@main`, same as `datacarebot-streamlit-auth` - `uv.lock` records the exact commit at lock time, so a later push here doesn't silently change a running app; run `uv lock --upgrade-package webapp-theme-streamlit` to pick up a change.

## Usage

```python
import streamlit as st
from webapp_theme_streamlit import inject_shared_theme, render_app_switcher

MY_APP_CSS = """
    [data-testid="stMetric"] { ... }  # this app's own page-content styling
"""

inject_shared_theme(extra_css=MY_APP_CSS)

with st.container(key="app_navbar"):
    cols = st.columns([4, 3, 2, 1])
    with cols[0]:
        st.html('<span class="navbar-brand">\U0001FA78 CGM<span class="brand-accent">Dashboard</span></span>')
    with cols[1]:
        render_app_switcher(
            current_app_id="cgm",
            user_groups=user["groups"],
            apps_label=translate(locale, "nav.apps"),
        )
    with cols[2]:
        ...  # this app's own profile popover - language/account links are
             # app-specific enough (own i18n, own vault) to stay out of here
    with cols[3]:
        ...  # this app's own logout button
```

`inject_shared_theme()` covers the navbar shell (`.st-key-app_navbar`, `.navbar-brand`, `.brand-accent`), the logout/profile-popover button styling (`.st-key-logout_btn`, `.st-key-profile_popover`), the base `stAppViewContainer`/`stHeader`/`stMainBlockContainer` overrides every app needs to make room for a custom navbar, and the app-switcher itself. Page-content styling (`stMetric`, `stForm`, whatever else a given app's own widgets need) stays out of this package - pass it via `extra_css`.

## Releasing a change

Same as this repo's CSS/JS: bump `version` in `pyproject.toml`, commit, push to `main` (or tag, if you want consuming apps to pin more precisely than `@main`). Nothing auto-propagates - each app's `uv.lock` only picks up a change when someone runs `uv lock --upgrade-package webapp-theme-streamlit` there and redeploys.
