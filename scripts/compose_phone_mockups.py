"""Composite game screenshots into phone-style mockups (white bezel, notch, depth cues).

Adds simulated thickness (smooth gradient of side slices + light edge blur), bezel shading, screen-edge vignette, cast shadow,
and a perspective warp (strength varies per asset). PNG alpha preserved (transparent background).

Run from repo root:
  python scripts/compose_phone_mockups.py

Reads:  app/static/images/app/game-screen-1.png … game-screen-4.png
Writes: app/static/images/app/game-phone-1.png … game-phone-4.png
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parents[1]
SRC_DIR = REPO / "app" / "static" / "images" / "app"

CANVAS_W, CANVAS_H = 900, 1400
MAX_SCREEN_W, MAX_SCREEN_H = 560, 980
BEZEL_SIDE = 26
BEZEL_TOP = 44
BEZEL_BOTTOM = 34
OUTER_RADIUS = 54
INNER_RADIUS = 36
FRAME_FILL = (255, 255, 255, 255)
FRAME_OUTLINE = (228, 230, 236, 255)
FRAME_OUTLINE_W = 1
NOTCH_W, NOTCH_H = 108, 26
NOTCH_RADIUS = 13
NOTCH_FILL = (38, 38, 42, 255)
# Cast shadow (device lifted off the “ground”)
SHADOW_ALPHA = 92
SHADOW_BLUR = 26
SHADOW_OFFSET = (14, 26)
# Fake thickness: many interpolated plates (avoids visible “steps”)
DEPTH_MAX_DX = 11
DEPTH_MAX_DY = 16
DEPTH_STEPS = 26
DEPTH_RGB_BACK = (118, 120, 128)
DEPTH_RGB_FRONT = (246, 247, 250)
DEPTH_EDGE_BLUR = 0.85
SCREEN_BOTTOM_VIGNETTE_PX = 36
SCREEN_VIGNETTE_STRENGTH = 0.18

# Indices 1–4: perspective strength ("tilt_subtle" | "tilt_back" | "tilt_yaw" | "flat")
PHONE_3D_PRESETS: dict[int, str] = {
    1: "tilt_back",
    2: "tilt_yaw",
    3: "tilt_subtle",
    4: "tilt_back",
}


def _gaussian_solve_8(A: list[list[float]], b: list[float]) -> list[float]:
    """Solve 8×8 linear system (A square, augmented elimination)."""
    n = 8
    M = [A[i][:] + [b[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(M[r][col]))
        M[col], M[pivot] = M[pivot], M[col]
        div = M[col][col]
        if abs(div) < 1e-14:
            raise ValueError("singular matrix")
        for j in range(col, n + 1):
            M[col][j] /= div
        for row in range(n):
            if row != col:
                f = M[row][col]
                if abs(f) < 1e-18:
                    continue
                for j in range(col, n + 1):
                    M[row][j] -= f * M[col][j]
    return [M[i][n] for i in range(n)]


def _homography_forward(src4: list[tuple[float, float]], dst4: list[tuple[float, float]]) -> list[list[float]]:
    """8 DOF homography (h22=1) mapping each src_k -> dst_k. Returns 3×3 forward matrix."""
    M: list[list[float]] = []
    rhs: list[float] = []
    for (u, v), (x, y) in zip(src4, dst4):
        M.append([u, v, 1.0, 0.0, 0.0, 0.0, -u * x, -v * x])
        rhs.append(x)
        M.append([0.0, 0.0, 0.0, u, v, 1.0, -u * y, -v * y])
        rhs.append(y)
    h = _gaussian_solve_8(M, rhs)
    return [
        [h[0], h[1], h[2]],
        [h[3], h[4], h[5]],
        [h[6], h[7], 1.0],
    ]


def _invert_3x3(m: list[list[float]]) -> list[list[float]]:
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, i = m[2]
    A = e * i - f * h
    B = -(d * i - f * g)
    C = d * h - e * g
    D = -(b * i - c * h)
    E = a * i - c * g
    F_ = -(a * h - b * g)
    G = b * f - c * e
    H = -(a * f - c * d)
    I = a * e - b * d
    det = a * A + b * B + c * C
    if abs(det) < 1e-18:
        raise ValueError("singular homography")
    s = 1.0 / det
    return [
        [A * s, D * s, G * s],
        [B * s, E * s, H * s],
        [C * s, F_ * s, I * s],
    ]


def _pillow_perspective_from_forward(H: list[list[float]]) -> tuple[float, ...]:
    """Pillow samples INPUT at coords given OUTPUT (x,y); use H⁻¹."""
    inv = _invert_3x3(H)
    k = inv[2][2]
    if abs(k) < 1e-14:
        k = 1e-14
    return (
        inv[0][0] / k,
        inv[0][1] / k,
        inv[0][2] / k,
        inv[1][0] / k,
        inv[1][1] / k,
        inv[1][2] / k,
        inv[2][0] / k,
        inv[2][1] / k,
    )


def _alpha_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    a = img.split()[3]
    return a.getbbox() or (0, 0, img.width, img.height)


def apply_perspective_style(img: Image.Image, style: str) -> Image.Image:
    """Warp full RGBA image so its rectangle maps to a mild 3D-style quad."""
    if style == "flat":
        return img

    w, h = img.size
    pad = 36
    ow = w + 2 * pad + max(48, int(w * 0.08))
    oh = h + 2 * pad + max(40, int(h * 0.06))

    src = [(0.0, 0.0), (float(w), 0.0), (float(w), float(h)), (0.0, float(h))]

    if style == "tilt_subtle":
        inset = max(14.0, ow * 0.048)
        dst = [
            (pad + inset, pad + 4),
            (ow - pad - inset, pad + 4),
            (ow - pad, oh - pad),
            (pad, oh - pad),
        ]
    elif style == "tilt_back":
        inset = max(28.0, ow * 0.092)
        dst = [
            (pad + inset, pad),
            (ow - pad - inset, pad),
            (ow - pad, oh - pad),
            (pad, oh - pad),
        ]
    elif style == "tilt_yaw":
        inset_l = ow * 0.078
        inset_r = ow * 0.042
        shift = 22.0
        dst = [
            (pad + inset_l, pad + shift),
            (ow - pad - inset_r, pad),
            (ow - pad - shift, oh - pad),
            (pad + shift, oh - pad),
        ]
    else:
        return img

    try:
        H = _homography_forward(src, dst)
        coeffs = _pillow_perspective_from_forward(H)
    except ValueError:
        return img

    return img.transform(
        (int(ow), int(oh)),
        Image.Transform.PERSPECTIVE,
        coeffs,
        Image.Resampling.BICUBIC,
        fillcolor=(0, 0, 0, 0),
    )


def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _lerp_channel(a: int, b: int, t: float) -> int:
    return int(round(a + (b - a) * t))


def _rounded_plate(size: tuple[int, int], radius: int, rgba: tuple[int, int, int, int]) -> Image.Image:
    """Filled rounded rectangle on transparent (same geometry as the phone body)."""
    w, h = size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=rgba)
    return im


def _shade_white_face(frame: Image.Image) -> Image.Image:
    """Bezel lighting with smoothstep falloff (no hard shading bands)."""
    w, h = frame.size
    out = frame.copy()
    px = out.load()
    left_w, right_w, top_h = 20, 14, 16
    for y in range(h):
        for x in range(min(left_w, w)):
            r, g, b, a = px[x, y]
            if a < 8:
                continue
            t = _smoothstep(1.0 - x / float(left_w))
            f = 1.0 - 0.14 * t
            px[x, y] = (int(r * f), int(g * f), int(b * f), a)
        for x in range(max(0, w - right_w), w):
            r, g, b, a = px[x, y]
            if a < 8:
                continue
            t = _smoothstep((x - (w - right_w)) / float(right_w))
            f = 1.0 + 0.055 * t
            px[x, y] = (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)), a)
    for x in range(w):
        for y in range(min(top_h, h)):
            r, g, b, a = px[x, y]
            if a < 8:
                continue
            t = _smoothstep(1.0 - y / float(top_h))
            f = 1.0 + 0.085 * t
            px[x, y] = (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)), a)
    return out


def _screen_bottom_depth(inner: Image.Image) -> Image.Image:
    """Slight darkening at the bottom of the glass (ambient occlusion)."""
    w, h = inner.size
    band = min(SCREEN_BOTTOM_VIGNETTE_PX, h)
    if band <= 0:
        return inner
    out = inner.copy()
    px = out.load()
    for y in range(h - band, h):
        t = (y - (h - band)) / float(band)
        dim = 1.0 - SCREEN_VIGNETTE_STRENGTH * (t**1.4)
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 8:
                continue
            px[x, y] = (int(r * dim), int(g * dim), int(b * dim), a)
    return out


def _rounded_rect_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def _fit_screen(img: Image.Image) -> Image.Image:
    w, h = img.size
    scale = min(MAX_SCREEN_W / w, MAX_SCREEN_H / h)
    nw, nh = int(w * scale), int(h * scale)
    return img.convert("RGBA").resize((nw, nh), Image.Resampling.LANCZOS)


def compose_phone(screenshot: Image.Image) -> Image.Image:
    screen = _fit_screen(screenshot)
    sw, sh = screen.size

    phone_w = sw + 2 * BEZEL_SIDE
    phone_h = sh + BEZEL_TOP + BEZEL_BOTTOM
    ox = (CANVAS_W - phone_w) // 2
    oy = (CANVAS_H - phone_h) // 2

    bg = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))

    sx_off, sy_off = SHADOW_OFFSET
    shadow_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow_layer).rounded_rectangle(
        (ox + sx_off, oy + sy_off, ox + phone_w + sx_off, oy + phone_h + sy_off),
        radius=OUTER_RADIUS,
        fill=(0, 0, 0, SHADOW_ALPHA),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
    bg = Image.alpha_composite(bg, shadow_layer)

    depth_canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    n = max(DEPTH_STEPS, 2)
    prev_dx, prev_dy = -1, -1
    for s in range(n):
        t_lin = s / (n - 1)
        t = _smoothstep(t_lin)
        dx = int(round(DEPTH_MAX_DX * (1.0 - t)))
        dy = int(round(DEPTH_MAX_DY * (1.0 - t)))
        if dx <= 0 and dy <= 0:
            break
        if dx == prev_dx and dy == prev_dy:
            continue
        prev_dx, prev_dy = dx, dy
        r = _lerp_channel(DEPTH_RGB_BACK[0], DEPTH_RGB_FRONT[0], t)
        gch = _lerp_channel(DEPTH_RGB_BACK[1], DEPTH_RGB_FRONT[1], t)
        bch = _lerp_channel(DEPTH_RGB_BACK[2], DEPTH_RGB_FRONT[2], t)
        plate = _rounded_plate((phone_w, phone_h), OUTER_RADIUS, (r, gch, bch, 255))
        depth_canvas.paste(plate, (ox + dx, oy + dy), plate)
    if DEPTH_EDGE_BLUR > 0:
        depth_canvas = depth_canvas.filter(ImageFilter.GaussianBlur(DEPTH_EDGE_BLUR))
    bg = Image.alpha_composite(bg, depth_canvas)

    frame_rgba = Image.new("RGBA", (phone_w, phone_h), (0, 0, 0, 0))
    fr = ImageDraw.Draw(frame_rgba)
    fr.rounded_rectangle(
        (0, 0, phone_w - 1, phone_h - 1),
        radius=OUTER_RADIUS,
        fill=FRAME_FILL,
        outline=FRAME_OUTLINE,
        width=FRAME_OUTLINE_W,
    )
    frame_rgba = _shade_white_face(frame_rgba)

    inner_mask = _rounded_rect_mask((sw, sh), INNER_RADIUS)
    inner = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    inner.paste(screen, (0, 0))
    inner.putalpha(inner_mask)
    inner = _screen_bottom_depth(inner)

    bg.paste(frame_rgba, (ox, oy), frame_rgba)
    sx = ox + BEZEL_SIDE
    sy = oy + BEZEL_TOP
    bg.paste(inner, (sx, sy), inner)

    rim = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(rim).rounded_rectangle(
        (sx, sy, sx + sw - 1, sy + sh - 1),
        radius=INNER_RADIUS,
        outline=(216, 218, 224, 200),
        width=1,
    )
    bg = Image.alpha_composite(bg, rim)

    # Notch
    nx0 = ox + (phone_w - NOTCH_W) // 2
    ny0 = oy + max(6, (BEZEL_TOP - NOTCH_H) // 2)
    notch_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(notch_layer).rounded_rectangle(
        (nx0, ny0, nx0 + NOTCH_W, ny0 + NOTCH_H),
        radius=NOTCH_RADIUS,
        fill=NOTCH_FILL,
    )
    bg = Image.alpha_composite(bg, notch_layer)

    return bg


def main() -> None:
    for i in range(1, 5):
        src = SRC_DIR / f"game-screen-{i}.png"
        if not src.is_file():
            print(f"Skip (missing): {src}", file=__import__("sys").stderr)
            continue
        out = SRC_DIR / f"game-phone-{i}.png"
        img = Image.open(src)
        mock = compose_phone(img)
        bb = _alpha_bbox(mock)
        pad_crop = 10
        mock = mock.crop(
            (
                max(0, bb[0] - pad_crop),
                max(0, bb[1] - pad_crop),
                min(mock.width, bb[2] + pad_crop),
                min(mock.height, bb[3] + pad_crop),
            )
        )
        style = PHONE_3D_PRESETS.get(i, "flat")
        mock = apply_perspective_style(mock, style)
        mock.save(out, "PNG", optimize=True)
        tag = f" ({style})"
        print(f"Wrote {out.relative_to(REPO)}{tag}")


if __name__ == "__main__":
    main()
