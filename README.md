# proAmazingSpiderWeb

FastAPI app that serves a trimmed **Small Apps** landing template with clean URLs (no `.html` in the path), static assets under dedicated mounts, and a custom HTML page for real 404s.

## Requirements

- Python 3.10+ recommended
- Dependencies listed in `requirements.txt`

## Quick start

```bash
cd /path/to/proAmazingSpiderWeb
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in a browser.

Interactive API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Project layout

| Path | Role |
|------|------|
| `app/main.py` | FastAPI app, static mounts, HTML 404 middleware |
| `app/site.py` | Page routes and legacy `*.html` → canonical URL redirects (308) |
| `app/api/routes.py` | JSON API (e.g. `GET /api/health`) |
| `app/static/` | Built HTML, `css/`, `js/`, `images/`, `plugins/` |
| `small-apps/` | Optional upstream theme reference (not mounted by the app) |
| `requirements.txt` | `fastapi`, `uvicorn[standard]` |

## Public URLs

| URL | Content |
|-----|---------|
| `/` | Home |
| `/about` | About |
| `/contact` | Contact |
| `/privacy-policy` | Privacy policy |
| `/css/*`, `/js/*`, `/images/*`, `/plugins/*` | Static assets |

Legacy bookmark URLs such as `/about.html` redirect with **308** to the extensionless path. Removed theme pages (for example old `comming-soon.html`) redirect to `/`.

## API

- **`GET /api/health`** — `{"status":"ok"}`

Add more routers under `app/api/` and include them from `app/main.py` as needed.

## 404 behavior

- Unknown **page-like** paths (typical browser `Accept` headers, non-asset extensions) return **`app/static/404.html`** with HTTP **404**.
- Missing **assets** (e.g. `.css`, `.js`, images) keep a normal **404** response without swapping in the HTML error page, so the layout does not break.

## Editing the site

- Change copy and structure in `app/static/*.html`.
- After large edits, keep internal links **extensionless** (e.g. `href="/contact"`) to match the routes in `app/site.py`.
- If you add a new HTML page, register a route in `app/site.py` and add a legacy redirect entry if you care about old `.html` links.

## Reference theme

The `small-apps/` directory is a copy of the original Themefisher template for comparison or rebuilding assets. The running app uses only **`app/static/`**.
