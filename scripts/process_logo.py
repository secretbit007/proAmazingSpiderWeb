"""Resize repo-root logo.png for the site (no circular masking—shape is CSS).

Writes:
  app/static/images/logo.png   (square canvas, full artwork scaled to fit)
  app/static/images/logo-alt.png (copy)
  app/static/images/favicon.png  (32×32)

Run from repo root:  python scripts/process_logo.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageOps

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "logo.png"
OUT_DIR = REPO / "app" / "static" / "images"
LOGO_SIZE = 256
FAVICON_SIZE = 32


def square_fit(im: Image.Image, size: int) -> Image.Image:
    """Fit entire image inside size×size, centered on transparent square."""
    im = im.convert("RGBA")
    fitted = ImageOps.contain(im, (size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ox = (size - fitted.width) // 2
    oy = (size - fitted.height) // 2
    canvas.paste(fitted, (ox, oy), fitted)
    return canvas


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"Missing {SRC}")
    im = Image.open(SRC)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    nav = square_fit(im, LOGO_SIZE)
    nav.save(OUT_DIR / "logo.png", "PNG", optimize=True)
    shutil.copyfile(OUT_DIR / "logo.png", OUT_DIR / "logo-alt.png")

    square_fit(im, FAVICON_SIZE).save(OUT_DIR / "favicon.png", "PNG", optimize=True)
    print("Updated images/logo.png, logo-alt.png, favicon.png (square assets; circle via CSS)")


if __name__ == "__main__":
    main()
