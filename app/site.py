"""Public site pages (extensionless URLs) and legacy *.html redirects."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response

from app.seo import SEO_MARKER, inject_seo, render_robots_txt, render_sitemap_xml

STATIC_DIR = Path(__file__).resolve().parent / "static"

router = APIRouter(include_in_schema=False)


def _page(file: str, canonical_path: str):
    path = STATIC_DIR / file

    async def serve() -> HTMLResponse:
        html_text = path.read_text(encoding="utf-8")
        if SEO_MARKER in html_text:
            html_text = inject_seo(html_text, canonical_path)
        return HTMLResponse(html_text)

    return serve


def _redirect(target: str):
    async def go() -> RedirectResponse:
        return RedirectResponse(url=target, status_code=308)

    return go


router.add_api_route("/", _page("index.html", "/"), methods=["GET", "HEAD"])
router.add_api_route("/about", _page("about.html", "/about"), methods=["GET", "HEAD"])
router.add_api_route("/contact", _page("contact.html", "/contact"), methods=["GET", "HEAD"])
router.add_api_route(
    "/privacy-policy",
    _page("privacy-policy.html", "/privacy-policy"),
    methods=["GET", "HEAD"],
)

async def robots_txt() -> PlainTextResponse:
    return PlainTextResponse(render_robots_txt())


async def sitemap_xml() -> Response:
    return Response(content=render_sitemap_xml(), media_type="application/xml")


router.add_api_route("/robots.txt", robots_txt, methods=["GET", "HEAD"])
router.add_api_route("/sitemap.xml", sitemap_xml, methods=["GET", "HEAD"])

_LEGACY_HTML = (
    ("index.html", "/"),
    ("about.html", "/about"),
    ("contact.html", "/contact"),
    ("privacy-policy.html", "/privacy-policy"),
    ("comming-soon.html", "/"),
    ("404.html", "/"),
)
for _legacy, _target in _LEGACY_HTML:
    router.add_api_route(f"/{_legacy}", _redirect(_target), methods=["GET", "HEAD"])
