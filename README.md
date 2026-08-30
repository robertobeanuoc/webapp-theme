# webapp-theme

Shared visual theme (design tokens, navbar, cards, tables, buttons) for
robertobeanuoc's small Flask/Jinja + Bootstrap 5 apps, so they look like one
family of apps instead of each inventing its own look.

Consumers today: `food_recognition_model`, `health-gen-ai-chat`,
`strava_to_db`, `cgm_abbot_connector`.

## Usage (Flask / Jinja / any static HTML)

Load Bootstrap 5, Bootstrap Icons and Inter first, then this file on top —
same CDN (jsDelivr) pattern already used for Bootstrap itself, no build step,
no local copy to keep in sync:

```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/robertobeanuoc/webapp-theme@v1.3.0/app.css">
```

Pin a version tag (`@v1.3.0`), not `@main` — a change here shouldn't be able
to silently reflow a running app. Bump the tag when you intentionally want
consumers to pick up a change, then update the pinned version in each app.

## Usage (Streamlit)

Streamlit's `st.html()` strips `<link>` and `<style>` tags whose text
contains anything that looks like another disallowed tag — including plain
text inside a CSS comment, since it isn't CSS-aware. In practice that rules
out linking `app.css` directly; fetch its text and inline it into a
`<style>` tag instead, stripping comments first:

```python
import re
import requests
import streamlit as st

@st.cache_data(ttl=3600)
def _fetch_shared_theme_css() -> str:
    resp = requests.get(
        "https://cdn.jsdelivr.net/gh/robertobeanuoc/webapp-theme@v1.3.0/app.css",
        timeout=5,
    )
    resp.raise_for_status()
    return resp.text

css = re.sub(r"/\*.*?\*/", "", _fetch_shared_theme_css(), flags=re.S)
st.html(f"<style>{css}</style>")
```

This only styles custom HTML you render yourself via `st.html()` (e.g.
badges, a navbar built from `st.container(key=...)`) — Streamlit's built-in
widgets (buttons, selects) are themed separately, since they don't carry
Bootstrap's class names. For those, fetch `theme.toml` the same way and
write it to `~/.streamlit/config.toml` before the Streamlit server starts —
see `cgm_abbot_connector`'s or `health-gen-ai-chat`'s `write_streamlit_secrets.py`
for a working example (it already runs once at container startup, before
`streamlit run`, to provision the OIDC `[auth]` secrets and TLS cert the
same way).

## Cross-app navigation (`apps.json` + `switcher.js`)

`apps.json` is the one place every app's identity (name, URL, icon) and
which Authentik access group grants entry to it are listed — see
`user-management-apps`'s `authentik/scripts/setup_app_access_control.py`
for how those groups get created and populated. Each app reads the logged-in
user's `groups` claim from its own OIDC token (request `groups` as an extra
scope — none of `openid`/`profile`/`email`/`offline_access` surface it) and
shows only the sibling apps whose `authentik_group` is in that list.

**`apps.json` is pinned to `@main`, not a version tag** — unlike `app.css`/
`theme.toml`/`switcher.js` above. It's pure data (URLs/names/groups), not
code or styling: a bad edit only breaks a menu link, not a running app's
layout, so it doesn't need the same "review a tag bump before it goes live"
gate. This also means updating a URL here needs **no redeploy of any app** —
see "Releasing an apps.json change" below for how it actually reaches
already-running apps, and how fast.

**Bootstrap/Jinja apps:** give the navbar a mount point, then load
`switcher.js` — it fetches `apps.json` itself and renders a "Apps" dropdown,
or removes the mount point entirely if the user has access to nothing else:

```html
<li class="nav-item" id="app-switcher" data-current-app="chat"></li>
<script>window.__USER_GROUPS__ = {{ session.user.groups | tojson }};</script>
<script src="https://cdn.jsdelivr.net/gh/robertobeanuoc/webapp-theme@v1.3.0/switcher.js" defer></script>
```

`switcher.js` itself stays pinned to a tag (it's code); only the `apps.json`
URL *inside* `switcher.js` floats on `@main`. Needs Bootstrap 5's JS bundle
on the page already (for the dropdown itself) and `data-current-app` set to
that app's `id` in `apps.json`, so it doesn't link to itself.

**Streamlit apps:** don't load `switcher.js` — Bootstrap's real dropdown JS
bundle can't be inlined via `st.html()` either (it builds Tooltip/Popover
markup from template strings containing tag-like text, which gets the whole
script stripped the same way a tag-like CSS comment does). Fetch `apps.json`
the same way as `app.css`/`theme.toml`, but pinned to `@main`, and render a
small hand-rolled open/close dropdown instead — see `cgm_abbot_connector`'s
or `health-gen-ai-chat`'s `streamlit_dashboard.py` (`_render_navbar()`) for
the full toggle script. In short:

```python
@st.cache_data(ttl=60)  # short: apps.json floats on @main, not a pinned tag - see above
def _fetch_apps_directory() -> list[dict]:
    resp = requests.get(
        "https://cdn.jsdelivr.net/gh/robertobeanuoc/webapp-theme@main/apps.json",
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()["apps"]

user_groups = st.user.get("groups") or []
other_apps = [
    app for app in _fetch_apps_directory()
    if app["id"] != "cgm" and app["authentik_group"] in user_groups
]
```

## What belongs here vs. in the app

This file only has generic, reusable pieces: color tokens, navbar, page
heading, cards, the primary button, data tables, editable-table inputs,
Select2 integration, and the empty-state pattern. A feature specific to one
app (e.g. a camera capture UI, a glucose-range chart) stays in that app's
own stylesheet, loaded *after* this one, so it can still use the shared
tokens (`var(--ns-primary)`, etc.) without polluting the shared file.

## Releasing a change

```bash
git commit -am "..."
git tag v1.3.0
git push && git push --tags
```

Then update the pinned `@vX.Y.Z` in whichever apps should pick it up.

## Releasing an `apps.json` change

No tag, no redeploy - just commit and push to `main`:

```bash
git commit -am "..."
git push
```

Two caches sit between that push and every app actually seeing it:

1. **jsDelivr's CDN cache** for `@main` (unlike a version tag, which is
   cached indefinitely since a tag shouldn't change) refreshes every ~12h on
   its own. To force it sooner, purge that one file:
   ```bash
   curl "https://purge.jsdelivr.net/gh/robertobeanuoc/webapp-theme@main/apps.json"
   ```
2. **Each Streamlit app's own `@st.cache_data(ttl=60)`** on `_fetch_apps_directory()`
   (see above) - expires on its own within a minute, nothing to purge.
   Bootstrap/Jinja apps have no server-side cache for this at all: `switcher.js`
   fetches fresh on every page load, so the jsDelivr purge alone is enough
   for those.
