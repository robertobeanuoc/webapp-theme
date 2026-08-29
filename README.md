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
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/robertobeanuoc/webapp-theme@v1.0.0/app.css">
```

Pin a version tag (`@v1.0.0`), not `@main` — a change here shouldn't be able
to silently reflow a running app. Bump the tag when you intentionally want
consumers to pick up a change, then update the pinned version in each app.

## Usage (Streamlit)

Streamlit doesn't load an external stylesheet by default, but `st.markdown`
can inject one into the page:

```python
import streamlit as st

st.markdown(
    '<link rel="stylesheet" '
    'href="https://cdn.jsdelivr.net/gh/robertobeanuoc/webapp-theme@v1.0.0/app.css">',
    unsafe_allow_html=True,
)
```

This only styles custom HTML you render yourself via `unsafe_allow_html`
(e.g. badges, cards) — Streamlit's built-in widgets are themed separately
through `.streamlit/config.toml` (`primaryColor = "#16a34a"`, etc.) since
they don't carry Bootstrap's class names.

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
git tag v1.1.0
git push && git push --tags
```

Then update the pinned `@vX.Y.Z` in whichever apps should pick it up.
