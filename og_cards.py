#!/usr/bin/env python3
"""Branded 1200x630 PNG Open Graph cards for A Silver Hair of Wisdom.

This module intentionally has no site-state side effects. build_site.py supplies an
output directory and article metadata; the renderer writes PNGs beneath assets/og.

Optional portrait:
    publisher/static/vivienne-og-portrait.png
    publisher/static/vivienne-og-portrait.jpg
    publisher/static/vivienne-og-portrait.jpeg
    publisher/static/vivienne-og-portrait.webp

If none exists, a branded silver-hair silhouette is rendered automatically.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence
import math
import re

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
except ImportError as exc:  # pragma: no cover - clearer build failure on a fresh runner
    raise RuntimeError(
        "Pillow is required for branded OG PNG generation. "
        "Run: python3 -m pip install -r requirements.txt"
    ) from exc

WIDTH = 1200
HEIGHT = 630


def _clean_text(value: object) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").split())


def extract_excerpt(entry: dict, max_chars: int = 170) -> str:
    """Use an explicit dek/description first, otherwise derive one from body text."""
    explicit = _clean_text(entry.get("dek") or entry.get("description") or entry.get("excerpt"))
    if explicit:
        text = explicit
    else:
        body = entry.get("body") or []
        if isinstance(body, str):
            body = [body]
        text = " ".join(_clean_text(p) for p in body if _clean_text(p))
    if not text:
        text = _clean_text(entry.get("title"))
    if len(text) <= max_chars:
        return text
    cut = text[: max_chars + 1]
    split_at = cut.rfind(" ")
    if split_at >= max_chars * 0.65:
        cut = cut[:split_at]
    return cut.rstrip(" ,.;:—-") + "…"


def _slug(value: object) -> str:
    value = _clean_text(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "article"


def _font_candidates(kind: str, bold: bool = False) -> Sequence[str]:
    # Paths cover GitHub ubuntu runners, common Debian/Ubuntu hosts, macOS and Windows.
    if kind == "serif":
        if bold:
            return (
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf",
                "/Library/Fonts/Georgia Bold.ttf",
                "C:/Windows/Fonts/georgiab.ttf",
            )
        return (
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
            "/Library/Fonts/Georgia.ttf",
            "C:/Windows/Fonts/georgia.ttf",
        )
    if bold:
        return (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        )
    return (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    )


def _font(kind: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in _font_candidates(kind, bold):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    # Pillow's bundled/default font is a last-resort local-development fallback.
    return ImageFont.load_default()


def _text_width(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    if not text:
        return 0
    box = draw.textbbox((0, 0), text, font=font)
    return int(box[2] - box[0])


def _wrap_pixels(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, max_lines: int) -> list[str]:
    words = _clean_text(text).split()
    if not words:
        return [""]
    lines: list[str] = []
    current = ""
    idx = 0
    while idx < len(words):
        word = words[idx]
        candidate = word if not current else current + " " + word
        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
            idx += 1
            continue
        if current:
            lines.append(current)
            current = ""
            if len(lines) == max_lines:
                break
            continue
        # Single overlong token: trim visually instead of overflowing.
        clipped = word
        while len(clipped) > 4 and _text_width(draw, clipped + "…", font) > max_width:
            clipped = clipped[:-1]
        lines.append(clipped + ("…" if clipped != word else ""))
        idx += 1
        if len(lines) == max_lines:
            break
    if len(lines) < max_lines and current:
        lines.append(current)
    truncated = idx < len(words)
    if truncated and lines:
        tail = lines[-1].rstrip(" ,.;:—-")
        while len(tail) > 4 and _text_width(draw, tail + "…", font) > max_width:
            tail = tail[:-1].rstrip()
        lines[-1] = tail + "…"
    return lines[:max_lines]


def _fit_title(draw: ImageDraw.ImageDraw, title: str, max_width: int, max_lines: int = 4):
    # Short titles get visual weight; long titles step down until they fit naturally.
    length = len(_clean_text(title))
    if length <= 32:
        start = 58
    elif length <= 55:
        start = 52
    elif length <= 82:
        start = 46
    else:
        start = 41
    for size in range(start, 33, -2):
        font = _font("serif", size, bold=True)
        lines = _wrap_pixels(draw, title, font, max_width, max_lines)
        if len(lines) <= max_lines and all(_text_width(draw, line, font) <= max_width for line in lines):
            # Approximate block height; reject a crowded 4-line block at very large sizes.
            if len(lines) < 4 or size <= 48:
                return font, lines, size
    size = 34
    font = _font("serif", size, bold=True)
    return font, _wrap_pixels(draw, title, font, max_width, max_lines), size


def _rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def _gradient_background() -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (12, 13, 18))
    px = img.load()
    c1 = (20, 22, 31)
    c2 = (10, 11, 16)
    c3 = (28, 22, 39)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            tx = x / max(1, WIDTH - 1)
            ty = y / max(1, HEIGHT - 1)
            # diagonal dark gradient with a restrained violet lift to lower-right
            base_t = min(1.0, 0.62 * tx + 0.38 * ty)
            r = int(c1[0] * (1 - base_t) + c2[0] * base_t)
            g = int(c1[1] * (1 - base_t) + c2[1] * base_t)
            b = int(c1[2] * (1 - base_t) + c2[2] * base_t)
            violet = max(0.0, (tx + ty - 1.05)) * 0.55
            r = int(r * (1 - violet) + c3[0] * violet)
            g = int(g * (1 - violet) + c3[1] * violet)
            b = int(b * (1 - violet) + c3[2] * violet)
            px[x, y] = (r, g, b)
    return img


def _portrait_candidates(static_dir: Path) -> Iterable[Path]:
    for ext in ("png", "jpg", "jpeg", "webp"):
        yield static_dir / f"vivienne-og-portrait.{ext}"


def _load_portrait(static_dir: Path, size: tuple[int, int]) -> Image.Image | None:
    for path in _portrait_candidates(static_dir):
        if not path.exists():
            continue
        try:
            img = Image.open(path).convert("RGB")
            return ImageOps.fit(img, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.42))
        except Exception as exc:
            print(f"WARNING: could not use OG portrait {path.name}: {exc}")
    return None


def _draw_fallback_portrait(size: tuple[int, int]) -> Image.Image:
    """Abstract silver-haired profile: branded fallback, not a fake portrait."""
    w, h = size
    img = Image.new("RGB", size, (20, 22, 30))
    d = ImageDraw.Draw(img)
    # Subtle halo
    for radius, alpha in ((165, 24), (135, 28), (105, 34)):
        overlay = Image.new("RGBA", size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        cx, cy = int(w * 0.56), int(h * 0.34)
        od.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(156, 134, 196, alpha))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)
    # Shoulder/body
    d.ellipse((30, int(h * 0.55), w - 20, h + 150), fill=(54, 57, 68))
    # Neck and face silhouette
    skin = (168, 155, 153)
    d.rounded_rectangle((int(w * 0.43), int(h * 0.38), int(w * 0.62), int(h * 0.69)), radius=30, fill=skin)
    d.ellipse((int(w * 0.30), int(h * 0.12), int(w * 0.73), int(h * 0.55)), fill=skin)
    # Silver hair mass and strands
    silver = (218, 219, 224)
    silver2 = (170, 174, 184)
    d.pieslice((int(w * 0.20), int(h * 0.03), int(w * 0.78), int(h * 0.62)), 165, 360, fill=silver2)
    d.polygon([
        (int(w * 0.24), int(h * 0.22)), (int(w * 0.15), int(h * 0.76)),
        (int(w * 0.34), int(h * 0.55)), (int(w * 0.29), int(h * 0.88)),
        (int(w * 0.47), int(h * 0.58)), (int(w * 0.44), int(h * 0.90)),
        (int(w * 0.61), int(h * 0.51)), (int(w * 0.68), int(h * 0.18)),
    ], fill=silver)
    # Minimal profile definition
    d.arc((int(w * 0.37), int(h * 0.20), int(w * 0.69), int(h * 0.50)), 190, 320, fill=(94, 78, 83), width=3)
    d.line((int(w * 0.63), int(h * 0.37), int(w * 0.70), int(h * 0.40)), fill=(104, 84, 91), width=3)
    return img.filter(ImageFilter.GaussianBlur(0.25))


@dataclass
class OGCardRenderer:
    out_dir: Path
    static_dir: Path
    site_name: str = "A Silver Hair of Wisdom"
    author_name: str = "Vivienne"

    def __post_init__(self):
        self.out_dir = Path(self.out_dir)
        self.static_dir = Path(self.static_dir)
        self.og_dir = self.out_dir / "assets" / "og"
        self.og_dir.mkdir(parents=True, exist_ok=True)

    def _base(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        img = _gradient_background()
        draw = ImageDraw.Draw(img)
        # Fine outer frame + top brand rule
        draw.rounded_rectangle((20, 20, WIDTH - 21, HEIGHT - 21), radius=26, outline=(62, 50, 83), width=2)
        draw.line((55, 124, WIDTH - 55, 124), fill=(66, 52, 89), width=1)
        return img, draw

    def _brand(self, draw: ImageDraw.ImageDraw):
        kicker_font = _font("sans", 16, bold=True)
        brand_font = _font("serif", 27, bold=True)
        draw.text((58, 48), "VIVIENNE", font=kicker_font, fill=(169, 170, 184))
        draw.text((58, 72), self.site_name, font=brand_font, fill=(241, 239, 245))
        # small silver accent
        draw.rounded_rectangle((WIDTH - 180, 54, WIDTH - 58, 89), radius=17, fill=(26, 31, 38), outline=(67, 106, 94), width=1)
        ro_font = _font("sans", 12, bold=True)
        draw.text((WIDTH - 155, 65), "PERSPECTIVE", font=ro_font, fill=(163, 211, 190))

    def _portrait_panel(self, img: Image.Image, draw: ImageDraw.ImageDraw):
        x, y, w, h = 58, 156, 316, 407
        portrait = _load_portrait(self.static_dir, (w, h)) or _draw_fallback_portrait((w, h))
        mask = _rounded_mask((w, h), 26)
        img.paste(portrait, (x, y), mask)
        draw.rounded_rectangle((x, y, x + w, y + h), radius=26, outline=(62, 65, 79), width=2)
        # translucent bottom name strip
        overlay = Image.new("RGBA", (w, 82), (9, 10, 15, 194))
        img.alpha_composite(overlay, (x, y + h - 82)) if img.mode == "RGBA" else img.paste(overlay, (x, y + h - 82), overlay)
        draw = ImageDraw.Draw(img)
        draw.text((x + 22, y + h - 62), self.author_name, font=_font("serif", 25, bold=True), fill=(241, 239, 245))
        draw.text((x + 22, y + h - 32), "Advice from Vivienne", font=_font("sans", 13), fill=(164, 167, 180))

    def render_default(self, description: str = "Short, thoughtful perspective on very human problems.") -> str:
        img, draw = self._base()
        self._brand(draw)
        self._portrait_panel(img, draw)
        draw = ImageDraw.Draw(img)
        x = 418
        draw.text((x, 171), "SHORT PERSPECTIVE · REAL QUESTIONS", font=_font("sans", 14, bold=True), fill=(169, 143, 203))
        headline = "A little perspective before you decide what you think."
        title_font, lines, size = _fit_title(draw, headline, 700, max_lines=3)
        y = 211
        line_gap = max(48, int(size * 1.17))
        for line in lines:
            draw.text((x, y), line, font=title_font, fill=(245, 243, 248))
            y += line_gap
        desc_font = _font("sans", 20)
        desc_lines = _wrap_pixels(draw, description, desc_font, 690, 3)
        y = max(y + 18, 403)
        for line in desc_lines:
            draw.text((x, y), line, font=desc_font, fill=(181, 183, 194))
            y += 30
        draw.line((x, 536, 1100, 536), fill=(72, 57, 94), width=1)
        draw.text((x, 553), "ASILVERHAIR.COM", font=_font("sans", 14, bold=True), fill=(197, 199, 210))
        path = self.og_dir / "og-default.png"
        img.save(path, format="PNG", optimize=True)
        return "/assets/og/og-default.png"

    def render_article(self, entry: dict) -> str:
        img, draw = self._base()
        self._brand(draw)
        self._portrait_panel(img, draw)
        draw = ImageDraw.Draw(img)

        number = int(entry.get("number") or 0)
        topic = _clean_text(entry.get("topic") or "wisdom").replace("-", " ").upper()
        title = _clean_text(entry.get("title"))
        excerpt = extract_excerpt(entry, max_chars=155)

        x = 418
        badge_font = _font("sans", 14, bold=True)
        badge = (f"#{number:03d}  ·  {topic}" if number else topic)[:58]
        badge_w = _text_width(draw, badge, badge_font) + 30
        draw.rounded_rectangle((x, 157, x + badge_w, 190), radius=16, fill=(25, 22, 33), outline=(81, 60, 106), width=1)
        draw.text((x + 15, 166), badge, font=badge_font, fill=(188, 159, 220))

        title_font, lines, size = _fit_title(draw, title, 700, max_lines=4)
        y = 215
        line_gap = max(42, int(size * 1.16))
        for line in lines:
            draw.text((x, y), line, font=title_font, fill=(247, 245, 249))
            y += line_gap

        # Keep excerpt far enough below title but never below the card footer.
        desc_y = min(max(y + 20, 410), 470)
        desc_font = _font("sans", 17)
        for line in _wrap_pixels(draw, excerpt, desc_font, 700, 2):
            draw.text((x, desc_y), line, font=desc_font, fill=(174, 177, 190))
            desc_y += 27

        draw.line((x, 536, 1100, 536), fill=(72, 57, 94), width=1)
        draw.text((x, 553), "NEW FROM A SILVER HAIR", font=_font("sans", 14, bold=True), fill=(214, 215, 224))
        draw.text((1004, 553), "ASILVERHAIR.COM", font=_font("sans", 12, bold=True), fill=(132, 136, 151))

        filename = f"{number:03d}-{_slug(entry.get('slug') or title)}.png" if number else f"{_slug(title)}.png"
        path = self.og_dir / filename
        img.save(path, format="PNG", optimize=True)
        return f"/assets/og/{filename}"
