"""Application entrypoint."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, Response

from app.api.routes import api_router
from app.site import STATIC_DIR, router as site_router

NOT_FOUND_PAGE = STATIC_DIR / "404.html"

# Missing static assets should keep a normal 404 (not HTML) for browsers and bundlers.
_ASSET_SUFFIXES = frozenset(
    {
        ".css",
        ".eot",
        ".gif",
        ".ico",
        ".jpeg",
        ".jpg",
        ".js",
        ".json",
        ".map",
        ".mjs",
        ".png",
        ".svg",
        ".ttf",
        ".txt",
        ".webmanifest",
        ".webp",
        ".woff",
        ".woff2",
        ".xml",
    }
)


class HtmlNotFoundMiddleware(BaseHTTPMiddleware):
    """Serve static/404.html for real 404s on page-like GET/HEAD requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if response.status_code != 404:
            return response
        ct = response.headers.get("content-type", "")
        if ct.partition(";")[0].strip().lower() == "text/html":
            return response
        if request.method not in ("GET", "HEAD"):
            return response
        path = request.url.path
        if path.startswith("/api"):
            return response
        suffix = Path(path).suffix.lower()
        if suffix in _ASSET_SUFFIXES:
            return response
        accept = request.headers.get("accept", "")
        if "text/html" not in accept and "*/*" not in accept and accept != "":
            return response
        if NOT_FOUND_PAGE.is_file():
            return FileResponse(NOT_FOUND_PAGE, status_code=404)
        return response


app = FastAPI(
    title="proAmazingSpider",
    description="Marketing site for AmazingSpider / proAmazingSpider (two-deck Spider patience, Android & iOS) by SuperAce.",
)

app.include_router(api_router, prefix="/api")
app.include_router(site_router)

for _name, _subdir in (("css", "css"), ("js", "js"), ("images", "images"), ("plugins", "plugins")):
    app.mount(
        f"/{_name}",
        StaticFiles(directory=str(STATIC_DIR / _subdir)),
        name=_name,
    )

app.add_middleware(HtmlNotFoundMiddleware)
