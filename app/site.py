"""Public site pages (extensionless URLs) and legacy *.html redirects."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

STATIC_DIR = Path(__file__).resolve().parent / "static"

router = APIRouter(include_in_schema=False)


def _page(file: str):
    path = STATIC_DIR / file

    async def serve() -> FileResponse:
        return FileResponse(path)

    return serve


def _redirect(target: str):
    async def go() -> RedirectResponse:
        return RedirectResponse(url=target, status_code=308)

    return go


router.add_api_route("/", _page("index.html"), methods=["GET", "HEAD"])
router.add_api_route("/about", _page("about.html"), methods=["GET", "HEAD"])
router.add_api_route("/contact", _page("contact.html"), methods=["GET", "HEAD"])
router.add_api_route("/privacy-policy", _page("privacy-policy.html"), methods=["GET", "HEAD"])

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
