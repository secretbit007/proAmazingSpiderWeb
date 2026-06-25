"""Generate a seamless felt noise tile for the site background.

Run from repo root:  python scripts/generate_felt_texture.py
Writes: app/static/images/background/felt-texture.png
"""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "app" / "static" / "images" / "background" / "felt-texture.png"
SIZE = 256
# Balanced green felt (readable, not too dark)
BASE = (20, 62, 48)


def main() -> None:
    random.seed(42)
    im = Image.new("RGB", (SIZE, SIZE))
    px = im.load()
    for y in range(SIZE):
        for x in range(SIZE):
            grain = random.randint(-16, 16)
            weave = ((x ^ y) & 3) - 1
            px[x, y] = tuple(max(0, min(255, BASE[i] + grain + weave * 2)) for i in range(3))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT, optimize=True)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
