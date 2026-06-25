"""SEO helpers: canonical URLs, social meta, JSON-LD, sitemap, and robots.txt."""

from __future__ import annotations

import html
import json
import os
import re
from datetime import date

SITE_URL = os.environ.get("SITE_URL", "https://www.proamazingspider.com").rstrip("/")

GOOGLE_PLAY_URL = "https://play.google.com/store/apps/details?id=com.Mamre.proAmazingSpider"
APP_STORE_URL = "https://apps.apple.com/us/app/proamazingspider/id6769407076"
OG_IMAGE_PATH = "/images/app/game-phone-1.png"

SEO_MARKER = "<!-- @seo -->"

PUBLIC_PAGES: tuple[dict[str, str], ...] = (
    {"path": "/", "changefreq": "weekly", "priority": "1.0"},
    {"path": "/about", "changefreq": "monthly", "priority": "0.8"},
    {"path": "/contact", "changefreq": "monthly", "priority": "0.7"},
    {"path": "/privacy-policy", "changefreq": "yearly", "priority": "0.5"},
)


def absolute_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{SITE_URL}{path if path.startswith('/') else '/' + path}"


def og_image_url() -> str:
    return absolute_url(OG_IMAGE_PATH)


def _parse_title_and_description(html_text: str) -> tuple[str, str]:
    title_match = re.search(r"<title>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    desc_match = re.search(
        r'<meta\s+name="description"\s+content="(.*?)"',
        html_text,
        re.IGNORECASE | re.DOTALL,
    )
    title = html.unescape(title_match.group(1).strip()) if title_match else "proAmazingSpider"
    description = html.unescape(desc_match.group(1).strip()) if desc_match else ""
    return title, description


def _organization_schema() -> dict:
    return {
        "@type": "Organization",
        "@id": f"{SITE_URL}/#organization",
        "name": "SuperAce",
        "url": SITE_URL,
        "logo": absolute_url("/images/logo.png"),
    }


def _website_schema() -> dict:
    return {
        "@type": "WebSite",
        "@id": f"{SITE_URL}/#website",
        "url": SITE_URL,
        "name": "proAmazingSpider",
        "description": "Official site for AmazingSpider / proAmazingSpider Spider Solitaire.",
        "publisher": {"@id": f"{SITE_URL}/#organization"},
    }


def _mobile_application_schema() -> dict:
    return {
        "@type": "MobileApplication",
        "@id": f"{SITE_URL}/#app",
        "name": "proAmazingSpider",
        "alternateName": "AmazingSpider",
        "description": (
            "Computerised two-deck Spider patience for Android and iPhone. "
            "Classic dealing, logical-path moves, and Solve."
        ),
        "applicationCategory": "GameApplication",
        "operatingSystem": "Android, iOS",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "installUrl": [GOOGLE_PLAY_URL, APP_STORE_URL],
        "downloadUrl": GOOGLE_PLAY_URL,
        "image": og_image_url(),
        "author": {"@type": "Organization", "name": "SuperAce"},
    }


def json_ld_for_page(canonical_path: str, title: str, description: str) -> list[dict]:
    graph: list[dict] = [
        _organization_schema(),
        _website_schema(),
        _mobile_application_schema(),
    ]
    if canonical_path != "/":
        page_url = absolute_url(canonical_path)
        graph.append(
            {
                "@type": "WebPage",
                "@id": f"{page_url}#webpage",
                "url": page_url,
                "name": title,
                "description": description,
                "isPartOf": {"@id": f"{SITE_URL}/#website"},
            }
        )
    return [{"@context": "https://schema.org", "@graph": graph}]


def render_seo_block(
    canonical_path: str,
    title: str,
    description: str,
    *,
    noindex: bool = False,
) -> str:
    if noindex:
        return '  <meta name="robots" content="noindex, follow">'

    canonical = absolute_url(canonical_path)
    image = og_image_url()
    title_attr = html.escape(title, quote=True)
    desc_attr = html.escape(description, quote=True)
    url_attr = html.escape(canonical, quote=True)
    image_attr = html.escape(image, quote=True)

    lines = [
        f'  <link rel="canonical" href="{url_attr}">',
    ]
    lines.extend(
        [
            f'  <meta property="og:type" content="website">',
            f'  <meta property="og:url" content="{url_attr}">',
            f'  <meta property="og:title" content="{title_attr}">',
            f'  <meta property="og:description" content="{desc_attr}">',
            f'  <meta property="og:image" content="{image_attr}">',
            '  <meta property="og:site_name" content="proAmazingSpider">',
            '  <meta name="twitter:card" content="summary_large_image">',
            f'  <meta name="twitter:title" content="{title_attr}">',
            f'  <meta name="twitter:description" content="{desc_attr}">',
            f'  <meta name="twitter:image" content="{image_attr}">',
        ]
    )

    json_ld = json.dumps(
        json_ld_for_page(canonical_path, title, description),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    lines.append(f'  <script type="application/ld+json">{json_ld}</script>')
    return "\n".join(lines)


def inject_seo(html_text: str, canonical_path: str, *, noindex: bool = False) -> str:
    if SEO_MARKER not in html_text:
        return html_text
    title, description = _parse_title_and_description(html_text)
    block = render_seo_block(canonical_path, title, description, noindex=noindex)
    return html_text.replace(SEO_MARKER, block, 1)


def render_robots_txt() -> str:
    return "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "",
            f"Sitemap: {absolute_url('/sitemap.xml')}",
            "",
        ]
    )


def render_sitemap_xml() -> str:
    lastmod = date.today().isoformat()
    urls = []
    for page in PUBLIC_PAGES:
        loc = html.escape(absolute_url(page["path"]), quote=True)
        urls.append(
            "\n".join(
                [
                    "  <url>",
                    f"    <loc>{loc}</loc>",
                    f"    <lastmod>{lastmod}</lastmod>",
                    f"    <changefreq>{page['changefreq']}</changefreq>",
                    f"    <priority>{page['priority']}</priority>",
                    "  </url>",
                ]
            )
        )
    body = "\n".join(urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n"
    )
